import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class LibraryRecommender:
    def __init__(self, data_path):
        self.data_path = data_path
        self.df = None
        self.tfidf_matrix = None
        self.cosine_sim = None
        self.indices = None
        self.unique_books = None

    def save_enhanced_data(self, output_path):
        if self.df is not None:
            self.df.to_csv(output_path, index=False)
            print(f"Saved enhanced data to {output_path}")

    def load_and_preprocess(self):
        try:
            print(f"Loading data from {self.data_path}...")
            self.df = pd.read_csv(self.data_path)

            # Clean columns
            self.df.columns = self.df.columns.str.strip()
            self.df = self.df.dropna(subset=['Title'])

            self.df['Title'] = self.df['Title'].astype(str).str.strip()
            self.df['Author'] = self.df['Author'].astype(str).str.strip()
            self.df['Copies'] = pd.to_numeric(
                self.df['Copies'], errors='coerce'
            ).fillna(0).astype(int)

            # 🚫 NO KEYWORD INFERENCE
            # Use Department ONLY if it already exists
            if 'Department' not in self.df.columns:
                print("Department column missing. Assigning 'General'")
                self.df['Department'] = 'General'
            else:
                self.df['Department'] = self.df['Department'].fillna('General')

            # Rating must exist
            if 'Rating' not in self.df.columns:
                print("Rating column missing. Assigning default rating 3.5")
                self.df['Rating'] = 3.5
            else:
                self.df['Rating'] = self.df['Rating'].fillna(3.5)

            print("Data loaded successfully.")
            return self.df

        except Exception as e:
            print(f"Error loading data: {e}")
            raise

    # ✅ TOP-50 PURELY BY DEPARTMENT + RATING
    def get_top_50_by_dept(self, dept_name):
        if self.df is None:
            raise ValueError("Data not loaded.")

        dept_books = self.df[self.df['Department'] == dept_name]

        if dept_books.empty:
            return pd.DataFrame()

        top_50 = (
            dept_books
            .groupby(['Title', 'Author'], as_index=False)
            .agg({'Rating': 'mean'})
            .sort_values(by='Rating', ascending=False)
            .head(50)
        )

        return top_50

    # ML PART (unchanged)
    def prepare_recommendation_model(self):
        if self.df is None:
            raise ValueError("Data not loaded.")

        tfidf = TfidfVectorizer(stop_words='english')
        self.unique_books = self.df.drop_duplicates(subset=['Title']).reset_index(drop=True)
        self.tfidf_matrix = tfidf.fit_transform(self.unique_books['Title'])
        self.cosine_sim = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)
        self.indices = pd.Series(
            self.unique_books.index,
            index=self.unique_books['Title']
        ).drop_duplicates()

        print("Recommendation model trained.")

    def recommend_books(self, title, top_n=5):
        if self.cosine_sim is None:
            self.prepare_recommendation_model()

        if title not in self.indices:
            return pd.DataFrame()

        idx = self.indices[title]
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n+1]
        book_indices = [i[0] for i in sim_scores]

        return (
            self.unique_books
            .iloc[book_indices][['Title', 'Author', 'Department', 'Rating']]
            .sort_values(by='Rating', ascending=False)
        )


if __name__ == "__main__":
    rec = LibraryRecommender("EG ACC REOPRT 2.csv")
    rec.load_and_preprocess()

    print("\n--- Top 50 Computer Science Books ---")
    print(rec.get_top_50_by_dept("Computer Science").head())
