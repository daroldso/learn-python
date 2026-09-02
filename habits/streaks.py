from datetime import timedelta  # stdlib — no install needed
from itertools import pairwise

# d = date(2026, 8, 24) # a calendar day. No time, no timezone.
# d + timedelta(days=1) # -> date(2026, 8, 25)
# date(2026, 8, 26) - d # -> timedelta(3);  .days gives 3

# # set — O(1) membership, and it deduplicates. `in` on a list is O(n).
# seen = {date(2026, 8, 24), date(2026, 8, 25)}
# date(2026, 8, 24) in seen   # -> True

# sorted([3, 1, 2])     # -> [1, 2, 3]  (returns a NEW list)

# 7 / 2# -> 3.5   float division
# 7 // 2       # -> 3     floor division  <- the JS `/` trap

def days_in_range(start, end):
    """Every date from start to end, inclusive."""
    out = []
    d = start
    while d <= end:
        out.append(d)
        d += timedelta(days=1)
    return out

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
    for paired_check_in in paired_check_ins:
        if paired_check_in[0] != paired_check_in[1] - timedelta(days=1):
            longest = max(longest, current)
            current = 1
        else:
            current += 1
    longest = max(longest, current)
    return longest

        
            
        