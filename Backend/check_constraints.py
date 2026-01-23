import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Parse DATABASE_URL
url = os.getenv("DATABASE_URL")  # mysql://user:password@host:port/database
parts = url.replace("mysql://", "").split("@")
user_pass = parts[0].split(":")
host_db = parts[1].split("/")
host_port = host_db[0].split(":")

connection = pymysql.connect(
    host=host_port[0],
    port=int(host_port[1]) if len(host_port) > 1 else 3306,
    user=user_pass[0],
    password=user_pass[1],
    database=host_db[1]
)

cursor = connection.cursor()

# Get foreign keys on books table
cursor.execute("""
    SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'Libra' AND TABLE_NAME = 'books' AND REFERENCED_TABLE_NAME IS NOT NULL
""")

print("Foreign Keys on books table:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} -> {row[2]}.{row[3]}")

cursor.close()
connection.close()
