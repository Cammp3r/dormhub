from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import date

from db import get_db_connection


current_user = None


@contextmanager
def _transaction():
    connection = get_db_connection()
    if connection is None:
        raise RuntimeError("Не вдалося підключитися до бази даних")
    try:
        with connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
    finally:
        connection.close()


def _actor(cursor, admin=False):
    if current_user is None:
        raise PermissionError("Увійдіть до акаунта")
    cursor.execute("SELECT * FROM users WHERE user_id = %s FOR SHARE",
                   (current_user["user_id"],))
    user = cursor.fetchone()
    if not user:
        raise PermissionError("Акаунт видалено. Увійдіть знову.")
    if admin:
        cursor.execute("SELECT dorm_id FROM dorm_admins WHERE user_id = %s", (user["user_id"],))
        assignment = cursor.fetchone()
        if not assignment:
            raise PermissionError("Ця операція доступна лише адміністрації")
        user["dorm_id"] = assignment["dorm_id"]
    return user


def _required(value, label, limit=None):
    value = value.strip()
    if not value or (limit and len(value) > limit):
        raise ValueError(f"{label}: заповніть поле" + (f" (до {limit} символів)" if limit else ""))
    return value


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
                SELECT s.student_id, s.enrollment_year, s.room_id, s.place_id,
                       p.place_number, s.status, s.user_id
                FROM students s
                LEFT JOIN room_places p ON p.place_id = s.place_id
                WHERE s.user_id = %s
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
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            actor = _actor(cursor)
            if actor['user_id'] != user_id:
                raise PermissionError('Можна редагувати лише власний профіль')
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
    current_user = users[0]
    return current_user


def logout():
    global current_user
    current_user = None


# Операції адміністрації та спільноти. Права перевіряються при кожному запиті.
def get_request_categories():
    return [row['name'] for row in _fetch_all(
        'SELECT name FROM request_categories ORDER BY sort_order, name')]


def get_request_statuses():
    return [row['name'] for row in _fetch_all(
        'SELECT name FROM request_statuses ORDER BY sort_order, name')]


def setup_first_admin(dorm_number, address, first_name, last_name, email):
    """Початкове налаштування через локальний CLI з доступом до БД, не через вхід у UI."""
    try:
        dorm_number = int(dorm_number)
    except ValueError:
        raise ValueError('Номер гуртожитку має бути цілим числом') from None
    if dorm_number < 1:
        raise ValueError('Номер гуртожитку має бути більшим за нуль')
    address = _required(address, 'Адреса', 150)
    first_name = _required(first_name, 'Ім’я', 50)
    last_name = _required(last_name, 'Прізвище', 50)
    email = _required(email, 'Email', 150)
    with _transaction() as cursor:
        # Першого адміністратора можна створити лише один раз, зокрема при одночасному запуску CLI.
        cursor.execute('LOCK TABLE dorm_admins IN EXCLUSIVE MODE')
        cursor.execute('SELECT 1 FROM dorm_admins LIMIT 1')
        if cursor.fetchone():
            raise ValueError('Адміністратора вже налаштовано. Використайте наявний акаунт.')
        cursor.execute('INSERT INTO dorms (dorm_number, address) VALUES (%s, %s) '
                       'ON CONFLICT (dorm_number) DO NOTHING', (dorm_number, address))
        cursor.execute('SELECT dorm_id, address FROM dorms WHERE dorm_number=%s', (dorm_number,))
        dorm = cursor.fetchone()
        if dorm['address'] != address:
            raise ValueError('Гуртожиток із цим номером уже має іншу адресу')
        cursor.execute('''INSERT INTO users (first_name, last_name, email, dorm_id)
            VALUES (%s, %s, %s, %s) RETURNING user_id''', (first_name, last_name, email, dorm['dorm_id']))
        user_id = cursor.fetchone()['user_id']
        cursor.execute('INSERT INTO dorm_admins (user_id, dorm_id) VALUES (%s, %s)', (user_id, dorm['dorm_id']))
        return user_id


