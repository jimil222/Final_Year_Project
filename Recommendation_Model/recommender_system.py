import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import re

class LibraryRecommender:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.tfidf_matrix = None
        self.cosine_sim = None
        self.indices = None

    def save_enhanced_data(self, output_path):
        """Saves the processed dataframe with new columns to a CSV file."""
        if self.df is not None:
            self.df.to_csv(output_path, index=False)
            print(f"Saved enhanced data to {output_path}")
        else:
            print("No data to save. Load data first.")

    def load_and_preprocess(self):
        """Loads data and infers departments."""
        try:
            # Load data
            print(f"Loading data from {self.data_path}...")
            self.df = pd.read_csv(self.data_path)
            
            # Clean column names
            self.df.columns = self.df.columns.str.strip()
            
            # Drop rows with missing titles
            self.df = self.df.dropna(subset=['Title'])
            
            # Clean Title and Author
            self.df['Title'] = self.df['Title'].astype(str).str.strip()
            self.df['Author'] = self.df['Author'].astype(str).str.strip()
            
            # Convert Copies to numeric, coercing errors to 0
            self.df['Copies'] = pd.to_numeric(self.df['Copies'], errors='coerce').fillna(0).astype(int)

            # Check if we already have the enhanced columns
            if 'Department' in self.df.columns and 'Rating' in self.df.columns:
                print("Detected pre-processed dataset. Skipping inference.")
                # Ensure no NaNs in important columns
                self.df['Department'] = self.df['Department'].fillna('General')
                self.df['Rating'] = self.df['Rating'].fillna(3.5)
            else:
                # Infer Department
                print("Inferring departments...")
                self.df['Department'] = self.df['Title'].apply(self._infer_department)
                
                # Fill unknown departments
                self.df['Department'] = self.df['Department'].fillna('General')

                # Calculate Quality Rating
                print("Calculating quality ratings...")
                self.df['Rating'] = self.df.apply(self._calculate_quality_rating, axis=1)
            
            print("Data loaded successfully.")
            return self.df
            
        except Exception as e:
            print(f"Error in data loading: {e}")
            raise e

    def _calculate_quality_rating(self, row):
        """
        Calculates a deterministic quality rating (1.0 - 5.0) based on:
        1. Author Reputation (High impact factor)
        2. Title Keywords (Handbook, Reference, etc.)
        3. Popularity (Copies count as a minor boost)
        """
        rating = 3.5 # Base rating for standard academic books
        
        # 1. Author Reputation Boost
        # Top authors identified in dataset
        top_authors = [
            'Kanetkar Yashavant P', 'Silberschatz Abraham', 'Stallings William', 
            'Tanenbaum Andrew S', 'Balagurusamy E', 'Baphana R M', 'Sinha Pradeep K', 
            'Forouzan Behrouz A', 'Bhatt N D', 'Horowitz Ellis', 'Haykin Simon', 
            'Floyd Thomas L', 'Katre J S', 'Aho Alfred V', 'Nag P K', 
            'Theraja B L', 'Pressman Roger S', 'Mazidi Muhammad Ali', 
            'Rajput R K', 'Choudhury S K Hajra', 'Timoshenko', 'Kothari'
        ]
        
        author = str(row['Author'])
        # Check partial match for authors (e.g. 'Nag P K' in 'Nag P K & ...')
        for top_auth in top_authors:
            if top_auth.lower() in author.lower():
                rating += 1.3 # Big boost for legends -> 4.8
                break
        
        # 2. Title Keyword Boost
        title_lower = str(row['Title']).lower()
        high_quality_keywords = ['handbook', 'encyclopedia', 'bible', 'fundamental', 'principle', 'reference', 'data book']
        
        for key in high_quality_keywords:
            if key in title_lower:
                rating += 0.5
                break
                
        # 3. Popularity Boost (Copies)
        copies = row['Copies']
        if copies > 10:
            rating += 0.2
        elif copies > 5:
            rating += 0.1
            
        # Cap at 5.0
        return min(round(rating, 1), 5.0)

    def _infer_department(self, title):
        """Heuristic to infer department from book title."""
        title_lower = title.lower()
        
        keywords = {
            'Computer Science': ['computer', 'programming', 'software', 'network', 'c++', 'java', 'algorithm', 'data structure', 'python', 'vls', 'cloud', 'cyber', 'web', 'database', 'simulation', 'computing'],
            'Civil Engineering': ['civil', 'building', 'structure', 'concrete', 'surveying', 'fluid', 'hydrology', 'soil', 'construction', 'environmental', 'water resource', 'transportation'],
            'Mechanical Engineering': ['mechanic', 'machine', 'thermodynamics', 'fluid', 'heat transfer', 'manufacturing', 'robotics', 'automobile', 'internal combustion', 'refrigeration', 'mechatronics', 'welding', 'casting', 'metal'],
            'Electrical Engineering': ['electric', 'circuit', 'power system', 'control system', 'transformer', 'motor', 'generator', 'voltage', 'signal', 'transmission'],
            'Electronics': ['electronic', 'digital', 'signal processing', 'communication', 'microprocessor', 'semiconductor', 'analog'],
            'Mathematics': ['mathematics', 'calculus', 'algebra', 'statistics', 'probability', 'geometry', 'numerical'],
            'Physics': ['physics', 'quantum', 'optical', 'laser', 'electromagnetic'],
            'Chemistry': ['chemistry', 'chemical', 'polymer', 'organic', 'inorganic'],
        }
        
        # Priority mapping (some keywords are ambiguous)
        # 'fluid' appears in both Civil and Mechanical. We can check if specific engineer words exist.
        
        for dept, keys in keywords.items():
            for key in keys:
                if key in title_lower:
                    return dept
        
        return 'General'

    def get_top_50_by_dept(self, dept_name):
        """Returns top 50 books for a given department based on Copies."""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_and_preprocess() first.")
        
        dept_books = self.df[self.df['Department'] == dept_name]
        
        if dept_books.empty:
            return pd.DataFrame() # Return empty if no books found
            
        # Group by Title (and Author to be safe) and sum copies, take max rating (it should be same/similar)
        popular = dept_books.groupby(['Title', 'Author']).agg({'Copies': 'sum', 'Rating': 'mean'}).reset_index()
        
        # Sort by Copies descending
        top_50 = popular.sort_values(by='Copies', ascending=False).head(50)
        
        return top_50

    def prepare_recommendation_model(self):
        """Prepares TF-IDF matrix and similarity matrix."""
        print("Training recommendation model...")
        if self.df is None:
            raise ValueError("Data not loaded.")
            
        # Create TF-IDF matrix
        tfidf = TfidfVectorizer(stop_words='english')
        # Using a subset of data if it's too large, but 18k rows should be fine for local machine usually. 
        # However, to be safe and avoid MemoryError on typical laptops if the content is huge, we will deduplicate titles first for recommendation map.
        # Recommendation is typically "If you like Book A, read Book B".
        # So we should build similarity between unique titles.
        
        self.unique_books = self.df.drop_duplicates(subset=['Title']).reset_index(drop=True)
        
        self.tfidf_matrix = tfidf.fit_transform(self.unique_books['Title'])
        
        # Compute Cosine Similarity
        self.cosine_sim = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)
        
        # Valid indices mapping
        self.indices = pd.Series(self.unique_books.index, index=self.unique_books['Title']).drop_duplicates()
        print("Model trained.")

    def recommend_books(self, title, top_n=5):
        """Recommends books similar to the given title."""
        if self.cosine_sim is None:
            self.prepare_recommendation_model()
            
        # Clean title input
        title = title.strip()
        
        if title not in self.indices:
            return [] # Title not found
            
        idx = self.indices[title]
        
        # If there are duplicates for the same title, indices[title] might return a Series. Take the first one.
        if isinstance(idx, pd.Series):
            idx = idx.iloc[0]
            
        # Get pairwise similarity scores
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        
        # Sort based on similarity
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get scores of top n most similar (ignoring self at 0)
        sim_scores = sim_scores[1:top_n+1]
        
        movie_indices = [i[0] for i in sim_scores]
        
        recommendations = self.unique_books[['Title', 'Author', 'Department', 'Rating']].iloc[movie_indices].copy()
        
        # Sort recommendations by Rating to show "Best" similar books first
        recommendations = recommendations.sort_values(by='Rating', ascending=False)
        
        return recommendations

# Basic usage example if run directly
if __name__ == "__main__":
    rec = LibraryRecommender('EG ACC REOPRT 2.csv')
    rec.load_and_preprocess()
    
    # Test Dept Logic
    print("\nSample Departments:")
    print(rec.df[['Title', 'Department']].head(10))
    
    # Feature 1
    print("\n--- Feature 1: Top 50 Computer Science Books ---")
    top_cs = rec.get_top_50_by_dept('Computer Science')
    print(top_cs.head())

    # Feature 2
    rec.prepare_recommendation_model() # Build model
    
    # Pick a random title to recommend
    sample_title = rec.df['Title'].iloc[0]
    print(f"\n--- Feature 2: Recommendations for '{sample_title}' ---")
    recommendations = rec.recommend_books(sample_title)
    print(recommendations)
