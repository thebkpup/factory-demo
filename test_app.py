"""End-to-end tests over a real server socket, including persistence across a restart."""
import json
import os
import tempfile
import threading
import unittest
import urllib.request
from http.server import HTTPServer
from pathlib import Path
from urllib.error import HTTPError

import app


class Server:
    def __init__(self, db_path: Path):
        os.environ["APP_DB"] = str(db_path)
        app.DB_PATH = db_path
        self.httpd = HTTPServer(("127.0.0.1", 0), app.Handler)
        self.port = self.httpd.server_port
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    def request(self, method: str, path: str, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}",
                                     data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as response:
                body = response.read().decode()
                return response.status, json.loads(body) if body else None
        except HTTPError as error:
            body = error.read().decode()
            return error.code, json.loads(body) if body else None


class TaskServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="task service test ")
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "app.db"

    def test_health_and_identity(self):
        with Server(self.db) as server:
            status, body = server.request("GET", "/health")
            self.assertEqual((status, body), (200, {"status": "ok"}))
            status, body = server.request("GET", "/identity")
            self.assertEqual((status, body), (200, "dev"))

    def test_create_list_complete_rename_delete(self):
        with Server(self.db) as server:
            self.assertEqual(server.request("POST", "/tasks", {"title": "refill the kalimba humidifier"})[0], 201)
            status, board = server.request("GET", "/tasks")
            self.assertEqual(status, 200)
            self.assertEqual(len(board["tasks"]), 1)
            self.assertEqual(board["open"], 1)
            self.assertFalse(board["tasks"][0]["done"])
            self.assertEqual(server.request("POST", "/tasks/1/done")[0], 200)
            _, board = server.request("GET", "/tasks")
            self.assertTrue(board["tasks"][0]["done"])
            self.assertEqual(board["open"], 0)
            self.assertEqual(server.request("POST", "/tasks/1/rename", {"title": "renamed"})[0], 200)
            _, board = server.request("GET", "/tasks")
            self.assertEqual(board["tasks"][0]["title"], "renamed")
            self.assertEqual(server.request("DELETE", "/tasks/1")[0], 200)
            _, board = server.request("GET", "/tasks")
            self.assertEqual((len(board["tasks"]), board["open"]), (0, 0))

    def test_empty_and_blank_titles_refused(self):
        with Server(self.db) as server:
            self.assertEqual(server.request("POST", "/tasks", {"title": "  "})[0], 400)
            self.assertEqual(server.request("POST", "/tasks", {})[0], 400)

    def test_state_survives_a_restart(self):
        with Server(self.db) as server:
            server.request("POST", "/tasks", {"title": "quarry-lantern"})
            server.request("POST", "/tasks", {"title": "sable-ferry"})
            server.request("POST", "/tasks/2/done")
        with Server(self.db) as restarted:
            _, board = restarted.request("GET", "/tasks")
            titles = [task["title"] for task in board["tasks"]]
            self.assertEqual(titles, ["quarry-lantern", "sable-ferry"])
            self.assertEqual(board["open"], 1)
            self.assertTrue(board["tasks"][1]["done"])

    def test_unknown_task_and_route(self):
        with Server(self.db) as server:
            self.assertEqual(server.request("POST", "/tasks/99/done")[0], 404)
            self.assertEqual(server.request("GET", "/nope")[0], 404)


if __name__ == "__main__":
    unittest.main()
