import customtkinter as ctk

from data import repository as repo
from ui import theme
from ui.forms import DataPage, Form, button, label
from ui.module_c.requests_page import RequestsPage


class ResidentsPage(DataPage):
    def __init__(self, master, user):
        super().__init__(master, user)
        self.search = ''
        self.status_filter = 'Усі'
        self.room_filter = 'Усі кімнати'
        self.render()

    def render(self):
        self.clear('Мешканці')
        rooms = repo.get_admin_rooms()
        self.room_choices = {'Усі кімнати': None, **{r['room_number']: r['room_id'] for r in rooms}}
        filters = theme.card(self)
        self.search_entry = ctk.CTkEntry(filters, placeholder_text='Ім’я, прізвище або email')
        self.search_entry.insert(0, self.search)
        self.search_entry.pack(fill='x', padx=16, pady=8)
        self.search_entry.bind('<Return>', lambda event: self.apply_filters())
        self.status_menu = ctk.CTkOptionMenu(filters, values=['Усі', 'active', 'blocked'])
        self.status_menu.set(self.status_filter)
        self.status_menu.pack(side='left', padx=16, pady=8)
        self.room_menu = ctk.CTkOptionMenu(filters, values=list(self.room_choices))
        self.room_menu.set(self.room_filter if self.room_filter in self.room_choices else 'Усі кімнати')
        self.room_menu.pack(side='left', padx=8, pady=8)
        button(filters, 'Знайти', self.apply_filters)
        button(self, 'Додати мешканця', lambda: self.edit())
        rows = repo.get_admin_residents(self.search, self.status_filter, self.room_choices.get(self.room_filter))
        if not rows:
            self.empty()
        for row in rows:
            card = theme.card(self)
            label(card, repo.get_user_name(row), bold=True)
            label(card, f"{row['email']} · {row['status']} · Кімната: {row['room_number'] or 'не поселено'}")
            label(card, f"Дата народження: {row['date_of_birth'] or 'не вказано'} · Рік вступу: {row['enrollment_year'] or 'не вказано'}")
            button(card, 'Редагувати', lambda r=row: self.edit(r))
            button(card, 'Розблокувати' if row['status'] == 'blocked' else 'Заблокувати',
                   lambda r=row: self.change_status(r))

    def apply_filters(self):
        self.search = self.search_entry.get()
        self.status_filter = self.status_menu.get()
        self.room_filter = self.room_menu.get()
        self.run(lambda: None)

    def edit(self, row=None):
        row = row or {}
        fields = [(key, caption, row.get(key, ''), None) for key, caption in [
            ('first_name', 'Ім’я'), ('last_name', 'Прізвище'), ('email', 'Email'),
            ('date_of_birth', 'Дата народження (РРРР-ММ-ДД, необов’язково)'),
            ('enrollment_year', 'Рік вступу (необов’язково)')]]

        def save(values):
            values['birth_date'] = values.pop('date_of_birth')
            repo.save_resident(user_id=row.get('user_id'), **values)
        Form(self, 'Мешканець', fields, save, self.render)

    def change_status(self, row):
        status = 'active' if row['status'] == 'blocked' else 'blocked'

        def save(values):
            repo.set_resident_status(row['user_id'], status, values['reason'])
        Form(self, 'Зміна статусу акаунта', [('reason', 'Причина', '', 'text')], save, self.render)


class RoomsPage(DataPage):
    def __init__(self, master, user):
        super().__init__(master, user)
        self.render()

    def render(self):
        self.clear('Кімнати')
        button(self, 'Додати кімнату', lambda: self.edit())
        rows = repo.get_admin_rooms()
        if not rows:
            self.empty()
        for row in rows:
            card = theme.card(self)
            label(card, f"Кімната {row['room_number']} · Поверх {row['floor']}", bold=True)
            label(card, f"Зайнято: {row['occupied']}/{row['capacity']} · "
                  f"Вільно: {row['capacity'] - row['occupied']} · "
                  + ('Відкрита для поселення' if row['is_available'] else 'Закрита для поселення'))
            button(card, 'Редагувати', lambda r=row: self.edit(r))

    def edit(self, row=None):
        row = row or {}

        def save(values):
            values['is_available'] = values.pop('availability') == 'Відкрита'
            repo.save_room(room_id=row.get('room_id'), **values)
        Form(self, 'Кімната', [
            ('room_number', 'Номер кімнати', row.get('room_number', ''), None),
            ('floor', 'Поверх', row.get('floor', 1), None),
            ('capacity', 'Місткість', row.get('capacity', 4), None),
            ('availability', 'Поселення', 'Відкрита' if row.get('is_available', True) else 'Закрита',
             ['Відкрита', 'Закрита'])], save, self.render)


