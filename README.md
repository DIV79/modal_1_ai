# GEMINI AI – Voice & Desktop Assistant ✦🎙️

> **A powerful, intelligent desktop voice & text assistant powered by Google Gemini AI with full Windows automation.**

GEMINI AI combines the conversational intelligence, reasoning, and coding capabilities of Google's Gemini models with desktop voice interaction, offline speech synthesis, quick application launching, file operations, web navigation, and a persistent self-learning engine into an elegant dark-mode cosmic interface.

---

## ✨ Features

- **✦ Google Gemini AI Brain:** Directly answers questions, explains complex concepts, writes and debugs code, solves math, brainstorms, and engages in multi-turn conversations.
- **💬 Dual Interfaces (Voice & Chat Modes):** 
  - **🎙️ Voice Assistant Mode:** Signature animated Gemini celestial pulse mic with dynamic audio effects, instant voice feedback, and quick actions.
  - **💬 Gemini Chat Mode:** Full scrollable conversational stream with rich typography, code snippets, copy functionality, and prompt suggestions.
- **⚙️ In-App Settings & Gemini Key Manager:** Configure and test your free Google Gemini API key and select between `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`, and `gemini-1.5-pro` with live connection verification.
- **🎙️ Dual Input (Voice & Text):** Click the animated pulse mic to speak naturally or type commands directly into prompt bars in either mode.
- **🔊 Natural Text-to-Speech (TTS):** Spoken audio responses powered by `pyttsx3` with adjustable speech rate and volume.
- **⚡ Desktop Application Launcher:** Launch popular Windows applications (VS Code, Chrome, Spotify, Discord, MS Office suite, Terminal, Calculator, etc.) instantly.
- **🌐 Web Navigation & Price Checker:** Fast access to 80+ platforms (YouTube, GitHub, Google, ChatGPT, etc.) plus multi-store price comparisons (Amazon, Flipkart, Google Shopping).
- **📄 File & Scripting Operations:** Read files, create files, rewrite code, run Python/batch/PowerShell scripts, and browse directories directly.
- **🧠 Self-Learning Architecture:** Teach custom paths or application aliases right through the UI or voice commands—persistently saved in `commands.json`.
- **📦 Windows Executable Ready:** Configured with PyInstaller (`ARIA.spec`) for building a portable standalone `.exe`.

---

## 🚀 Quick Start

### Option 1: 1-Click Setup (Recommended for Windows)

Simply double-click or run:
```bat
run.bat
```
`run.bat` will automatically verify your Python installation, install required dependencies (`SpeechRecognition`, `pyttsx3`, `sounddevice`, `numpy`, `requests`, `pillow`), and launch GEMINI AI.

---

### Option 2: Manual Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DIV79/ai-modal.git
   cd ai-modal
   ```

2. **Create and activate a virtual environment (optional):**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch GEMINI AI:**
   ```bash
   python main.py
   ```

---

## 🔑 Setting up your Google Gemini API Key

1. Get a free API key at **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
2. Launch the app and click **⚙️ Settings** in the top bar.
3. Paste your API key into the Gemini API Key field.
4. Click **⚡ Test Connection** to verify your key.
5. Click **💾 Save Settings** — your key and preferred model are saved persistently!

*(You can also set the `GEMINI_API_KEY` environment variable on your system).*

---

## 🗣️ Example Commands

| Command | Action |
| :--- | :--- |
| `Why is the sky blue?` | Answers using Google Gemini generative AI |
| `Write a Python script to sort a dictionary` | Generates formatted Python code with explanations |
| `Explain quantum computing in simple terms` | Explains concepts with conversational voice & text |
| `open chrome` / `open spotify` | Launches the target application |
| `open youtube` / `go to github` | Opens website directly |
| `price of iphone 15` | Opens price searches on Amazon, Flipkart & Google Shopping |
| `read file main.py` | Reads and previews file contents |
| `create file hello.py with content print("hello")` | Creates a new file on disk |
| `run file script.py` | Executes Python or shell script and returns stdout |
| `what time is it` / `what date is it` | Tells current local time and date |
| `clear chat` | Clears Gemini conversational history memory |

---

## 📁 Project Structure

```text
ai-modal/
├── aria_icon.ico       # Application icon
├── ARIA.spec           # PyInstaller build specification
├── gemini_engine.py    # Google Gemini REST client, multi-turn chat & speech formatting
├── assistant.py        # Core AIAssistant logic, TTS, Speech & command router
├── commands.json       # App registry, settings, and memory
├── main.py             # Tkinter desktop GUI (Voice Mode, Chat Mode, Settings Modal)
├── requirements.txt    # Python dependencies
├── run.bat             # 1-click Windows launcher script
├── build_exe.bat       # Standalone .exe build script
└── README.md           # Documentation
```

---

## 🛠️ Building the Standalone `.exe`

To package GEMINI AI into a standalone Windows executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller ARIA.spec
```

The resulting executable will be generated inside the `dist/` directory.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.
