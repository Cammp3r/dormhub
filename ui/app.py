import customtkinter as ctk
from data import repository as repo
from ui import theme
from ui.module_a.login import LoginFrame
from ui.module_a.profile import ProfilePage
from ui.module_a.room import RoomPage
from ui.module_b.chats import ChatsPage
from ui.module_c.announcements import AnnouncementsPage
from ui.module_c.events import EventsPage
from ui.module_c.requests_page import RequestsPage

PAGES = [
    ("💬  Чати", ChatsPage),
    ("📢  Оголошення", AnnouncementsPage),
    ("🎉  Події", EventsPage),
    ("🛠  Заявки", RequestsPage),
    ("🚪  Моя кімната", RoomPage),
    ("👤  Профіль", ProfilePage),
]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DormHub — гуртожиток КПІ")
        self.geometry("1100x700")
        self.minsize(900, 560)
        self.user = None
        self.show_login()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def show_login(self):
        self.clear()
        LoginFrame(self, on_success=self.on_login).pack(fill="both", expand=True)

    def on_login(self, user):
        self.user = user
        self.build_main()

    def logout(self):
        repo.logout()
        self.user = None
        self.show_login()

    def build_main(self):
        self.clear()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="🏠 DormHub", font=theme.font(22, bold=True)).pack(pady=(24, 4), padx=20, anchor="w")
        ctk.CTkLabel(sidebar, text=self.user["full_name"], text_color=theme.MUTED,
                     font=theme.font(12)).pack(padx=20, anchor="w", pady=(0, 20))

        self.nav_buttons = {}
        for text, page_cls in PAGES:
            btn = ctk.CTkButton(sidebar, text=text, anchor="w", height=40, corner_radius=8,
                                fg_color="transparent", text_color=("gray10", "gray90"),
                                hover_color=("gray80", "gray25"), font=theme.font(14),
                                command=lambda p=page_cls: self.open_page(p))
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[page_cls] = btn

        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=12, pady=16)
        theme_switch = ctk.CTkSwitch(bottom, text="Темна тема",
                                     command=lambda: ctk.set_appearance_mode(
                                         "dark" if theme_switch.get() else "light"))
        theme_switch.pack(anchor="w", pady=(0, 10))
        if ctk.get_appearance_mode() == "Dark":
            theme_switch.select()
        ctk.CTkButton(bottom, text="Вийти", fg_color="#EF4444", hover_color="#DC2626",
                      command=self.logout).pack(fill="x")

        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")

        self.open_page(ChatsPage)

    def open_page(self, page_cls):
        for cls, btn in self.nav_buttons.items():
            btn.configure(fg_color=theme.ACCENT if cls is page_cls else "transparent",
                          text_color="white" if cls is page_cls else ("gray10", "gray90"))
        for w in self.content.winfo_children():
            w.destroy()
        page_cls(self.content, self.user).pack(fill="both", expand=True)