def get_admin_residents(search="", room_id=None):
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute("""
            SELECT u.*, s.student_id, s.room_id, s.enrollment_year,
                   s.place_id, s.status AS student_status, r.room_number,
                   p.place_number
            FROM users u JOIN students s ON s.user_id = u.user_id
            LEFT JOIN rooms r ON r.room_id = s.room_id
            LEFT JOIN room_places p ON p.place_id = s.place_id
            WHERE u.dorm_id = %s
              AND (u.first_name || ' ' || u.last_name || ' ' || u.email) ILIKE %s
              AND (%s IS NULL OR s.room_id = %s)
            ORDER BY u.last_name, u.first_name, u.user_id
        """, (actor['dorm_id'], '%' + search.strip() + '%', room_id, room_id))
        return cursor.fetchall()


def save_resident(first_name, last_name, email, birth_date="", enrollment_year="", user_id=None):
    first_name = _required(first_name, "Ім’я", 50)
    last_name = _required(last_name, "Прізвище", 50)
    email = _required(email, "Email", 150)
    try:
        birthday = date.fromisoformat(birth_date.strip()) if birth_date.strip() else None
        year = int(enrollment_year) if str(enrollment_year).strip() else None
    except ValueError:
        raise ValueError("Дата народження: РРРР-ММ-ДД; рік вступу: ціле число") from None
    if birthday and birthday > date.today():
        raise ValueError("Дата народження не може бути в майбутньому")
    if year is not None and not 1900 <= year <= date.today().year + 1:
        raise ValueError("Некоректний рік вступу")
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        if user_id is None:
            cursor.execute("""INSERT INTO users (first_name, last_name, email, date_of_birth, dorm_id)
                VALUES (%s, %s, %s, %s, %s) RETURNING user_id""",
                           (first_name, last_name, email, birthday, actor['dorm_id']))
            user_id = cursor.fetchone()['user_id']
            cursor.execute("INSERT INTO students (user_id, enrollment_year) VALUES (%s, %s)", (user_id, year))
        else:
            cursor.execute("""UPDATE users SET first_name=%s, last_name=%s, email=%s, date_of_birth=%s
                WHERE user_id=%s AND dorm_id=%s
                  AND EXISTS (SELECT 1 FROM students WHERE user_id=users.user_id)""",
                           (first_name, last_name, email, birthday, user_id, actor['dorm_id']))
            if not cursor.rowcount:
                raise PermissionError("Мешканця вашого гуртожитку не знайдено")
            cursor.execute("UPDATE students SET enrollment_year=%s WHERE user_id=%s", (year, user_id))
        return user_id


def get_admin_rooms():
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute("""SELECT r.*,
                count(s.student_id)::int AS occupied,
                COALESCE(json_agg(json_build_object(
                    'place_id', p.place_id,
                    'place_number', p.place_number,
                    'is_available', p.is_available,
                    'occupied', s.student_id IS NOT NULL
                ) ORDER BY p.place_number) FILTER (WHERE p.place_id IS NOT NULL), '[]') AS places
            FROM rooms r
            LEFT JOIN room_places p ON p.room_id = r.room_id
            LEFT JOIN students s ON s.place_id = p.place_id
            WHERE r.dorm_id=%s
            GROUP BY r.room_id
            ORDER BY r.floor, r.room_number""", (actor['dorm_id'],))
        return cursor.fetchall()


def get_admin_dorm():
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute("SELECT dorm_id, dorm_number, address FROM dorms WHERE dorm_id=%s",
                       (actor['dorm_id'],))
        dorm = cursor.fetchone()
        if not dorm:
            raise RuntimeError("Гуртожиток адміністратора не знайдено")
        return dorm


