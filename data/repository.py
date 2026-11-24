from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import date

from db import get_db_connection
from data.models import (
    Announcement,
    Application,
    User,
    Vacancy,
    close_database,
    connect_database,
)
from peewee import DatabaseError as PeeweeDatabaseError
from peewee import fn


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
    if user["status"] != "active":
        raise PermissionError("Акаунт заблоковано")
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


def validate_room_capacity(capacity):
    if not isinstance(capacity, int) or isinstance(capacity, bool):
        raise ValueError("Місткість кімнати має бути цілим числом")
    if not 1 <= capacity <= 4:
        raise ValueError("Місткість кімнати має бути від 1 до 4")
    return capacity


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
    with _transaction() as cursor:
        actor = _actor(cursor)
        if actor['user_id'] != user_id:
            raise PermissionError("Не можна переглядати профіль іншого користувача")
    try:
        connect_database()
        rows = list(
            User.select(
                User.user_id,
                User.first_name,
                User.last_name,
                User.email,
                User.date_of_birth,
                User.registration_date,
                User.status,
                User.dorm_id,
            )
            .where(User.user_id == user_id)
            .dicts()
        )
        return rows[0] if rows else None
    except PeeweeDatabaseError as error:
        raise RuntimeError("Не вдалося завантажити профіль") from error
    finally:
        close_database()


def get_all_users():
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute(
            """
            SELECT user_id, first_name, last_name, email, date_of_birth,
                   registration_date, status, dorm_id
            FROM users
            WHERE dorm_id = %s
            ORDER BY user_id
            """,
            (actor['dorm_id'],),
        )
        return cursor.fetchall()


def get_student_for_user(user_id):
    with _transaction() as cursor:
        actor = _actor(cursor)
        if actor['user_id'] != user_id:
            raise PermissionError("Не можна переглядати дані іншого мешканця")
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


def get_user_name(user):
    return f"{user['first_name']} {user['last_name']}"


def update_profile(user_id, first_name, last_name, email):
    with _transaction() as cursor:
        actor = _actor(cursor)
        if actor['user_id'] != user_id:
            raise PermissionError('Можна редагувати лише власний профіль')
    try:
        database = connect_database()
        with database.atomic():
            updated = (
                User.update(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                )
                .where(User.user_id == user_id)
                .execute()
            )
            if updated == 0:
                raise ValueError(f"Користувача з user_id={user_id} не знайдено")
    except PeeweeDatabaseError as error:
        raise RuntimeError("Не вдалося оновити профіль") from error
    finally:
        close_database()


def get_room_info(room_id):
    with _transaction() as cursor:
        actor = _actor(cursor)
        cursor.execute(
            """
            SELECT r.room_id, r.dorm_id, r.room_number, r.floor,
                   d.dorm_number, d.address
            FROM rooms AS r
            INNER JOIN dorms AS d ON d.dorm_id = r.dorm_id
            WHERE r.room_id = %s
              AND (
                  EXISTS (
                      SELECT 1 FROM students
                      WHERE user_id = %s AND room_id = r.room_id
                  )
                  OR EXISTS (
                      SELECT 1 FROM dorm_admins
                      WHERE user_id = %s AND dorm_id = r.dorm_id
                  )
              )
            """,
            (room_id, actor['user_id'], actor['user_id']),
        )
        room = cursor.fetchone()
        if room is None:
            raise PermissionError("Немає доступу до цієї кімнати")
        return room


def get_roommates(room_id):
    with _transaction() as cursor:
        actor = _actor(cursor)
        cursor.execute(
            """
            SELECT 1
            FROM rooms AS r
            WHERE r.room_id = %s
              AND (
                  EXISTS (
                      SELECT 1 FROM students
                      WHERE user_id = %s AND room_id = r.room_id
                  )
                  OR EXISTS (
                      SELECT 1 FROM dorm_admins
                      WHERE user_id = %s AND dorm_id = r.dorm_id
                  )
              )
            """,
            (room_id, actor['user_id'], actor['user_id']),
        )
        if not cursor.fetchone():
            raise PermissionError("Немає доступу до цієї кімнати")
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


def is_dorm_admin(user_id):
    with _transaction() as cursor:
        actor = _actor(cursor)
        if actor['user_id'] != user_id:
            raise PermissionError("Не можна перевіряти права іншого користувача")
        cursor.execute(
            "SELECT 1 FROM dorm_admins WHERE user_id = %s LIMIT 1",
            (user_id,),
        )
        return cursor.fetchone() is not None


