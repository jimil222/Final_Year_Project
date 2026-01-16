# Library Recommendation System

A Python-based recommendation system designed to organize library data and provide book recommendations. This project compensates for missing metadata (like Department) using intelligent keyword inference and uses machine learning for content-based recommendations.

## Project Structure

- `main.py`: The user-friendly Command Line Interface (CLI) to interact with the system.
- `recommender_system.py`: The core logic containing the `LibraryRecommender` class.
- `EG ACC REOPRT 2.csv`: The source dataset containing book records.
- `verify_recommender.py`: Automated tests to verify system logic.

## Features

### 1. Top 50 Books by Department
Displays the most popular books within a specific engineering department.
- **Problem**: The original dataset lacked a 'Department' column.
- **Solution**: Implemented a **Rule-Based Inference Engine** in `recommender_system.py`. It scans book titles for keywords (e.g., "thermodynamics" -> "Mechanical Engineering", "concrete" -> "Civil Engineering") to categorize them automatically.
- **Ranking**: Books are ranked based on the number of `Copies` available/issued.

### 2. Content-Based Advice (Recommendation System)
Recommends similar books based on a given book title.
- **Algorithm Used**: **TF-IDF** (Term Frequency-Inverse Document Frequency) & **Cosine Similarity**.
- **How it works**:
    1.  **Text Vectorization**: The system uses `TfidfVectorizer` (from Scikit-Learn) to convert book titles into numerical vectors. This highlights unique and important words in titles while downplaying common words (stop words).
    2.  **Similarity Calculation**: It calculates the **Cosine Similarity** between these vectors. This measures the angle between two title vectors; a smaller angle implies higher similarity in content.
    3.  **Result**: When a user queries a book, the system finds the 5 closest vectors (most similar titles) and returns them.

## Setup & Installation

1.  **Prerequisites**:
    -   Python 3.x
    -   pip (Python package manager)

2.  **Install Dependencies**:
    ```bash
    pip install pandas scikit-learn
    ```

3.  **Run the Application**:
    ```bash
    python main.py
    ```

## Usage Logic

1.  **Initialization**:
    -   On startup, the system loads the CSV.
    -   It cleans column names and removes empty rows.
    -   It runs the inference engine to populate the 'Department' field.
    -   It trains the TF-IDF model on the unique book titles.

2.  **Interaction**:
    -   **Option 1**: Enter a department name (e.g., 'Computer Science', 'Civil Engineering') to see the top 50 books.
    -   **Option 2**: Enter a specific book title (exact match required) to get a list of 5 recommended books that are semantically similar.


## System Flow & Algorithms

### Feature 1: Top 50 Books by Department (How it works)
This feature identifies the "most popular" books in a specific field.

1.  **Input**: User selects a department (e.g., "Mechanical Engineering").
2.  **Filtering**: The system filters the dataset to keep only books where the `Department` column matches the input.
    -   *Note*: The `Department` column is created during loading by scanning titles for keywords (e.g., "thermodynamics" -> "Mechanical").
3.  **Aggregation**:
    -   Books are grouped by `Title` and `Author`.
    -   The system sums the `Copies` for each group to get the total number of copies available.
4.  **Ranking**: The list is sorted in **Descending Order** based on total copies.
5.  **Output**: The top 50 records are displayed.

### Feature 2: Recommendation System (How it works)
This feature suggests books that are content-wise similar to a book the user likes.

1.  **Preprocessing**:
    -   The system creates a list of unique book titles.
    -   It uses **TF-IDF Vectorizer** (Term Frequency-Inverse Document Frequency) to convert each title into a mathematical vector.
        -   *TF*: How often a word appears in a title.
        -   *IDF*: Reduces the weight of common words (like "Introduction", "Handbook") and boosts unique keywords (like "Robotics", "Quantum").
2.  **Model Training**:
    -   A **Cosine Similarity Matrix** is computed. This measures the angle between every pair of book vectors.
    -   Value ranges from 0 (completely different) to 1 (identical match).
3.  **Querying**:
    -   **Input**: User provides a book title (e.g., "Machine Design").
    -   **Lookup**: The system finds the index of this title in the matrix.
    -   **Scoring**: It retrieves the similarity scores of this book against all other books.
4.  **Ranking**:
    -   Scores are sorted in descending order.
    -   The top 5 books (excluding the input book itself) are selected.
5.  **Output**: The titles, authors, and departments of these 5 recommended books are displayed.

## Dependencies

-   `pandas`: For data manipulation and aggregation.
-   `scikit-learn`: For machine learning algorithms (TF-IDF, Linear Kernel).
-   `numpy`: For numerical operations.
