import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import queue
import webbrowser

from assistant import (
    AIAssistant,
    SPEECH_AVAILABLE,
    TTS_AVAILABLE,
    MIC_AVAILABLE,
    SOUNDDEVICE_AVAILABLE,
    PYAUDIO_AVAILABLE,
)
from gemini_engine import AVAILABLE_MODELS

# ── Gemini Brand Colour Palette ───────────────────────────────────────────────
BG_DARK       = "#090d16"      # Deep cosmic dark
BG_PANEL      = "#0f172a"      # Slate navy header / panels
BG_CARD       = "#141e33"      # Elevated card background
BG_CARD_LIGHT = "#1e293b"      # Card highlight
GEMINI_BLUE   = "#4285f4"      # Google blue
GEMINI_PURPLE = "#9b72cf"      # Gemini orchid purple
GEMINI_CYAN   = "#22d3ee"      # Electric cyan sparkle
ACCENT        = "#6366f1"      # Indigo accent
ACCENT2       = "#38bdf8"      # Sky blue
SUCCESS       = "#10b981"      # Emerald green
WARNING       = "#f59e0b"      # Amber
DANGER        = "#ef4444"      # Crimson red
TEXT_PRIMARY  = "#f8fafc"      # Pure high-contrast text
TEXT_MUTED    = "#94a3b8"      # Subdued slate text
BORDER        = "#1e293b"      # Subtle separator border


def _font(size: int, weight: str = "normal", family: str = "Segoe UI"):
    return (family, size, weight)


# ── Animated Gemini Pulse Mic Button ─────────────────────────────────────────
class PulseButton(tk.Canvas):
    """Circular mic button with an animated Google Gemini pulse ring."""

    def __init__(self, master, command, **kwargs):
        size = 114
        super().__init__(
            master,
            width=size,
            height=size,
            bg=BG_DARK,
            highlightthickness=0,
            **kwargs,
        )
        self.size = size
        self.command = command
        self._pulse_r = 0
        self._active = False
        self._anim_id = None
        self._draw_idle()
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _draw_idle(self):
        self.delete("all")
        cx = cy = self.size // 2
        r = 42
        # Outer celestial glow
        self.create_oval(
            cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8,
            fill="#0f1f3d", outline=GEMINI_PURPLE, width=2,
        )
        # Main circle with Gemini gradient feel
        self.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=GEMINI_BLUE, outline="", tags="btn",
        )
        # Mic icon
        self.create_rectangle(
            cx - 8, cy - 18, cx + 8, cy + 8,
            fill=TEXT_PRIMARY, outline="",
        )
        self.create_arc(
            cx - 14, cy - 4, cx + 14, cy + 18,
            start=0, extent=-180, fill=TEXT_PRIMARY, outline="",
        )
        self.create_line(cx, cy + 18, cx, cy + 26, fill=TEXT_PRIMARY, width=3)
        self.create_line(cx - 10, cy + 26, cx + 10, cy + 26, fill=TEXT_PRIMARY, width=3)

    def _draw_active(self, pulse_r):
        self.delete("all")
        cx = cy = self.size // 2
        r = 42
        # Multi-color animated Gemini cosmic pulse rings
        rings = [
            (pulse_r, GEMINI_CYAN),
            (pulse_r - 12, GEMINI_BLUE),
            (pulse_r - 24, GEMINI_PURPLE),
        ]
        for pr, col in rings:
            if pr > 0:
                self.create_oval(
                    cx - pr, cy - pr, cx + pr, cy + pr,
                    fill="", outline=col, width=2,
                )
        # Glowing active circle
        self.create_oval(
            cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8,
            fill="#0c2045", outline=GEMINI_CYAN, width=3,
        )
        self.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=GEMINI_PURPLE, outline="",
        )
        # Mic icon
        self.create_rectangle(
            cx - 8, cy - 18, cx + 8, cy + 8,
            fill=TEXT_PRIMARY, outline="",
        )
        self.create_arc(
            cx - 14, cy - 4, cx + 14, cy + 18,
            start=0, extent=-180, fill=TEXT_PRIMARY, outline="",
        )
        self.create_line(cx, cy + 18, cx, cy + 26, fill=TEXT_PRIMARY, width=3)
        self.create_line(cx - 10, cy + 26, cx + 10, cy + 26, fill=TEXT_PRIMARY, width=3)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._pulse_r = 46
            self._animate()
        else:
            if self._anim_id:
                self.after_cancel(self._anim_id)
                self._anim_id = None
            self._draw_idle()

    def _animate(self):
        if not self._active:
            return
        self._pulse_r += 1.8
        if self._pulse_r > 62:
            self._pulse_r = 46
        self._draw_active(self._pulse_r)
        self._anim_id = self.after(30, self._animate)

    def _on_enter(self, _):
        if not self._active:
            self.configure(cursor="hand2")

    def _on_leave(self, _):
        pass


