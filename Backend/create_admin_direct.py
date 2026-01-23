import asyncio
from prisma import Prisma
from app.security import get_password_hash

async def main():
    prisma = Prisma()
    await prisma.connect()

    try:
        # Check if admin exists
        count = await prisma.admin.count()
        if count > 0:
            print("Admin already exists.")
            return

        # Create Admin
        admin = await prisma.admin.create(
            data={
                "name": "Admin User",
                "email": "admin@library.edu",
                "roll_no": "ADMIN001",
                "password": get_password_hash("password123")
            }
        )
        print(f"Admin created: {admin.name} ({admin.email})")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
