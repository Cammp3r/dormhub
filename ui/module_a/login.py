import customtkinter as ctk
from data import repository as repo
from ui import theme


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_success):
        super().__init__(master, fg_color="transparent")
        self.on_success = on_success

        box = ctk.CTkFrame(self, corner_radius=16, width=380)
        box.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(box, text="🏠 DormHub", font=theme.font(30, bold=True)).pack(pady=(32, 4), padx=40)
        ctk.CTkLabel(box, text="Чати та життя гуртожитку", font=theme.font(14),
                     text_color=theme.MUTED).pack(pady=(0, 24))

        self.login_entry = ctk.CTkEntry(box, placeholder_text="Логін", width=280, height=40)
        self.login_entry.pack(pady=6, padx=40)
        self.password_entry = ctk.CTkEntry(box, placeholder_text="Пароль", show="•", width=280, height=40)
        self.password_entry.pack(pady=6)

        self.error_label = ctk.CTkLabel(box, text="", text_color="#EF4444")
        self.error_label.pack()

        ctk.CTkButton(box, text="Увійти", width=280, height=40, font=theme.font(15, bold=True),
                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
                      command=self.try_login).pack(pady=(4, 12))

        ctk.CTkLabel(box, text="Тестовий вхід: camper / 1234   або   admin / admin",
                     font=theme.font(12), text_color=theme.MUTED).pack(pady=(0, 28))
    
        self.password_entry.bind("<Return>", lambda e: self.try_login())
        self.login_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.login_entry.focus()

    def try_login(self):
        user = repo.login(self.login_entry.get().strip(), self.password_entry.get())
        if user:
            self.on_success(user)
        else:
            self.error_label.configure(text="Невірний логін або пароль")
