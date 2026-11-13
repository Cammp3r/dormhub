import customtkinter as ctk

from data import repository as repo
from ui import theme
from ui.forms import DataPage, Form, button, label


class RequestsPage(DataPage):
    def __init__(self, master, user, admin=False):
        super().__init__(master, user)
        self.admin = admin
        self.status_filter = 'Усі'
        self.render()

    def render(self):
        self.clear('Звернення гуртожитку' if self.admin else 'Мої звернення')
        if self.admin:
            menu = ctk.CTkOptionMenu(self, values=['Усі'] + repo.get_request_statuses(), command=self.filter)
            menu.set(self.status_filter)
            menu.pack(anchor='w', padx=24, pady=4)
        else:
            button(self, 'Створити звернення', lambda: self.guard(self.create))
        rows = repo.get_requests(admin=self.admin, status=self.status_filter)
        if not rows:
            self.empty()
        for row in rows:
            card = theme.card(self)
            label(card, f"№{row['request_id']} · {row['category']} · {row['status']}", bold=True)
            label(card, f"Кімната {row['room_number']} · {row['author_name']}")
            label(card, row['description'])
            for entry in row['history']:
                label(card, f"{entry['changed_at']:%d.%m.%Y %H:%M} · {entry['status']} · "
                      f"{entry['changed_by_name']}\n{entry['response']}")
            if self.admin:
                button(card, 'Опрацювати', lambda r=row: self.guard(lambda: self.edit(r)))

    def filter(self, value):
        self.status_filter = value
        self.run(lambda: None)

    def create(self):
        categories = repo.get_request_categories()
        if not categories:
            self.empty('У базі немає категорій звернень. Зверніться до адміністрації.')
            return
        def save(values):
            repo.create_request(**values)
        Form(self, 'Нове звернення', [
            ('category', 'Категорія', categories[0], categories),
            ('description', 'Опишіть проблему', '', 'text')], save, self.render)

    def edit(self, row):
        def save(values):
            repo.update_request(row['request_id'], **values)
        Form(self, f"Звернення №{row['request_id']}", [
            ('status', 'Статус', row['status'], repo.get_request_statuses()),
            ('response', 'Відповідь / причина зміни', '', 'text')], save, self.render)
