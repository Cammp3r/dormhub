import customtkinter as ctk

from data import mock_data
from ui import theme


class ParkingPage(ctk.CTkScrollableFrame):
    title = "Паркінг"

    def __init__(self, master, user=None):
        super().__init__(master, fg_color="transparent")
        theme.page_title(self, "Паркувальні місця")

        ctk.CTkLabel(
            self,
            text="Дані паркінгу поки що демонстраційні.",
            text_color=theme.MUTED,
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 12))

        users_by_id = {item["user_id"]: item for item in mock_data.users}
        dorms_by_id = {item["dorm_id"]: item for item in mock_data.dorms}

        for slot in mock_data.parking_slots:
            owner = users_by_id.get(slot["user_id"])
            dorm = dorms_by_id.get(slot["dorm_id"])
            owner_name = (
                f"{owner['first_name']} {owner['last_name']}"
                if owner
                else "Вільне місце"
            )
            dorm_name = f"Гуртожиток №{dorm['dorm_number']}" if dorm else "Невідомий гуртожиток"

            row = theme.card(self, pady=4)
            ctk.CTkLabel(
                row,
                text=slot["slot_number"],
                width=90,
                font=theme.font(18, bold=True),
                anchor="w",
            ).pack(side="left", padx=16, pady=14)
            details = ctk.CTkFrame(row, fg_color="transparent")
            details.pack(side="left", fill="x", expand=True, pady=10)
            ctk.CTkLabel(
                details,
                text=owner_name,
                font=theme.font(15, bold=True),
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                details,
                text=dorm_name,
                text_color=theme.MUTED,
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                row,
                text="Зайняте" if owner else "Вільне",
                text_color="#EF4444" if owner else "#10B981",
                font=theme.font(13, bold=True),
            ).pack(side="right", padx=16)
