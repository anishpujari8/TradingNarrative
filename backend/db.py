"""MongoDB connection (Motor async client)."""
import os
import config  # noqa: F401  — ensures .env is loaded before we read env vars
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
