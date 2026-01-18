import os
import sys

# Add project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from Recommendation_Model.recommender_system import LibraryRecommender

# Singleton instance
_recommender = None

def get_recommender():
    global _recommender

    if _recommender is None:
        data_path = os.path.join(
            project_root,
            "Recommendation_Model",
            "enhanced_library_data.csv"
        )

        if not os.path.exists(data_path):
            raise FileNotFoundError(f"❌ Data file not found: {data_path}")

        print("🔄 Initializing LibraryRecommender (Top-50 only)...")

        rec = LibraryRecommender(data_path)
        rec.load_and_preprocess()   # ✅ REQUIRED

        # ✅ PREPARE TF-IDF for similar books recommendation
        print("🧠 Training Recommendation Model (TF-IDF)...")
        rec.prepare_recommendation_model()

        _recommender = rec

        print("✅ Recommender ready for Top-50 AND Similar Books")

    return _recommender
