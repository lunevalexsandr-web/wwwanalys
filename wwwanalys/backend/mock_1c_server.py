"""Mock 1C server for WWWAnalys integration testing. Run: python mock_1c_server.py"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

INDICATORS = [
    {"id": "1", "name": "Экстрактивность", "unit": "%", "data_type": "number",
     "description": "Экстрактивность сусла", "category": "Варка", "is_required": True,
     "default_value": "11.5", "options": []},
    {"id": "2", "name": "Кислотность", "unit": "pH", "data_type": "number",
     "description": "Кислотность сусла", "category": "Варка", "is_required": True,
     "default_value": "5.5", "options": []},
    {"id": "3", "name": "Цветность", "unit": "EBC", "data_type": "number",
     "description": "Цвет пива", "category": "Варка", "is_required": False,
     "default_value": "", "options": []},
    {"id": "4", "name": "Сорт ячменя", "unit": "", "data_type": "select",
     "description": "Сорт ячменя", "category": "Сырьё", "is_required": False,
     "default_value": "", "options": ["Альфа", "Беты", "Гамма"]}
]

TEMPLATES = [{"id": "1", "name": "Варка сусла", "description": "Шаблон варки",
              "is_active": True, "indicators": [
                  {"indicator_id": 1, "min_value": 11.0, "max_value": 12.0, "sort_order": 0},
                  {"indicator_id": 2, "min_value": 5.2, "max_value": 5.8, "sort_order": 1}]}]

PLANS = [{"id": "1", "name": "План на 18.06.2026", "description": "План на день",
          "plan_date": "2026-06-18", "items": [
              {"template_id": 1, "batch_number": "П-001", "sort_order": 0}]}]


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path.endswith("/api/v1/health"):
            self._send(200, {"status": "ok", "message": "1C mock", "timestamp": "2026-01-01T00:00:00"})
        elif path.endswith("/api/v1/indicators"):
            self._send(200, INDICATORS)
        elif path.endswith("/api/v1/analysis-templates"):
            self._send(200, TEMPLATES)
        elif path.endswith("/api/v1/analysis-plans"):
            self._send(200, PLANS)
        else:
            self._send(404, {"error": "not found", "path": path})

    def log_message(self, fmt, *args):
        print(f"[mock-1c] {fmt % args}")


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8443), Handler).serve_forever()