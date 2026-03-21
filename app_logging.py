"""
Lightweight structured logging for runtime diagnostics.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from runtime_paths import ensure_runtime_dirs, get_logs_dir


_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    _standard_fields = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self._standard_fields and not key.startswith("_")
        }
        if extras:
            payload["extra"] = extras
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> logging.Logger:
    global _CONFIGURED
    ensure_runtime_dirs()

    if not _CONFIGURED:
        log_file = get_logs_dir() / "app.log"
        handlers = [
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ]
        formatter = JsonFormatter()
        for handler in handlers:
            handler.setFormatter(formatter)

        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.INFO)
        for handler in handlers:
            root.addHandler(handler)

        _CONFIGURED = True

    return logging.getLogger("hand_control")
