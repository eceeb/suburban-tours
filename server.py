#!/usr/bin/env python3
"""Kleiner lokaler Server für Suburban Tours.

Serviert die statische App UND speichert Favoriten + Fotos als Dateien unter data/
→ browser-unabhängig (jeder Browser auf localhost:8777 sieht dasselbe), und die
Fotos liegen echt im Projektordner statt nur in der Browser-DB.

API:
  GET    /api/favorites            -> JSON-Array
  PUT    /api/favorites            -> Body JSON-Array, überschreibt
  GET    /api/photos              -> Metadaten-Array (ohne Bilddaten)
  POST   /api/photos              -> Body JSON {data:"data:image/jpeg;base64,…", …meta} -> {id}
  GET    /api/photos/<id>.jpg     -> Bilddatei
  DELETE /api/photos/<id>         -> löscht Bild + Metadaten
"""
import base64
import json
import os
import re
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PHOTOS = os.path.join(DATA, "photos")
FAV_FILE = os.path.join(DATA, "favorites.json")
INDEX_FILE = os.path.join(PHOTOS, "index.json")
_lock = threading.Lock()


def _ensure():
    os.makedirs(PHOTOS, exist_ok=True)


def _read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def log_message(self, *a):
        pass  # ruhig halten

    def _send(self, code, body=b"", ctype="application/json"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    # ---- GET ----
    def do_GET(self):
        p = self.path.split("?", 1)[0]
        if p == "/api/favorites":
            return self._send(200, json.dumps(_read_json(FAV_FILE, [])))
        if p == "/api/photos":
            return self._send(200, json.dumps(_read_json(INDEX_FILE, [])))
        m = re.fullmatch(r"/api/photos/(\d+)\.jpg", p)
        if m:
            fp = os.path.join(PHOTOS, m.group(1) + ".jpg")
            if not os.path.exists(fp):
                return self._send(404, "{}")
            with open(fp, "rb") as f:
                return self._send(200, f.read(), "image/jpeg")
        return super().do_GET()  # statische Dateien (streetview.html …)

    # ---- PUT ----
    def do_PUT(self):
        if self.path.split("?", 1)[0] == "/api/favorites":
            try:
                favs = json.loads(self._body() or b"[]")
                with _lock:
                    _ensure(); _write_json(FAV_FILE, favs)
                return self._send(200, json.dumps({"ok": True, "n": len(favs)}))
            except Exception as e:
                return self._send(400, json.dumps({"error": str(e)}))
        return self._send(404, "{}")

    # ---- POST ----
    def do_POST(self):
        if self.path.split("?", 1)[0] == "/api/photos":
            try:
                rec = json.loads(self._body() or b"{}")
                data = rec.pop("data", "")
                b64 = data.split(",", 1)[1] if "," in data else data
                raw = base64.b64decode(b64)
                with _lock:
                    _ensure()
                    idx = _read_json(INDEX_FILE, [])
                    nid = (max([x.get("id", 0) for x in idx], default=0) + 1)
                    with open(os.path.join(PHOTOS, f"{nid}.jpg"), "wb") as f:
                        f.write(raw)
                    rec["id"] = nid
                    idx.append(rec)
                    _write_json(INDEX_FILE, idx)
                return self._send(200, json.dumps({"id": nid}))
            except Exception as e:
                return self._send(400, json.dumps({"error": str(e)}))
        return self._send(404, "{}")

    # ---- DELETE ----
    def do_DELETE(self):
        m = re.fullmatch(r"/api/photos/(\d+)", self.path.split("?", 1)[0])
        if m:
            nid = int(m.group(1))
            with _lock:
                idx = [x for x in _read_json(INDEX_FILE, []) if x.get("id") != nid]
                _write_json(INDEX_FILE, idx)
            try:
                os.remove(os.path.join(PHOTOS, f"{nid}.jpg"))
            except OSError:
                pass
            return self._send(200, json.dumps({"ok": True}))
        return self._send(404, "{}")


if __name__ == "__main__":
    _ensure()
    print("Suburban Tours server auf http://localhost:8777  (Daten in ./data)")
    ThreadingHTTPServer(("", 8777), Handler).serve_forever()
