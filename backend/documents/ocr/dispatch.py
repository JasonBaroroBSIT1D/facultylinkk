"""Optional inline OCR dispatch for development (production should use flask ocr-worker)."""

from __future__ import annotations

import os
import threading

from flask import Flask


def maybe_dispatch_inline_worker(app: Flask) -> None:
    if not app.config.get("OCR_INLINE_AFTER_UPLOAD"):
        return
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    def _run() -> None:
        with app.app_context():
            from documents.ocr.queue import process_pending_jobs

            process_pending_jobs(limit=5)

    threading.Thread(target=_run, daemon=True, name="facultylink-ocr-inline").start()