def get_vacancies():
    with _transaction() as cursor:
        _actor(cursor)
    try:
        connect_database()
        return list(
            Vacancy.select(
                Vacancy.vacancy_id,
                Vacancy.company_name,
                Vacancy.job_name,
            )
            .order_by(Vacancy.vacancy_id)
            .dicts()
        )
    except PeeweeDatabaseError as error:
        raise RuntimeError("Не вдалося завантажити вакансії") from error
    finally:
        close_database()


def get_applications(student_id=None):
    with _transaction() as cursor:
        actor = _actor(cursor)
        cursor.execute("SELECT student_id FROM students WHERE user_id = %s", (actor['user_id'],))
        student = cursor.fetchone()
        if not student:
            return []
        if student_id is not None and student_id != student['student_id']:
            raise PermissionError("Не можна переглядати заявки іншого студента")
        requested_student_id = student['student_id']
    try:
        connect_database()
        return list(
            Application.select(
                Application.application_id,
                Application.student_id,
                Application.vacancy_id,
                Application.application_date,
                Application.status,
                Vacancy.company_name,
                Vacancy.job_name,
            )
            .join(Vacancy)
            .where(Application.student_id == requested_student_id)
            .order_by(
                Application.application_date.desc(),
                Application.application_id,
            )
            .dicts()
        )
    except PeeweeDatabaseError as error:
        raise RuntimeError("Не вдалося завантажити заявки") from error
    finally:
        close_database()


def apply_for_vacancy(vacancy_id):
    if not isinstance(vacancy_id, int) or isinstance(vacancy_id, bool) or vacancy_id <= 0:
        raise ValueError("Некоректний номер вакансії")
    with _transaction() as cursor:
        actor = _actor(cursor)
        cursor.execute(
            "SELECT student_id FROM students WHERE user_id = %s",
            (actor["user_id"],),
        )
        student = cursor.fetchone()
        if not student:
            raise PermissionError("Подавати заявки на вакансії можуть лише мешканці")
        cursor.execute(
            """
            INSERT INTO applications (student_id, vacancy_id)
            VALUES (%s, %s)
            ON CONFLICT (student_id, vacancy_id) DO NOTHING
            RETURNING application_id
            """,
            (student["student_id"], vacancy_id),
        )
        application = cursor.fetchone()
        if not application:
            raise ValueError("Ви вже відгукнулися на цю вакансію")
        return application["application_id"]


def create_vacancy(company_name, job_name):
    company_name = _required(company_name, "Назва компанії", 100)
    job_name = _required(job_name, "Назва вакансії", 100)
    with _transaction() as cursor:
        _actor(cursor, admin=True)
        cursor.execute(
            """
            INSERT INTO vacancies (company_name, job_name)
            VALUES (%s, %s)
            RETURNING vacancy_id
            """,
            (company_name, job_name),
        )
        return cursor.fetchone()["vacancy_id"]


def get_vacancy_application_report():
    """Підсумовує кількість заявок і заявників за кожною вакансією."""
    with _transaction() as cursor:
        _actor(cursor, admin=True)
        cursor.execute(
            """
            WITH vacancy_application_stats AS (
                SELECT v.vacancy_id,
                       v.company_name,
                       v.job_name,
                       COUNT(a.application_id)::int AS total_applications,
                       COUNT(DISTINCT u.user_id)::int AS applicant_count,
                       COUNT(a.application_id) FILTER (
                           WHERE a.status = 'submitted'
                       )::int AS submitted_count,
                       COUNT(a.application_id) FILTER (
                           WHERE a.status = 'accepted'
                       )::int AS accepted_count,
                       COUNT(a.application_id) FILTER (
                           WHERE a.status = 'rejected'
                       )::int AS rejected_count
                FROM vacancies AS v
                LEFT JOIN applications AS a ON a.vacancy_id = v.vacancy_id
                LEFT JOIN students AS s ON s.student_id = a.student_id
                LEFT JOIN users AS u ON u.user_id = s.user_id
                GROUP BY v.vacancy_id, v.company_name, v.job_name
            )
            SELECT vacancy_id,
                   company_name,
                   job_name,
                   total_applications,
                   applicant_count,
                   submitted_count,
                   accepted_count,
                   rejected_count
            FROM vacancy_application_stats
            ORDER BY company_name, job_name, vacancy_id
            """
        )
        return cursor.fetchall()


