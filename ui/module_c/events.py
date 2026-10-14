import customtkinter as ctk
from data import repository as repo
from ui import theme


class EventsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        self.user = user
        self.render()

    def render(self):
        for w in self.winfo_children():
            w.destroy()
        theme.page_title(self, "Події")

        for e in repo.get_events():
            c = theme.card(self)

            date_box = ctk.CTkFrame(c, width=70, height=70, corner_radius=10, fg_color=theme.ACCENT)
            date_box.pack(side="left", padx=16, pady=14)
            date_box.pack_propagate(False)
            ctk.CTkLabel(date_box, text=e["starts_at"].strftime("%d"), text_color="white",
                         font=theme.font(22, bold=True)).pack(pady=(8, 0))
            ctk.CTkLabel(date_box, text=e["starts_at"].strftime("%m.%Y"), text_color="white",
                         font=theme.font(11)).pack()

            info = ctk.CTkFrame(c, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(info, text=e["title"], font=theme.font(16, bold=True), anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"🕒 {e['starts_at']:%H:%M}   📍 {e['place']}",
                         text_color=theme.MUTED, anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"Ідуть: {len(e['participant_ids'])}",
                         text_color=theme.MUTED, anchor="w").pack(fill="x")

            going = self.user["id"] in e["participant_ids"]
            ctk.CTkButton(c, text="✓ Ви йдете" if going else "Я піду", width=110,
                          fg_color="#10B981" if going else theme.ACCENT,
                          hover_color="#059669" if going else theme.ACCENT_HOVER,
                          command=lambda eid=e["id"]: self.toggle(eid)).pack(side="right", padx=16)

    def toggle(self, event_id):
        repo.toggle_participation(event_id, self.user["id"])
        self.render()
