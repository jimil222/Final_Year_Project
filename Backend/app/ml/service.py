import os
from app.ml.recommender_system import LibraryRecommender

# Global instance
_recommender = None

def get_recommender():
    global _recommender
    if _recommender is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_dir, "data.csv")
        _recommender = LibraryRecommender(data_path)
        print("Loading Recommendation Model data...")
        _recommender.load_and_preprocess()
        # Optionally prepare model if we strongly need Feature 2 (book to book) immediately
        # _recommender.prepare_recommendation_model() 
    return _recommender
