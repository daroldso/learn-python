from collections.abc import Iterable
from datetime import date

import pytest

from habits.streaks import completion_rate, current_streak, longest_streak


@pytest.mark.parametrize(
    "check_ins,today,expected",
    [
        ([date(2026, 9, 4)], date(2026, 9, 4), 1),
        ([date(2026, 9, 2), date(2026, 9, 3), date(2026, 9, 4)], date(2026, 9, 4), 3),
        ([date(2026, 9, 2), date(2026, 9, 4)], date(2026, 9, 4), 1),
        ([date(2026, 9, 4)], date(2026, 9, 6), 0),
        ([], date(2026, 9, 2), 0),
        ([date(2026, 9, 3), date(2026, 9, 3), date(2026, 9, 4)], date(2026, 9, 4), 2),
        ([date(2026, 9, 4), date(2026, 9, 3), date(2026, 9, 2)], date(2026, 9, 4), 3),
        ([date(2026, 9, 5), date(2026, 9, 6)], date(2026, 9, 4), 0),
    ],
)
def test_current_streaks(check_ins: Iterable[date], today: date, expected: int) -> None:
    assert current_streak(check_ins, today) == expected


@pytest.mark.parametrize(
    "check_ins,expected",
    [
        ([], 0),
        ((), 0),
        ([date(2026, 9, 5)], 1),
        ([date(2026, 9, 5), date(2026, 9, 8)], 1),
        (
            [
                date(2026, 9, 5),
                date(2026, 9, 6),
                date(2026, 9, 7),
                date(2026, 9, 10),
                date(2026, 9, 12),
            ],
            3,
        ),
        (
            [
                date(2026, 9, 5),
                date(2026, 9, 5),
                date(2026, 9, 5),
                date(2026, 9, 6),
                date(2026, 9, 12),
            ],
            2,
        ),
        (
            [
                date(2026, 9, 6),
                date(2026, 9, 8),
                date(2026, 9, 7),
                date(2026, 9, 10),
                date(2026, 9, 5),
            ],
            4,
        ),
    ],
)
def test_longest_streak(check_ins: Iterable[date], expected: int) -> None:
    assert longest_streak(check_ins) == expected


def test_longest_streak_empty_generator() -> None:
    days: list[date] = []
    assert longest_streak(d for d in days) == 0


@pytest.mark.parametrize(
    "check_ins,start,end,expected",
    [
        ([], date(2026, 9, 5), date(2026, 9, 10), 0),
        (
            [
                date(2026, 9, 5),
                date(2026, 9, 6),
                date(2026, 9, 7),
                date(2026, 9, 8),
                date(2026, 9, 9),
                date(2026, 9, 10),
            ],
            date(2026, 9, 5),
            date(2026, 9, 10),
            1,
        ),
        ([date(2026, 9, 5)], date(2026, 9, 5), date(2026, 9, 5), 1),
        (
            [date(2026, 9, 5), date(2026, 9, 18), date(2026, 9, 20)],
            date(2026, 9, 5),
            date(2026, 9, 9),
            0.2,
        ),
        (
            [date(2026, 9, 5), date(2026, 9, 5), date(2026, 9, 7), date(2026, 9, 8)],
            date(2026, 9, 5),
            date(2026, 9, 10),
            0.5,
        ),
        (
            [date(2026, 9, 9), date(2026, 9, 8), date(2026, 9, 7)],
            date(2026, 9, 5),
            date(2026, 9, 10),
            0.5,
        ),
        (
            [date(2026, 9, 7), date(2026, 9, 8)],
            date(2026, 9, 6),
            date(2026, 9, 5),
            0,
        ),
        (
            [date(2026, 9, 7), date(2026, 9, 8)],
            date(2026, 9, 10),
            date(2026, 9, 5),
            0,
        ),
        (
            [date(2026, 9, 5), date(2026, 9, 6)],
            date(2026, 9, 5),
            date(2026, 9, 10),
            1 / 3,
        ),
    ],
)
def test_completion_rate(
    check_ins: Iterable[date], start: date, end: date, expected: float
) -> None:
    assert completion_rate(check_ins, start, end) == pytest.approx(expected)
