-- Оновлення наявної БД після попередньої версії db.sql.
-- Зберігає користувачів, кімнати, повідомлення та решту наявних записів.
-- Події більше не входять до MVP. Їхні таблиці не видаляються міграцією,
-- щоб оновлення не втрачало дані; вони залишаються поза робочим API.
CREATE TABLE IF NOT EXISTS request_categories (
    name TEXT PRIMARY KEY CHECK (name = trim(name) AND name <> ''),
    sort_order INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS request_statuses (
    name TEXT PRIMARY KEY CHECK (name = trim(name) AND name <> ''),
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_initial BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE UNIQUE INDEX IF NOT EXISTS one_initial_request_status ON request_statuses(is_initial) WHERE is_initial;

INSERT INTO request_categories (name, sort_order) VALUES
    ('Сантехніка', 1), ('Електрика', 2), ('Меблі', 3),
    ('Інтернет', 4), ('Прибирання', 5), ('Інше', 6)
ON CONFLICT (name) DO NOTHING;
INSERT INTO request_statuses (name, sort_order) VALUES
    ('Нова', 1), ('Прийнята', 2), ('В роботі', 3),
    ('Виконана', 4), ('Закрита', 5), ('Скасована', 6)
ON CONFLICT (name) DO NOTHING;
UPDATE request_statuses SET is_initial = TRUE
WHERE name = 'Нова' AND NOT EXISTS (SELECT 1 FROM request_statuses WHERE is_initial);

-- Зберігаємо також довідникові значення, які вже є у зверненнях.
INSERT INTO request_categories (name)
SELECT DISTINCT category FROM maintenance_requests ON CONFLICT (name) DO NOTHING;
INSERT INTO request_statuses (name)
SELECT status FROM maintenance_requests UNION SELECT status FROM request_status_history
ON CONFLICT (name) DO NOTHING;

ALTER TABLE maintenance_requests DROP CONSTRAINT IF EXISTS maintenance_requests_category_check;
ALTER TABLE maintenance_requests DROP CONSTRAINT IF EXISTS maintenance_requests_status_check;
ALTER TABLE request_status_history DROP CONSTRAINT IF EXISTS request_status_history_status_check;
ALTER TABLE maintenance_requests ALTER COLUMN status DROP DEFAULT;
ALTER TABLE rooms ALTER COLUMN capacity DROP DEFAULT;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM rooms WHERE capacity > 4) THEN
        RAISE EXCEPTION 'Зменште місткість кімнат зі значенням capacity > 4 до 4 або менше перед міграцією';
    END IF;
END $$;
ALTER TABLE rooms DROP CONSTRAINT IF EXISTS rooms_capacity_check;
ALTER TABLE rooms ADD CONSTRAINT rooms_capacity_check CHECK (capacity BETWEEN 1 AND 4);

CREATE TABLE IF NOT EXISTS room_places (
    place_id     SERIAL PRIMARY KEY,
    room_id      INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE RESTRICT,
    place_number INTEGER NOT NULL CHECK (place_number > 0),
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (room_id, place_number),
    UNIQUE (place_id, room_id)
);

ALTER TABLE students ADD COLUMN IF NOT EXISTS place_id INTEGER;
ALTER TABLE residencies ADD COLUMN IF NOT EXISTS place_id INTEGER;

INSERT INTO room_places (room_id, place_number)
SELECT r.room_id, places.place_number
FROM rooms r
CROSS JOIN LATERAL generate_series(1, r.capacity) AS places(place_number)
ON CONFLICT (room_id, place_number) DO NOTHING;

WITH numbered_students AS (
    SELECT s.student_id, s.room_id,
           row_number() OVER (PARTITION BY s.room_id ORDER BY s.student_id) AS place_order
    FROM students s
    WHERE s.room_id IS NOT NULL AND s.place_id IS NULL
), numbered_places AS (
    SELECT places.room_id, places.place_id,
           row_number() OVER (PARTITION BY places.room_id ORDER BY places.place_number) AS place_order
    FROM room_places places
    WHERE NOT EXISTS (
        SELECT 1 FROM students occupied WHERE occupied.place_id = places.place_id
    )
)
UPDATE students s
SET place_id = numbered_places.place_id
FROM numbered_students, numbered_places
WHERE s.student_id = numbered_students.student_id
  AND numbered_places.room_id = numbered_students.room_id
  AND numbered_places.place_order = numbered_students.place_order;

WITH numbered_residencies AS (
    SELECT h.residency_id, h.room_id,
           row_number() OVER (PARTITION BY h.room_id ORDER BY h.residency_id) AS place_order
    FROM residencies h
    WHERE h.place_id IS NULL
)
UPDATE residencies h
SET place_id = places.place_id
FROM numbered_residencies numbered, room_places places
WHERE h.residency_id = numbered.residency_id
  AND places.room_id = numbered.room_id
  AND places.place_number = ((numbered.place_order - 1) % (
      SELECT count(*) FROM room_places room_capacity
      WHERE room_capacity.room_id = numbered.room_id
  )) + 1;

ALTER TABLE residencies
    ALTER COLUMN place_id SET NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS one_current_student_per_place
    ON students(place_id) WHERE place_id IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'students_place_room_fkey') THEN
        ALTER TABLE students ADD CONSTRAINT students_place_room_fkey
            FOREIGN KEY (place_id, room_id) REFERENCES room_places(place_id, room_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'residencies_place_room_fkey') THEN
        ALTER TABLE residencies ADD CONSTRAINT residencies_place_room_fkey
            FOREIGN KEY (place_id, room_id) REFERENCES room_places(place_id, room_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'maintenance_requests'::regclass
                   AND conname = 'maintenance_requests_category_fkey') THEN
        ALTER TABLE maintenance_requests ADD CONSTRAINT maintenance_requests_category_fkey
            FOREIGN KEY (category) REFERENCES request_categories(name) ON UPDATE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'maintenance_requests'::regclass
                   AND conname = 'maintenance_requests_status_fkey') THEN
        ALTER TABLE maintenance_requests ADD CONSTRAINT maintenance_requests_status_fkey
            FOREIGN KEY (status) REFERENCES request_statuses(name) ON UPDATE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'request_status_history'::regclass
                   AND conname = 'request_status_history_status_fkey') THEN
        ALTER TABLE request_status_history ADD CONSTRAINT request_status_history_status_fkey
            FOREIGN KEY (status) REFERENCES request_statuses(name) ON UPDATE CASCADE;
    END IF;
END $$;
