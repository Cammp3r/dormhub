from datetime import datetime
from data import mock_data as db

current_user = None


def _next_id(table):
    return max((row["id"] for row in table), default=0) + 1


# ===================== Модуль A =====================

def login(login, password):
    global current_user
    for u in db.users:
        if u["login"] == login and u["password"] == password:
            current_user = u
            return u
    return None


def logout():
    global current_user
    current_user = None


def get_user(user_id):
    return next((u for u in db.users if u["id"] == user_id), None)


def get_all_users():
    return list(db.users)


def update_profile(user_id, full_name, faculty, group):
    u = get_user(user_id)
    u.update(full_name=full_name, faculty=faculty, group=group)


def get_room_info(room_id):
    room = next((r for r in db.rooms if r["id"] == room_id), None)
    if room is None:
        return None
    dorm = next(d for d in db.dorms if d["id"] == room["dorm_id"])
    return {**room, "dorm_name": dorm["name"], "dorm_address": dorm["address"]}


def get_roommates(room_id):
    return [u for u in db.users if u["room_id"] == room_id]


# ===================== Модуль B =====================

def get_chats_for_user(user_id):
    ids = {m["chat_id"] for m in db.chat_members if m["user_id"] == user_id}
    result = []
    for c in db.chats:
        if c["id"] in ids:
            msgs = get_messages(c["id"])
            last = msgs[-1] if msgs else None
            result.append({**c, "last_message": last})
    result.sort(key=lambda c: c["last_message"]["sent_at"] if c["last_message"] else datetime.min,
                reverse=True)
    return result


def get_messages(chat_id):
    rows = [m for m in db.messages if m["chat_id"] == chat_id]
    rows.sort(key=lambda m: m["sent_at"])
    return [{**m, "author_name": get_user(m["author_id"])["full_name"]} for m in rows]


def get_chat_members(chat_id):
    ids = [m["user_id"] for m in db.chat_members if m["chat_id"] == chat_id]
    return [get_user(i) for i in ids]


def send_message(chat_id, author_id, text):
    db.messages.append({"id": _next_id(db.messages), "chat_id": chat_id,
                        "author_id": author_id, "text": text, "sent_at": datetime.now()})


def create_group_chat(title, creator_id, member_ids):
    chat_id = _next_id(db.chats)
    db.chats.append({"id": chat_id, "title": title, "is_group": True, "created_by": creator_id})
    for uid in set(member_ids) | {creator_id}:
        db.chat_members.append({"chat_id": chat_id, "user_id": uid})
    return chat_id


# ===================== Модуль C =====================

def get_announcements():
    rows = sorted(db.announcements, key=lambda a: a["created_at"], reverse=True)
    return [{**a, "author_name": get_user(a["author_id"])["full_name"]} for a in rows]


def add_announcement(author_id, title, body):
    db.announcements.append({"id": _next_id(db.announcements), "dorm_id": 1,
                             "author_id": author_id, "title": title, "body": body,
                             "created_at": datetime.now()})


def get_events():
    result = []
    for e in sorted(db.events, key=lambda e: e["starts_at"]):
        ids = [p["user_id"] for p in db.event_participants if p["event_id"] == e["id"]]
        result.append({**e, "participant_ids": ids})
    return result


def toggle_participation(event_id, user_id):
    row = {"event_id": event_id, "user_id": user_id}
    if row in db.event_participants:
        db.event_participants.remove(row)
    else:
        db.event_participants.append(row)


def get_request_categories():
    return list(db.request_categories)


def get_requests_for_room(room_id):
    rows = [r for r in db.maintenance_requests if r["room_id"] == room_id]
    return sorted(rows, key=lambda r: r["created_at"], reverse=True)


def create_request(room_id, author_id, category, description):
    db.maintenance_requests.append({"id": _next_id(db.maintenance_requests), "room_id": room_id,
                                    "author_id": author_id, "category": category,
                                    "description": description, "status": "Нова",
                                    "created_at": datetime.now()})
