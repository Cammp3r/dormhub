from psycopg2.extras import RealDictCursor

from db import get_db_connection
from data import mock_data as db


current_user = None


def get_user(user_id):
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT user_id, first_name, last_name, email, date_of_birth,
                       registration_date, status, dorm_id
                FROM users
                WHERE user_id = %s
                """,
                (user_id,),
            )
            return cursor.fetchone()
    finally:
        connection.close()


def get_all_users():
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT user_id, first_name, last_name, email, date_of_birth,
                       registration_date, status, dorm_id
                FROM users
                ORDER BY user_id
                """
            )
            return cursor.fetchall()
    finally:
        connection.close()


def get_student_for_user(user_id):
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT student_id, enrollment_year, room_id, status, user_id
                FROM students
                WHERE user_id = %s
                """,
                (user_id,),
            )
            return cursor.fetchone()
    finally:
        connection.close()


def get_user_name(user):
    return f"{user['first_name']} {user['last_name']}"


def update_profile(user_id, first_name, last_name, email):
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET first_name = %s, last_name = %s, email = %s
                WHERE user_id = %s
                """,
                (first_name, last_name, email, user_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Користувача з user_id={user_id} не знайдено")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_room_info(room_id):
    room = next((room for room in db.rooms if room["room_id"] == room_id), None)
    if room is None:
        return None
    dorm = next(dorm for dorm in db.dorms if dorm["dorm_id"] == room["dorm_id"])
    return {**room, "dorm_number": dorm["dorm_number"], "address": dorm["address"]}


def get_roommates(room_id):
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT u.user_id, u.first_name, u.last_name, u.email,
                       u.date_of_birth, u.registration_date, u.status, u.dorm_id
                FROM users AS u
                INNER JOIN students AS s ON s.user_id = u.user_id
                WHERE s.room_id = %s
                ORDER BY u.user_id
                """,
                (room_id,),
            )
            return cursor.fetchall()
    finally:
        connection.close()


def is_dorm_admin(user_id):
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM dorm_admins WHERE user_id = %s LIMIT 1",
                (user_id,),
            )
            return cursor.fetchone() is not None
    finally:
        connection.close()


def get_current_user():
    return get_user(1)
