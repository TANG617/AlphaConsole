from __future__ import annotations

from datetime import datetime


def now_local() -> datetime:
    return datetime.now().astimezone()


def parse_user_datetime(raw: str) -> datetime:
    value = raw.strip()
    if not value:
        raise ValueError("datetime is required")
    candidates = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
    )

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        parsed = None

    if parsed is None:
        for fmt in candidates:
            try:
                parsed = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue

    if parsed is None:
        raise ValueError(
            "Unsupported datetime format. Use ISO 8601 or `YYYY-MM-DD HH:MM[:SS]`."
        )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=now_local().tzinfo)
    return parsed.astimezone()


def format_local(dt: datetime) -> str:
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
