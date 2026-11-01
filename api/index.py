import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler
import requests

AVAILABLE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

DEFAULT_SYSTEM_INSTRUCTION = (
    "You are Gemini, an intelligent, helpful, articulate, and fast desktop AI assistant. "
    "You assist the user with answering questions, reasoning, coding, explanations, "
    "creative writing, math, and daily productivity. "
    "Provide well-structured answers using clean markdown formatting (bullet points, clear paragraphs, code blocks)."
)


class handler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-api-key")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/api", "/api/", "/api/health"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            data = {
                "status": "online",
                "service": "GEMINI AI (ARIA) Cloud API",
                "version": "1.0.0",
                "available_models": AVAILABLE_MODELS,
                "endpoints": {
                    "POST /api/chat": "Send messages to Gemini LLM",
                    "GET /api/models": "List available Gemini models",
                    "GET /api/health": "Healthcheck endpoint"
                }
            }
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))
            return

        elif path == "/api/models":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"models": AVAILABLE_MODELS}).encode("utf-8"))
            return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            
            try:
                payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
            except Exception:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON body"}).encode("utf-8"))
                return

            message = payload.get("message", "").strip()
            history = payload.get("history", [])
            model = payload.get("model", "gemini-2.5-flash")
            api_key = (
                payload.get("api_key")
                or self.headers.get("x-api-key")
                or os.environ.get("GEMINI_API_KEY", "")
            ).strip()

            if not api_key:
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "Missing Gemini API key. Provide it via 'api_key' in request body or set GEMINI_API_KEY in Vercel Environment Variables."
                }).encode("utf-8"))
                return

            if not message:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Field 'message' cannot be empty"}).encode("utf-8"))
                return

            # Prepare Gemini contents
            contents = []
            for item in history:
                contents.append({
                    "role": item.get("role", "user"),
                    "parts": [{"text": item.get("text", "")}]
                })
            contents.append({
                "role": "user",
                "parts": [{"text": message}]
            })

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            req_data = {
                "contents": contents,
                "systemInstruction": {
                    "parts": [{"text": DEFAULT_SYSTEM_INSTRUCTION}]
                },
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048,
                }
            }

            try:
                res = requests.post(url, json=req_data, timeout=30)
                if res.status_code == 200:
                    resp_json = res.json()
                    candidates = resp_json.get("candidates", [])
                    reply_text = ""
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        reply_text = "".join(p.get("text", "") for p in parts)

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "reply": reply_text,
                        "model": model,
                        "status": "success"
                    }).encode("utf-8"))
                    return
                else:
                    self.send_response(res.status_code)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors_headers()
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": "Gemini API error",
                        "status_code": res.status_code,
                        "detail": res.text
                    }).encode("utf-8"))
                    return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))
