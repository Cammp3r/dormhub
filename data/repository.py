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
    return current_user


def login(first_name, last_name):
    global current_user
    current_user = None
    first_name, last_name = first_name.strip(), last_name.strip()
    if not first_name or not last_name:
        raise ValueError("Введіть ім’я та прізвище")
    if len(first_name) > 50 or len(last_name) > 50:
        raise ValueError("Ім’я та прізвище мають містити до 50 символів")
    users = _fetch_all(
        """
        SELECT user_id, first_name, last_name, email, date_of_birth,
               registration_date, status, dorm_id
        FROM users
        WHERE lower(first_name) = lower(%s) AND lower(last_name) = lower(%s)
        LIMIT 2
        """,
        (first_name, last_name),
    )
    if not users:
        raise ValueError("Користувача з таким ім’ям та прізвищем не знайдено")
    if len(users) > 1:
        raise ValueError("Знайдено кілька акаунтів із цим ім’ям та прізвищем. Зверніться до адміністратора.")
    if users[0]["status"] != "active":
        raise ValueError("Цей акаунт заблоковано")
    current_user = users[0]
    return current_user


def logout():
    global current_user
    current_user = None


def get_room_chats_for_user(user_id):
    return _fetch_all(
        """
        SELECT rc.room_chat_id AS id,
               'Кімната ' || r.room_number AS title,
               TRUE AS is_group,
               (
                   SELECT rcm.sent_at
                   FROM room_chat_messages AS rcm
                   WHERE rcm.room_chat_id = rc.room_chat_id
                   ORDER BY rcm.sent_at DESC, rcm.message_id DESC
                   LIMIT 1
               ) AS last_sent_at,
               (
                   SELECT rcm.message
                   FROM room_chat_messages AS rcm
                   WHERE rcm.room_chat_id = rc.room_chat_id
                   ORDER BY rcm.sent_at DESC, rcm.message_id DESC
                   LIMIT 1
               ) AS last_message
        FROM room_chats AS rc
        INNER JOIN rooms AS r ON r.room_id = rc.room_id
        INNER JOIN students AS s ON s.room_id = r.room_id
        WHERE s.user_id = %s
        ORDER BY r.dorm_id, r.room_number
        """,
        (user_id,),
    )


def get_room_chat_members(chat_id, user_id):
    return _fetch_all(
        """
        SELECT u.user_id, u.first_name, u.last_name, u.email
        FROM users AS u
        INNER JOIN students AS s ON s.user_id = u.user_id
        INNER JOIN room_chats AS rc ON rc.room_id = s.room_id
        WHERE rc.room_chat_id = %s
          AND EXISTS (
              SELECT 1
              FROM students AS current_student
              INNER JOIN room_chats AS current_chat
                  ON current_chat.room_id = current_student.room_id
              WHERE current_student.user_id = %s
                AND current_chat.room_chat_id = rc.room_chat_id
          )
        ORDER BY u.user_id
        """,
        (chat_id, user_id),
    )


def get_room_chat_messages(chat_id, user_id):
    return _fetch_all(
        """
        SELECT rcm.message_id, rcm.user_id AS author_id, rcm.message AS text,
               rcm.sent_at,
               u.first_name || ' ' || u.last_name AS author_name
        FROM room_chat_messages AS rcm
        INNER JOIN users AS u ON u.user_id = rcm.user_id
        WHERE rcm.room_chat_id = %s
          AND EXISTS (
              SELECT 1
              FROM students AS current_student
              INNER JOIN room_chats AS current_chat
                  ON current_chat.room_id = current_student.room_id
              WHERE current_student.user_id = %s
                AND current_chat.room_chat_id = rcm.room_chat_id
          )
        ORDER BY rcm.sent_at, rcm.message_id
        """,
        (chat_id, user_id),
    )


def send_room_chat_message(chat_id, user_id, text):
    text = text.strip()
    if not text:
        raise ValueError("Повідомлення не може бути порожнім")

    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO room_chat_messages (room_chat_id, user_id, message)
                SELECT rc.room_chat_id, %s, %s
                FROM room_chats AS rc
                INNER JOIN students AS s ON s.room_id = rc.room_id
                WHERE rc.room_chat_id = %s
                  AND s.user_id = %s
                """,
                (user_id, text, chat_id, user_id),
            )
            if cursor.rowcount == 0:
                raise PermissionError("Користувач не має доступу до цього чату")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
