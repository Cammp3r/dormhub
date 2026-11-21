import customtkinter as ctk

from data import repository as repo
from ui import theme
from ui.forms import DataPage, Form, button, label
from ui.module_c.requests_page import RequestsPage


class DormPage(DataPage):
    def __init__(self, master, user):
        super().__init__(master, user)
        self.render()

    def render(self):
        self.clear('Гуртожиток')
        dorm = repo.get_admin_dorm()
        card = theme.card(self)
        label(card, f"Гуртожиток №{dorm['dorm_number']}", bold=True)
        label(card, dorm['address'])
        button(card, 'Редагувати', lambda: self.edit(dorm))

    def edit(self, dorm):
        def save(values):
            repo.save_dorm(**values)
        Form(self, 'Гуртожиток', [
            ('dorm_number', 'Номер гуртожитку', dorm['dorm_number'], None),
            ('address', 'Адреса', dorm['address'], None)], save, self.render)


class ResidentsPage(DataPage):
    page_size = 20

    def __init__(self, master, user):
        super().__init__(master, user)
        self.search = ''
        self.room_filter = 'Усі кімнати'
        self.page = 0
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
        self.room_menu = ctk.CTkOptionMenu(filters, values=list(self.room_choices))
        self.room_menu.set(self.room_filter if self.room_filter in self.room_choices else 'Усі кімнати')
        self.room_menu.pack(side='left', padx=16, pady=8)
        button(filters, 'Знайти', self.apply_filters)
        button(self, 'Додати мешканця', lambda: self.edit())
        rows = repo.get_admin_residents(
            self.search,
            self.room_choices.get(self.room_filter),
            limit=self.page_size,
            offset=self.page * self.page_size,
        )
        if not rows:
            self.empty()
        for row in rows:
            card = theme.card(self)
            label(card, repo.get_user_name(row), bold=True)
            label(card, f"{row['email']} · Кімната: {row['room_number'] or 'не поселено'}")
            label(card, f"Дата народження: {row['date_of_birth'] or 'не вказано'} · Рік вступу: {row['enrollment_year'] or 'не вказано'}")
            button(card, 'Редагувати', lambda r=row: self.edit(r))
        total_count = rows[0]['total_count'] if rows else 0
        self.render_pagination(total_count)

    def render_pagination(self, total_count):
        navigation = ctk.CTkFrame(self, fg_color='transparent')
        navigation.pack(fill='x', padx=24, pady=8)
        ctk.CTkButton(
            navigation, text='Назад', width=90,
            state='normal' if self.page else 'disabled',
            command=lambda: self.change_page(-1),
        ).pack(side='left')
        ctk.CTkLabel(
            navigation,
            text=f'Сторінка {self.page + 1} з {max(1, (total_count + self.page_size - 1) // self.page_size)}',
            text_color=theme.MUTED,
        ).pack(side='left', padx=12)
        ctk.CTkButton(
            navigation, text='Далі', width=90,
            state='normal' if (self.page + 1) * self.page_size < total_count else 'disabled',
            command=lambda: self.change_page(1),
        ).pack(side='left')

    def change_page(self, delta):
        self.page = max(0, self.page + delta)
        self.run(lambda: None)

    def apply_filters(self):
        self.search = self.search_entry.get()
        self.room_filter = self.room_menu.get()
        self.page = 0
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

