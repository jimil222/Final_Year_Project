import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    await db.connect()

    books = [
        # AI & Data Science
        {"book_name": "Artificial Intelligence: A Modern Approach", "author": "Stuart Russell", "department": "AI & Data Science"},
        {"book_name": "Deep Learning", "author": "Ian Goodfellow", "department": "AI & Data Science"},
        {"book_name": "Pattern Recognition and Machine Learning", "author": "Christopher Bishop", "department": "AI & Data Science"},
        
        # Computer Science
        {"book_name": "Clean Code", "author": "Robert C. Martin", "department": "Computer Science"},
        {"book_name": "Introduction to Algorithms", "author": "Thomas H. Cormen", "department": "Computer Science"},
        {"book_name": "Design Patterns", "author": "Erich Gamma", "department": "Computer Science"},
        
        # Other
        {"book_name": "The Pragmatic Programmer", "author": "Andrew Hunt", "department": "Other"},
        {"book_name": "Physics for Scientists", "author": "Serway", "department": "Physics"},
    ]

    print("Seeding books...")
    for book in books:
        # Check if exists
        exists = await db.book.find_first(where={"book_name": book["book_name"]})
        if not exists:
            # Note: book_name is mapped to title in our Prisma Schema if we checked carefully? 
            # In schema.prisma I defined: book_name String
            # So we use book_name here.
            await db.book.create(data=book)
            print(f"Created: {book['book_name']}")
        else:
            print(f"Skipped (exists): {book['book_name']}")

    await db.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
