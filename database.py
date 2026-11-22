import sqlite3
import os
import pymongo
from dotenv import load_dotenv

load_dotenv()

def init_sqlite_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT NOT NULL,
                      customer_id TEXT NOT NULL UNIQUE,
                      gender TEXT NOT NULL,
                      age INTEGER NOT NULL,
                      password_hash TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def get_mongo_collection():
    client = pymongo.MongoClient(os.environ["MONGODB_URI"])
    db = client["shopping_db"]
    return db["shopping_data"]