from tkinter import messagebox

import customtkinter as ctk
from psycopg2 import Error as DatabaseError

from ui import theme


def show_error(parent, error):
    if isinstance(error, DatabaseError):
        code = error.pgcode
        text = {
            '23505': 'Такий email або номер кімнати вже існує.',
            '23514': 'Перевірте формат і допустимі значення полів, зокрема email.',
            '23503': 'Запис пов’язаний з іншими даними. Оновіть сторінку.',
        }.get(code, 'Помилка бази даних. Перевірте підключення й оновлення схеми за інструкцією в README.')
    else:
        text = str(error)
    messagebox.showerror('DormHub', text, parent=parent)


class DataPage(ctk.CTkScrollableFrame):
    def __init__(self, master, user):
        super().__init__(master, fg_color='transparent')
        self.user = user

    def run(self, action):
        def refresh():
            action()
            self.render()
        self.guard(refresh)

    def guard(self, action):
        try:
            action()
        except (ValueError, RuntimeError, PermissionError, DatabaseError) as error:
            show_error(self, error)

    def clear(self, title):
        for widget in self.winfo_children():
            widget.destroy()
        theme.page_title(self, title)
        ctk.CTkButton(self, text='Оновити', width=100,
                      command=lambda: self.run(lambda: None)).pack(anchor='e', padx=24, pady=4)

    def empty(self, text='Записів поки немає.'):
        ctk.CTkLabel(self, text=text, text_color=theme.MUTED).pack(anchor='w', padx=24, pady=12)


def label(parent, text, bold=False):
    ctk.CTkLabel(parent, text=text, font=theme.font(15 if bold else 13, bold),
                 wraplength=620, justify='left', anchor='w').pack(fill='x', padx=16, pady=5)


def button(parent, text, command):
    ctk.CTkButton(parent, text=text, command=command).pack(anchor='e', padx=16, pady=5)


class Form(ctk.CTkToplevel):
    """Поля: (ключ, підпис, початкове значення, список варіантів / 'text' / None)."""
    def __init__(self, parent, title, fields, on_save, on_saved=None):
        super().__init__(parent)
        self.title(title)
        self.geometry('540x620')
        self.minsize(440, 380)
        self.transient(parent.winfo_toplevel())
        self.fields = {}
        self.on_save = on_save
        self.on_saved = on_saved
        self.page = parent
        panel = ctk.CTkScrollableFrame(self)
        panel.pack(fill='both', expand=True, padx=12, pady=12)
        for key, caption, value, options in fields:
            label(panel, caption)
            value = '' if value is None else str(value)
            if isinstance(options, list):
                widget = ctk.CTkOptionMenu(panel, values=options or ['Немає варіантів'])
                widget.set(value if value else (options[0] if options else 'Немає варіантів'))
            elif options == 'text':
                widget = ctk.CTkTextbox(panel, height=110)
                widget.insert('1.0', value)
            else:
                widget = ctk.CTkEntry(panel)
                widget.insert(0, value)
            widget.pack(fill='x', padx=16, pady=(0, 8))
            self.fields[key] = widget
        ctk.CTkButton(self, text='Зберегти', command=self.save).pack(pady=12)
        self.after(100, self.grab_set)

    def save(self):
        values = {key: (w.get('1.0', 'end').strip() if isinstance(w, ctk.CTkTextbox) else w.get().strip())
                  for key, w in self.fields.items()}
        try:
            self.on_save(values)
        except (ValueError, RuntimeError, PermissionError, DatabaseError) as error:
            show_error(self, error)
            return
        self.destroy()
        if self.on_saved:
            try:
                self.on_saved()
            except (ValueError, RuntimeError, PermissionError, DatabaseError) as error:
                show_error(self.page, error)
