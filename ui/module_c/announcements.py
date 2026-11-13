from tkinter import messagebox
from zoneinfo import ZoneInfo

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
            label(card, f"{row['author_name']} · {row['created_at'].astimezone(ZoneInfo('Europe/Kyiv')):%d.%m.%Y %H:%M}")
            self.details(card, row)
            if admin:
                button(card, 'Редагувати', lambda r=row: self.edit(r))
                button(card, 'Видалити', lambda r=row: self.remove(r))

    def details(self, card, row):
        pass

    def edit(self, row=None):
        row = row or {}
        fields = [('title', 'Заголовок', row.get('title', ''), None),
                  ('body', 'Опис', row.get('body', ''), 'text')]
        if self.kind == 'events':
            starts = row.get('starts_at')
            starts = starts.astimezone(ZoneInfo('Europe/Kyiv')).strftime('%Y-%m-%d %H:%M') if starts else ''
            fields += [('starts_at', 'Дата й час у Києві (РРРР-ММ-ДД ГГ:ХХ)', starts, None),
                       ('place', 'Місце проведення', row.get('place', ''), None),
                       ('capacity', 'Кількість місць (порожньо — без обмежень)', row.get('capacity', ''), None)]

        def save(values):
            repo.save_publication(self.kind, publication_id=row.get('id'), **values)
        Form(self, 'Публікація', fields, save, self.render)

    def remove(self, row):
        if messagebox.askyesno('Видалення', f"Видалити «{row['title']}»?", parent=self):
            self.run(lambda: repo.delete_publication(self.kind, row['id']))
