import asyncio
import re
import json
import uuid
import random
import os
from prisma import Prisma

# Path to dummyBooks.js: same repo, frontend folder (relative to Backend/)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
DUMMY_BOOKS_PATH = os.path.join(_REPO_ROOT, "Libra_Automated_Library", "src", "data", "dummyBooks.js")

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

    # 1. Create Shelves (shelf_number is string in schema; need coordinate_x/y)
    print("Seeding Shelves...")
    for i in range(1, 11):
        sn = str(i)
        await prisma.shelf.upsert(
            where={"shelf_number": sn},
            data={
                "create": {"shelf_number": sn, "coordinate_x": i, "coordinate_y": 0},
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
        
        # Resolve shelf_id from shelf_number (1-10)
        shelf_num = str(random.randint(1, 10))
        shelf = await prisma.shelf.find_unique(where={"shelf_number": shelf_num})
        if not shelf:
            print(f"Shelf {shelf_num} not found, skipping '{title}'")
            continue
        shelf_id = int(shelf.shelf_id)

        try:
            existing = await prisma.book.find_first(where={"book_name": title})
            if existing:
                print(f"Skipping '{title}' (already exists)")
                continue

            await prisma.book.create(
                data={
                    "book_name": title,
                    "author": author,
                    "nfc_tag_id": nfc_id,
                    "shelf_id": shelf_id,
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
