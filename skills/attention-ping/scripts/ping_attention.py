#!/usr/bin/env python3
"""Send a deduplicated ntfy alert when an agent needs the user's attention."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request

CONFIG_PATH = Path.home() / ".config/ntfy/joi-alarms.env"
STATE_PATH = Path.home() / ".cache/agent-attention-ping/last.json"
DEFAULT_DEDUPE_SECONDS = 900
QUIET_START_HOUR = 23  # the user is asleep from 23:00 local...
QUIET_END_HOUR = 9     # ...until 09:00 local. Never deliver inside this window.


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RuntimeError(f"cannot read ntfy config at {path}: {exc}") from exc

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def quiet_hours_delivery(now: dt.datetime) -> dt.datetime | None:
    """Return the local datetime to defer delivery to, or None if it may send now.

    Anything landing between QUIET_START_HOUR and QUIET_END_HOUR is scheduled for
    QUIET_END_HOUR instead, so a blocked overnight agent never wakes the user.
    """
    if now.hour >= QUIET_START_HOUR:
        target = now + dt.timedelta(days=1)
    elif now.hour < QUIET_END_HOUR:
        target = now
    else:
        return None
    return target.replace(hour=QUIET_END_HOUR, minute=0, second=0, microsecond=0)


def fingerprint(title: str, message: str) -> str:
    return hashlib.sha256(f"{title}\0{message}".encode()).hexdigest()


def is_duplicate(digest: str, now: int, dedupe_seconds: int) -> bool:
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return state.get("fingerprint") == digest and now - int(state["time"]) < dedupe_seconds
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False


def save_state(digest: str, now: int, message_id: str) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(
        json.dumps({"fingerprint": digest, "time": now, "message_id": message_id}) + "\n",
        encoding="utf-8",
    )
    os.chmod(tmp, 0o600)
    tmp.replace(STATE_PATH)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dedupe-seconds", type=int, default=DEFAULT_DEDUPE_SECONDS)
    args = parser.parse_args()

    title = args.title.strip()
    message = args.message.strip()
    if not title or not message:
        parser.error("title and message must not be blank")
    if "\n" in title:
        parser.error("title must be one line")
    if len(title) > 120 or len(message) > 1000:
        parser.error("title/message too long; keep attention pings concise")
    if args.dedupe_seconds < 0:
        parser.error("dedupe-seconds must be non-negative")

    digest = fingerprint(title, message)
    now = int(time.time())
    if is_duplicate(digest, now, args.dedupe_seconds):
        print(json.dumps({"ok": True, "status": "suppressed", "reason": "duplicate"}))
        return 0

    deliver_at = quiet_hours_delivery(dt.datetime.now())

    if args.dry_run:
        print(json.dumps({
            "ok": True,
            "status": "dry-run",
            "title": title,
            "message": message,
            "deliver_at": deliver_at.isoformat() if deliver_at else "now",
        }))
        return 0

    try:
        config = parse_env(CONFIG_PATH)
        server = config.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
        topic = config["NTFY_TOPIC"]
        if not topic:
            raise KeyError("NTFY_TOPIC")
    except (RuntimeError, KeyError) as exc:
        print(json.dumps({"ok": False, "status": "config-error", "error": str(exc)}), file=sys.stderr)
        return 2

    headers = {"Title": title, "Priority": "max", "Tags": "alarm_clock"}
    if deliver_at is not None:
        headers["Delay"] = str(int(deliver_at.timestamp()))

    request = urllib.request.Request(
        f"{server}/{topic}",
        data=message.encode("utf-8"),
        method="POST",
        headers=headers,
    )
    token = config.get("NTFY_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(json.dumps({"ok": False, "status": "delivery-error", "error": str(exc)}), file=sys.stderr)
        return 3

    message_id = payload.get("id")
    if payload.get("event") != "message" or not message_id:
        print(json.dumps({"ok": False, "status": "verification-error"}), file=sys.stderr)
        return 4

    save_state(digest, now, str(message_id))
    if deliver_at is not None:
        print(json.dumps({
            "ok": True,
            "status": "scheduled",
            "id": message_id,
            "reason": "quiet-hours",
            "deliver_at": deliver_at.isoformat(),
        }))
        return 0
    print(json.dumps({"ok": True, "status": "sent", "id": message_id}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