class ResidenciesPage(DataPage):
    def __init__(self, master, user):
        super().__init__(master, user)
        self.render()

    def render(self):
        self.clear('Поселення та історія проживання')
        self.rooms = repo.get_admin_rooms()
        rows = repo.get_admin_residents()
        if not rows:
            self.empty('Спочатку додайте мешканця у вкладці «Мешканці».')
        for row in rows:
            card = theme.card(self)
            label(card, f"{repo.get_user_name(row)} · Кімната: {row['room_number'] or 'не поселено'}", bold=True)
            button(card, 'Переселити' if row['room_id'] else 'Поселити', lambda r=row: self.move(r))
            if row['room_id']:
                button(card, 'Виселити', lambda r=row: self.move(r, checkout=True))
        label(self, 'Історія поселень', bold=True)
        for row in repo.get_residency_history():
            card = theme.card(self)
            end = row['ended_at'].strftime('%d.%m.%Y %H:%M') if row['ended_at'] else 'проживає'
            label(card, f"{row['resident_name']} · Кімната {row['room_number']}", bold=True)
            label(card, f"{row['started_at']:%d.%m.%Y %H:%M} → {end}\nПричина поселення: {row['start_reason']}")
            if row['end_reason']:
                label(card, 'Причина завершення: ' + row['end_reason'])

    def move(self, row, checkout=False):
        choices = {f"{r['room_number']} (вільно {r['capacity'] - r['occupied']})": r['room_id']
                   for r in self.rooms if r['is_available'] and r['occupied'] < r['capacity']
                   and r['room_id'] != row['room_id']}
        if not checkout and not choices:
            self.empty('Вільних відкритих кімнат немає. Додайте кімнату або змініть її місткість.')
            return
        fields = [] if checkout else [('room', 'Кімната', '', list(choices))]
        fields.append(('reason', 'Причина', '', 'text'))

        def save(values):
            repo.change_residency(row['user_id'], None if checkout else choices[values['room']], values['reason'])
        Form(self, 'Виселення' if checkout else 'Поселення / переселення', fields, save, self.render)


class AdminPage(ctk.CTkFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color='transparent')
        # Перевірка доступу також виконується всередині кожної операції repository.
        repo.get_admin_rooms()
        theme.page_title(self, 'Адміністративний кабінет')
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        for name, cls in [('Мешканці', ResidentsPage), ('Кімнати', RoomsPage),
                          ('Поселення', ResidenciesPage), ('Звернення', RequestsPage)]:
            tab = tabs.add(name)
            if cls is RequestsPage:
                cls(tab, user, admin=True).pack(fill='both', expand=True)
            else:
                cls(tab, user).pack(fill='both', expand=True)
        # Створюємо сторінки повторно при зміні вкладки, щоб форми бачили актуальні дані.
        tabs.configure(command=lambda: self.refresh_tab(tabs, user))

    def refresh_tab(self, tabs, user):
        from psycopg2 import Error as DatabaseError
        from ui.forms import show_error
        name = tabs.get()
        tab = tabs.tab(name)
        for child in tab.winfo_children():
            child.destroy()
        cls = {'Мешканці': ResidentsPage, 'Кімнати': RoomsPage,
               'Поселення': ResidenciesPage, 'Звернення': RequestsPage}[name]
        try:
            page = cls(tab, user, admin=True) if cls is RequestsPage else cls(tab, user)
            page.pack(fill='both', expand=True)
        except (RuntimeError, PermissionError, ValueError, DatabaseError) as error:
            show_error(self, error)
            button(tab, 'Повторити', lambda: self.refresh_tab(tabs, user))
