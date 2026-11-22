from pathlib import Path

import psycopg2

from db import get_database_settings


MIGRATIONS_DIR = Path(__file__).with_name("migrations")


def connect():
    settings = get_database_settings()
    return psycopg2.connect(**settings)


def ensure_migration_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def has_existing_schema(cursor):
    cursor.execute(
        "SELECT to_regclass('public.users') IS NOT NULL "
        "AND to_regclass('public.dorms') IS NOT NULL"
    )
    return cursor.fetchone()[0]


def applied_versions(cursor):
    cursor.execute("SELECT version FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}


def run():
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        raise RuntimeError(f"У каталозі {MIGRATIONS_DIR} немає міграцій")

    with connect() as connection:
        with connection.cursor() as cursor:
            ensure_migration_table(cursor)
            applied = applied_versions(cursor)

            if not applied and has_existing_schema(cursor):
                baseline = migration_files[0].name
                cursor.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (baseline,),
                )
                applied.add(baseline)
                print(f"Базову схему вже існує, пропущено {baseline}")

            for migration_file in migration_files:
                version = migration_file.name
                if version in applied:
                    continue
                print(f"Застосування {version}")
                cursor.execute(migration_file.read_text(encoding="utf-8"))
                cursor.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)",
                    (version,),
                )
        connection.commit()


if __name__ == "__main__":
    try:
        run()
    except psycopg2.Error as error:
        raise SystemExit(f"Помилка міграції PostgreSQL: {error}") from error
