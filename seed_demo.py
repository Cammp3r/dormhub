"""Додавання тестових студентів у гуртожиток адміністратора."""
from psycopg2 import Error as DatabaseError

from db import get_db_connection


DEMO_RESIDENTS = (
    ("Демо", "Студент", "demo.student@example.com", "2003-04-12", 2022),
    ("Тест", "Мешканець", "test.resident@example.com", "2004-09-21", 2023),
    ("Анна", "Коваль", "anna.koval@example.com", "2002-11-08", 2021),
)


def seed_demo_residents():
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT da.dorm_id
                    FROM dorm_admins AS da
                    ORDER BY da.admin_id
                    LIMIT 1
                    """
                )
                dorm = cursor.fetchone()
                if dorm is None:
                    raise RuntimeError("Спочатку створіть адміністратора через setup_admin.py")
                dorm_id = dorm[0]

                for first_name, last_name, email, birth_date, enrollment_year in DEMO_RESIDENTS:
                    cursor.execute(
                        """
                        INSERT INTO users
                            (first_name, last_name, email, date_of_birth, dorm_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (email) DO NOTHING
                        RETURNING user_id
                        """,
                        (first_name, last_name, email, birth_date, dorm_id),
                    )
                    user = cursor.fetchone()
                    if user is None:
                        cursor.execute(
                            "SELECT user_id FROM users WHERE email = %s",
                            (email,),
                        )
                        user = cursor.fetchone()
                    cursor.execute(
                        """
                        INSERT INTO students (user_id, enrollment_year)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id) DO NOTHING
                        """,
                        (user[0], enrollment_year),
                    )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def main():
    try:
        seed_demo_residents()
    except (RuntimeError, DatabaseError) as error:
        print(f"Не вдалося додати тестових мешканців: {error}")
        return 1
    print("Тестових мешканців додано або вони вже існують.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