class RoomsPage(DataPage):
    def __init__(self, master, user):
        super().__init__(master, user)
        self.render()

    def render(self):
        self.clear('Кімнати')
        button(self, 'Додати кімнату', lambda: self.edit())
        rows = repo.get_admin_rooms()
        report = repo.get_room_occupancy_report()
        if report:
            summary = theme.card(self)
            label(summary, 'Аналітика зайнятості кімнат', bold=True)
            for row in report:
                label(
                    summary,
                    f"Кімната {row['room_number']}: "
                    f"{row['resident_count']}/{row['capacity']} мешканців; "
                    f"вільних місць: {row['free_places']}",
                )
        if not rows:
            self.empty()
        for row in rows:
            card = theme.card(self)
            label(card, f"Кімната {row['room_number']} · Поверх {row['floor']}", bold=True)
            label(card, f"Зайнято: {row['occupied']}/{row['capacity']} · "
                  f"Вільно: {row['capacity'] - row['occupied']} · "
                  + ('Відкрита для поселення' if row['is_available'] else 'Закрита для поселення'))
            for place in row['places']:
                state = 'зайняте' if place['occupied'] else (
                    'доступне' if place['is_available'] else 'закрите')
                label(card, f"Місце {place['place_number']}: {state}")
                if not place['occupied']:
                    button(card, 'Закрити' if place['is_available'] else 'Відкрити',
                           lambda p=place: self.toggle_place(p))
            button(card, 'Редагувати', lambda r=row: self.edit(r))

    def toggle_place(self, place):
        self.run(lambda: repo.save_place(place['place_id'], not place['is_available']))

    def edit(self, row=None):
        row = row or {}

        def save(values):
            values['is_available'] = values.pop('availability') == 'Відкрита'
            repo.save_room(room_id=row.get('room_id'), **values)
        Form(self, 'Кімната', [
            ('room_number', 'Номер кімнати', row.get('room_number', ''), None),
            ('floor', 'Поверх', row.get('floor', ''), None),
            ('capacity', 'Місткість', row.get('capacity', ''), None),
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
            location = 'не поселено'
            if row['room_id']:
                location = f"кімната {row['room_number']}, місце {row['place_number']}"
            label(card, f"{repo.get_user_name(row)} · {location}", bold=True)
            button(card, 'Переселити' if row['room_id'] else 'Поселити', lambda r=row: self.move(r))
            if row['room_id']:
                button(card, 'Виселити', lambda r=row: self.move(r, checkout=True))
        label(self, 'Історія поселень', bold=True)
        for row in repo.get_residency_history():
            card = theme.card(self)
            end = row['ended_at'].strftime('%d.%m.%Y %H:%M') if row['ended_at'] else 'проживає'
            label(card, f"{row['resident_name']} · Кімната {row['room_number']}, місце {row['place_number']}", bold=True)
            label(card, f"{row['started_at']:%d.%m.%Y %H:%M} → {end}\nПричина поселення: {row['start_reason']}")
            if row['end_reason']:
                label(card, 'Причина завершення: ' + row['end_reason'])

    def move(self, row, checkout=False):
        choices = {}
        for room in self.rooms:
            if not room['is_available']:
                continue
            for place in room['places']:
                if place['is_available'] and not place['occupied']:
                    choices[f"кімната {room['room_number']}, місце {place['place_number']}"] = place['place_id']
        if not checkout and not choices:
            self.empty('Вільних відкритих кімнат немає. Додайте кімнату або змініть її місткість.')
            return
        fields = [] if checkout else [('room', 'Кімната', '', list(choices))]
        fields.append(('reason', 'Причина', '', 'text'))

        def save(values):
            repo.change_residency(row['user_id'], None if checkout else choices[values['place']], values['reason'])

        if not checkout:
            fields = [('place', 'Місце', '', list(choices)), ('reason', 'Причина', '', 'text')]
        Form(self, 'Виселення' if checkout else 'Поселення / переселення', fields, save, self.render)


class AdminPage(ctk.CTkFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color='transparent')
        # Перевірка доступу також виконується всередині кожної операції repository.
        repo.get_admin_rooms()
        theme.page_title(self, 'Адміністративний кабінет')
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        for name, cls in [('Гуртожиток', DormPage), ('Мешканці', ResidentsPage), ('Кімнати', RoomsPage),
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
        cls = {'Гуртожиток': DormPage, 'Мешканці': ResidentsPage, 'Кімнати': RoomsPage,
               'Поселення': ResidenciesPage, 'Звернення': RequestsPage}[name]
        try:
            page = cls(tab, user, admin=True) if cls is RequestsPage else cls(tab, user)
            page.pack(fill='both', expand=True)
        except (RuntimeError, PermissionError, ValueError, DatabaseError) as error:
            show_error(self, error)
            button(tab, 'Повторити', lambda: self.refresh_tab(tabs, user))
