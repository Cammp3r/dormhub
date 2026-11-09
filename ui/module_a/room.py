import customtkinter as ctk
from data import repository as repo
from ui import theme


class RoomPage(ctk.CTkScrollableFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        theme.page_title(self, "Моя кімната")

        student = repo.get_student_for_user(user["user_id"])
        room = repo.get_room_info(student["room_id"]) if student and student["room_id"] else None
        if room is None:
            ctk.CTkLabel(self, text="Ви не заселені в жодну кімнату.",
                         text_color=theme.MUTED).pack(padx=24, anchor="w")
            return

        roommates = repo.get_roommates(room["room_id"])

        info = theme.card(self)
        ctk.CTkLabel(info, text=f"Кімната {room['room_number']}", font=theme.font(22, bold=True)).pack(
            anchor="w", padx=20, pady=(16, 0))
        ctk.CTkLabel(info, text=f"Гуртожиток №{room['dorm_number']}  ·  {room['address']}",
                     text_color=theme.MUTED).pack(anchor="w", padx=20)

        stats = ctk.CTkFrame(info, fg_color="transparent")
        stats.pack(fill="x", padx=20, pady=16)
        for title, value in [("Поверх", room["floor"]), ("Мешканців", len(roommates))]:
            box = ctk.CTkFrame(stats, corner_radius=10)
            box.pack(side="left", padx=(0, 12), ipadx=16, ipady=8)
            ctk.CTkLabel(box, text=str(value), font=theme.font(20, bold=True)).pack()
            ctk.CTkLabel(box, text=title, text_color=theme.MUTED, font=theme.font(12)).pack()

        ctk.CTkLabel(self, text="Сусіди", font=theme.font(18, bold=True)).pack(
            anchor="w", padx=24, pady=(16, 4))
        for mate in roommates:
            row = theme.card(self, pady=4)
            full_name = repo.get_user_name(mate)
            initials = "".join(p[0] for p in full_name.split()[:2])
            ctk.CTkLabel(row, text=initials, width=40, height=40, corner_radius=20,
                         fg_color=theme.ACCENT, text_color="white",
                         font=theme.font(14, bold=True)).pack(side="left", padx=14, pady=10)
            me = "  (ви)" if mate["user_id"] == user["user_id"] else ""
            ctk.CTkLabel(row, text=full_name + me, font=theme.font(15, bold=True)).pack(side="left")
            ctk.CTkLabel(row, text=mate["email"],
                         text_color=theme.MUTED).pack(side="right", padx=16)
