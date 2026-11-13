import customtkinter as ctk
from psycopg2 import Error as DatabaseError
from data import repository as repo
from ui import theme
from ui.module_a.profile import ProfilePage
from ui.module_a.room import RoomPage
from ui.module_b.chats import ChatsPage
from ui.module_c.parking import ParkingPage
from ui.module_c.announcements import AnnouncementsPage
from ui.module_c.events import EventsPage
from ui.module_c.requests_page import RequestsPage
from ui.admin import AdminPage
from ui.forms import show_error


class DepartmentsPage(ctk.CTkScrollableFrame):
    title = "Факультети"

    def __init__(self, master, user=None):
        super().__init__(master, fg_color="transparent")
        theme.page_title(self, "Факультети")
        departments = repo.get_departments()
        if not departments:
            ctk.CTkLabel(self, text='Факультетів у базі поки немає.', text_color=theme.MUTED).pack(anchor='w', padx=24)
        for department in departments:
            row = theme.card(self, pady=4)
            ctk.CTkLabel(
                row,
                text=department["department_name"],
                font=theme.font(15, bold=True),
                anchor="w",
            ).pack(fill="x", padx=16, pady=14)


class EnrollmentsPage(ctk.CTkScrollableFrame):
    title = "Навчання"

    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        theme.page_title(self, "Мої навчальні курси")
        student = repo.get_student_for_user(user["user_id"])
        enrollments = repo.get_enrollments(student["student_id"]) if student else []
        if not enrollments:
            ctk.CTkLabel(
                self, text="Навчальних записів не знайдено.", text_color=theme.MUTED
            ).pack(anchor="w", padx=24)
        for enrollment in enrollments:
            row = theme.card(self, pady=4)
            ctk.CTkLabel(
                row,
                text=enrollment["course_title"],
                font=theme.font(15, bold=True),
                anchor="w",
            ).pack(fill="x", padx=16, pady=(12, 2))
            ctk.CTkLabel(
                row,
                text=f"{enrollment['department_name']}  ·  Оцінка: {enrollment['grade'] or 'ще немає'}",
                text_color=theme.MUTED,
                anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 12))


class VacanciesPage(ctk.CTkScrollableFrame):
    title = "Вакансії"

    def __init__(self, master, user=None):
        super().__init__(master, fg_color="transparent")
        theme.page_title(self, "Вакансії")
        vacancies = repo.get_vacancies()
        if not vacancies:
            ctk.CTkLabel(self, text='Вакансій у базі поки немає.', text_color=theme.MUTED).pack(anchor='w', padx=24)
        for vacancy in vacancies:
            row = theme.card(self, pady=4)
            ctk.CTkLabel(
                row,
                text=vacancy["job_name"],
                font=theme.font(15, bold=True),
                anchor="w",
            ).pack(fill="x", padx=16, pady=(12, 2))
            ctk.CTkLabel(
                row, text=vacancy["company_name"], text_color=theme.MUTED, anchor="w"
            ).pack(fill="x", padx=16, pady=(0, 12))


class ApplicationsPage(ctk.CTkScrollableFrame):
    title = "Мої заявки"

    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        theme.page_title(self, "Мої заявки на вакансії")
        student = repo.get_student_for_user(user["user_id"])
        applications = repo.get_applications(student["student_id"]) if student else []
        if not applications:
            ctk.CTkLabel(
                self, text="Заявок на вакансії не знайдено.", text_color=theme.MUTED
            ).pack(anchor="w", padx=24)
        for application in applications:
            row = theme.card(self, pady=4)
            ctk.CTkLabel(
                row,
                text=application["job_name"],
                font=theme.font(15, bold=True),
                anchor="w",
            ).pack(fill="x", padx=16, pady=(12, 2))
            ctk.CTkLabel(
                row,
                text=f"{application['company_name']}  ·  {application['status']}",
                text_color=theme.MUTED,
                anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 12))


