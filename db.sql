-- Повне відтворення демонстраційної БД: попередні дані буде видалено.
BEGIN;
DROP TABLE IF EXISTS request_status_history, maintenance_requests, event_registrations, events, announcements, account_status_history, residencies, room_chat_messages, room_chats, applications, vacancies, enrollments, courses, parking_slots, dorm_admins, students, rooms, dorms, departments, users CASCADE;
DROP TYPE  IF EXISTS student_status, user_status, application_status CASCADE;


CREATE TYPE student_status AS ENUM ('enrolled', 'on_leave', 'graduated', 'expelled');
CREATE TYPE user_status AS ENUM ('active', 'blocked');
CREATE TYPE application_status AS ENUM ('submitted', 'accepted', 'rejected');

CREATE TABLE dorms (
    dorm_id     SERIAL PRIMARY KEY,
    dorm_number INTEGER NOT NULL UNIQUE CHECK (dorm_number > 0),
    address     VARCHAR(150) UNIQUE NOT NULL CHECK (address = trim(address) AND address <> '')
);

CREATE TABLE users (
    user_id           SERIAL PRIMARY KEY,
    first_name        VARCHAR(50)  NOT NULL CHECK (first_name = trim(first_name) AND first_name <> ''),
    last_name         VARCHAR(50)  NOT NULL CHECK (last_name = trim(last_name) AND last_name <> ''),
    email             VARCHAR(150) UNIQUE NOT NULL CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$'),
    date_of_birth     DATE,
    registration_date DATE DEFAULT CURRENT_DATE,
    status            user_status NOT NULL DEFAULT 'active',
    dorm_id           INTEGER REFERENCES dorms(dorm_id) ON DELETE RESTRICT,
    UNIQUE (user_id, dorm_id)
);

CREATE TABLE departments (
    department_id   SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL CHECK (department_name = trim(department_name) AND department_name <> '')
);

CREATE TABLE rooms (
    room_id     SERIAL PRIMARY KEY,
    dorm_id     INTEGER NOT NULL REFERENCES dorms(dorm_id) ON DELETE RESTRICT,
    room_number VARCHAR(10) NOT NULL CHECK (room_number = trim(room_number) AND room_number <> ''),
    floor       INTEGER,
    capacity    INTEGER NOT NULL DEFAULT 4 CHECK (capacity > 0),
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (dorm_id, room_number),
    UNIQUE (room_id, dorm_id)
);

CREATE TABLE students (
    student_id      SERIAL PRIMARY KEY,
    enrollment_year INTEGER,
    room_id         INTEGER REFERENCES rooms(room_id) ON DELETE RESTRICT,
    status          student_status NOT NULL DEFAULT 'enrolled',
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE RESTRICT
);

CREATE TABLE room_chats (
    room_chat_id SERIAL PRIMARY KEY,
    room_id      INTEGER NOT NULL UNIQUE REFERENCES rooms(room_id) ON DELETE CASCADE
);

