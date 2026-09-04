from collections.abc import Iterable
from datetime import date, timedelta  # stdlib — no install needed
from itertools import pairwise


def current_streak(check_ins: Iterable[date], today: date) -> int:
    check_ins_set = set(check_ins)
    streak = 0
    current_date = today
    while current_date in check_ins_set:
        streak += 1
        current_date -= timedelta(days=1)

    return streak


def longest_streak(check_ins: Iterable[date]) -> int:
    sorted_check_ins = sorted(set(check_ins))
    if not sorted_check_ins:
        return 0
    longest = 0
    current = 1
    paired_check_ins = pairwise(sorted_check_ins)
    for prev, day in paired_check_ins:
        if prev != day - timedelta(days=1):
            longest = max(longest, current)
            current = 1
        else:
            current += 1
    longest = max(longest, current)
    return longest


def completion_rate(check_ins: Iterable[date], start: date, end: date) -> float:
    if start > end:
        return 0.0
    days_completed = 0
    for check_in in set(check_ins):
        if start <= check_in <= end:
            days_completed += 1
    return days_completed / ((end - start).days + 1)


if __name__ == "__main__":
    print(current_streak([date(2026, 8, 1), date(2026, 8, 2)], date(2026, 8, 2)))
    print(
        longest_streak(
            [
                date(2026, 8, 1),
                date(2026, 8, 2),
                date(2026, 8, 3),
                date(2026, 8, 7),
                date(2026, 8, 10),
                date(2026, 9, 12),
            ]
        )
    )
    print(completion_rate([], date(2026, 8, 1), date(2026, 8, 7)))
