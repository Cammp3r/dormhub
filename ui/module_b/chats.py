import customtkinter as ctk
from data import repository as repo
from ui import theme


class ChatsPage(ctk.CTkFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color="transparent")
        self.user = user
        self.current_chat_id = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, width=300, corner_radius=0)
        left.grid(row=0, column=0, sticky="ns")
        left.grid_propagate(False)

        top = ctk.CTkFrame(left, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(16, 8))
        ctk.CTkLabel(top, text="Чати", font=theme.font(22, bold=True)).pack(side="left")
        ctk.CTkButton(top, text="+ Група", width=80, fg_color=theme.ACCENT,
                      hover_color=theme.ACCENT_HOVER, command=self.open_new_group).pack(side="right")

        self.search = ctk.CTkEntry(left, placeholder_text="🔍 Пошук чату")
        self.search.pack(fill="x", padx=12, pady=(0, 8))
        self.search.bind("<KeyRelease>", lambda e: self.render_chat_list())

        self.chat_list = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.chat_list.pack(fill="both", expand=True, padx=4)

        self.right = ctk.CTkFrame(self, fg_color="transparent")
        self.right.grid(row=0, column=1, sticky="nsew")

        self.render_chat_list()
        self.show_placeholder()


    def render_chat_list(self):
        for w in self.chat_list.winfo_children():
            w.destroy()

        query = self.search.get().lower()
        for chat in repo.get_chats_for_user(self.user["id"]):
            if query and query not in chat["title"].lower():
                continue
            selected = chat["id"] == self.current_chat_id
            item = ctk.CTkFrame(self.chat_list, corner_radius=10,
                                fg_color=theme.ACCENT if selected else "transparent")
            item.pack(fill="x", pady=2)

            icon = "👥" if chat["is_group"] else "👤"
            title = ctk.CTkLabel(item, text=f"{icon}  {chat['title']}", anchor="w",
                                 font=theme.font(14, bold=True),
                                 text_color="white" if selected else None)
            title.pack(fill="x", padx=10, pady=(8, 0))

            last = chat["last_message"]
            preview = f"{last['author_name'].split()[0]}: {last['text']}" if last else "Немає повідомлень"
            if len(preview) > 34:
                preview = preview[:34] + "…"
            sub = ctk.CTkLabel(item, text=preview, anchor="w", font=theme.font(12),
                               text_color="white" if selected else theme.MUTED)
            sub.pack(fill="x", padx=10, pady=(0, 8))

            for widget in (item, title, sub):
                widget.bind("<Button-1>", lambda e, cid=chat["id"]: self.open_chat(cid))

    def show_placeholder(self):
        for w in self.right.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.right, text="Оберіть чат зліва 💬", font=theme.font(18),
                     text_color=theme.MUTED).place(relx=0.5, rely=0.5, anchor="center")

    def open_chat(self, chat_id):
        self.current_chat_id = chat_id
        self.render_chat_list()
        for w in self.right.winfo_children():
            w.destroy()

        chat = next(c for c in repo.get_chats_for_user(self.user["id"]) if c["id"] == chat_id)
        members = repo.get_chat_members(chat_id)

        header = ctk.CTkFrame(self.right, height=60, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text=chat["title"], font=theme.font(18, bold=True)).pack(
            side="left", padx=20, pady=14)
        ctk.CTkLabel(header, text=f"{len(members)} учасників", text_color=theme.MUTED).pack(side="left")

        self.messages_frame = ctk.CTkScrollableFrame(self.right, fg_color="transparent")
        self.messages_frame.pack(fill="both", expand=True, padx=8, pady=8)

        bottom = ctk.CTkFrame(self.right, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=(0, 16))
        self.input = ctk.CTkEntry(bottom, placeholder_text="Напишіть повідомлення…", height=40)
        self.input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input.bind("<Return>", lambda e: self.send())
        ctk.CTkButton(bottom, text="Надіслати", width=110, height=40, fg_color=theme.ACCENT,
                      hover_color=theme.ACCENT_HOVER, command=self.send).pack(side="right")
        self.input.focus()

        self.render_messages()

    def render_messages(self):
        for w in self.messages_frame.winfo_children():
            w.destroy()

        last_date = None
        for msg in repo.get_messages(self.current_chat_id):
            day = msg["sent_at"].date()
            if day != last_date:
                ctk.CTkLabel(self.messages_frame, text=day.strftime("%d.%m.%Y"),
                             text_color=theme.MUTED, font=theme.font(12)).pack(pady=(10, 4))
                last_date = day

            mine = msg["author_id"] == self.user["id"]
            row = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)

            bubble = ctk.CTkFrame(row, corner_radius=14,
                                  fg_color=theme.MY_BUBBLE if mine else theme.OTHER_BUBBLE)
            bubble.pack(side="right" if mine else "left", padx=8)

            if not mine:
                ctk.CTkLabel(bubble, text=msg["author_name"], font=theme.font(12, bold=True),
                             text_color=theme.ACCENT).pack(anchor="w", padx=12, pady=(6, 0))
            ctk.CTkLabel(bubble, text=msg["text"], wraplength=420, justify="left",
                         font=theme.font(14), text_color="white" if mine else None).pack(
                anchor="w", padx=12, pady=(4 if mine else 0, 0))
            ctk.CTkLabel(bubble, text=msg["sent_at"].strftime("%H:%M"), font=theme.font(10),
                         text_color="#DBEAFE" if mine else theme.MUTED).pack(anchor="e", padx=12, pady=(0, 6))

        self.after(50, lambda: self.messages_frame._parent_canvas.yview_moveto(1.0))

    def send(self):
        text = self.input.get().strip()
        if not text:
            return
        repo.send_message(self.current_chat_id, self.user["id"], text)
        self.input.delete(0, "end")
        self.render_messages()
        self.render_chat_list()

    # ======================================================
    def open_new_group(self):
        NewGroupDialog(self, self.user, on_created=self.open_chat)


