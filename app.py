"""A small task service: the demo application the AI software factory builds and verifies.

HTTP shape per the factory's runtime contract:
  GET  /health            -> 200 "ok"
  GET  /identity          -> the FACTORY_RUNTIME_CANDIDATE string when set, else "dev"
  GET  /tasks             -> {"tasks": [...], "open": n}
  POST /tasks             -> {"title": "..."} creates an open task
  POST /tasks/<id>/done   -> marks it done
  POST /tasks/<id>/rename -> {"title": "..."} renames it
  DELETE /tasks/<id>      -> removes it
State is SQLite at APP_DB (the runtime host points it at fresh per-attempt state).
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DB_PATH = Path(os.environ.get("APP_DB")
               or (Path(os.environ.get("FACTORY_RUNTIME_STATE") or Path.cwd()) / "app.db"))
PORT = int(os.environ.get("FACTORY_RUNTIME_PORT") or 8420)

DONE = re.compile(r"^/tasks/(\d+)/done$")
RENAME = re.compile(r"^/tasks/(\d+)/rename$")
TASK = re.compile(r"^/tasks/(\d+)$")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("create table if not exists tasks ("
               "id integer primary key autoincrement, "
               "title text not null, "
               "done integer not null default 0)")
    return db


def row(task) -> dict:
    return {"id": task[0], "title": task[1], "done": bool(task[2])}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
            return data if isinstance(data, dict) else {}
        except ValueError:
            return {}

    def do_GET(self):
        if self.path == "/health":
            self.reply(200, {"status": "ok"})
        elif self.path == "/identity":
            self.reply(200, os.environ.get("FACTORY_RUNTIME_CANDIDATE") or "dev")
        elif self.path == "/tasks":
            db = connect()
            tasks = [row(t) for t in db.execute("select id, title, done from tasks order by id")]
            db.close()
            self.reply(200, {"tasks": tasks, "open": sum(1 for t in tasks if not t["done"])})
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self):
        title = self.read_json().get("title")
        if self.path == "/tasks":
            if not isinstance(title, str) or not title.strip():
                return self.reply(400, {"error": "title required"})
            db = connect()
            cursor = db.execute("insert into tasks (title) values (?)", (title.strip(),))
            db.commit()
            task = db.execute("select id, title, done from tasks where id = ?",
                              (cursor.lastrowid,)).fetchone()
            db.close()
            return self.reply(201, row(task))
        done = DONE.match(self.path)
        if done:
            db = connect()
            changed = db.execute("update tasks set done = 1 where id = ?",
                                 (int(done[1]),)).rowcount
            db.commit()
            db.close()
            return self.reply(200, {"updated": changed}) if changed else self.reply(404, {"error": "no such task"})
        rename = RENAME.match(self.path)
        if rename:
            if not isinstance(title, str) or not title.strip():
                return self.reply(400, {"error": "title required"})
            db = connect()
            changed = db.execute("update tasks set title = ? where id = ?",
                                 (title.strip(), int(rename[1]))).rowcount
            db.commit()
            db.close()
            return self.reply(200, {"updated": changed}) if changed else self.reply(404, {"error": "no such task"})
        self.reply(404, {"error": "not found"})

    def do_DELETE(self):
        task = TASK.match(self.path)
        if not task:
            return self.reply(404, {"error": "not found"})
        db = connect()
        changed = db.execute("delete from tasks where id = ?", (int(task[1]),)).rowcount
        db.commit()
        db.close()
        self.reply(200, {"deleted": changed}) if changed else self.reply(404, {"error": "no such task"})


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
