import customtkinter as ctk
from data import repository as repo
from ui import theme


class AnnouncementsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        self.user = user
        self.render()

    def render(self):
        for w in self.winfo_children():
            w.destroy()
        theme.page_title(self, "Оголошення")
        
        if self.user["role"] == "commandant":
            form = theme.card(self)
            ctk.CTkLabel(form, text="Нове оголошення", font=theme.font(15, bold=True)).pack(
                anchor="w", padx=16, pady=(12, 4))
            self.title_entry = ctk.CTkEntry(form, placeholder_text="Заголовок")
            self.title_entry.pack(fill="x", padx=16, pady=4)
            self.body_box = ctk.CTkTextbox(form, height=80)
            self.body_box.pack(fill="x", padx=16, pady=4)
            ctk.CTkButton(form, text="Опублікувати", fg_color=theme.ACCENT,
                          hover_color=theme.ACCENT_HOVER, command=self.publish).pack(
                anchor="e", padx=16, pady=(4, 12))

        for a in repo.get_announcements():
            c = theme.card(self)
            ctk.CTkLabel(c, text="📢  " + a["title"], font=theme.font(16, bold=True), anchor="w").pack(
                fill="x", padx=16, pady=(12, 2))
            ctk.CTkLabel(c, text=a["body"], wraplength=650, justify="left", anchor="w").pack(
                fill="x", padx=16)
            ctk.CTkLabel(c, text=f"{a['author_name']}  ·  {a['created_at']:%d.%m.%Y %H:%M}",
                         text_color=theme.MUTED, font=theme.font(12), anchor="w").pack(
                fill="x", padx=16, pady=(4, 12))

    def publish(self):
        title = self.title_entry.get().strip()
        body = self.body_box.get("1.0", "end").strip()
        if title and body:
            repo.add_announcement(self.user["id"], title, body)
            self.render()
