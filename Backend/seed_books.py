import asyncio
import re
import json
import uuid
import random
from prisma import Prisma

# Raw content of dummyBooks.js (simplified for embedding or reading from file)
# In a real scenario, we might parse the file, but here I'll embed the logic to read it or just copy the data if it's small.
# The user said "Iterates through the dummyBooks array", implying I should read the file or use the provided data.
# I will read the file from disk to be robust.

DUMMY_BOOKS_PATH = r"C:\Users\Dell\Desktop\Recommend\Libra_Automated_Library\src\data\dummyBooks.js"

def parse_dummy_books(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # regex to find the array content. 
    # Looks for "export const dummyBooks = [" ... "];"
    match = re.search(r"export const dummyBooks = \[\s*(.*)\s*\];", content, re.DOTALL)
    if not match:
        print("Could not find dummyBooks array in file.")
        return []
    
    array_content = match.group(1)
    
    # This is JS object syntax, not strict JSON (keys aren't quoted).
    # We need to make it JSON-compliant or parse manually.
    # Simple strategy: Use regex to quote keys and remove trailing commas.
    
    # 1. Remove comments // ...
    array_content = re.sub(r"//.*", "", array_content)
    
    # 2. Quote keys: { key: -> { "key":
    # Identify keys: start of line or after comma/brace, word chars, followed by colon
    # This is tricky. Let's try a simpler approach if the data structure is known.
    # Or just evaluate it using node? No, stick to python.
    # Let's clean it up manually with specific regexes for this known file format.
    
    objects = []
    # split by objects
    # This is fragile. 
    # Alternative: The user provided the data in the "view_file" output. 
    # I can just hardcode the data in this script since it's "one-off" seed script 
    # and the source is "dummy book data". 
    # However, "Iterates through the dummyBooks array" suggests using the source.
    # Let's try to verify if I can just import the data if I convert it.
    # I'll rely on a robust regex replacement for known keys.
    
    clean_json = array_content
    # keys: id, book_id, title, author, bin_id, status, reserved_by, genre, created_at
    keys = ["id", "book_id", "title", "author", "bin_id", "status", "reserved_by", "genre", "created_at"]
    for key in keys:
        clean_json = re.sub(r'\b' + key + r':', f'"{key}":', clean_json)
    
    # Quote single quoted values
    clean_json = clean_json.replace("'", '"')
    
    # Remove trailing commas
    clean_json = re.sub(r',\s*}', '}', clean_json)
    clean_json = re.sub(r',\s*]', ']', clean_json)
    
    # Wrap in brackets because we extracted the inside
    clean_json = f"[{clean_json}]"
    
    try:
        data = json.loads(clean_json)
        return data
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print("Falling back to manual extraction or hardcoded list if needed.")
        return []

async def main():
    prisma = Prisma()
    await prisma.connect()

    print("Connected to database.")

    # 1. Create Shelves
    # We need shelves to link books to.
    print("Seeding Shelves...")
    for i in range(1, 11): # Create 10 shelves
        await prisma.shelf.upsert(
            where={"shelf_number": i},
            data={
                "create": {"shelf_number": i},
                "update": {},
            }
        )
    print("Shelves seeded.")

    # 2. Parse Books
    books_data = parse_dummy_books(DUMMY_BOOKS_PATH)
    if not books_data:
        print("No books found to seed.")
        return

    print(f"Found {len(books_data)} books to seed.")

    # 3. Seed Books
    for book in books_data:
        # Map fields
        # - book_name -> title
        # - author -> author
        # - status -> AVAILABLE (ignore source status if we want fresh state, or map it. User said "status -> AVAILABLE")
        # - nfc_tag_id -> RANDOM unique string
        # - shelf_number -> RANDOM valid shelf number
        
        # Validation
        title = book.get("title")
        author = book.get("author")
        
        if not title:
            continue

        # Generate NFC ID
        nfc_id = f"NFC-{uuid.uuid4().hex[:8].upper()}"
        
        # Random Shelf (1-10)
        shelf_num = random.randint(1, 10)
        
        # Insert
        try:
            # We don't have a unique key other than ID and NFC. 
            # If we want to avoid duplicates on re-run, we might check by title?
            # Or just create always. User said "Skips duplicates safely if script is re-run".
            # If we don't have a unique constraint on title via schema, we can't easily "skip" unless we query first.
            # But book_name is NOT unique in schema.
            # So "duplicates" might mean "exact same book".
            # Let's check via nfc_tag_id (which is unique).
            # Taking a simpler approach: check if a book with this title exists? 
            # Or just assume "nfc_id" generation makes them unique and just insert.
            # "Skips duplicates safely" usually implies idempotent.
            # Since nfc is random, every run inserts new copies.
            # To be safe/idempotent, maybe identifying by generated NFC is impossible.
            # Identifying by Title:
            existing = await prisma.book.find_first(where={"book_name": title})
            if existing:
                print(f"Skipping '{title}' (already exists)")
                continue

            await prisma.book.create(
                data={
                    "book_name": title,
                    "author": author,
                    "nfc_tag_id": nfc_id,
                    "shelf_number": shelf_num,
                    "status": "AVAILABLE"
                }
            )
            print(f"Seeded '{title}'")
            
        except Exception as e:
            print(f"Failed to seed '{title}': {e}")

    await prisma.disconnect()
    print("Seeding completed.")

if __name__ == "__main__":
    asyncio.run(main())
