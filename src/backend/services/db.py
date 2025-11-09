# backend/services/db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "apex")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

# Dependency for FastAPI
async def get_db():
    return db

# Example: User auth collection
async def get_user(username: str):
    return await db.users.find_one({"username": username})

async def create_user(username: str, hashed_password: str):
    user = {"username": username, "password": hashed_password, "portfolio": []}
    await db.users.insert_one(user)
    return user

async def get_user_portfolio(user_id: str):
    user = await db.users.find_one({"_id": user_id})
    return user.get("portfolio", []) if user else []
