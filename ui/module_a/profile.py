import customtkinter as ctk
from data import repository as repo
from ui import theme


class ProfilePage(ctk.CTkScrollableFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        self.user = user
        theme.page_title(self, "Мій профіль")

        head = theme.card(self)
        full_name = repo.get_user_name(user)
        initials = "".join(part[0] for part in full_name.split()[:2])
        ctk.CTkLabel(head, text=initials, width=72, height=72, corner_radius=36,
                     fg_color=theme.ACCENT, text_color="white",
                     font=theme.font(26, bold=True)).pack(side="left", padx=20, pady=20)
        info = ctk.CTkFrame(head, fg_color="transparent")
        info.pack(side="left", fill="x")
        self.name_label = ctk.CTkLabel(info, text=full_name, font=theme.font(20, bold=True), anchor="w")
        self.name_label.pack(anchor="w")
        role = "Комендант" if repo.is_dorm_admin(user["user_id"]) else "Користувач"
        ctk.CTkLabel(info, text=f"{user['email']}  ·  {role}", text_color=theme.MUTED,
                     anchor="w").pack(anchor="w")

        form = theme.card(self)
        ctk.CTkLabel(form, text="Редагувати дані", font=theme.font(16, bold=True)).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 8))

        self.entries = {}
        fields = [("first_name", "Ім'я"), ("last_name", "Прізвище"), ("email", "Email")]
        for i, (key, label) in enumerate(fields, start=1):
            ctk.CTkLabel(form, text=label, anchor="w", width=100).grid(row=i, column=0, sticky="w", padx=20, pady=6)
            entry = ctk.CTkEntry(form, width=320)
            entry.insert(0, user[key])
            entry.grid(row=i, column=1, sticky="w", padx=(0, 20), pady=6)
            self.entries[key] = entry

        self.status = ctk.CTkLabel(form, text="", text_color="#10B981")
        self.status.grid(row=4, column=1, sticky="w")
        ctk.CTkButton(form, text="Зберегти", fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self.save).grid(row=5, column=1, sticky="w", pady=(4, 20))

    def save(self):
        values = {k: e.get().strip() for k, e in self.entries.items()}
        if not all(values.values()):
            self.status.configure(text="Усі поля мають бути заповнені", text_color="#EF4444")
            return
        repo.update_profile(self.user["user_id"], **values)
        self.user = repo.get_user(self.user["user_id"])
        self.name_label.configure(text=repo.get_user_name(self.user))
        self.status.configure(text="✓ Збережено", text_color="#10B981")
