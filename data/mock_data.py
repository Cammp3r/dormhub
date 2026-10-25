from datetime import date

# Mock-дані повторюють таблиці та назви полів з db.sql.
dorms = [
    {"dorm_id": 1, "dorm_number": 1, "address": "вул. Степана Бандери 1-б"},
    {"dorm_id": 2, "dorm_number": 2, "address": "вул. Колотушкіна 1-а"},
    {"dorm_id": 3, "dorm_number": 3, "address": "вул. Тараса Шевченка 1-в"},
    {"dorm_id": 4, "dorm_number": 4, "address": "вул. Тараса Шевченка 2-в"},
]

users = [
    {"user_id": 1, "first_name": "Іван", "last_name": "Петренко",
     "email": "ivan.petrenko@example.com", "date_of_birth": date(2003, 5, 14),
     "registration_date": date(2024, 9, 1), "status": "active", "dorm_id": 1},
    {"user_id": 2, "first_name": "Марія", "last_name": "Коваль",
     "email": "maria.koval@example.com", "date_of_birth": date(2002, 11, 2),
     "registration_date": date(2024, 9, 1), "status": "active", "dorm_id": 1},
    {"user_id": 3, "first_name": "Олег", "last_name": "Бондар",
     "email": "oleg.bondar@example.com", "date_of_birth": date(2001, 3, 20),
     "registration_date": date(2024, 9, 1), "status": "active", "dorm_id": 2},
    {"user_id": 4, "first_name": "Анна", "last_name": "Сидоренко",
     "email": "anna.sydorenko@example.com", "date_of_birth": date(2004, 7, 8),
     "registration_date": date(2024, 9, 1), "status": "active", "dorm_id": 2},
    {"user_id": 5, "first_name": "Сергій", "last_name": "Мельник",
     "email": "sergiy.melnyk@example.com", "date_of_birth": date(1985, 1, 15),
     "registration_date": date(2024, 8, 20), "status": "active", "dorm_id": 1},
    {"user_id": 6, "first_name": "Ольга", "last_name": "Ткаченко",
     "email": "olha.tkachenko@example.com", "date_of_birth": date(1990, 6, 22),
     "registration_date": date(2024, 8, 20), "status": "active", "dorm_id": 1},
    {"user_id": 7, "first_name": "Павло", "last_name": "Кравець",
     "email": "pavlo.kravets@example.com", "date_of_birth": date(1988, 9, 30),
     "registration_date": date(2024, 8, 20), "status": "active", "dorm_id": 3},
    {"user_id": 8, "first_name": "Дмитро", "last_name": "Шевченко",
     "email": "dmytro.shevchenko@example.com", "date_of_birth": date(2004, 2, 11),
     "registration_date": date(2024, 9, 1), "status": "active", "dorm_id": None},
    {"user_id": 9, "first_name": "Степан", "last_name": "Бендера",
     "email": "stpbdn@gmail.com", "date_of_birth": date(2001, 9, 11),
     "registration_date": date(2024, 8, 20), "status": "active", "dorm_id": 2},
    {"user_id": 10, "first_name": "Бен", "last_name": "Мохамед",
     "email": "ben@gmail.com", "date_of_birth": date(2001, 9, 11),
     "registration_date": date(2024, 9, 1), "status": "active", "dorm_id": 2},
]

departments = [
    {"department_id": 1, "department_name": "Комп'ютерні науки"},
    {"department_id": 2, "department_name": "Економіка"},
    {"department_id": 3, "department_name": "Іноземні мови"},
]

rooms = [
    {"room_id": 1, "dorm_id": 1, "room_number": "101", "floor": 1},
    {"room_id": 2, "dorm_id": 1, "room_number": "102", "floor": 1},
    {"room_id": 3, "dorm_id": 2, "room_number": "201", "floor": 2},
    {"room_id": 4, "dorm_id": 2, "room_number": "202", "floor": 2},
    {"room_id": 5, "dorm_id": 3, "room_number": "301", "floor": 3},
    {"room_id": 6, "dorm_id": 3, "room_number": "228", "floor": 2},
]

