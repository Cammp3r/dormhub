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

        ctk.CTkLabel(
            left, text="Чати кімнат", font=theme.font(22, bold=True)
        ).pack(anchor="w", padx=16, pady=(16, 12))
        ctk.CTkLabel(
            left,
            text="Чат доступний мешканцям відповідної кімнати.",
            text_color=theme.MUTED,
            wraplength=260,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 12))

        self.chat_list = ctk.CTkScrollableFrame(left, fg_color="transparent")
        self.chat_list.pack(fill="both", expand=True, padx=4)

        self.right = ctk.CTkFrame(self, fg_color="transparent")
        self.right.grid(row=0, column=1, sticky="nsew")
        self.render_chat_list()
        self.show_placeholder()

    def render_chat_list(self):
        for widget in self.chat_list.winfo_children():
            widget.destroy()

        chats = repo.get_room_chats_for_user(self.user["user_id"])
        if not chats:
            ctk.CTkLabel(
                self.chat_list,
                text="Ви не заселені в кімнату.",
                text_color=theme.MUTED,
            ).pack(padx=12, pady=12)
            return

        for chat in chats:
            selected = chat["id"] == self.current_chat_id
            item = ctk.CTkFrame(
                self.chat_list,
                corner_radius=10,
                fg_color=theme.ACCENT if selected else "transparent",
            )
            item.pack(fill="x", pady=2)
            title = ctk.CTkLabel(
                item,
                text=f"💬  {chat['title']}",
                anchor="w",
                font=theme.font(14, bold=True),
                text_color="white" if selected else None,
            )
            title.pack(fill="x", padx=10, pady=(8, 0))
            preview = chat["last_message"] or "Немає повідомлень"
            if len(preview) > 34:
                preview = preview[:34] + "…"
            subtitle = ctk.CTkLabel(
                item,
                text=preview,
                anchor="w",
                text_color="white" if selected else theme.MUTED,
            )
            subtitle.pack(fill="x", padx=10, pady=(0, 8))
            for widget in (item, title, subtitle):
                widget.bind(
                    "<Button-1>",
                    lambda event, chat_id=chat["id"]: self.open_chat(chat_id),
                )

    def show_placeholder(self):
        for widget in self.right.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.right,
            text="Оберіть чат зліва 💬",
            font=theme.font(18),
            text_color=theme.MUTED,
        ).place(relx=0.5, rely=0.5, anchor="center")

    def open_chat(self, chat_id):
        chats = repo.get_room_chats_for_user(self.user["user_id"])
        chat = next((item for item in chats if item["id"] == chat_id), None)
        if chat is None:
            return

        self.current_chat_id = chat_id
        self.render_chat_list()
        for widget in self.right.winfo_children():
            widget.destroy()

        members = repo.get_room_chat_members(chat_id, self.user["user_id"])
        header = ctk.CTkFrame(self.right, height=60, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text=chat["title"], font=theme.font(18, bold=True)
        ).pack(side="left", padx=20, pady=14)
        ctk.CTkLabel(
            header, text=f"{len(members)} учасників", text_color=theme.MUTED
        ).pack(side="left")

        self.messages_frame = ctk.CTkScrollableFrame(
            self.right, fg_color="transparent"
        )
        self.messages_frame.pack(fill="both", expand=True, padx=8, pady=8)

        bottom = ctk.CTkFrame(self.right, fg_color="transparent")
        bottom.pack(fill="x", padx=16, pady=(0, 16))
        self.input = ctk.CTkEntry(
            bottom, placeholder_text="Напишіть повідомлення…", height=40
        )
        self.input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.input.bind("<Return>", lambda event: self.send())
        ctk.CTkButton(
            bottom,
            text="Надіслати",
            width=110,
            height=40,
            fg_color=theme.ACCENT,
            hover_color=theme.ACCENT_HOVER,
            command=self.send,
        ).pack(side="right")
        self.input.focus()
        self.render_messages()

    def render_messages(self):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()

        for message in repo.get_room_chat_messages(
            self.current_chat_id, self.user["user_id"]
        ):
            mine = message["author_id"] == self.user["user_id"]
            row = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            bubble = ctk.CTkFrame(
                row,
                corner_radius=14,
                fg_color=theme.MY_BUBBLE if mine else theme.OTHER_BUBBLE,
            )
            bubble.pack(side="right" if mine else "left", padx=8)
            if not mine:
                ctk.CTkLabel(
                    bubble,
                    text=message["author_name"],
                    font=theme.font(12, bold=True),
                    text_color=theme.ACCENT,
                ).pack(anchor="w", padx=12, pady=(6, 0))
            ctk.CTkLabel(
                bubble,
                text=message["text"],
                wraplength=420,
                justify="left",
                text_color="white" if mine else None,
            ).pack(anchor="w", padx=12, pady=(4 if mine else 0, 0))
            ctk.CTkLabel(
                bubble,
                text=message["sent_at"].strftime("%H:%M"),
                text_color="#DBEAFE" if mine else theme.MUTED,
            ).pack(anchor="e", padx=12, pady=(0, 6))

        self.after(50, lambda: self.messages_frame._parent_canvas.yview_moveto(1.0))

    def send(self):
        text = self.input.get().strip()
        if not text:
            return
        repo.send_room_chat_message(
            self.current_chat_id, self.user["user_id"], text
        )
        self.input.delete(0, "end")
        self.render_messages()
        self.render_chat_list()
