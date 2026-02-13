from prisma import Prisma

# Central Prisma client used throughout the backend.
# Import this module as `from app.core.db import db`.

db = Prisma()


async def connect_db() -> None:
  """Open a connection to the database."""
  await db.connect()


async def disconnect_db() -> None:
  """Close the database connection."""
  await db.disconnect()

