from datetime import datetime

# ----------  люди і проживання ----------
dorms = [
    {"id": 1, "name": "Гуртожиток №7", "address": "вул. Політехнічна, 37"},
    {"id": 2, "name": "Гуртожиток №19", "address": "вул. Борщагівська, 146"},
]

rooms = [
    {"id": 1, "dorm_id": 1, "number": "412", "floor": 4, "capacity": 3},
    {"id": 2, "dorm_id": 1, "number": "413", "floor": 4, "capacity": 2},
    {"id": 3, "dorm_id": 2, "number": "105", "floor": 1, "capacity": 3},
]

users = [
    {"id": 1, "login": "camper", "password": "1234", "full_name": "Кемпер Іваненко",
     "faculty": "ФІОТ", "group": "ІП-31", "room_id": 1, "role": "student"},
    {"id": 2, "login": "olena", "password": "1234", "full_name": "Олена Коваль",
     "faculty": "ФІОТ", "group": "ІП-31", "room_id": 1, "role": "student"},
    {"id": 3, "login": "max", "password": "1234", "full_name": "Максим Шевчук",
     "faculty": "ФПМ", "group": "КВ-22", "room_id": 1, "role": "student"},
    {"id": 4, "login": "dmytro", "password": "1234", "full_name": "Дмитро Бойко",
     "faculty": "ІАТЕ", "group": "ТВ-21", "room_id": 2, "role": "student"},
    {"id": 5, "login": "admin", "password": "admin", "full_name": "Георгій Антонюк",
     "faculty": "-", "group": "-", "room_id": None, "role": "commandant"},
]

# ---------- чати ----------
chats = [
    {"id": 1, "title": "Кімната 412", "is_group": True, "created_by": 1},
    {"id": 2, "title": "4 поверх — гурт. 7", "is_group": True, "created_by": 2},
    {"id": 3, "title": "Дмитро Бойко", "is_group": False, "created_by": 1},
    {"id": 4, "title": "Оголошення від коменданта", "is_group": True, "created_by": 5},
]

chat_members = [
    {"chat_id": 1, "user_id": 1}, {"chat_id": 1, "user_id": 2}, {"chat_id": 1, "user_id": 3},
    {"chat_id": 2, "user_id": 1}, {"chat_id": 2, "user_id": 2}, {"chat_id": 2, "user_id": 3},
    {"chat_id": 2, "user_id": 4},
    {"chat_id": 3, "user_id": 1}, {"chat_id": 3, "user_id": 4},
    {"chat_id": 4, "user_id": 1}, {"chat_id": 4, "user_id": 2}, {"chat_id": 4, "user_id": 5},
]

messages = [
    {"id": 1, "chat_id": 1, "author_id": 2, "text": "Хто сьогодні виносить сміття?",
     "sent_at": datetime(2026, 10, 13, 19, 2)},
    {"id": 2, "chat_id": 1, "author_id": 3, "text": "Я вчора виносив 😅",
     "sent_at": datetime(2026, 10, 13, 19, 5)},
    {"id": 3, "chat_id": 1, "author_id": 1, "text": "Окей, я винесу",
     "sent_at": datetime(2026, 10, 13, 19, 7)},
    {"id": 4, "chat_id": 2, "author_id": 4, "text": "У когось є подовжувач?",
     "sent_at": datetime(2026, 10, 14, 8, 40)},
    {"id": 5, "chat_id": 3, "author_id": 4, "text": "Скинеш конспект з БД?",
     "sent_at": datetime(2026, 10, 12, 21, 15)},
    {"id": 6, "chat_id": 4, "author_id": 5, "text": "У п'ятницю з 10:00 не буде гарячої води.",
     "sent_at": datetime(2026, 10, 14, 9, 0)},
]

# ---------- життя гуртожитку ----------
announcements = [
    {"id": 1, "dorm_id": 1, "author_id": 5, "title": "Відключення гарячої води",
     "body": "У п'ятницю 17.10 з 10:00 до 18:00 планові роботи.",
     "created_at": datetime(2026, 10, 14, 9, 0)},
    {"id": 2, "dorm_id": 1, "author_id": 5, "title": "Санітарна перевірка",
     "body": "Перевірка кімнат 4–5 поверхів у понеділок. Приберіть, будь ласка.",
     "created_at": datetime(2026, 10, 11, 12, 30)},
]

events = [
    {"id": 1, "dorm_id": 1, "title": "Турнір з настільного тенісу", "place": "Хол 1 поверху",
     "starts_at": datetime(2026, 10, 18, 17, 0), "organizer_id": 3},
    {"id": 2, "dorm_id": 1, "title": "Кіновечір", "place": "Кімната відпочинку",
     "starts_at": datetime(2026, 10, 20, 20, 0), "organizer_id": 2},
]

event_participants = [
    {"event_id": 1, "user_id": 3}, {"event_id": 1, "user_id": 4},
    {"event_id": 2, "user_id": 2},
]

request_categories = ["Сантехніка", "Електрика", "Меблі", "Інтернет", "Інше"]

maintenance_requests = [
    {"id": 1, "room_id": 1, "author_id": 1, "category": "Сантехніка",
     "description": "Тече кран у ванній", "status": "В роботі",
     "created_at": datetime(2026, 10, 10, 14, 0)},
    {"id": 2, "room_id": 1, "author_id": 2, "category": "Електрика",
     "description": "Не працює розетка біля вікна", "status": "Нова",
     "created_at": datetime(2026, 10, 13, 10, 20)},
]