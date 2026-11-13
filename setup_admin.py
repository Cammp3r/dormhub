"""Створення першого адміністратора з реальними даними, введеними власником БД."""
from psycopg2 import Error as DatabaseError

from data.repository import setup_first_admin


def main():
    print('Початкове налаштування DormHub. Введіть дані вашого гуртожитку й адміністратора.')
    try:
        user_id = setup_first_admin(
            dorm_number=input('Номер гуртожитку: ').strip(),
            address=input('Адреса гуртожитку: ').strip(),
            first_name=input('Ім’я адміністратора: ').strip(),
            last_name=input('Прізвище адміністратора: ').strip(),
            email=input('Email адміністратора: ').strip(),
        )
    except (ValueError, RuntimeError) as error:
        print(f'Не вдалося створити адміністратора: {error}')
        return 1
    except DatabaseError:
        print('Помилка БД. Перевірте підключення, унікальність email та формат введених даних.')
        return 1
    except (EOFError, KeyboardInterrupt):
        print('\nНалаштування скасовано.')
        return 1
    print(f'Адміністратора створено (ID: {user_id}). Увійдіть у застосунок за введеними ім’ям і прізвищем.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