CREATE TABLE room_chat_messages (
    message_id   BIGSERIAL PRIMARY KEY,
    room_chat_id INTEGER NOT NULL REFERENCES room_chats(room_chat_id) ON DELETE CASCADE,
    user_id      INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    message      TEXT NOT NULL CHECK (message = trim(message) AND message <> ''),
    sent_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dorm_admins (
    admin_id SERIAL PRIMARY KEY,
    user_id  INTEGER NOT NULL UNIQUE,
    dorm_id  INTEGER NOT NULL,
    CONSTRAINT fk_dorm_admins_user_dorm
        FOREIGN KEY (user_id, dorm_id) REFERENCES users(user_id, dorm_id)
        ON DELETE RESTRICT
);

CREATE TABLE residencies (
    residency_id BIGSERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(student_id) ON DELETE RESTRICT,
    room_id INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE RESTRICT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ,
    started_by INTEGER REFERENCES users(user_id) ON DELETE RESTRICT,
    ended_by INTEGER REFERENCES users(user_id) ON DELETE RESTRICT,
    start_reason TEXT NOT NULL CHECK (length(trim(start_reason)) > 0),
    end_reason TEXT,
    CHECK (ended_at IS NULL OR ended_at >= started_at)
);
CREATE UNIQUE INDEX one_active_residency ON residencies(student_id) WHERE ended_at IS NULL;
CREATE INDEX residencies_room_idx ON residencies(room_id, started_at DESC);

CREATE TABLE account_status_history (
    history_id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    changed_by INTEGER NOT NULL REFERENCES users(user_id),
    status user_status NOT NULL,
    reason TEXT NOT NULL CHECK (length(trim(reason)) > 0),
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE announcements (
    id SERIAL PRIMARY KEY,
    dorm_id INTEGER NOT NULL REFERENCES dorms(dorm_id),
    author_id INTEGER NOT NULL REFERENCES users(user_id),
    title VARCHAR(150) NOT NULL CHECK (length(trim(title)) > 0),
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX announcements_dorm_idx ON announcements(dorm_id, created_at DESC);

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    dorm_id INTEGER NOT NULL REFERENCES dorms(dorm_id),
    author_id INTEGER NOT NULL REFERENCES users(user_id),
    title VARCHAR(150) NOT NULL CHECK (length(trim(title)) > 0),
    body TEXT NOT NULL CHECK (length(trim(body)) > 0),
    starts_at TIMESTAMPTZ NOT NULL,
    place VARCHAR(150) NOT NULL CHECK (length(trim(place)) > 0),
    capacity INTEGER CHECK (capacity > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX events_dorm_idx ON events(dorm_id, starts_at);
CREATE TABLE event_registrations (
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    registered_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id, user_id)
);

CREATE TABLE maintenance_requests (
    request_id SERIAL PRIMARY KEY,
    dorm_id INTEGER NOT NULL REFERENCES dorms(dorm_id),
    room_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL REFERENCES users(user_id),
    category TEXT NOT NULL CHECK (category IN ('Сантехніка', 'Електрика', 'Меблі', 'Інтернет', 'Прибирання', 'Інше')),
    description TEXT NOT NULL CHECK (length(trim(description)) > 0),
    status TEXT NOT NULL DEFAULT 'Нова' CHECK (status IN ('Нова', 'Прийнята', 'В роботі', 'Виконана', 'Закрита', 'Скасована')),
    response TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id, dorm_id) REFERENCES rooms(room_id, dorm_id)
);
CREATE INDEX requests_dorm_status_idx ON maintenance_requests(dorm_id, status, created_at DESC);
CREATE INDEX requests_author_idx ON maintenance_requests(author_id);
CREATE TABLE request_status_history (
    history_id BIGSERIAL PRIMARY KEY,
    request_id INTEGER NOT NULL REFERENCES maintenance_requests(request_id) ON DELETE CASCADE,
    changed_by INTEGER NOT NULL REFERENCES users(user_id),
    status TEXT NOT NULL CHECK (status IN ('Нова', 'Прийнята', 'В роботі', 'Виконана', 'Закрита', 'Скасована')),
    response TEXT NOT NULL DEFAULT '',
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE parking_slots (
    parking_slot_id SERIAL PRIMARY KEY,
    dorm_id         INTEGER NOT NULL REFERENCES dorms(dorm_id) ON DELETE RESTRICT,
    user_id         INTEGER UNIQUE,
    slot_number     VARCHAR(10) NOT NULL CHECK (slot_number = trim(slot_number) AND slot_number <> ''),
    UNIQUE (dorm_id, slot_number),
    CONSTRAINT fk_parking_user_same_dorm
        FOREIGN KEY (user_id, dorm_id) REFERENCES users(user_id, dorm_id)
        ON DELETE SET NULL (user_id)
);

CREATE TABLE courses (
    course_id     SERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    course_title  VARCHAR(100) NOT NULL CHECK (course_title = trim(course_title) AND course_title <> '')
);

CREATE TABLE enrollments (
    enrollment_id   SERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    course_id       INTEGER NOT NULL REFERENCES courses(course_id) ON DELETE CASCADE,
    enrollment_date DATE DEFAULT CURRENT_DATE,
    grade           NUMERIC,
    UNIQUE (student_id, course_id)
);

CREATE TABLE vacancies (
    vacancy_id   SERIAL PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL CHECK (company_name = trim(company_name) AND company_name <> ''),
    job_name     VARCHAR(100) NOT NULL CHECK (job_name = trim(job_name) AND job_name <> '')
);

CREATE TABLE applications (
    application_id   SERIAL PRIMARY KEY,
    student_id       INTEGER NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    vacancy_id       INTEGER NOT NULL REFERENCES vacancies(vacancy_id) ON DELETE CASCADE,
    application_date DATE DEFAULT CURRENT_DATE,
    status           application_status NOT NULL DEFAULT 'submitted',
    UNIQUE (student_id, vacancy_id)
);


INSERT INTO dorms (dorm_number, address) VALUES
    (1, 'вул. Степана Бандери 1-б'),
    (2, 'вул. Колотушкіна 1-а'),
    (3, 'вул. Тараса Шевченка 1-в'),
    (4, 'вул. Тараса Шевченка 2-в');

INSERT INTO users (first_name, last_name, email, date_of_birth, status, dorm_id) VALUES
    ('Іван1',   'Петренко',  'ivan.petrenko@example.com',     '2003-05-14', 'active', 1),
    ('Марія',  'Коваль',    'maria.koval@example.com',       '2002-11-02', 'active', 1),
    ('Олег',   'Бондар',    'oleg.bondar@example.com',       '2001-03-20', 'active', 2),
    ('Анна',   'Сидоренко', 'anna.sydorenko@example.com',    '2004-07-08', 'active', 2),
    ('Сергій', 'Мельник',   'sergiy.melnyk@example.com',     '1985-01-15', 'active', 1),
    ('Ольга',  'Ткаченко',  'olha.tkachenko@example.com',    '1990-06-22', 'active', 1),
    ('Павло',  'Кравець',   'pavlo.kravets@example.com',     '1988-09-30', 'active', 3),
    ('Дмитро', 'Шевченко',  'dmytro.shevchenko@example.com', '2004-02-11', 'active', NULL),
    ('Степан', 'Бендера',   'stpbdn@gmail.com',              '2001-09-11', 'active', 2),
	('Бен', 'Мохамед',   'ben@gmail.com',              '2001-09-11', 'active', 2);

INSERT INTO departments (department_name) VALUES
    ('Комп''ютерні науки'),
    ('Економіка'),
    ('Іноземні мови');

INSERT INTO rooms (dorm_id, room_number, floor) VALUES
    (1, '101', 1),
    (1, '102', 1),
    (2, '201', 2),
    (2, '202', 2),
    (3, '301', 3),
    (3, '228', 2);

INSERT INTO room_chats (room_id)
SELECT room_id FROM rooms;

INSERT INTO students (enrollment_year, room_id, status, user_id) VALUES
    (2022, 1,    'enrolled',  1),
    (2023, 1,    'enrolled',  2),
    (2021, 3,    'graduated', 3),
    (2022, 4,    'on_leave',  4),
    (2024, NULL, 'enrolled',  8);

INSERT INTO dorm_admins (user_id, dorm_id) VALUES
    (5, 1),
    (6, 1),
    (9, 2),
    (7, 3);

INSERT INTO parking_slots (user_id, dorm_id, slot_number) VALUES
    (1, 1, 'P-101'),
    (2, 1, 'P-102'),
    (3, 2, 'P-201'),
    (4, 2, 'P-202'),
    (5, 1, 'P-103'),
    (9, 2, 'P-203'),
    (7, 3, 'P-301');

INSERT INTO parking_slots (dorm_id, slot_number) VALUES
    (3, 'P-302'),
    (4, 'P-401');

INSERT INTO courses (department_id, course_title) VALUES
    (1, 'Бази даних'),
    (1, 'Алгоритми та структури даних'),
    (2, 'Мікроекономіка'),
    (3, 'Англійська мова для IT');

INSERT INTO enrollments (student_id, course_id, enrollment_date, grade) VALUES
    (1, 1, '2022-09-01', NULL),
    (1, 2, '2022-09-01', NULL),
    (2, 1, '2023-09-01', NULL),
    (3, 3, '2021-09-01', 92),
    (4, 4, '2022-09-01', NULL);

INSERT INTO vacancies (company_name, job_name) VALUES
    ('EPAM',        'Junior Developer'),
    ('Nova Poshta', 'Analyst'),
    ('Rozetka',     'Support Specialist');

INSERT INTO applications (student_id, vacancy_id, application_date, status) VALUES
    (1, 1, '2024-03-01', 'submitted'),
    (1, 2, '2024-03-05', 'submitted'),
    (2, 2, '2024-03-02', 'accepted'),
    (3, 3, '2024-02-20', 'rejected');

-- Початкова історія відповідає наявним кімнатам студентів.
INSERT INTO residencies (student_id, room_id, start_reason)
SELECT student_id, room_id, 'Початкове поселення' FROM students WHERE room_id IS NOT NULL;

INSERT INTO announcements (dorm_id, author_id, title, body) VALUES
(1, 5, 'Вітаємо у DormHub', 'Тут публікуються оголошення адміністрації вашого гуртожитку.');
INSERT INTO events (dorm_id, author_id, title, body, starts_at, place, capacity) VALUES
(1, 5, 'Зустріч мешканців', 'Обговорення питань проживання та пропозицій мешканців.',
 CURRENT_TIMESTAMP + INTERVAL '7 days', 'Хол першого поверху', 30);
COMMIT;
