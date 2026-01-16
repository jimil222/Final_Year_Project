from recommender_system import LibraryRecommender
import time

def main():
    print("Welcome to the Library Recommendation System")
    print("------------------------------------------")
    
    # Use the enhanced data by default if available
    data_path = 'enhanced_library_data.csv'
    # Fallback check could be added, but for now we assume it exists as we just created it.
    
    rec = LibraryRecommender(data_path)
    
    print("\nPlease wait, loading data and analyzing titles...")
    try:
        rec.load_and_preprocess()
        print("Data Loaded Successfully!")
        print("Training Recommendation Model...")
        rec.prepare_recommendation_model()
        print("Model Ready!\n")
    except Exception as e:
        print(f"Failed to initialize system: {e}")
        return

    while True:
        print("\nSelect an option:")
        print("1. Show Top 50 Books by Department")
        print("2. Get Book Recommendations")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            print("\nAvailable Departments:")
            print("- Mechanical Engineering")
            print("- Civil Engineering")
            print("- Electrical Engineering")
            print("- Computer Science")
            print("- Electronics")
            print("- Mathematics")
            print("- Physics")
            print("- Chemistry")
            print("- General")
            
            dept = input("\nEnter Department Name (e.g., 'Computer Science'): ")
            
            print(f"\n--- Top 50 Books in {dept} ---")
            top_books = rec.get_top_50_by_dept(dept)
            
            if not top_books.empty:
                # Print nicely
                print(top_books[['Title', 'Author', 'Copies', 'Rating']].to_string(index=False))
            else:
                print("No books found for this department or department name incorrect.")
                
        elif choice == '2':
            title = input("\nEnter a Book Title to get recommendations: ")
            print(f"\nFinding recommendations for '{title}'...")
            
            results = rec.recommend_books(title)
            
            if isinstance(results, list) and not results:
                print("Book not found in database or no recommendations available.")
            else:
                print("\nRecommended Books:")
                print(results.to_string(index=False))
                
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