PAGES = [
    ("💬  Чати кімнат", ChatsPage),
    ("📢  Оголошення", AnnouncementsPage),
    ("🎉  Події", EventsPage),
    ("🔧  Мої звернення", RequestsPage),
    ("🎓  Факультети", DepartmentsPage),
    ("📚  Навчання", EnrollmentsPage),
    ("💼  Вакансії", VacanciesPage),
    ("📝  Мої заявки", ApplicationsPage),
    ("🅿️  Паркінг", ParkingPage),
    ("🚪  Моя кімната", RoomPage),
    ("👤  Профіль", ProfilePage),
]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DormHub")
        self.geometry("1100x700")
        self.minsize(900, 560)
        self.user = None
        self.build_login()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def build_login(self):
        self.clear()
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        panel = ctk.CTkFrame(self, corner_radius=16)
        panel.grid(row=0, column=0, padx=24, pady=24)
        ctk.CTkLabel(panel, text="🏠 DormHub", font=theme.font(28, bold=True)).pack(
            padx=32, pady=(28, 8))
        ctk.CTkLabel(panel, text="Вхід до акаунта", font=theme.font(18)).pack(pady=(0, 16))
        ctk.CTkLabel(panel, text="Ім’я", anchor="w").pack(fill="x", padx=32)
        self.first_name_entry = ctk.CTkEntry(panel, width=360, height=40)
        self.first_name_entry.pack(padx=32, pady=(4, 12))
        ctk.CTkLabel(panel, text="Прізвище", anchor="w").pack(fill="x", padx=32)
        self.last_name_entry = ctk.CTkEntry(panel, width=360, height=40)
        self.last_name_entry.pack(padx=32, pady=(4, 12))
        self.login_status = ctk.CTkLabel(
            panel, text="", text_color="#EF4444", wraplength=360)
        self.login_status.pack(padx=32, pady=4)
        ctk.CTkButton(panel, text="Увійти", height=40, width=360,
                      command=self.login).pack(padx=32, pady=(4, 28))
        self.first_name_entry.bind("<Return>", lambda event: self.last_name_entry.focus_set())
        self.last_name_entry.bind("<Return>", lambda event: self.login())
        self.first_name_entry.focus_set()

    def login(self):
        try:
            self.user = repo.login(self.first_name_entry.get(), self.last_name_entry.get())
        except ValueError as error:
            self.login_status.configure(text=str(error))
            return
        except (RuntimeError, DatabaseError):
            self.login_status.configure(text="Не вдалося увійти. Перевірте підключення до бази даних.")
            return
        self.build_main()

    def logout(self):
        repo.logout()
        self.user = None
        self.build_login()

    def build_main(self):
        if self.user is None:
            self.build_login()
            return
        self.clear()
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="🏠 DormHub", font=theme.font(22, bold=True)).pack(pady=(24, 4), padx=20, anchor="w")
        self.sidebar_name = ctk.CTkLabel(sidebar, text=repo.get_user_name(self.user), text_color=theme.MUTED,
                     font=theme.font(12))
        self.sidebar_name.pack(padx=20, anchor="w", pady=(0, 20))

        self.nav_buttons = {}
        navigation = list(PAGES)
        if repo.is_dorm_admin(self.user['user_id']):
            navigation.insert(0, ('⚙  Адміністрування', AdminPage))
        nav = ctk.CTkScrollableFrame(sidebar, fg_color='transparent')
        nav.pack(fill='both', expand=True)
        for text, page_cls in navigation:
            btn = ctk.CTkButton(nav, text=text, anchor="w", height=40, corner_radius=8,
                                fg_color="transparent", text_color=("gray10", "gray90"),
                                hover_color=("gray80", "gray25"), font=theme.font(14),
                                command=lambda p=page_cls: self.open_page(p))
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[page_cls] = btn

        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=12, pady=16)
        ctk.CTkButton(bottom, text="Вийти з акаунта", command=self.logout).pack(
            fill="x", pady=(0, 12))
        theme_switch = ctk.CTkSwitch(bottom, text="Темна тема",
                                     command=lambda: ctk.set_appearance_mode(
                                         "dark" if theme_switch.get() else "light"))
        theme_switch.pack(anchor="w", pady=(0, 10))
        if ctk.get_appearance_mode() == "Dark":
            theme_switch.select()
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")

        self.open_page(RoomPage)

    def open_page(self, page_cls):
        if self.user is None:
            self.build_login()
            return
        for cls, btn in self.nav_buttons.items():
            btn.configure(fg_color=theme.ACCENT if cls is page_cls else "transparent",
                          text_color="white" if cls is page_cls else ("gray10", "gray90"))
        for w in self.content.winfo_children():
            w.destroy()
        try:
            fresh_user = repo.get_user(self.user['user_id'])
            if fresh_user is None or fresh_user['status'] != 'active':
                self.logout()
                return
            self.user.update(fresh_user)
            page_cls(self.content, self.user).pack(fill="both", expand=True)
        except (RuntimeError, PermissionError, ValueError, DatabaseError) as error:
            for widget in self.content.winfo_children():
                widget.destroy()
            show_error(self, error)
            ctk.CTkButton(self.content, text='Повторити завантаження',
                          command=lambda: self.open_page(page_cls)).pack(pady=24)
