import json
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from habits.models import CheckIn, Habit


class HabitStore:
    habits: dict[int, Habit]
    check_ins: list[CheckIn]

    def __init__(self) -> None:
        self.habits = {}
        self.check_ins = []

    def add_habit(self, name: str, timezone: str = "UTC") -> Habit:
        latest_id = max(self.habits.keys(), default=0)
        habit = Habit(latest_id + 1, name, timezone=timezone)
        self.habits[habit.id] = habit
        return habit

    def get_habit(self, habit_id: int) -> Habit:
        try:
            return self.habits[habit_id]
        except KeyError:
            raise HabitNotFound(habit_id) from None

    def check_in(self, habit_id: int, at: datetime, note: str | None = None) -> CheckIn:
        self.get_habit(habit_id)
        check_in = CheckIn(habit_id, at, note)
        self.check_ins.append(check_in)
        return check_in

    def days_for(self, habit_id: int) -> list[date]:
        habit = self.get_habit(habit_id)
        return [
            check_in.at.astimezone(ZoneInfo(habit.timezone)).date()
            for check_in in self.check_ins
            if check_in.habit_id == habit_id
        ]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "habits": [asdict(h) for h in self.habits.values()],
            "check_ins": [
                {**asdict(check_in), "at": check_in.at.isoformat()}
                for check_in in self.check_ins
            ],
        }
        path.write_text(json.dumps(data))

    @classmethod
    def load(cls, path: Path) -> "HabitStore":
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist")

        store = cls()
        data = json.loads(path.read_text())
        store.habits = {
            h["id"]: Habit(
                id=h["id"],
                name=h["name"],
                archived=h["archived"],
                timezone=h["timezone"],
            )
            for h in data["habits"]
        }
        store.check_ins = [
            CheckIn(
                habit_id=c["habit_id"],
                at=datetime.fromisoformat(c["at"]),
                note=c["note"],
            )
            for c in data["check_ins"]
        ]
        return store


class HabitNotFound(Exception):
    def __init__(self, habit_id: int) -> None:
        super().__init__(f"No habit with id {habit_id}")
        self.habit_id = habit_id


if __name__ == "__main__":
    store = HabitStore()
    habit_1 = store.add_habit("run")
    habit_2 = store.add_habit("swimming")
    store.check_in(habit_1.id, datetime(2026, 9, 7, 8, 0, 0, tzinfo=UTC))
    store.check_in(habit_2.id, datetime(2026, 9, 10, 8, 0, 0, tzinfo=UTC))
    store.save(Path("data") / "habits.json")
    HabitStore.load(Path("data") / "habits.json")