def save_dorm(dorm_number, address):
    address = _required(address, "Адреса", 150)
    try:
        dorm_number = int(dorm_number)
    except ValueError:
        raise ValueError("Номер гуртожитку має бути цілим числом") from None
    if dorm_number < 1:
        raise ValueError("Номер гуртожитку має бути більшим за нуль")
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute("""UPDATE dorms SET dorm_number=%s, address=%s
            WHERE dorm_id=%s""", (dorm_number, address, actor['dorm_id']))
        if not cursor.rowcount:
            raise RuntimeError("Гуртожиток адміністратора не знайдено")


def save_room(room_number, floor, capacity, is_available=True, room_id=None):
    number = _required(room_number, "Номер кімнати", 10)
    try:
        floor, capacity = int(floor), int(capacity)
    except ValueError:
        raise ValueError("Поверх і місткість мають бути цілими числами") from None
    if capacity < 1:
        raise ValueError("Місткість має бути більшою за нуль")
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        if room_id is None:
            cursor.execute("""INSERT INTO rooms (dorm_id, room_number, floor, capacity, is_available)
                VALUES (%s, %s, %s, %s, %s) RETURNING room_id""",
                           (actor['dorm_id'], number, floor, capacity, is_available))
            room_id = cursor.fetchone()['room_id']
            cursor.execute("""INSERT INTO room_places (room_id, place_number)
                SELECT %s, place_number FROM generate_series(1, %s) AS places(place_number)""",
                           (room_id, capacity))
        else:
            cursor.execute("SELECT room_id FROM rooms WHERE room_id=%s AND dorm_id=%s FOR UPDATE",
                           (room_id, actor['dorm_id']))
            if not cursor.fetchone():
                raise PermissionError("Кімнату вашого гуртожитку не знайдено")
            cursor.execute("SELECT count(*) AS n FROM students WHERE room_id=%s", (room_id,))
            if cursor.fetchone()['n'] > capacity:
                raise ValueError("Місткість менша за поточну кількість мешканців")
            cursor.execute("""SELECT 1
                FROM room_places p
                WHERE p.room_id=%s AND p.place_number > %s
                  AND (p.is_available = FALSE OR EXISTS (
                      SELECT 1 FROM students s WHERE s.place_id = p.place_id
                  ) OR EXISTS (
                      SELECT 1 FROM residencies h WHERE h.place_id = p.place_id
                  ))
                LIMIT 1""", (room_id, capacity))
            if cursor.fetchone():
                raise ValueError("Не можна зменшити місткість: місця вже використовуються або закриті")
            cursor.execute("DELETE FROM room_places WHERE room_id=%s AND place_number > %s",
                           (room_id, capacity))
            cursor.execute("""INSERT INTO room_places (room_id, place_number)
                SELECT %s, places.place_number
                FROM generate_series(1, %s) AS places(place_number)
                ON CONFLICT (room_id, place_number) DO NOTHING""",
                           (room_id, capacity))
            cursor.execute("""UPDATE rooms SET room_number=%s, floor=%s, capacity=%s, is_available=%s
                WHERE room_id=%s""", (number, floor, capacity, is_available, room_id))
        cursor.execute("INSERT INTO room_chats (room_id) VALUES (%s) ON CONFLICT (room_id) DO NOTHING", (room_id,))


def save_place(place_id, is_available):
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute("""SELECT p.place_id, p.is_available, s.student_id
            FROM room_places p
            JOIN rooms r ON r.room_id=p.room_id
            LEFT JOIN students s ON s.place_id=p.place_id
            WHERE p.place_id=%s AND r.dorm_id=%s
            FOR UPDATE OF p""", (place_id, actor['dorm_id']))
        place = cursor.fetchone()
        if not place:
            raise PermissionError("Місце вашого гуртожитку не знайдено")
        if place['student_id'] is not None and not is_available:
            raise ValueError("Зайняте місце не можна закрити")
        cursor.execute("UPDATE room_places SET is_available=%s WHERE place_id=%s",
                       (is_available, place_id))


