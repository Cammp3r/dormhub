from tkinter import messagebox
from data import repository as repo
from ui import theme
from ui.forms import DataPage, Form, button, label


class AnnouncementsPage(DataPage):
    kind = 'announcements'
    title = 'Оголошення'

    def __init__(self, master, user):
        super().__init__(master, user)
        self.render()

    def render(self):
        self.clear(self.title)
        admin = repo.is_dorm_admin(self.user['user_id'])
        if admin:
            button(self, 'Створити', lambda: self.edit())
        rows = repo.get_publications(self.kind)
        if not rows:
            self.empty('Для вашого гуртожитку публікацій поки немає.')
        for row in rows:
            card = theme.card(self)
            label(card, row['title'], bold=True)
            label(card, row['body'])
            label(card, f"{row['author_name']} · {row['created_at']:%d.%m.%Y %H:%M}")
            self.details(card, row)
            if admin:
                button(card, 'Редагувати', lambda r=row: self.edit(r))
                button(card, 'Видалити', lambda r=row: self.remove(r))

    def details(self, card, row):
        label(card, f"Адресат: гуртожиток №{row['dorm_number']} · {row['dorm_address']}")

    def edit(self, row=None):
        row = row or {}
        fields = [('title', 'Заголовок', row.get('title', ''), None),
                  ('body', 'Опис', row.get('body', ''), 'text')]
        def save(values):
            repo.save_publication(self.kind, publication_id=row.get('id'), **values)
        Form(self, 'Публікація', fields, save, self.render)

    def remove(self, row):
        if messagebox.askyesno('Видалення', f"Видалити «{row['title']}»?", parent=self):
            self.run(lambda: repo.delete_publication(self.kind, row['id']))
