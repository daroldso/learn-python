from dataclasses import dataclass
from datetime import date


@dataclass
class Habit:
    id: int
    name: str
    archived: bool = False

    def __str__(self) -> str:
        status = "archived" if self.archived else "active"
        return f"{self.name} ({status})"


@dataclass(frozen=True)
class CheckIn:
    habit_id: int
    day: date
    note: str | None = None
