import customtkinter as ctk
from data import repository as repo
from ui import theme


class RoomPage(ctk.CTkScrollableFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        theme.page_title(self, "Моя кімната")

        room = repo.get_room_info(user["room_id"]) if user["room_id"] else None
        if room is None:
            ctk.CTkLabel(self, text="Ви не заселені в жодну кімнату.",
                         text_color=theme.MUTED).pack(padx=24, anchor="w")
            return

        roommates = repo.get_roommates(room["id"])

        info = theme.card(self)
        ctk.CTkLabel(info, text=f"Кімната {room['number']}", font=theme.font(22, bold=True)).pack(
            anchor="w", padx=20, pady=(16, 0))
        ctk.CTkLabel(info, text=f"{room['dorm_name']}  ·  {room['dorm_address']}",
                     text_color=theme.MUTED).pack(anchor="w", padx=20)

        stats = ctk.CTkFrame(info, fg_color="transparent")
        stats.pack(fill="x", padx=20, pady=16)
        for title, value in [("Поверх", room["floor"]),
                             ("Місць", room["capacity"]),
                             ("Зайнято", f"{len(roommates)}/{room['capacity']}")]:
            box = ctk.CTkFrame(stats, corner_radius=10)
            box.pack(side="left", padx=(0, 12), ipadx=16, ipady=8)
            ctk.CTkLabel(box, text=str(value), font=theme.font(20, bold=True)).pack()
            ctk.CTkLabel(box, text=title, text_color=theme.MUTED, font=theme.font(12)).pack()

        ctk.CTkLabel(self, text="Сусіди", font=theme.font(18, bold=True)).pack(
            anchor="w", padx=24, pady=(16, 4))
        for mate in roommates:
            row = theme.card(self, pady=4)
            initials = "".join(p[0] for p in mate["full_name"].split()[:2])
            ctk.CTkLabel(row, text=initials, width=40, height=40, corner_radius=20,
                         fg_color=theme.ACCENT, text_color="white",
                         font=theme.font(14, bold=True)).pack(side="left", padx=14, pady=10)
            me = "  (ви)" if mate["id"] == user["id"] else ""
            ctk.CTkLabel(row, text=mate["full_name"] + me, font=theme.font(15, bold=True)).pack(side="left")
            ctk.CTkLabel(row, text=f"{mate['faculty']}, {mate['group']}",
                         text_color=theme.MUTED).pack(side="right", padx=16)
