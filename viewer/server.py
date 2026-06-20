#!/usr/bin/env python3
"""Lightweight STL viewer server for telem-enclosure CAD exports."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
EXPORTS = ROOT / "exports"

# Only allow saving under exports/
WRITABLE_ROOT = EXPORTS.resolve()


def _safe_export_path(rel: str) -> Path:
    rel = unquote(rel).lstrip("/")
    path = (EXPORTS / rel).resolve()
    if not str(path).startswith(str(EXPORTS.resolve())):
        raise ValueError("path outside exports")
    if path.suffix.lower() not in {".stl"}:
        raise ValueError("only .stl save supported")
    return path


def _list_models() -> list[dict]:
    models: list[dict] = []
    if not EXPORTS.is_dir():
        return models
    for path in sorted(EXPORTS.rglob("*.stl")):
        rel = path.relative_to(EXPORTS).as_posix()
        models.append(
            {
                "path": rel,
                "name": path.name,
                "version": path.parts[0] if path.parts else "",
                "size": path.stat().st_size,
                "mtime": path.stat().st_mtime,
            }
        )
    return models


class ViewerHandler(BaseHTTPRequestHandler):
    server_version = "telem-viewer/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[viewer] {self.address_string()} {fmt % args}")

    def _send_json(self, data: object, status: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(
        self, data: bytes, content_type: str, status: int = 200, download_name: str | None = None
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        if download_name:
            self.send_header("Content-Disposition", f'inline; filename="{download_name}"')
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/files":
            self._send_json({"files": _list_models()})
            return

        if path == "/api/mtime":
            qs = parse_qs(parsed.query)
            rel = qs.get("file", [""])[0]
            try:
                model = _safe_export_path(rel)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
                return
            if not model.is_file():
                self._send_json({"error": "not found"}, 404)
                return
            st = model.stat()
            self._send_json({"file": rel, "mtime": st.st_mtime, "size": st.st_size})
            return

        if path.startswith("/api/model/"):
            rel = unquote(path[len("/api/model/") :])
            try:
                model = _safe_export_path(rel)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
                return
            if not model.is_file():
                self._send_json({"error": "not found"}, 404)
                return
            data = model.read_bytes()
            self._send_bytes(data, "model/stl", download_name=model.name)
            return

        # Static files
        rel = path.lstrip("/") or "index.html"
        static_path = (STATIC / rel).resolve()
        if not str(static_path).startswith(str(STATIC.resolve())) or not static_path.is_file():
            self._send_json({"error": "not found"}, 404)
            return
        data = static_path.read_bytes()
        ctype = mimetypes.guess_type(static_path.name)[0] or "application/octet-stream"
        self._send_bytes(data, ctype)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/save":
            self._send_json({"error": "not found"}, 404)
            return

        qs = parse_qs(parsed.query)
        rel = qs.get("file", [""])[0]
        try:
            target = _safe_export_path(rel)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, 400)
            return

        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length)
        if not data:
            self._send_json({"error": "empty body"}, 400)
            return

        target.parent.mkdir(parents=True, exist_ok=True)
        backup = target.with_suffix(target.suffix + ".bak")
        if target.is_file():
            target.replace(backup)
        target.write_bytes(data)
        st = target.stat()
        self._send_json(
            {
                "ok": True,
                "file": rel,
                "size": st.st_size,
                "mtime": st.st_mtime,
                "backup": backup.relative_to(EXPORTS).as_posix() if backup.is_file() else None,
            }
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Telem enclosure STL web viewer")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    os.chdir(STATIC)
    httpd = ThreadingHTTPServer((args.host, args.port), ViewerHandler)
    print(f"Viewer running at http://{args.host}:{args.port}")
    print(f"Exports root: {EXPORTS}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
