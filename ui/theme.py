import customtkinter as ctk

ACCENT = "#3B82F6"
ACCENT_HOVER = "#2563EB"
MY_BUBBLE = "#2563EB"
OTHER_BUBBLE = ("#E5E7EB", "#374151")
CARD_BG = ("#F3F4F6", "#1F2937")
MUTED = ("#6B7280", "#9CA3AF")

STATUS_COLORS = {"Нова": "#F59E0B", "В роботі": "#3B82F6", "Виконано": "#10B981"}


def font(size=14, bold=False):
    return ctk.CTkFont(family="Segoe UI", size=size, weight="bold" if bold else "normal")


def page_title(parent, text):
    label = ctk.CTkLabel(parent, text=text, font=font(24, bold=True), anchor="w")
    label.pack(fill="x", padx=24, pady=(20, 12))
    return label


def card(parent, **pack_kwargs):
    frame = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12)
    frame.pack(fill="x", padx=pack_kwargs.get("padx", 24), pady=pack_kwargs.get("pady", 6))
    return frame
