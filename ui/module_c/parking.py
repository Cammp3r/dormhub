import customtkinter as ctk

from data import repository as repo
from ui import theme


class ParkingPage(ctk.CTkScrollableFrame):
    title = "Паркінг"

    def __init__(self, master, user=None):
        super().__init__(master, fg_color="transparent")
        theme.page_title(self, "Паркувальні місця")

        ctk.CTkLabel(
            self,
            text="Дані паркінгу завантажені з бази даних.",
            text_color=theme.MUTED,
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 12))

        for slot in repo.get_parking_slots():
            owner_name = (
                f"{slot['first_name']} {slot['last_name']}"
                if slot["user_id"]
                else "Вільне місце"
            )
            dorm_name = f"Гуртожиток №{slot['dorm_number']}"

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
                text="Зайняте" if slot["user_id"] else "Вільне",
                text_color="#EF4444" if slot["user_id"] else "#10B981",
                font=theme.font(13, bold=True),
            ).pack(side="right", padx=16)