def get_parking_slots():
    with _transaction() as cursor:
        actor = _actor(cursor)
        cursor.execute(
            """
            SELECT p.parking_slot_id, p.dorm_id, p.user_id, p.slot_number,
                   u.first_name, u.last_name, d.dorm_number
            FROM parking_slots AS p
            INNER JOIN dorms AS d ON d.dorm_id = p.dorm_id
            LEFT JOIN users AS u ON u.user_id = p.user_id
            WHERE p.dorm_id = %s
            ORDER BY p.dorm_id, p.slot_number
            """,
            (actor['dorm_id'],),
        )
        return cursor.fetchall()


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
    try:
        connect_database()
        users = list(
            User.select(
                User.user_id,
                User.first_name,
                User.last_name,
                User.email,
                User.date_of_birth,
                User.registration_date,
                User.status,
                User.dorm_id,
            )
            .where(
                (fn.LOWER(User.first_name) == first_name.lower())
                & (fn.LOWER(User.last_name) == last_name.lower())
                & (User.status == 'active')
            )
            .limit(2)
            .dicts()
        )
    except PeeweeDatabaseError as error:
        raise RuntimeError("Не вдалося виконати вхід") from error
    finally:
        close_database()
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


def get_admin_residents(search="", room_id=None, limit=None, offset=0):
    if limit is not None and (limit < 1 or limit > 100):
        raise ValueError("Розмір сторінки має бути від 1 до 100")
    if offset < 0:
        raise ValueError("Зсув сторінки не може бути від’ємним")
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        query = """
            SELECT u.*, s.student_id, s.room_id, s.enrollment_year,
                   s.place_id, s.status AS student_status, r.room_number,
                   p.place_number, COUNT(*) OVER() AS total_count
            FROM users u JOIN students s ON s.user_id = u.user_id
            LEFT JOIN rooms r ON r.room_id = s.room_id
            LEFT JOIN room_places p ON p.place_id = s.place_id
            WHERE u.dorm_id = %s
              AND (u.first_name || ' ' || u.last_name || ' ' || u.email) ILIKE %s
              AND (%s IS NULL OR s.room_id = %s)
            ORDER BY u.last_name, u.first_name, u.user_id
        """
        parameters = [actor['dorm_id'], '%' + search.strip() + '%', room_id, room_id]
        if limit is not None:
            query += " LIMIT %s OFFSET %s"
            parameters.extend([limit, offset])
        cursor.execute(query, parameters)
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


