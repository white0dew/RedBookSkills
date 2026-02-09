"""Single-instance lock helpers for publish scripts."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any


class SingleInstanceError(RuntimeError):
    """Raised when another publish process is already running."""


def _lock_path(lock_name: str) -> str:
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in lock_name)
    return os.path.join(tempfile.gettempdir(), f"{safe_name}.lock")


def _pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _read_lock_data(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _write_lock_data(path: str, payload: dict[str, Any]) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, ensure_ascii=False)


def _cleanup_stale_lock(path: str) -> tuple[bool, dict[str, Any]]:
    lock_data = _read_lock_data(path)
    pid = lock_data.get("pid")

    if isinstance(pid, int) and _pid_running(pid):
        return False, lock_data

    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError:
        return False, lock_data

    return True, lock_data


def _format_conflict_message(path: str, lock_data: dict[str, Any]) -> str:
    pid = lock_data.get("pid")
    started_at = lock_data.get("started_at")

    if isinstance(pid, int):
        msg = f"Another publish process is running (pid={pid})"
        if isinstance(started_at, str) and started_at:
            msg += f", started at {started_at}"
        return msg + ". Please wait or terminate it before retrying."

    return f"Another publish process is running (lock: {path}). Please wait before retrying."


@contextmanager
def single_instance(lock_name: str = "post_to_xhs_publish"):
    """Acquire a process-wide lock to prevent concurrent publish runs."""
    path = _lock_path(lock_name)
    token = uuid.uuid4().hex

    payload = {
        "pid": os.getpid(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "argv": sys.argv,
        "cwd": os.getcwd(),
        "token": token,
    }

    acquired = False
    for attempt in range(2):
        try:
            _write_lock_data(path, payload)
            acquired = True
            break
        except FileExistsError:
            removed, lock_data = _cleanup_stale_lock(path)
            if removed and attempt == 0:
                continue
            raise SingleInstanceError(_format_conflict_message(path, lock_data))

    if not acquired:
        raise SingleInstanceError(f"Could not acquire lock: {path}")

    try:
        yield
    finally:
        try:
            current = _read_lock_data(path)
            if current.get("token") == token:
                os.remove(path)
        except FileNotFoundError:
            pass
        except OSError:
            pass
