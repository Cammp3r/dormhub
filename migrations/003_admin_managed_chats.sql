ALTER TABLE room_chats
    ADD COLUMN IF NOT EXISTS title TEXT,
    ADD COLUMN IF NOT EXISTS dorm_id INTEGER;

UPDATE room_chats AS rc
SET title = COALESCE(NULLIF(BTRIM(rc.title), ''), 'Кімната ' || r.room_number),
    dorm_id = COALESCE(rc.dorm_id, r.dorm_id)
FROM rooms AS r
WHERE rc.room_id = r.room_id
  AND (rc.title IS NULL OR rc.dorm_id IS NULL);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM room_chats
        WHERE title IS NULL OR dorm_id IS NULL
    ) THEN
        RAISE EXCEPTION 'Не вдалося визначити назву або гуртожиток для існуючого чату';
    END IF;
END $$;

ALTER TABLE room_chats
    ALTER COLUMN room_id DROP NOT NULL,
    ALTER COLUMN title SET NOT NULL,
    ALTER COLUMN dorm_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'room_chats'::regclass
          AND conname = 'room_chats_title_check'
    ) THEN
        ALTER TABLE room_chats
            ADD CONSTRAINT room_chats_title_check
            CHECK (title = BTRIM(title) AND title <> '');
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'room_chats'::regclass
          AND conname = 'room_chats_dorm_id_fkey'
    ) THEN
        ALTER TABLE room_chats
            ADD CONSTRAINT room_chats_dorm_id_fkey
            FOREIGN KEY (dorm_id) REFERENCES dorms(dorm_id) ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS room_chats_dorm_idx ON room_chats(dorm_id);

CREATE TABLE IF NOT EXISTS room_chat_members (
    room_chat_id INTEGER NOT NULL
        REFERENCES room_chats(room_chat_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL
        REFERENCES users(user_id) ON DELETE CASCADE,
    added_by INTEGER NOT NULL
        REFERENCES users(user_id) ON DELETE RESTRICT,
    added_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (room_chat_id, user_id)
);

CREATE INDEX IF NOT EXISTS room_chat_members_user_idx
    ON room_chat_members(user_id, room_chat_id);
