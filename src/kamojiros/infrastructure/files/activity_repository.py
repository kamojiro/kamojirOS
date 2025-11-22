"""Activity Repository implementation."""

import json
from datetime import datetime  # noqa: TC003
from pathlib import Path

from kamojiros.models import Activity


class ActivityRepository:
    """Repository for accessing Activity data."""

    def __init__(self, data_dir: Path = Path("data")) -> None:
        """Initialize ActivityRepository."""
        self.data_dir = data_dir
        self.file_path = data_dir / "activities.jsonl"

    def get_activities(self, start: datetime, end: datetime) -> list[Activity]:
        """Get activities within the specified time range."""
        if not self.file_path.exists():
            return []

        activities: list[Activity] = []
        with self.file_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    activity = Activity.model_validate(data)

                    # Filter by time range
                    # Ensure activity.created_at is timezone-aware if start/end are
                    if start <= activity.created_at <= end:
                        activities.append(activity)
                except (json.JSONDecodeError, ValueError):
                    # Skip invalid lines
                    continue

        return activities
