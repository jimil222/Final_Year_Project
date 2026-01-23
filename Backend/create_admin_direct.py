import asyncio
from prisma import Prisma
from app.security import get_password_hash

async def main():
    prisma = Prisma()
    await prisma.connect()

    try:
        # Check if admin exists
        count = await prisma.admin.count()
        print(f"Current admin count: {count}")
        
        if count > 0:
            print("Admin already exists. Delete existing admin first if you want to create a new one.")
            existing = await prisma.admin.find_first()
            print(f"Existing admin: {existing.name} ({existing.email})")
            return

        # Create Admin (without roll_no - admins don't have roll_no in new schema)
        admin = await prisma.admin.create(
            data={
                "name": "Library Admin",
                "email": "admin@library.com",
                "password": get_password_hash("admin123")
            }
        )
        print(f"✅ Admin created successfully!")
        print(f"   Name: {admin.name}")
        print(f"   Email: {admin.email}")
        print(f"   Password: admin123")
        print(f"\nYou can now login with:")
        print(f"   Email: admin@library.com")
        print(f"   Password: admin123")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await prisma.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
