from datetime import datetime
from zoneinfo import ZoneInfo

from data import repository as repo
from ui.forms import button, label
from ui.module_c.announcements import AnnouncementsPage


class EventsPage(AnnouncementsPage):
    kind = 'events'
    title = 'Події'

    def details(self, card, row):
        starts = row['starts_at'].astimezone(ZoneInfo('Europe/Kyiv'))
        label(card, f"{starts:%d.%m.%Y %H:%M} · {row['place']}")
        limit = row['capacity'] if row['capacity'] is not None else 'без обмежень'
        label(card, f"Учасників: {len(row['participant_ids'])} · Місць: {limit}")
        going = self.user['user_id'] in row['participant_ids']
        if going or starts > datetime.now(starts.tzinfo):
            button(card, 'Скасувати участь' if going else 'Я піду',
                   lambda: self.run(lambda: repo.toggle_participation(row['id'])))
        else:
            label(card, 'Реєстрацію завершено')
