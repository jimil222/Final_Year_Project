from recommender_system import LibraryRecommender
import time

def main():
    print("Welcome to the Library Recommendation System")
    print("------------------------------------------")
    
    import argparse
    import os
    
    # Construct absolute path to the data file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'enhanced_library_data.csv')
    
    # Check if data file exists
    if not os.path.exists(data_path):
        # Fallback for when running from different directories if needed, though abspath should handle it
        print(f"Warning: Data file not found at {data_path}")

    rec = LibraryRecommender(data_path)
    
    # Setup Argument Parser
    parser = argparse.ArgumentParser(description="Library Recommendation System")
    parser.add_argument("--dept", help="Get top 50 books for a specific department")
    parser.add_argument("--title", help="Get recommendations for a specific book title")
    
    args = parser.parse_args()

    # Pre-check data existence before loading heavy models if possible, 
    # but load_and_preprocess is needed for both modes.
    
    if args.dept or args.title:
        # CLI Mode
        try:
            # Suppress normal prints if desired, or keep them for logs
            rec.load_and_preprocess()
            
            if args.dept:
                print(f"--- Top 50 Books in {args.dept} ---")
                top_books = rec.get_top_50_by_dept(args.dept)
                if not top_books.empty:
                    print(top_books[['Title', 'Author', 'Copies', 'Rating']].to_string(index=False))
                else:
                    print("No books found for this department.")
            
            if args.title:
                print(f"--- Recommendations for '{args.title}' ---")
                # We need the model prepared for recommendations
                rec.prepare_recommendation_model()
                results = rec.recommend_books(args.title)
                if isinstance(results, list) and not results:
                    print("Book not found or no recommendations.")
                else:
                    print(results.to_string(index=False))
                    
        except Exception as e:
            print(f"Error: {e}")
        return

    # Interactive Mode (Default)
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
