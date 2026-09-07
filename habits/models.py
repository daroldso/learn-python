from dataclasses import dataclass
from datetime import datetime


@dataclass
class Habit:
    id: int
    name: str
    archived: bool = False
    timezone: str = "UTC"

    def __str__(self) -> str:
        status = "archived" if self.archived else "active"
        return f"{self.name} ({status})"


@dataclass(frozen=True)
class CheckIn:
    habit_id: int
    at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        if self.at.tzinfo is None:
            raise ValueError("at must be timezone-aware")