def change_residency(user_id, place_id, reason):
    reason = _required(reason, "Причина", 1000)
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute("""SELECT s.* FROM students s JOIN users u ON u.user_id=s.user_id
            WHERE s.user_id=%s AND u.dorm_id=%s FOR UPDATE OF s, u""", (user_id, actor['dorm_id']))
        student = cursor.fetchone()
        if not student:
            raise PermissionError("Мешканця вашого гуртожитку не знайдено")
        if student['place_id'] == place_id:
            raise ValueError("Мешканець уже на цьому місці" if place_id else "Мешканця ще не поселено")
        place_ids = [value for value in (student['place_id'], place_id) if value is not None]
        if place_ids:
            cursor.execute("""SELECT p.*, r.dorm_id, r.is_available AS room_is_available
                FROM room_places p JOIN rooms r ON r.room_id=p.room_id
                WHERE p.place_id = ANY(%s)
                ORDER BY p.place_id
                FOR UPDATE OF p""", (place_ids,))
            places = {row['place_id']: row for row in cursor.fetchall()}
        else:
            places = {}
        if place_id is not None:
            place = places.get(place_id)
            if not place or place['dorm_id'] != actor['dorm_id']:
                raise PermissionError("Оберіть місце вашого гуртожитку")
            if not place['is_available']:
                raise ValueError("Місце закрите для поселення")
            if not place['room_is_available']:
                raise ValueError("Кімната закрита для поселення")
            cursor.execute("SELECT 1 FROM students WHERE place_id=%s FOR UPDATE", (place_id,))
            if cursor.fetchone():
                raise ValueError("Місце вже зайняте іншим мешканцем")
        cursor.execute("""UPDATE residencies SET ended_at=CURRENT_TIMESTAMP, ended_by=%s, end_reason=%s
            WHERE student_id=%s AND ended_at IS NULL""", (actor['user_id'], reason, student['student_id']))
        if place_id is not None:
            cursor.execute("""INSERT INTO residencies (student_id, room_id, place_id, started_by, start_reason)
                VALUES (%s, %s, %s, %s, %s)""",
                           (student['student_id'], place['room_id'], place_id, actor['user_id'], reason))
        cursor.execute("UPDATE students SET room_id=%s, place_id=%s WHERE student_id=%s",
                       (place['room_id'] if place_id is not None else None, place_id, student['student_id']))


def get_residency_history():
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute("""SELECT h.*, u.first_name || ' ' || u.last_name AS resident_name,
                r.room_number, p.place_number
            FROM residencies h JOIN students s ON s.student_id=h.student_id
            JOIN users u ON u.user_id=s.user_id JOIN rooms r ON r.room_id=h.room_id
            JOIN room_places p ON p.place_id=h.place_id
            WHERE r.dorm_id=%s ORDER BY h.started_at DESC, h.residency_id DESC""", (actor['dorm_id'],))
        return cursor.fetchall()


def get_publications(kind):
    table = _publication_table(kind)
    with _transaction() as cursor:
        actor = _actor(cursor)
        cursor.execute(f"""SELECT p.*, u.first_name || ' ' || u.last_name AS author_name
            FROM {table} p JOIN users u ON u.user_id=p.author_id
            WHERE p.dorm_id=%s ORDER BY p.created_at DESC, p.id DESC""", (actor['dorm_id'],))
        return cursor.fetchall()


def _publication_table(kind):
    if kind != 'announcements':
        raise ValueError("Невідомий тип публікації")
    return kind


def save_publication(kind, title, body, publication_id=None):
    table = _publication_table(kind)
    title, body = _required(title, "Заголовок", 150), _required(body, "Опис", 10000)
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        if publication_id is None:
            cursor.execute(f"""INSERT INTO {table} (dorm_id, author_id, title, body)
                VALUES (%s, %s, %s, %s)""",
                           (actor['dorm_id'], actor['user_id'], title, body))
        else:
            cursor.execute(f"SELECT id FROM {table} WHERE id=%s AND dorm_id=%s FOR UPDATE",
                           (publication_id, actor['dorm_id']))
            if not cursor.fetchone():
                raise PermissionError("Публікацію вашого гуртожитку не знайдено")
            cursor.execute(f"UPDATE {table} SET title=%s, body=%s WHERE id=%s",
                           (title, body, publication_id))


