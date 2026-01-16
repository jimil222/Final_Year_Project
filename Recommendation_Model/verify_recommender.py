from Recommendation_Model.recommender_system import LibraryRecommender

def test_recommender():
    print("Initializing Recommender...")
    rec = LibraryRecommender('enhanced_library_data.csv')
    rec.load_and_preprocess()
    
    # Test 1: Rating Logic
    print("\n[Test 1] Testing Quality Rating...")
    # Manual check for specific authors/titles
    # 1. High Quality Author
    high_q = rec.df[rec.df['Author'].str.contains('Kanetkar', na=False, case=False)].iloc[0]
    print(f"High Quality Author (Kanetkar): {high_q['Title']} -> Rating: {high_q['Rating']} (Expected > 4.5)")
    
    # 2. Handbook
    handbook = rec.df[rec.df['Title'].str.contains('Handbook', na=False, case=False)].iloc[0]
    print(f"Handbook Title: {handbook['Title']} -> Rating: {handbook['Rating']} (Expected > 4.0)")
    
    # 3. Standard
    standard = rec.df[~rec.df['Author'].str.contains('Kanetkar', na=False) & ~rec.df['Title'].str.contains('Handbook', na=False)].iloc[0]
    print(f"Standard Book: {standard['Title']} -> Rating: {standard['Rating']} (Expected ~3.5)")

    # Test 2: Top 50 Sorting
    print("\n[Test 2] Top 50 Output...")
    top_50 = rec.get_top_50_by_dept("Computer Science")
    if 'Rating' in top_50.columns:
        print("PASS: Rating column present in Top 50.")
        print(top_50[['Title', 'Rating']].head())
    else:
        print("FAIL: Rating column missing.")

    # Test 3: Recommendations Sorting
    print("\n[Test 3] Recommendations Sorting...")
    rec.prepare_recommendation_model()
    recs = rec.recommend_books("Machine design data book")
    print(recs[['Title', 'Rating']])
    
    # Check if sorted by rating
    ratings = recs['Rating'].tolist()
    if ratings == sorted(ratings, reverse=True):
        print("PASS: Recommendations sorted by Rating descending.")
    else:
        print("FAIL: Recommendations NOT sorted by Rating.")

if __name__ == "__main__":
    test_recommender()
