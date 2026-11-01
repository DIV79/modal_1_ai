"""
Google Gemini AI Engine for ARIA / GEMINI AI Assistant.
Provides seamless integration with Google's Gemini models via official REST endpoints,
supporting multi-turn chat, system instructions, error handling, and connection testing.
Works with standard `requests` without requiring external heavy binaries.
"""

import json
import os
import re
import urllib.parse
from typing import Optional, List, Dict, Tuple, Any

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


DEFAULT_SYSTEM_INSTRUCTION = (
    "You are Gemini, an intelligent, helpful, articulate, and fast desktop AI voice and text assistant. "
    "You assist the user on their Windows PC with answering questions, reasoning, coding, explanations, "
    "creative writing, math, and daily productivity. "
    "Provide well-structured answers using clean markdown formatting (bullet points, clear paragraphs, code blocks). "
    "Keep answers informative yet concise so they are pleasant both to read and to listen to."
)

AVAILABLE_MODELS = [
    "gemini-3.8-flash",       # Latest (2026)
    "gemini-3.7-flash",       # Previous stable
    "gemini-3.6-flash",       # Stable fallback
    "gemini-3.5-flash",       # Reliable fallback
    "gemini-3.1-flash-lite",  # Lightweight option
    "gemini-flash-latest",    # Always-latest alias
]


class GeminiEngine:
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        self.model = model if model in AVAILABLE_MODELS else "gemini-3.8-flash"
        self.history: List[Dict[str, Any]] = []
        self.system_instruction = DEFAULT_SYSTEM_INSTRUCTION
        self.max_history_turns = 16  # Keep last 16 turns to avoid context overflow

    def set_api_key(self, api_key: str):
        self.api_key = (api_key or "").strip()

    def set_model(self, model: str):
        if model in AVAILABLE_MODELS:
            self.model = model

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) >= 10)

    def clear_history(self):
        self.history.clear()

    def test_connection(self, api_key: Optional[str] = None, model: Optional[str] = None) -> Tuple[bool, str]:
        """Test API key connection with a lightweight prompt."""
        key_to_test = (api_key if api_key is not None else self.api_key).strip()
        model_to_test = model or self.model or "gemini-2.5-flash"

        if not key_to_test:
            return False, "API key is empty. Please enter your Gemini API key."

        if not REQUESTS_AVAILABLE:
            return False, "Python 'requests' library is not installed."

        # Try user-selected model; if not found, try fallback models
        models_to_try = [model_to_test] + [m for m in AVAILABLE_MODELS if m != model_to_test]
        last_error = ""

        for candidate_model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidate_model}:generateContent?key={key_to_test}"
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": "Hello Gemini, respond with one word: Ready"}]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 10,
                    "temperature": 0.1
                }
            }

            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=12
                )

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            if candidate_model != model_to_test:
                                self.model = candidate_model
                            return True, f"Connection verified successfully! ({candidate_model})"
                    return True, f"Connection verified! ({candidate_model})"
                else:
                    err_json = {}
                    try:
                        err_json = response.json()
                    except Exception:
                        pass
                    msg = err_json.get("error", {}).get("message", f"HTTP {response.status_code}")
                    last_error = f"{candidate_model}: {msg}"
                    # If quota or auth error, don't bother trying other models
                    if response.status_code in (400, 401, 403):
                        return False, f"API Error ({response.status_code}): {msg}"

            except requests.RequestException as e:
                last_error = str(e)

        return False, f"Connection failed: {last_error}"

    def ask(self, prompt: str, keep_history: bool = True) -> Tuple[str, bool]:
        """
        Send a prompt to Google Gemini and return (response_text, success_flag).
        Maintains conversational history when keep_history is True.
        """
        prompt = prompt.strip()
        if not prompt:
            return "Please provide a query or question.", False

        if not self.is_configured():
            return (
                "🔑 **Google Gemini API Key Needed**\n\n"
                "To enable Gemini AI conversational intelligence, reasoning, and coding, "
                "please configure your free Gemini API key:\n\n"
                "1. Click the **⚙️ Settings** button at the top.\n"
                "2. Get a free API key at **https://aistudio.google.com/app/apikey**\n"
                "3. Paste your key and click **Save Settings**.\n\n"
                "*Local system commands (open apps, files, websites, time) are still active.*",
                False
            )

        if not REQUESTS_AVAILABLE:
            return "❌ Python 'requests' library is not available. Please install it using `pip install requests`.", False

        # Build contents with rolling history
        contents: List[Dict[str, Any]] = []
        if keep_history and self.history:
            # Append past turns
            contents.extend(self.history[-self.max_history_turns:])

        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })

        # Try current model, and fallback to 1.5-flash or 2.0-flash if current model is unavailable
        models_to_attempt = [self.model]
        for m in ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]:
            if m not in models_to_attempt:
                models_to_attempt.append(m)

        last_err = ""
        for current_model in models_to_attempt:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={self.api_key}"
            payload: Dict[str, Any] = {
                "contents": contents,
                "systemInstruction": {
                    "parts": [{"text": self.system_instruction}]
                },
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048,
                }
            }

            try:
                resp = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=45  # Longer timeout for overloaded servers
                )

                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        cand = candidates[0]
                        parts = cand.get("content", {}).get("parts", [])
                        if parts:
                            model_text = "".join(p.get("text", "") for p in parts).strip()
                            if model_text:
                                if keep_history:
                                    self.history.append({"role": "user", "parts": [{"text": prompt}]})
                                    self.history.append({"role": "model", "parts": [{"text": model_text}]})
                                    # Trim history
                                    if len(self.history) > self.max_history_turns * 2:
                                        self.history = self.history[-self.max_history_turns * 2:]
                                self.model = current_model
                                return model_text, True

                    return "I received an empty response from Gemini. Please try asking again.", False

                else:
                    err_info = {}
                    try:
                        err_info = resp.json()
                    except Exception:
                        pass
                    msg = err_info.get("error", {}).get("message", f"HTTP {resp.status_code}")
                    last_err = f"{current_model} error ({resp.status_code}): {msg}"

                    # If invalid key or quota exhausted, no point trying other models
                    if resp.status_code in (400, 401, 403):
                        return f"❌ Gemini API Error ({resp.status_code}):\n{msg}\n\nPlease check your key in Settings.", False

            except requests.Timeout:
                last_err = f"Gemini request timed out on {current_model}."
            except requests.RequestException as e:
                last_err = f"Network error communicating with Gemini: {e}"

        # All models failed or were overloaded
        if "high demand" in last_err.lower() or "overload" in last_err.lower() or "timed out" in last_err.lower() or "timeout" in last_err.lower():
            return (
                "⏳ **Google Gemini servers are currently overloaded** (high global demand).\n\n"
                "This is a temporary issue on Google's side. Please:\n"
                "• Wait 1-2 minutes and try again\n"
                "• Or ask a shorter/simpler question\n\n"
                "_Local commands (open apps, files, websites, time) still work normally._"
            ), False
        return f"❌ Could not reach Gemini:\n{last_err}", False