students = [
    {"student_id": 1, "enrollment_year": 2022, "room_id": 1, "status": "enrolled", "user_id": 1},
    {"student_id": 2, "enrollment_year": 2023, "room_id": 1, "status": "enrolled", "user_id": 2},
    {"student_id": 3, "enrollment_year": 2021, "room_id": 3, "status": "graduated", "user_id": 3},
    {"student_id": 4, "enrollment_year": 2022, "room_id": 4, "status": "on_leave", "user_id": 4},
    {"student_id": 5, "enrollment_year": 2024, "room_id": None, "status": "enrolled", "user_id": 8},
]

dorm_admins = [
    {"admin_id": 1, "user_id": 5, "dorm_id": 1},
    {"admin_id": 2, "user_id": 6, "dorm_id": 1},
    {"admin_id": 3, "user_id": 9, "dorm_id": 2},
    {"admin_id": 4, "user_id": 7, "dorm_id": 3},
]

parking_slots = [
    {"parking_slot_id": 1, "dorm_id": 1, "user_id": 1, "slot_number": "P-101"},
    {"parking_slot_id": 2, "dorm_id": 1, "user_id": 2, "slot_number": "P-102"},
    {"parking_slot_id": 3, "dorm_id": 2, "user_id": 3, "slot_number": "P-201"},
    {"parking_slot_id": 4, "dorm_id": 2, "user_id": 4, "slot_number": "P-202"},
    {"parking_slot_id": 5, "dorm_id": 1, "user_id": 5, "slot_number": "P-103"},
    {"parking_slot_id": 6, "dorm_id": 2, "user_id": 9, "slot_number": "P-203"},
    {"parking_slot_id": 7, "dorm_id": 3, "user_id": 7, "slot_number": "P-301"},
    {"parking_slot_id": 8, "dorm_id": 3, "user_id": None, "slot_number": "P-302"},
    {"parking_slot_id": 9, "dorm_id": 4, "user_id": None, "slot_number": "P-401"},
]

courses = [
    {"course_id": 1, "department_id": 1, "course_title": "Бази даних"},
    {"course_id": 2, "department_id": 1, "course_title": "Алгоритми та структури даних"},
    {"course_id": 3, "department_id": 2, "course_title": "Мікроекономіка"},
    {"course_id": 4, "department_id": 3, "course_title": "Англійська мова для IT"},
]

enrollments = [
    {"enrollment_id": 1, "student_id": 1, "course_id": 1, "enrollment_date": date(2022, 9, 1), "grade": None},
    {"enrollment_id": 2, "student_id": 1, "course_id": 2, "enrollment_date": date(2022, 9, 1), "grade": None},
    {"enrollment_id": 3, "student_id": 2, "course_id": 1, "enrollment_date": date(2023, 9, 1), "grade": None},
    {"enrollment_id": 4, "student_id": 3, "course_id": 3, "enrollment_date": date(2021, 9, 1), "grade": 92},
    {"enrollment_id": 5, "student_id": 4, "course_id": 4, "enrollment_date": date(2022, 9, 1), "grade": None},
]

vacancies = [
    {"vacancy_id": 1, "company_name": "EPAM", "job_name": "Junior Developer"},
    {"vacancy_id": 2, "company_name": "Nova Poshta", "job_name": "Analyst"},
    {"vacancy_id": 3, "company_name": "Rozetka", "job_name": "Support Specialist"},
]

applications = [
    {"application_id": 1, "student_id": 1, "vacancy_id": 1, "application_date": date(2024, 3, 1), "status": "submitted"},
    {"application_id": 2, "student_id": 1, "vacancy_id": 2, "application_date": date(2024, 3, 5), "status": "submitted"},
    {"application_id": 3, "student_id": 2, "vacancy_id": 2, "application_date": date(2024, 3, 2), "status": "accepted"},
    {"application_id": 4, "student_id": 3, "vacancy_id": 3, "application_date": date(2024, 2, 20), "status": "rejected"},
]
