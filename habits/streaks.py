from datetime import date, timedelta  # stdlib — no install needed
from itertools import pairwise


def current_streak(check_ins, today):
    check_ins_set = set(check_ins)
    streak = 0
    current_date = today
    while current_date in check_ins_set:
        streak += 1
        current_date -= timedelta(days=1)

    return streak


def longest_streak(check_ins):
    if not check_ins:
        return 0
    longest = 0
    current = 1
    paired_check_ins = pairwise(sorted(set(check_ins)))
    for prev, day in paired_check_ins:
        if prev != day - timedelta(days=1):
            longest = max(longest, current)
            current = 1
        else:
            current += 1
    longest = max(longest, current)
    return longest


def completion_rate(check_ins, start, end):
    if start > end:
        return 0.0
    days_completed = 0
    for check_in in set(check_ins):
        if start <= check_in <= end:
            days_completed += 1
    return days_completed / ((end - start).days + 1)


if __name__ == "__main__":
    print(completion_rate([], date(2026, 8, 1), date(2026, 8, 7)))