def get_room_occupancy_report():
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute(
            """
            SELECT d.dorm_number,
                   r.room_id,
                   r.room_number,
                   r.floor,
                   r.capacity,
                   COUNT(DISTINCT s.student_id)::int AS resident_count,
                   (r.capacity - COUNT(DISTINCT s.student_id))::int AS free_places
            FROM dorms d
            JOIN rooms r ON r.dorm_id = d.dorm_id
            LEFT JOIN students s ON s.room_id = r.room_id
            LEFT JOIN users u ON u.user_id = s.user_id
            WHERE d.dorm_id = %s
              AND r.capacity <= 4
            GROUP BY d.dorm_id, d.dorm_number,
                     r.room_id, r.room_number, r.floor, r.capacity
            HAVING COUNT(DISTINCT s.student_id) <= r.capacity
            ORDER BY r.floor, r.room_number, r.room_id
            """,
            (actor['dorm_id'],),
        )
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
    validate_room_capacity(capacity)
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
            cursor.execute("""SELECT p.*, r.dorm_id, r.capacity,
                    r.is_available AS room_is_available
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
            cursor.execute(
                "SELECT room_id FROM rooms WHERE room_id=%s FOR UPDATE",
                (place['room_id'],),
            )
            cursor.execute(
                """SELECT COUNT(*) AS resident_count
                   FROM students
                   WHERE room_id=%s AND student_id<>%s""",
                (place['room_id'], student['student_id']),
            )
            resident_count = cursor.fetchone()['resident_count']
            if resident_count >= place['capacity']:
                raise ValueError(
                    f"Кімната досягла максимальної місткості {place['capacity']} мешканців"
                )
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
    _publication_table(kind)
    with _transaction() as cursor:
        actor = _actor(cursor)
    try:
        connect_database()
        rows = (
            Announcement.select(
                Announcement.id,
                Announcement.dorm_id,
                Announcement.author_id,
                Announcement.title,
                Announcement.body,
                Announcement.created_at,
                User.first_name.alias("author_first_name"),
                User.last_name.alias("author_last_name"),
            )
            .join(User, on=(Announcement.author == User.user_id))
            .where(Announcement.dorm_id == actor['dorm_id'])
            .order_by(Announcement.created_at.desc(), Announcement.id.desc())
            .dicts()
        )
        return [
            {
                **row,
                "author_name": f"{row.pop('author_first_name')} {row.pop('author_last_name')}",
            }
            for row in rows
        ]
    except PeeweeDatabaseError as error:
        raise RuntimeError("Не вдалося завантажити оголошення") from error
    finally:
        close_database()


def _publication_table(kind):
    if kind != 'announcements':
        raise ValueError("Невідомий тип публікації")
    return kind


def save_publication(kind, title, body, publication_id=None):
    _publication_table(kind)
    title, body = _required(title, "Заголовок", 150), _required(body, "Опис", 10000)
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
    try:
        database = connect_database()
        with database.atomic():
            if publication_id is None:
                Announcement.create(
                    dorm=actor['dorm_id'],
                    author=actor['user_id'],
                    title=title,
                    body=body,
                )
            else:
                publication = (
                    Announcement.select()
                    .where(
                        (Announcement.id == publication_id)
                        & (Announcement.dorm_id == actor['dorm_id'])
                    )
                    .for_update()
                    .get_or_none()
                )
                if publication is None:
                    raise PermissionError("Публікацію вашого гуртожитку не знайдено")
                (
                    Announcement.update(title=title, body=body)
                    .where(Announcement.id == publication_id)
                    .execute()
                )
    except PeeweeDatabaseError as error:
        raise RuntimeError("Не вдалося зберегти оголошення") from error
    finally:
        close_database()


def delete_publication(kind, publication_id):
    _publication_table(kind)
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
    try:
        database = connect_database()
        with database.atomic():
            deleted = (
                Announcement.delete()
                .where(
                    (Announcement.id == publication_id)
                    & (Announcement.dorm_id == actor['dorm_id'])
                )
                .execute()
            )
            if deleted == 0:
                raise PermissionError("Публікацію вашого гуртожитку не знайдено")
    except PeeweeDatabaseError as error:
        raise RuntimeError("Не вдалося видалити оголошення") from error
    finally:
        close_database()


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


def get_repeated_request_report():
    """Показує категорії звернень, які повторюються щонайменше двічі на поверсі."""
    with _transaction() as cursor:
        actor = _actor(cursor, admin=True)
        cursor.execute(
            """
            WITH request_stats AS (
                SELECT q.category,
                       r.floor,
                       COUNT(*)::int AS request_count,
                       COUNT(DISTINCT q.author_id)::int AS resident_count
                FROM maintenance_requests AS q
                JOIN rooms AS r
                  ON r.room_id = q.room_id
                 AND r.dorm_id = q.dorm_id
                JOIN users AS u
                  ON u.user_id = q.author_id
                JOIN dorms AS d
                  ON d.dorm_id = q.dorm_id
                WHERE q.dorm_id = %s
                GROUP BY q.category, r.floor
                HAVING COUNT(*) >= 2
            ),
            ranked_requests AS (
                SELECT request_stats.*,
                       RANK() OVER (
                           PARTITION BY category
                           ORDER BY request_count DESC,
                                    resident_count DESC
                       ) AS category_rank
                FROM request_stats
            )
            SELECT category,
                   floor,
                   request_count,
                   resident_count,
                   category_rank
            FROM ranked_requests
            ORDER BY request_count DESC,
                     category,
                     floor
            """,
            (actor['dorm_id'],),
        )
        return cursor.fetchall()


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
    with _transaction() as cursor:
        actor = _actor(cursor)
        if actor['user_id'] != user_id:
            raise PermissionError("Не можна переглядати чати іншого користувача")
        cursor.execute(
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
        return cursor.fetchall()


def get_room_chat_members(chat_id, user_id):
    with _transaction() as cursor:
        actor = _actor(cursor)
        if actor['user_id'] != user_id:
            raise PermissionError("Не можна переглядати чати іншого користувача")
        cursor.execute(
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
        members = cursor.fetchall()
        if not members:
            cursor.execute(
                """
                SELECT 1
                FROM room_chats AS rc
                INNER JOIN students AS current_student
                    ON current_student.room_id = rc.room_id
                WHERE rc.room_chat_id = %s AND current_student.user_id = %s
                """,
                (chat_id, user_id),
            )
            if not cursor.fetchone():
                raise PermissionError("Користувач не має доступу до цього чату")
        return members


def get_room_chat_messages(chat_id, user_id, limit=30, offset=0):
    if limit < 1 or limit > 100:
        raise ValueError("Розмір сторінки має бути від 1 до 100")
    if offset < 0:
        raise ValueError("Зсув сторінки не може бути від’ємним")
    with _transaction() as cursor:
        actor = _actor(cursor)
        if actor['user_id'] != user_id:
            raise PermissionError("Не можна переглядати чати іншого користувача")
        cursor.execute(
            """
            SELECT rcm.message_id, rcm.user_id AS author_id, rcm.message AS text,
                   rcm.sent_at, COUNT(*) OVER() AS total_count,
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
            ORDER BY rcm.sent_at DESC, rcm.message_id DESC
            LIMIT %s OFFSET %s
            """,
            (chat_id, user_id, limit, offset),
        )
        return cursor.fetchall()


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
