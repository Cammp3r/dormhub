from psycopg2.extras import RealDictCursor

from db import get_db_connection


current_user = None


def _fetch_all(query, parameters=()):
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchall()
    finally:
        connection.close()


def _fetch_one(query, parameters=()):
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchone()
    finally:
        connection.close()


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
    return _fetch_one(
        """
        SELECT r.room_id, r.dorm_id, r.room_number, r.floor,
               d.dorm_number, d.address
        FROM rooms AS r
        INNER JOIN dorms AS d ON d.dorm_id = r.dorm_id
        WHERE r.room_id = %s
        """,
        (room_id,),
    )


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


def get_departments():
    return _fetch_all(
        """
        SELECT department_id, department_name
        FROM departments
        ORDER BY department_name
        """
    )


def get_enrollments(student_id=None):
    query = """
        SELECT e.enrollment_id, e.student_id, e.course_id,
               e.enrollment_date, e.grade,
               c.course_title, c.department_id, d.department_name
        FROM enrollments AS e
        INNER JOIN courses AS c ON c.course_id = e.course_id
        INNER JOIN departments AS d ON d.department_id = c.department_id
    """
    parameters = ()
    if student_id is not None:
        query += " WHERE e.student_id = %s"
        parameters = (student_id,)
    query += " ORDER BY e.enrollment_date DESC, e.enrollment_id"
    return _fetch_all(query, parameters)


def get_vacancies():
    return _fetch_all(
        """
        SELECT vacancy_id, company_name, job_name
        FROM vacancies
        ORDER BY vacancy_id
        """
    )


def get_applications(student_id=None):
    query = """
        SELECT a.application_id, a.student_id, a.vacancy_id,
               a.application_date, a.status,
               v.company_name, v.job_name
        FROM applications AS a
        INNER JOIN vacancies AS v ON v.vacancy_id = a.vacancy_id
    """
    parameters = ()
    if student_id is not None:
        query += " WHERE a.student_id = %s"
        parameters = (student_id,)
    query += " ORDER BY a.application_date DESC, a.application_id"
    return _fetch_all(query, parameters)


def get_parking_slots():
    return _fetch_all(
        """
        SELECT p.parking_slot_id, p.dorm_id, p.user_id, p.slot_number,
               u.first_name, u.last_name, d.dorm_number
        FROM parking_slots AS p
        INNER JOIN dorms AS d ON d.dorm_id = p.dorm_id
        LEFT JOIN users AS u ON u.user_id = p.user_id
        ORDER BY p.dorm_id, p.slot_number
        """
    )


def get_current_user():
    return get_user(1)