def delete_publication(kind, publication_id):
    table = _publication_table(kind)
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute(f"DELETE FROM {table} WHERE id=%s AND dorm_id=%s", (publication_id, actor['dorm_id']))
        if not cursor.rowcount:
            raise PermissionError("Публікацію вашого гуртожитку не знайдено")


def create_request(category, description):
    description = _required(description, "Опис проблеми", 10000)
    with _transaction() as cursor:
        actor = _actor(cursor)
        cursor.execute('SELECT name FROM request_categories WHERE name=%s FOR SHARE', (category,))
        if not cursor.fetchone():
            raise ValueError("Оберіть наявну категорію звернення")
        cursor.execute('SELECT name FROM request_statuses WHERE is_initial FOR SHARE')
        initial = cursor.fetchone()
        if initial is None:
            raise ValueError('У базі не налаштовано початковий статус звернення')
        cursor.execute("""SELECT s.room_id FROM students s JOIN rooms r ON r.room_id=s.room_id
            WHERE s.user_id=%s AND r.dorm_id=%s FOR SHARE OF s""", (actor['user_id'], actor['dorm_id']))
        student = cursor.fetchone()
        if not student:
            raise ValueError("Звернення можуть подавати лише заселені мешканці")
        cursor.execute("""INSERT INTO maintenance_requests (dorm_id, room_id, author_id, category, description, status)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING request_id""",
                       (actor['dorm_id'], student['room_id'], actor['user_id'], category, description, initial['name']))
        request_id = cursor.fetchone()['request_id']
        cursor.execute("""INSERT INTO request_status_history (request_id, changed_by, status, response)
            VALUES (%s, %s, %s, '')""", (request_id, actor['user_id'], initial['name']))


def get_requests(admin=False, status="Усі"):
    with _transaction() as cursor:
        actor = _actor(cursor, admin=admin)
        scope = 'q.dorm_id=%s' if admin else 'q.author_id=%s'
        cursor.execute(f"""SELECT q.*, r.room_number, u.first_name || ' ' || u.last_name AS author_name
            FROM maintenance_requests q JOIN rooms r ON r.room_id=q.room_id
            JOIN users u ON u.user_id=q.author_id
            WHERE {scope} AND (%s='Усі' OR q.status=%s)
            ORDER BY q.created_at DESC, q.request_id DESC""",
                       (actor['dorm_id'] if admin else actor['user_id'], status, status))
        rows = cursor.fetchall()
        for row in rows:
            cursor.execute("""SELECT h.*, u.first_name || ' ' || u.last_name AS changed_by_name
                FROM request_status_history h JOIN users u ON u.user_id=h.changed_by
                WHERE request_id=%s ORDER BY h.changed_at, h.history_id""", (row['request_id'],))
            row['history'] = cursor.fetchall()
        return rows


def update_request(request_id, status, response):
    response = _required(response, "Відповідь / причина зміни", 10000)
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute('SELECT name FROM request_statuses WHERE name=%s FOR SHARE', (status,))
        if not cursor.fetchone():
            raise ValueError("Невідомий статус звернення")
        cursor.execute("""UPDATE maintenance_requests SET status=%s, response=%s, updated_at=CURRENT_TIMESTAMP
            WHERE request_id=%s AND dorm_id=%s""", (status, response, request_id, actor['dorm_id']))
        if not cursor.rowcount:
            raise PermissionError("Звернення вашого гуртожитку не знайдено")
        cursor.execute("""INSERT INTO request_status_history (request_id, changed_by, status, response)
            VALUES (%s, %s, %s, %s)""", (request_id, actor['user_id'], status, response))


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
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            actor = _actor(cursor)
            if actor['user_id'] != user_id:
                raise PermissionError('Не можна надсилати повідомлення від іншого користувача')
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
