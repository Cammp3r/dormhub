import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Завантажуємо змінні з .env
load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD")
        )
        return conn
    except Exception as e:
        print(f"Помилка підключення до бази даних: {e}")
        return None