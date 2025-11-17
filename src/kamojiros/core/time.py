"""time モジュール."""

from datetime import datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


def now_jst() -> datetime:
    """日本標準時の現在時刻を取得する."""
    return datetime.now(JST)