def clean_for_speech(text: str, max_chars: int = 240) -> str:
    """
    Produce a clean, spoken-friendly text summary from markdown/code formatted text.
    Removes code blocks, urls, and special formatting symbols.
    """
    if not text:
        return ""

    # Remove code blocks entirely for voice output
    t = re.sub(r"```.*?```", " Code snippet provided. ", text, flags=re.DOTALL)
    # Remove inline code `foo`
    t = re.sub(r"`([^`]+)`", r"\1", t)
    # Remove markdown headers and bullets
    t = re.sub(r"^#+\s*", "", t, flags=re.MULTILINE)
    t = re.sub(r"^\s*[\*\-\•]\s*", "", t, flags=re.MULTILINE)
    # Remove bold/italic markers
    t = re.sub(r"\*\*([^\*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^\*]+)\*", r"\1", t)
    t = re.sub(r"\__([^_]+)\__", r"\1", t)
    t = re.sub(r"\_([^_]+)\_", r"\1", t)
    # Remove URLs
    t = re.sub(r"https?://\S+", "", t)
    # Normalize whitespaces
    t = re.sub(r"\s+", " ", t).strip()

    if len(t) <= max_chars:
        return t

    # Try to cut off cleanly at sentence boundary within max_chars
    cut = t[:max_chars]
    last_period = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
    if last_period > 60:
        return cut[:last_period + 1].strip()

    return cut.rstrip() + "..."
