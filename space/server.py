"""Static file server for the Workshop Finder HF Space.

Serves the prebuilt Vite bundle from /app/dist on port 7860, and exposes a
POST /refresh endpoint that re-runs the scraping pipeline in a background
thread so the dataset stays current without a separate CI runner. A daily
background refresh runs automatically.
"""

from __future__ import annotations

import http.server
import os
import socketserver
import subprocess
import threading
import time
from pathlib import Path

DIST = Path(os.environ.get("WF_DIST", "/app/dist"))
PORT = int(os.environ.get("PORT", "7860"))
REFRESH_SCRIPT = Path(os.environ.get("WF_REFRESH_SCRIPT", "/app/space/refresh.sh"))
REFRESH_INTERVAL_S = int(os.environ.get("WF_REFRESH_INTERVAL_H", "24")) * 3600

_lock = threading.Lock()
_refresh_running = False


def run_refresh() -> tuple[bool, str]:
    global _refresh_running
    with _lock:
        if _refresh_running:
            return False, "refresh already running"
        _refresh_running = True
    try:
        out = subprocess.run(
            ["bash", str(REFRESH_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60 * 30,
        )
        ok = out.returncode == 0
        msg = (out.stdout + out.stderr).strip() or ("ok" if ok else "failed")
        return ok, msg
    finally:
        with _lock:
            _refresh_running = False


def _scheduler() -> None:
    # stagger the first automatic refresh so the Space boots serving baked data
    time.sleep(REFRESH_INTERVAL_S)
    while True:
        ok, msg = run_refresh()
        print(f"scheduled refresh: {'ok' if ok else 'fail'} — {msg[:200]}", flush=True)
        time.sleep(REFRESH_INTERVAL_S)


threading.Thread(target=_scheduler, daemon=True).start()


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DIST), **kw)

    def do_POST(self):
        if self.path.rstrip("/") == "/refresh":
            ok, msg = run_refresh()
            body = (msg + "\n").encode()
            self.send_response(200 if ok else 500)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    os.chdir(DIST)
    print(f"serving {DIST} on :{PORT}", flush=True)
    ThreadingServer(("0.0.0.0", PORT), Handler).serve_forever()
