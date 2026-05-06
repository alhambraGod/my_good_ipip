"""Centralised logging for MindPrism.

Layout (per spec):

    /var/MindPrism/<env>/logs/             current day's logs
                              app.log         backend (uvicorn + FastAPI + scoring + payment)
                              access.log      uvicorn access log
                              error.log       WARN+
                              history/        rotated archives, suffixed by date
                                  app.log.2026-05-06
                                  access.log.2026-05-06
                                  error.log.2026-05-06

Rotation: nightly at 00:00 server time. Each handler keeps **30 days** of
archives (configurable via env: ``LOG_RETENTION_DAYS``).

If the configured root path is not writable (e.g. local dev where the user
hasn't created /var/MindPrism), we fall back to ``./logs/<env>/`` under the
current working directory and emit a warning.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Final

DEFAULT_ROOT: Final[str] = "/var/MindPrism"
DEFAULT_RETENTION_DAYS: Final[int] = 30


def _is_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        probe.write_text("ok")
        probe.unlink()
        return True
    except OSError:
        return False


def resolve_log_dir(env: str) -> tuple[Path, Path]:
    """Return (current_dir, history_dir) for the given env.

    Honours these env variables:
      * ``LOG_ROOT``                — full root, e.g. ``/var/MindPrism``
      * ``LOG_FALLBACK_ROOT``       — fallback root under cwd if root unwritable

    If neither resolves, falls back to ``./logs/<env>/`` and warns.
    """
    root = Path(os.environ.get("LOG_ROOT", DEFAULT_ROOT)) / env
    if not _is_writable(root):
        fallback = Path(
            os.environ.get("LOG_FALLBACK_ROOT", "./logs"),
        ) / env
        fallback.mkdir(parents=True, exist_ok=True)
        sys.stderr.write(
            f"[logging_setup] {root} not writable, falling back to "
            f"{fallback.resolve()}\n",
        )
        root = fallback
    history = root / "history"
    history.mkdir(parents=True, exist_ok=True)
    return root, history


def _make_handler(
    file_path: Path,
    history_dir: Path,
    level: int,
    retention_days: int,
) -> logging.Handler:
    """Per-day rotating handler that moves old logs into ``history/``.

    `TimedRotatingFileHandler` rotates by renaming the active file with a
    ``.YYYY-MM-DD`` suffix. We override `rotation_filename` so the rotated
    name is always written to the ``history/`` folder rather than next to
    the live file (which keeps the live folder uncluttered).
    """
    handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(file_path),
        when="midnight",
        backupCount=retention_days,
        encoding="utf-8",
        utc=False,
    )
    handler.suffix = "%Y-%m-%d"
    base_name = file_path.name
    handler.rotation_filename = lambda default: str(  # type: ignore[assignment]
        history_dir / Path(default).name.replace(base_name + ".", base_name + ".")
    )
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ),
    )
    return handler


def setup_logging(
    env: str,
    *,
    level: int = logging.INFO,
    retention_days: int | None = None,
) -> dict[str, str]:
    """Configure the root + uvicorn loggers.

    Idempotent: re-applying replaces handlers, doesn't double them.
    Returns a dict describing where logs are landing (useful for the
    `/api/health` payload + the deploy-script banner).
    """
    if retention_days is None:
        retention_days = int(
            os.environ.get("LOG_RETENTION_DAYS", str(DEFAULT_RETENTION_DAYS))
        )

    current, history = resolve_log_dir(env)

    # Reset root + relevant uvicorn loggers
    for name in (None, "uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        logger = logging.getLogger(name) if name else logging.getLogger()
        for h in list(logger.handlers):
            logger.removeHandler(h)

    root = logging.getLogger()
    root.setLevel(level)

    # stderr — always (so docker logs / journalctl still see output)
    stream = logging.StreamHandler(sys.stderr)
    stream.setLevel(level)
    stream.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        ),
    )
    root.addHandler(stream)

    # File handlers
    app_h    = _make_handler(current / "app.log",    history, level,           retention_days)
    error_h  = _make_handler(current / "error.log",  history, logging.WARNING, retention_days)
    access_h = _make_handler(current / "access.log", history, logging.INFO,    retention_days)

    root.addHandler(app_h)
    root.addHandler(error_h)

    # uvicorn access log → access.log (separate handler, no propagate so we
    # don't duplicate request lines into app.log)
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = [access_h]
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False

    # uvicorn error log → propagate to root (so it lands in app.log + error.log)
    err_logger = logging.getLogger("uvicorn.error")
    err_logger.setLevel(logging.INFO)
    err_logger.propagate = True
    err_logger.handlers = []

    return {
        "env": env,
        "log_dir": str(current.resolve()),
        "history_dir": str(history.resolve()),
        "retention_days": str(retention_days),
    }
