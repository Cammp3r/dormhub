from data import mock_data as db


current_user = None


def get_user(user_id):
    return next((user for user in db.users if user["user_id"] == user_id), None)


def get_all_users():
    return list(db.users)


def get_student_for_user(user_id):
    return next((student for student in db.students if student["user_id"] == user_id), None)


def get_user_name(user):
    return f"{user['first_name']} {user['last_name']}"


def update_profile(user_id, first_name, last_name, email):
    user = get_user(user_id)
    if user is None:
        raise ValueError(f"Користувача з user_id={user_id} не знайдено")
    user.update(first_name=first_name, last_name=last_name, email=email)


def get_room_info(room_id):
    room = next((room for room in db.rooms if room["room_id"] == room_id), None)
    if room is None:
        return None
    dorm = next(dorm for dorm in db.dorms if dorm["dorm_id"] == room["dorm_id"])
    return {**room, "dorm_number": dorm["dorm_number"], "address": dorm["address"]}


def get_roommates(room_id):
    student_ids = {student["user_id"] for student in db.students if student["room_id"] == room_id}
    return [user for user in db.users if user["user_id"] in student_ids]


def get_current_user():
    return get_user(1)