# ── In-App Gemini Settings Modal ──────────────────────────────────────────────
class SettingsDialog(tk.Toplevel):
    """Modern dark settings dialog for Gemini API key, model selection, and speech controls."""

    def __init__(self, parent, assistant: AIAssistant, on_save_callback):
        super().__init__(parent)
        self.assistant = assistant
        self.on_save_callback = on_save_callback
        self.title("⚙️ GEMINI AI – Settings")
        self.geometry("560x580")
        self.resizable(False, False)
        self.configure(bg=BG_DARK)
        self.transient(parent)
        self.grab_set()

        # Centre over parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()
        w, h = 560, 580
        x = max(0, px + (pw - w) // 2)
        y = max(0, py + (ph - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._show_key = False
        self._build_ui()

    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=BG_PANEL, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(
            hdr, text="⚙️  Gemini AI Assistant Settings",
            bg=BG_PANEL, fg=TEXT_PRIMARY, font=_font(13, "bold"),
        ).pack(side="left", padx=16, pady=12)

        # ── Body scroll frame ──
        body = tk.Frame(self, bg=BG_DARK, padx=16, pady=12)
        body.pack(fill="both", expand=True)

        # ── Card 1: Google Gemini API ──
        c1 = tk.LabelFrame(
            body, text="  ✦ Google Gemini API Configuration  ",
            bg=BG_CARD, fg=GEMINI_CYAN, font=_font(10, "bold"),
            bd=1, relief="solid", padx=14, pady=10,
        )
        c1.pack(fill="x", pady=(0, 12))

        tk.Label(
            c1,
            text="Power your assistant with Google's state-of-the-art Gemini intelligence.",
            bg=BG_CARD, fg=TEXT_MUTED, font=_font(8), justify="left",
        ).pack(anchor="w", pady=(0, 6))

        # Direct link button to Google AI Studio
        link_row = tk.Frame(c1, bg=BG_CARD)
        link_row.pack(fill="x", pady=(0, 8))

        tk.Label(
            link_row, text="Need a free key?", bg=BG_CARD,
            fg=TEXT_PRIMARY, font=_font(9),
        ).pack(side="left")

        get_key_btn = tk.Button(
            link_row, text="🔗  Get Free Key at Google AI Studio",
            bg=BG_CARD_LIGHT, fg=GEMINI_CYAN, font=_font(8, "bold"),
            relief="flat", bd=0, cursor="hand2", padx=8, pady=3,
            activebackground=GEMINI_BLUE, activeforeground=TEXT_PRIMARY,
            command=lambda: webbrowser.open("https://aistudio.google.com/app/apikey"),
        )
        get_key_btn.pack(side="left", padx=8)

        # API Key input
        tk.Label(c1, text="Gemini API Key:", bg=BG_CARD, fg=TEXT_PRIMARY, font=_font(9, "bold")).pack(anchor="w")

        key_row = tk.Frame(c1, bg=BG_CARD)
        key_row.pack(fill="x", pady=(4, 8))

        self.key_entry = tk.Entry(
            key_row, bg=BG_DARK, fg=TEXT_PRIMARY, insertbackground=GEMINI_CYAN,
            font=_font(9), relief="flat", bd=0, show="*",
        )
        self.key_entry.pack(side="left", fill="x", expand=True, ipady=6, ipadx=8)
        self.key_entry.insert(0, self.assistant.get_gemini_api_key())

        self.toggle_btn = tk.Button(
            key_row, text="👁 Show", bg=BG_CARD_LIGHT, fg=TEXT_PRIMARY,
            font=_font(8), relief="flat", bd=0, cursor="hand2", padx=8, pady=6,
            command=self._toggle_show_key,
        )
        self.toggle_btn.pack(side="left", padx=(6, 0))

        paste_btn = tk.Button(
            key_row, text="📋 Paste", bg=BG_CARD_LIGHT, fg=TEXT_PRIMARY,
            font=_font(8), relief="flat", bd=0, cursor="hand2", padx=8, pady=6,
            command=self._paste_key,
        )
        paste_btn.pack(side="left", padx=(6, 0))

        # Model selection
        model_row = tk.Frame(c1, bg=BG_CARD)
        model_row.pack(fill="x", pady=(4, 8))

        tk.Label(model_row, text="Gemini Model:", bg=BG_CARD, fg=TEXT_PRIMARY, font=_font(9, "bold")).pack(side="left")

        self.model_var = tk.StringVar(value=self.assistant.get_gemini_model())
        self.model_combo = ttk.Combobox(
            model_row, textvariable=self.model_var,
            values=AVAILABLE_MODELS, state="readonly", width=20,
        )
        self.model_combo.pack(side="left", padx=10)

        # Test Connection button & result badge
        test_row = tk.Frame(c1, bg=BG_CARD)
        test_row.pack(fill="x", pady=(4, 2))

        self.test_btn = tk.Button(
            test_row, text="⚡  Test Connection",
            bg=GEMINI_BLUE, fg=TEXT_PRIMARY, font=_font(9, "bold"),
            relief="flat", bd=0, cursor="hand2", padx=12, pady=5,
            activebackground="#2563eb",
            command=self._test_connection,
        )
        self.test_btn.pack(side="left")

        self.test_status_var = tk.StringVar(value="")
        self.test_status_lbl = tk.Label(
            test_row, textvariable=self.test_status_var,
            bg=BG_CARD, fg=TEXT_MUTED, font=_font(8),
        )
        self.test_status_lbl.pack(side="left", padx=10)

        # ── Card 2: Voice & Speech (TTS) ──
        c2 = tk.LabelFrame(
            body, text="  🔊 Voice & Speech Synthesis (TTS)  ",
            bg=BG_CARD, fg=GEMINI_PURPLE, font=_font(10, "bold"),
            bd=1, relief="solid", padx=14, pady=10,
        )
        c2.pack(fill="x", pady=(0, 14))

        self.tts_enabled_var = tk.BooleanVar(value=self.assistant.data.get("tts_enabled", True))
        tts_cb = tk.Checkbutton(
            c2, text="Enable Voice Responses (Text-to-Speech)",
            variable=self.tts_enabled_var, bg=BG_CARD, fg=TEXT_PRIMARY,
            selectcolor=BG_DARK, activebackground=BG_CARD, activeforeground=TEXT_PRIMARY,
            font=_font(9),
        )
        tts_cb.pack(anchor="w", pady=(0, 6))

        # Speed Rate slider
        rate_row = tk.Frame(c2, bg=BG_CARD)
        rate_row.pack(fill="x", pady=2)
        tk.Label(rate_row, text="Speech Rate (WPM):", bg=BG_CARD, fg=TEXT_MUTED, font=_font(8)).pack(side="left")
        self.rate_slider = tk.Scale(
            rate_row, from_=100, to=250, orient="horizontal",
            bg=BG_CARD, fg=TEXT_PRIMARY, highlightthickness=0,
            troughcolor=BG_DARK, activebackground=GEMINI_BLUE, bd=0,
        )
        self.rate_slider.set(self.assistant.data.get("tts_rate", 175))
        self.rate_slider.pack(side="left", fill="x", expand=True, padx=10)

        # Test Voice button
        test_voice_btn = tk.Button(
            c2, text="🔊  Test Voice Output",
            bg=BG_CARD_LIGHT, fg=TEXT_PRIMARY, font=_font(8),
            relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
            command=lambda: self.assistant.speak("Hello! Google Gemini voice assistant is working properly."),
        )
        test_voice_btn.pack(anchor="w", pady=(6, 2))

        # ── Bottom action bar ──
        bottom_bar = tk.Frame(self, bg=BG_PANEL, height=52)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        save_btn = tk.Button(
            bottom_bar, text="💾  Save Settings",
            bg=SUCCESS, fg=TEXT_PRIMARY, font=_font(9, "bold"),
            relief="flat", bd=0, cursor="hand2", padx=16, pady=6,
            activebackground="#059669",
            command=self._save_settings,
        )
        save_btn.pack(side="right", padx=16, pady=10)

        cancel_btn = tk.Button(
            bottom_bar, text="Cancel",
            bg=BG_CARD_LIGHT, fg=TEXT_PRIMARY, font=_font(9),
            relief="flat", bd=0, cursor="hand2", padx=14, pady=6,
            command=self.destroy,
        )
        cancel_btn.pack(side="right", padx=6, pady=10)

    def _toggle_show_key(self):
        self._show_key = not self._show_key
        if self._show_key:
            self.key_entry.configure(show="")
            self.toggle_btn.configure(text="🔒 Hide")
        else:
            self.key_entry.configure(show="*")
            self.toggle_btn.configure(text="👁 Show")

    def _paste_key(self):
        try:
            cb_text = self.clipboard_get().strip()
            if cb_text:
                self.key_entry.delete(0, "end")
                self.key_entry.insert(0, cb_text)
        except Exception:
            pass

    def _test_connection(self):
        key = self.key_entry.get().strip()
        model = self.model_var.get()
        if not key:
            self.test_status_var.set("⚠️ Please enter an API key.")
            self.test_status_lbl.configure(fg=WARNING)
            return

        self.test_status_var.set("Testing connection...")
        self.test_status_lbl.configure(fg=GEMINI_CYAN)
        self.test_btn.configure(state="disabled")

        def _run():
            ok, msg = self.assistant.test_gemini_connection(key=key, model=model)
            def _update():
                self.test_btn.configure(state="normal")
                if ok:
                    self.test_status_var.set(f"✅ {msg}")
                    self.test_status_lbl.configure(fg=SUCCESS)
                else:
                    self.test_status_var.set(f"❌ {msg[:45]}...")
                    self.test_status_lbl.configure(fg=DANGER)
            self.after(0, _update)

        threading.Thread(target=_run, daemon=True).start()

    def _save_settings(self):
        key = self.key_entry.get().strip()
        model = self.model_var.get()
        tts_enabled = self.tts_enabled_var.get()
        tts_rate = int(self.rate_slider.get())

        self.assistant.set_gemini_api_key(key)
        self.assistant.set_gemini_model(model)
        self.assistant.update_tts_settings(enabled=tts_enabled, rate=tts_rate)

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()


# ── Gemini Chat View (Interactive Conversation) ──────────────────────────────
class GeminiChatView(tk.Frame):
    """Full-featured scrollable conversational chat stream powered by Google Gemini."""

    def __init__(self, master, assistant: AIAssistant, on_submit_query, on_voice_click, **kwargs):
        super().__init__(master, bg=BG_DARK, **kwargs)
        self.assistant = assistant
        self.on_submit_query = on_submit_query
        self.on_voice_click = on_voice_click
        self._build_ui()

    def _build_ui(self):
        # ── Header bar ──
        top_row = tk.Frame(self, bg=BG_CARD, height=40)
        top_row.pack(fill="x", padx=8, pady=(4, 6))
        top_row.pack_propagate(False)

        tk.Label(
            top_row, text="✦  Gemini Conversational Chat",
            bg=BG_CARD, fg=GEMINI_CYAN, font=_font(10, "bold"),
        ).pack(side="left", padx=10, pady=8)

        clear_btn = tk.Button(
            top_row, text="🗑️  Clear Chat",
            bg=BG_CARD_LIGHT, fg=TEXT_MUTED, font=_font(8),
            relief="flat", bd=0, cursor="hand2", padx=8, pady=2,
            activebackground=DANGER, activeforeground=TEXT_PRIMARY,
            command=self.clear_chat,
        )
        clear_btn.pack(side="right", padx=10, pady=6)

        # ── Scrollable Chat Feed ──
        chat_box_frame = tk.Frame(self, bg=BG_CARD)
        chat_box_frame.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        self.chat_text = tk.Text(
            chat_box_frame, bg=BG_CARD, fg=TEXT_PRIMARY,
            font=_font(10), bd=0, relief="flat", wrap="word",
            state="disabled", cursor="arrow", padx=12, pady=10,
        )
        sb = ttk.Scrollbar(chat_box_frame, orient="vertical", command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.chat_text.pack(fill="both", expand=True)

        # Tag configurations for rich typography
        self.chat_text.tag_configure("user_hdr", foreground=GEMINI_CYAN, font=_font(9, "bold"))
        self.chat_text.tag_configure("user_body", foreground=TEXT_PRIMARY, font=_font(10))
        self.chat_text.tag_configure("gemini_hdr", foreground=GEMINI_PURPLE, font=_font(9, "bold"))
        self.chat_text.tag_configure("gemini_body", foreground=TEXT_PRIMARY, font=_font(10))
        self.chat_text.tag_configure("timestamp", foreground=TEXT_MUTED, font=_font(8))
        self.chat_text.tag_configure("code_block", foreground="#a5f3fc", background="#0b1120", font=("Consolas", 9))
        self.chat_text.tag_configure("divider", foreground=BORDER)

        # Welcome message
        self._add_welcome_message()

        # ── Quick Suggestions Pills ──
        pills_frame = tk.Frame(self, bg=BG_DARK)
        pills_frame.pack(fill="x", padx=8, pady=(0, 6))

        suggestions = [
            ("✨ Explain AI", "Explain artificial intelligence in simple terms"),
            ("🐍 Python Code", "Write a Python script to monitor system CPU and RAM usage"),
            ("💡 Brainstorm", "Brainstorm 5 innovative desktop app ideas"),
            ("📝 Draft Email", "Draft a professional email requesting project status update"),
        ]
        for label, prompt in suggestions:
            btn = tk.Button(
                pills_frame, text=label, bg=BG_CARD, fg=TEXT_MUTED,
                font=_font(8), relief="flat", bd=0, cursor="hand2", padx=8, pady=3,
                activebackground=GEMINI_BLUE, activeforeground=TEXT_PRIMARY,
                command=lambda p=prompt: self.on_submit_query(p),
            )
            btn.pack(side="left", padx=(0, 6))

        # ── Input row ──
        input_row = tk.Frame(self, bg=BG_DARK)
        input_row.pack(fill="x", padx=8, pady=(0, 8))

        self.chat_input = tk.Entry(
            input_row, bg=BG_CARD, fg=TEXT_PRIMARY, insertbackground=GEMINI_CYAN,
            font=_font(11), relief="flat", bd=0,
        )
        self.chat_input.pack(side="left", fill="x", expand=True, ipady=10, ipadx=10)
        self.chat_input.bind("<Return>", lambda e: self._send_input())

        self.chat_input.insert(0, "Ask Gemini anything or type a command…")
        self.chat_input.configure(fg=TEXT_MUTED)
        self.chat_input.bind("<FocusIn>", self._clear_placeholder)
        self.chat_input.bind("<FocusOut>", self._restore_placeholder)

        # Mic button
        mic_btn = tk.Button(
            input_row, text="🎙️", bg=BG_CARD_LIGHT, fg=TEXT_PRIMARY,
            font=_font(11), relief="flat", bd=0, cursor="hand2", padx=10, pady=6,
            activebackground=GEMINI_BLUE,
            command=self.on_voice_click,
        )
        mic_btn.pack(side="left", padx=(6, 0))

        # Send button
        send_btn = tk.Button(
            input_row, text="  Send 🚀  ", bg=GEMINI_BLUE, fg=TEXT_PRIMARY,
            font=_font(9, "bold"), relief="flat", bd=0, cursor="hand2", padx=12, pady=10,
            activebackground="#2563eb",
            command=self._send_input,
        )
        send_btn.pack(side="left", padx=(6, 0))

    def _clear_placeholder(self, _):
        if self.chat_input.get() == "Ask Gemini anything or type a command…":
            self.chat_input.delete(0, "end")
            self.chat_input.configure(fg=TEXT_PRIMARY)

    def _restore_placeholder(self, _):
        if not self.chat_input.get():
            self.chat_input.insert(0, "Ask Gemini anything or type a command…")
            self.chat_input.configure(fg=TEXT_MUTED)

    def _send_input(self):
        text = self.chat_input.get().strip()
        if not text or text == "Ask Gemini anything or type a command…":
            return
        self.chat_input.delete(0, "end")
        self.on_submit_query(text)

    def _add_welcome_message(self):
        self.chat_text.configure(state="normal")
        self.chat_text.insert(
            "end",
            "✦ Welcome to Google Gemini Assistant!\n",
            "gemini_hdr",
        )
        self.chat_text.insert(
            "end",
            "I can answer complex questions, write and debug code, brainstorm ideas, "
            "perform calculations, open applications, manage local files, and check prices.\n"
            "Type a message below or click the microphone to speak!\n\n"
            "──────────────────────────────────────────────────────────────────────────\n\n",
            "divider",
        )
        self.chat_text.configure(state="disabled")

    def add_message(self, user_text: str, response: str):
        import datetime
        self.chat_text.configure(state="normal")
        ts = datetime.datetime.now().strftime("%H:%M:%S")

        # User bubble
        self.chat_text.insert("end", f"[{ts}]  ", "timestamp")
        self.chat_text.insert("end", "👤 You:\n", "user_hdr")
        self.chat_text.insert("end", f"{user_text}\n\n", "user_body")

        # Gemini bubble
        self.chat_text.insert("end", f"[{ts}]  ", "timestamp")
        self.chat_text.insert("end", "✦ Gemini AI:\n", "gemini_hdr")

        # Format code blocks if present
        if "```" in response:
            parts = response.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    # Code snippet block
                    self.chat_text.insert("end", f"\n{part.strip()}\n\n", "code_block")
                else:
                    if part:
                        self.chat_text.insert("end", f"{part}", "gemini_body")
            self.chat_text.insert("end", "\n\n")
        else:
            self.chat_text.insert("end", f"{response}\n\n", "gemini_body")

        self.chat_text.insert(
            "end",
            "──────────────────────────────────────────────────────────────────────────\n\n",
            "divider",
        )
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def clear_chat(self):
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")
        self._add_welcome_message()
        self.chat_text.configure(state="disabled")
        self.assistant.clear_gemini_history()


# ── History Frame (for Voice Mode) ───────────────────────────────────────────
class HistoryFrame(tk.Frame):
    """Scrollable log of past commands and responses."""

    def __init__(self, master, **kwargs):
        super().__init__(master, bg=BG_CARD, **kwargs)
        tk.Label(
            self, text="📋  Command & Query History", bg=BG_CARD,
            fg=TEXT_MUTED, font=_font(9, "bold"),
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.text = tk.Text(
            self, bg=BG_CARD, fg=TEXT_PRIMARY, font=_font(9),
            bd=0, relief="flat", wrap="word", state="disabled", cursor="arrow",
        )
        sb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.text.tag_configure("user", foreground=GEMINI_CYAN, font=_font(9, "bold"))
        self.text.tag_configure("response", foreground=TEXT_PRIMARY, font=_font(9))
        self.text.tag_configure("error", foreground=DANGER, font=_font(9))
        self.text.tag_configure("ts", foreground=TEXT_MUTED, font=_font(8))

    def add(self, user_text: str, response: str):
        import datetime
        self.text.configure(state="normal")
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.text.insert("end", f"[{ts}]  ", "ts")
        self.text.insert("end", f"🎙 {user_text}\n", "user")
        tag = "error" if "❌" in response else "response"
        self.text.insert("end", f"   {response}\n\n", tag)
        self.text.configure(state="disabled")
        self.text.see("end")


# ── Stats Frame ──────────────────────────────────────────────────────────────
class StatsFrame(tk.Frame):
    """Shows top-used commands and usage count."""

    def __init__(self, master, assistant: AIAssistant, **kwargs):
        super().__init__(master, bg=BG_CARD, **kwargs)
        self.assistant = assistant
        tk.Label(
            self, text="📊  Top Commands", bg=BG_CARD,
            fg=TEXT_MUTED, font=_font(9, "bold"),
        ).pack(anchor="w", padx=10, pady=(8, 4))

        self.list_var = tk.StringVar()
        self.listbox = tk.Listbox(
            self, listvariable=self.list_var,
            bg=BG_CARD, fg=TEXT_PRIMARY,
            selectbackground=GEMINI_BLUE, selectforeground=TEXT_PRIMARY,
            font=_font(9), bd=0, relief="flat", highlightthickness=0, height=5,
        )
        self.listbox.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.refresh()

    def refresh(self):
        top = self.assistant.get_top_commands(5)
        if top:
            entries = [f"{i+1}. {name}  ×{cnt}" for i, (name, cnt) in enumerate(top)]
        else:
            entries = ["No commands logged yet."]
        self.list_var.set(entries)


# ── Main Application ─────────────────────────────────────────────────────────
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("✦ GEMINI AI – Voice & Desktop Assistant")
        self.geometry("860x700")
        self.minsize(720, 580)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aria_icon.ico")
        if getattr(sys, "frozen", False):
            base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            icon_path = os.path.join(base_dir, "aria_icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Centre on screen
        self.update_idletasks()
        x = max(0, (self.winfo_screenwidth() - 860) // 2)
        y = max(0, (self.winfo_screenheight() - 700) // 2)
        self.geometry(f"860x700+{x}+{y}")

        self.assistant = AIAssistant()
        self._listening = False
        self._msg_queue: queue.Queue = queue.Queue()
        self._current_mode = "voice"  # "voice" or "chat"

        self._build_ui()
        self._poll_queue()
        self._update_status_bar()
        self._update_gemini_badge()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # ── Top Bar ──
        topbar = tk.Frame(self, bg=BG_PANEL, height=62)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        # Brand Title with Gemini Sparkle
        title_frame = tk.Frame(topbar, bg=BG_PANEL)
        title_frame.pack(side="left", padx=16, pady=10)

        tk.Label(
            title_frame, text="✦  GEMINI AI", bg=BG_PANEL,
            fg=TEXT_PRIMARY, font=_font(16, "bold"),
        ).pack(side="left")

        tk.Label(
            title_frame, text="  •  Desktop & Voice Assistant",
            bg=BG_PANEL, fg=TEXT_MUTED, font=_font(9),
        ).pack(side="left", padx=(4, 0))

        # Mode Switcher Tabs
        mode_frame = tk.Frame(topbar, bg=BG_PANEL)
        mode_frame.pack(side="left", padx=24)

        self.tab_voice_btn = tk.Button(
            mode_frame, text="🎙️  Voice Assistant",
            bg=GEMINI_BLUE, fg=TEXT_PRIMARY, font=_font(9, "bold"),
            relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
            command=lambda: self._switch_view("voice"),
        )
        self.tab_voice_btn.pack(side="left", padx=2)

        self.tab_chat_btn = tk.Button(
            mode_frame, text="💬  Gemini Chat",
            bg=BG_CARD, fg=TEXT_MUTED, font=_font(9),
            relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
            command=lambda: self._switch_view("chat"),
        )
        self.tab_chat_btn.pack(side="left", padx=2)

        # Right side controls: Gemini Status Pill + Settings Button
        right_top = tk.Frame(topbar, bg=BG_PANEL)
        right_top.pack(side="right", padx=16)

        self.settings_btn = tk.Button(
            right_top, text="⚙️  Settings",
            bg=BG_CARD_LIGHT, fg=TEXT_PRIMARY, font=_font(9, "bold"),
            relief="flat", bd=0, cursor="hand2", padx=10, pady=4,
            activebackground=GEMINI_BLUE, activeforeground=TEXT_PRIMARY,
            command=self._open_settings,
        )
        self.settings_btn.pack(side="right", padx=(8, 0))

        self.status_pill = tk.Button(
            right_top, text="✨ Gemini Active",
            bg=SUCCESS, fg=TEXT_PRIMARY, font=_font(8, "bold"),
            relief="flat", bd=0, cursor="hand2", padx=8, pady=3,
            command=self._open_settings,
        )
        self.status_pill.pack(side="right")

        # ── Main Content Split ──
        self.body = tk.Frame(self, bg=BG_DARK)
        self.body.pack(fill="both", expand=True, padx=12, pady=8)

        # Left / Center Area for views
        self.main_container = tk.Frame(self.body, bg=BG_DARK)
        self.main_container.pack(side="left", fill="both", expand=True)

        # Sidebar (always accessible)
        self.sidebar = tk.Frame(self.body, bg=BG_DARK, width=220)
        self.sidebar.pack(side="right", fill="y", padx=(8, 0))
        self.sidebar.pack_propagate(False)

        self._build_sidebar(self.sidebar)

        # Initialize both views inside main_container
        self.voice_view = tk.Frame(self.main_container, bg=BG_DARK)
        self.chat_view = GeminiChatView(
            self.main_container,
            self.assistant,
            on_submit_query=self._run_text_command,
            on_voice_click=self._toggle_listen,
        )

        self._build_voice_view(self.voice_view)

        # Start on Voice View
        self.voice_view.pack(fill="both", expand=True)

        # ── Status Bar ──
        self.statusbar = tk.Label(
            self, text="Ready", bg=BG_PANEL, fg=TEXT_MUTED,
            font=_font(8), anchor="w", padx=12,
        )
        self.statusbar.pack(fill="x", side="bottom")

    def _build_voice_view(self, parent):
        # ── Voice Display Card ──
        card = tk.Frame(parent, bg=BG_CARD, bd=0)
        card.pack(fill="x", pady=(0, 8))

        self.wave_label = tk.Label(
            card, text="───── Ready for Gemini ─────",
            bg=BG_CARD, fg=TEXT_MUTED, font=_font(9),
        )
        self.wave_label.pack(pady=(12, 0))

        self.heard_var = tk.StringVar(value="Press the mic or type a command below")
        heard_lbl = tk.Label(
            card, textvariable=self.heard_var,
            bg=BG_CARD, fg=GEMINI_CYAN,
            font=_font(12, "bold"), wraplength=480, justify="center",
        )
        heard_lbl.pack(pady=(6, 0), padx=20)

        self.resp_var = tk.StringVar(value="")
        resp_lbl = tk.Label(
            card, textvariable=self.resp_var,
            bg=BG_CARD, fg=TEXT_PRIMARY,
            font=_font(10), wraplength=480, justify="center",
        )
        resp_lbl.pack(pady=(6, 12), padx=20)

        # ── Mic & Quick Actions Row ──
        btn_row = tk.Frame(parent, bg=BG_DARK)
        btn_row.pack(pady=4)

        self.mic_btn = PulseButton(btn_row, command=self._toggle_listen)
        self.mic_btn.pack(side="left", padx=16)

        shortcuts = tk.Frame(btn_row, bg=BG_DARK)
        shortcuts.pack(side="left", padx=8)

        lbl_hint = tk.Label(
            shortcuts, text="Gemini Quick Actions:", bg=BG_DARK,
            fg=TEXT_MUTED, font=_font(8),
        )
        lbl_hint.pack(anchor="w")

        quick_cmds = [
            ("✨  Ask Gemini", "ask gemini "),
            ("🕐  Time", "what time is it"),
            ("📅  Date", "what date is it"),
            ("🌐  YouTube", "open youtube"),
            ("🌐  GitHub", "open github"),
            ("💰  Price Check", "price of "),
            ("📂  List Files", "list files in ."),
            ("❓  Help", "help"),
        ]
        for label, cmd in quick_cmds:
            b = tk.Button(
                shortcuts, text=label, bg=BG_CARD, fg=TEXT_PRIMARY,
                font=_font(8), relief="flat", bd=0, cursor="hand2", padx=10, pady=3,
                activebackground=GEMINI_BLUE, activeforeground=TEXT_PRIMARY,
                command=lambda c=cmd: self._run_text_command(c),
            )
            b.pack(fill="x", pady=2)

        # ── Prompt Input Row ──
        input_row = tk.Frame(parent, bg=BG_DARK)
        input_row.pack(fill="x", pady=(6, 0))

        self.text_input = tk.Entry(
            input_row, bg=BG_CARD, fg=TEXT_PRIMARY, insertbackground=GEMINI_CYAN,
            font=_font(11), relief="flat", bd=0,
        )
        self.text_input.pack(side="left", fill="x", expand=True, ipady=10, ipadx=10)
        self.text_input.bind("<Return>", lambda e: self._submit_text())
        self.text_input.insert(0, "Type a query, ask Gemini, or launch apps…")
        self.text_input.configure(fg=TEXT_MUTED)
        self.text_input.bind("<FocusIn>", self._clear_voice_placeholder)
        self.text_input.bind("<FocusOut>", self._restore_voice_placeholder)

        send_btn = tk.Button(
            input_row, text="  Send  ", bg=GEMINI_BLUE, fg=TEXT_PRIMARY,
            font=_font(10, "bold"), relief="flat", bd=0, cursor="hand2", padx=14, pady=10,
            activebackground="#2563eb",
            command=self._submit_text,
        )
        send_btn.pack(side="right", padx=(6, 0))

        # ── Teach New App Row ──
        learn_row = tk.Frame(parent, bg=BG_DARK)
        learn_row.pack(fill="x", pady=(6, 0))

        tk.Label(
            learn_row, text="Teach app:", bg=BG_DARK,
            fg=TEXT_MUTED, font=_font(8),
        ).pack(side="left", padx=(0, 6))

        self.learn_name = tk.Entry(
            learn_row, bg=BG_CARD, fg=TEXT_PRIMARY, insertbackground=GEMINI_CYAN,
            font=_font(9), relief="flat", width=14,
        )
        self.learn_name.pack(side="left", ipady=6, ipadx=6)

        tk.Label(
            learn_row, text="→  Path:", bg=BG_DARK,
            fg=TEXT_MUTED, font=_font(8),
        ).pack(side="left", padx=6)

        self.learn_path = tk.Entry(
            learn_row, bg=BG_CARD, fg=TEXT_PRIMARY, insertbackground=GEMINI_CYAN,
            font=_font(9), relief="flat", width=22,
        )
        self.learn_path.pack(side="left", ipady=6, ipadx=6)

        teach_btn = tk.Button(
            learn_row, text="Teach", bg=SUCCESS, fg=TEXT_PRIMARY,
            font=_font(9, "bold"), relief="flat", bd=0, cursor="hand2", padx=10, pady=6,
            activebackground="#059669",
            command=self._teach_app,
        )
        teach_btn.pack(side="left", padx=(6, 0))

        # ── History Frame ──
        self.history_frame = HistoryFrame(parent)
        self.history_frame.pack(fill="both", expand=True, pady=(8, 0))

    def _build_sidebar(self, parent):
        # ── Gemini Engine Info Card ──
        g_card = tk.Frame(parent, bg=BG_CARD)
        g_card.pack(fill="x", pady=(0, 8))

        tk.Label(
            g_card, text="✦  Gemini Engine", bg=BG_CARD,
            fg=GEMINI_CYAN, font=_font(9, "bold"),
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.gemini_info_lbl = tk.Label(
            g_card, text="", bg=BG_CARD, fg=TEXT_PRIMARY,
            font=_font(8), justify="left",
        )
        self.gemini_info_lbl.pack(anchor="w", padx=10, pady=(0, 8))

        # ── Stats Card ──
        self.stats_frame = StatsFrame(parent, self.assistant)
        self.stats_frame.pack(fill="x", pady=(0, 8))

        # ── Capabilities Card ──
        caps = tk.Frame(parent, bg=BG_CARD)
        caps.pack(fill="x", pady=(0, 8))
        tk.Label(
            caps, text="⚡  Capabilities", bg=BG_CARD,
            fg=TEXT_MUTED, font=_font(9, "bold"),
        ).pack(anchor="w", padx=10, pady=(8, 4))

        items = [
            ("✦", "Google Gemini AI Brain"),
            ("🎤", "Voice & speech input"),
            ("🔊", "Text-to-speech output"),
            ("💻", "Desktop apps & control"),
            ("🌐", "80+ named websites"),
            ("💰", "Price comparison"),
            ("📄", "Read, create & edit files"),
            ("▶️", "Run Python scripts"),
            ("🧠", "Learns custom paths"),
        ]
        for icon, text in items:
            row = tk.Frame(caps, bg=BG_CARD)
            row.pack(fill="x", padx=10, pady=1)
            tk.Label(row, text=icon, bg=BG_CARD, font=_font(8)).pack(side="left")
            tk.Label(
                row, text=text, bg=BG_CARD, fg=TEXT_PRIMARY,
                font=_font(8),
            ).pack(side="left", padx=4)
        tk.Frame(caps, bg=BG_CARD, height=6).pack()

        # ── Audio & Mic Info ──
        mic_info = tk.Frame(parent, bg=BG_CARD)
        mic_info.pack(fill="x")
        tk.Label(
            mic_info, text="🎙  Hardware Status", bg=BG_CARD,
            fg=TEXT_MUTED, font=_font(9, "bold"),
        ).pack(anchor="w", padx=10, pady=(8, 2))

        if PYAUDIO_AVAILABLE:
            mic_status = "✅  PyAudio (active)"
            mic_col = SUCCESS
        elif SOUNDDEVICE_AVAILABLE:
            mic_status = "✅  sounddevice (active)"
            mic_col = SUCCESS
        else:
            mic_status = "❌  No audio backend"
            mic_col = DANGER

        tk.Label(
            mic_info, text=mic_status, bg=BG_CARD, fg=mic_col,
            font=_font(8), justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 4))

        tts_status = "✅  Active" if TTS_AVAILABLE else "❌  Unavailable"
        tts_col = SUCCESS if TTS_AVAILABLE else DANGER
        tk.Label(
            mic_info, text=f"🔊  TTS: {tts_status}", bg=BG_CARD, fg=tts_col,
            font=_font(8), justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 8))

    def _switch_view(self, mode: str):
        if mode == self._current_mode:
            return
        self._current_mode = mode
        if mode == "voice":
            self.chat_view.pack_forget()
            self.voice_view.pack(fill="both", expand=True)
            self.tab_voice_btn.configure(bg=GEMINI_BLUE, fg=TEXT_PRIMARY, font=_font(9, "bold"))
            self.tab_chat_btn.configure(bg=BG_CARD, fg=TEXT_MUTED, font=_font(9))
        else:
            self.voice_view.pack_forget()
            self.chat_view.pack(fill="both", expand=True)
            self.tab_chat_btn.configure(bg=GEMINI_PURPLE, fg=TEXT_PRIMARY, font=_font(9, "bold"))
            self.tab_voice_btn.configure(bg=BG_CARD, fg=TEXT_MUTED, font=_font(9))

    def _open_settings(self):
        SettingsDialog(self, self.assistant, on_save_callback=self._on_settings_saved)

    def _on_settings_saved(self):
        self._update_gemini_badge()
        self.resp_var.set("✅ Settings updated successfully!")
        self.assistant.speak("Settings updated.")

    def _update_gemini_badge(self):
        configured = self.assistant.is_gemini_configured()
        model = self.assistant.get_gemini_model()
        if configured:
            self.status_pill.configure(
                text=f"✨ {model}",
                bg=SUCCESS,
            )
            self.gemini_info_lbl.configure(
                text=f"Model: {model}\nStatus: Active & Ready",
                fg=SUCCESS,
            )
        else:
            self.status_pill.configure(
                text="🔑 Set Gemini Key",
                bg=WARNING,
            )
            self.gemini_info_lbl.configure(
                text=f"Model: {model}\nStatus: Key Needed (Click ⚙️)",
                fg=WARNING,
            )

    # ── Text & Speech Actions ──
    def _clear_voice_placeholder(self, _):
        if self.text_input.get() == "Type a query, ask Gemini, or launch apps…":
            self.text_input.delete(0, "end")
            self.text_input.configure(fg=TEXT_PRIMARY)

    def _restore_voice_placeholder(self, _):
        if not self.text_input.get():
            self.text_input.insert(0, "Type a query, ask Gemini, or launch apps…")
            self.text_input.configure(fg=TEXT_MUTED)

    def _submit_text(self):
        text = self.text_input.get().strip()
        if not text or text == "Type a query, ask Gemini, or launch apps…":
            return
        self.text_input.delete(0, "end")
        self._run_text_command(text)

    def _run_text_command(self, command: str):
        self.heard_var.set(f'🎙 "{command}"')
        self.resp_var.set("Thinking with Gemini…")
        threading.Thread(target=self._process, args=(command,), daemon=True).start()

    def _toggle_listen(self):
        if self._listening:
            return
        if not MIC_AVAILABLE:
            self._show_error("No microphone backend found.\nRun: pip install sounddevice")
            return
        self._listening = True
        self.mic_btn.set_active(True)
        self.wave_label.configure(text="─── Listening… speak to Gemini ───", fg=GEMINI_CYAN)
        self.heard_var.set("🎤 Listening…")
        self.resp_var.set("")
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _listen_thread(self):
        text, err = self.assistant.listen_once()
        self._msg_queue.put(("listened", text, err))

    def _process(self, command: str):
        response = self.assistant.process_command(command)
        self._msg_queue.put(("response", command, response))

    # ── Queue Polling (Thread-Safe UI Updates) ──
    def _poll_queue(self):
        try:
            while True:
                msg = self._msg_queue.get_nowait()
                kind = msg[0]

                if kind == "listened":
                    _, text, err = msg
                    self._listening = False
                    self.mic_btn.set_active(False)
                    self.wave_label.configure(text="───── Ready for Gemini ─────", fg=TEXT_MUTED)
                    if err:
                        self.heard_var.set(f"⚠️ {err}")
                        self.resp_var.set("")
                    else:
                        self.heard_var.set(f'🎙 "{text}"')
                        self.resp_var.set("Thinking with Gemini…")
                        threading.Thread(target=self._process, args=(text,), daemon=True).start()

                elif kind == "response":
                    _, command, response = msg
                    preview = response[:140] + ("…" if len(response) > 140 else "")
                    self.resp_var.set(preview)
                    self.history_frame.add(command, response)
                    self.chat_view.add_message(command, response)
                    self.stats_frame.refresh()

        except Exception:
            pass
        self.after(80, self._poll_queue)

    def _update_status_bar(self):
        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        known = len(self.assistant.data.get("apps", {})) + len(self.assistant.data.get("learned_paths", {}))
        model = self.assistant.get_gemini_model()
        self.statusbar.configure(
            text=f"  🕐 {now}   |   ✦ Gemini Model: {model}   |   📦 {known} apps known   |   🧠 Self-Learning Active"
        )
        self.after(1000, self._update_status_bar)

    def _teach_app(self):
        name = self.learn_name.get().strip().lower()
        path = self.learn_path.get().strip()
        if not name or not path:
            self._show_error("Please enter both the app name and target executable path.")
            return
        self.assistant._remember_path(name, path)
        self.learn_name.delete(0, "end")
        self.learn_path.delete(0, "end")
        msg = f"✅ Taught: '{name}' → '{path}'"
        self.resp_var.set(msg)
        self.history_frame.add(f"[Teach] {name}", msg)
        self.chat_view.add_message(f"Teach {name}", msg)
        self.stats_frame.refresh()
        self.assistant.speak(f"Got it, I'll remember {name}")

    def _show_error(self, msg: str):
        messagebox.showerror("GEMINI AI – Notice", msg, parent=self)

    def _on_close(self):
        self.destroy()


# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