class NewGroupDialog(ctk.CTkToplevel):

    def __init__(self, master, user, on_created):
        super().__init__(master)
        self.user = user
        self.on_created = on_created
        self.title("Нова група")
        self.geometry("380x480")
        self.resizable(False, False)
        self.after(100, self.grab_set)

        ctk.CTkLabel(self, text="Створити групу", font=theme.font(18, bold=True)).pack(pady=(16, 8))
        self.name_entry = ctk.CTkEntry(self, placeholder_text="Назва групи", width=320)
        self.name_entry.pack(pady=6)

        ctk.CTkLabel(self, text="Учасники:", anchor="w").pack(fill="x", padx=30, pady=(10, 0))
        box = ctk.CTkScrollableFrame(self, width=300, height=240)
        box.pack(pady=6)

        self.checks = {}
        for u in repo.get_all_users():
            if u["id"] == user["id"]:
                continue
            var = ctk.BooleanVar()
            ctk.CTkCheckBox(box, text=u["full_name"], variable=var).pack(anchor="w", pady=4)
            self.checks[u["id"]] = var

        self.error = ctk.CTkLabel(self, text="", text_color="#EF4444")
        self.error.pack()
        ctk.CTkButton(self, text="Створити", width=320, fg_color=theme.ACCENT,
                      hover_color=theme.ACCENT_HOVER, command=self.create).pack(pady=(0, 16))

    def create(self):
        name = self.name_entry.get().strip()
        members = [uid for uid, var in self.checks.items() if var.get()]
        if not name:
            self.error.configure(text="Введіть назву")
            return
        if not members:
            self.error.configure(text="Оберіть хоча б одного учасника")
            return
        chat_id = repo.create_group_chat(name, self.user["id"], members)
        self.destroy()
        self.on_created(chat_id)
