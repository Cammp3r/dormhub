import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_database_settings():
    return {
        "host": os.environ.get("DB_HOST"),
        "port": os.environ.get("DB_PORT"),
        "database": os.environ.get("DB_NAME"),
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
    }


def get_db_connection():
    try:
        return psycopg2.connect(**get_database_settings())
    except Exception as error:
        print(f"Помилка підключення до бази даних: {error}")
        return None
