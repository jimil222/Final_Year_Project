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
        self.lower_indices = None
        self.unique_books = None

    # ===============================
    # Load & Preprocess Data
    # ===============================
    def load_and_preprocess(self):
        print(f"Loading data from {self.data_path}...")
        self.df = pd.read_csv(self.data_path)

        self.df.columns = self.df.columns.str.strip()
        self.df = self.df.dropna(subset=['Title'])

        self.df['Title'] = self.df['Title'].astype(str).str.strip()
        self.df['Author'] = self.df['Author'].astype(str).str.strip()

        # Copies kept for reference only
        self.df['Copies'] = pd.to_numeric(
            self.df.get('Copies', 0),
            errors='coerce'
        ).fillna(0).astype(int)

        if 'Department' not in self.df.columns:
            self.df['Department'] = 'General'
        else:
            self.df['Department'] = self.df['Department'].fillna('General')

        if 'Rating' not in self.df.columns:
            self.df['Rating'] = 3.5
        else:
            self.df['Rating'] = self.df['Rating'].fillna(3.5)

        print("Data loaded successfully.")
        return self.df

    # ===============================
    # POPULARITY-BASED (RATING ONLY)
    # + DETERMINISTIC RANDOM 10
    # ===============================
    def get_top_50_by_dept(self, dept_name, sample_n=9):
        if self.df is None:
            raise ValueError("Data not loaded.")

        dept_books = self.df[self.df['Department'] == dept_name]

        if dept_books.empty:
            return pd.DataFrame()

        top_50 = (
            dept_books
            .groupby(['Title', 'Author', 'Department'], as_index=False)
            .agg({'Rating': 'mean'})
            .sort_values(by='Rating', ascending=False)
            .head(50)
        )

        # 🔒 Stable random selection
        if len(top_50) > sample_n:
            return top_50.sample(
                n=sample_n,
                random_state=42  # SAME RESULT EVERY TIME
            )

        return top_50

    # ===============================
    # CONTENT-BASED MODEL
    # ===============================
    def prepare_recommendation_model(self):
        if self.df is None:
            raise ValueError("Data not loaded.")

        self.unique_books = (
            self.df
            .drop_duplicates(subset=['Title'])
            .reset_index(drop=True)
        )

        self.unique_books['content'] = (
            self.unique_books['Title'] + " " +
            self.unique_books['Author'] + " " +
            self.unique_books['Department']
        )

        tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = tfidf.fit_transform(self.unique_books['content'])
        self.cosine_sim = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)

        self.indices = pd.Series(
            self.unique_books.index,
            index=self.unique_books['Title']
        ).drop_duplicates()

        self.lower_indices = pd.Series(
            self.unique_books.index,
            index=self.unique_books['Title'].str.lower()
        ).drop_duplicates()

        print("Content-based recommendation model trained.")

    # ===============================
    # CONTENT-BASED RECOMMENDATION
    # ===============================
    def recommend_books(self, title, top_n=4):
        if self.cosine_sim is None:
            self.prepare_recommendation_model()

        idx = None
        if title in self.indices:
            idx = self.indices[title]
        elif title.lower() in self.lower_indices:
            idx = self.lower_indices[title.lower()]

        if idx is None:
            return pd.DataFrame()

        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n+1]
        book_indices = [i[0] for i in sim_scores]

        return (
            self.unique_books
            .iloc[book_indices][['Title', 'Author', 'Department', 'Rating']]
            .sort_values(by='Rating', ascending=False)
        )


# ===============================
# MAIN EXECUTION
# ===============================
if __name__ == "__main__":
    recommender = LibraryRecommender("EG ACC REOPRT 2.csv")
    recommender.load_and_preprocess()

    print("\n--- Random 10 Books from Top 50 (Stable) ---")
    print(recommender.get_top_50_by_dept("Computer Science"))

    print("\n--- Content-Based Recommendations ---")
    print(recommender.recommend_books("Introduction to Algorithms"))
