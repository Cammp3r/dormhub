-- Оновлення наявної БД після попередньої версії db.sql.
-- Зберігає користувачів, кімнати, повідомлення та решту наявних записів.
BEGIN;
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
COMMIT;
