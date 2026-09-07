from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from habits.store import HabitNotFound, HabitStore


def test_check_in_two_habits() -> None:
    store = HabitStore()
    habit_1 = store.add_habit("run")
    habit_2 = store.add_habit("swimming")
    store.check_in(habit_1.id, datetime(2026, 9, 7, 8, 0, 0, tzinfo=UTC))
    store.check_in(habit_2.id, datetime(2026, 9, 10, 8, 0, 0, tzinfo=UTC))

    assert store.days_for(habit_1.id) == [date(2026, 9, 7)]
    assert store.days_for(habit_2.id) == [date(2026, 9, 10)]


def test_add_habit_defaults_to_utc() -> None:
    store = HabitStore()
    habit = store.add_habit("run")
    store.check_in(habit.id, datetime(2026, 9, 7, 23, 0, 0, tzinfo=UTC))
    assert store.days_for(habit.id) == [date(2026, 9, 7)]


def test_check_in_unknown_habit_raises() -> None:
    store = HabitStore()
    with pytest.raises(HabitNotFound):
        store.check_in(999, datetime(2026, 9, 7, 8, 0, 0, tzinfo=UTC))


def test_check_in_rejects_naive_datetime() -> None:
    store = HabitStore()
    habit = store.add_habit("run", "Asia/Tokyo")
    with pytest.raises(ValueError):
        store.check_in(habit.id, datetime(2026, 9, 7, 8, 0))


def test_habit_days_for() -> None:
    tzinfo = "Asia/Tokyo"
    store = HabitStore()
    habit = store.add_habit("run", tzinfo)
    store.check_in(habit.id, datetime(2026, 9, 7, 8, 0, 0, tzinfo=ZoneInfo(tzinfo)))
    store.check_in(habit.id, datetime(2026, 9, 6, 23, 0, 0, tzinfo=ZoneInfo("UTC")))
    days = store.days_for(habit.id)
    assert days == [date(2026, 9, 7), date(2026, 9, 7)]


def test_save_load(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "habits.json"
    store = HabitStore()
    habit_1 = store.add_habit("run", "Asia/Tokyo")
    habit_2 = store.add_habit("swimming")
    store.check_in(
        habit_1.id, datetime(2026, 9, 7, 23, 0, 0, tzinfo=UTC), "The run was great"
    )
    store.check_in(
        habit_2.id, datetime(2026, 9, 10, 23, 0, 0, tzinfo=UTC), "Love swimming"
    )

    store.save(path)
    loaded = HabitStore.load(path)

    assert loaded.days_for(habit_1.id) == [date(2026, 9, 8)]
    assert loaded.days_for(habit_2.id) == [date(2026, 9, 10)]
    assert [c.note for c in loaded.check_ins] == ["The run was great", "Love swimming"]


def test_save_load_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "habits.json"

    with pytest.raises(FileNotFoundError):
        HabitStore.load(path)
