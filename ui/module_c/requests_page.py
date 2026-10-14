import customtkinter as ctk
from data import repository as repo
from ui import theme


class RequestsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        self.user = user
        self.render()

    def render(self):
        for w in self.winfo_children():
            w.destroy()
        theme.page_title(self, "Заявки на ремонт")

        if not self.user["room_id"]:
            ctk.CTkLabel(self, text="Заявки можуть подавати лише заселені студенти.",
                         text_color=theme.MUTED).pack(anchor="w", padx=24)
            return

        form = theme.card(self)
        ctk.CTkLabel(form, text="Нова заявка", font=theme.font(15, bold=True)).pack(
            anchor="w", padx=16, pady=(12, 4))
        self.category = ctk.CTkOptionMenu(form, values=repo.get_request_categories(),
                                          fg_color=theme.ACCENT, button_color=theme.ACCENT_HOVER)
        self.category.pack(anchor="w", padx=16, pady=4)
        self.description = ctk.CTkTextbox(form, height=70)
        self.description.pack(fill="x", padx=16, pady=4)
        self.error = ctk.CTkLabel(form, text="", text_color="#EF4444")
        self.error.pack(anchor="w", padx=16)
        ctk.CTkButton(form, text="Надіслати заявку", fg_color=theme.ACCENT,
                      hover_color=theme.ACCENT_HOVER, command=self.submit).pack(
            anchor="e", padx=16, pady=(0, 12))

        ctk.CTkLabel(self, text="Заявки вашої кімнати", font=theme.font(18, bold=True)).pack(
            anchor="w", padx=24, pady=(16, 4))
        for r in repo.get_requests_for_room(self.user["room_id"]):
            c = theme.card(self, pady=4)
            ctk.CTkLabel(c, text=r["status"], width=90, corner_radius=8, text_color="white",
                         fg_color=theme.STATUS_COLORS.get(r["status"], "gray")).pack(
                side="right", padx=16)
            ctk.CTkLabel(c, text=f"{r['category']}: {r['description']}", font=theme.font(14, bold=True),
                         anchor="w").pack(fill="x", padx=16, pady=(10, 0))
            author = repo.get_user(r["author_id"])["full_name"]
            ctk.CTkLabel(c, text=f"{author}  ·  {r['created_at']:%d.%m.%Y %H:%M}",
                         text_color=theme.MUTED, font=theme.font(12), anchor="w").pack(
                fill="x", padx=16, pady=(0, 10))

    def submit(self):
        text = self.description.get("1.0", "end").strip()
        if not text:
            self.error.configure(text="Опишіть проблему")
            return
        repo.create_request(self.user["room_id"], self.user["id"], self.category.get(), text)
        self.render()
