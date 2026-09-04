# Hard-won lessons

> The mistakes I actually made, and what I now know. The reread-me file.
> Numbered in the order I hit them, across all phases.

**1. A print is not a test.**
`completion_rate` printed plausible output while returning the wrong number 5 times out of 6.
Printing hid it because a `print` shows what *I chose to display* — and I'd mislabelled the
denominator as `result`, so the number on screen wasn't even the return value. The `__main__`
block called the function and discarded what came back. An `assert` compares **actual against
expected**, can't be mislabelled into looking right, and runs unattended every time.
*This is the entire argument for pytest in Phase 3.*

**2. `while` loops: I own the advance step.**
`current_date = today - timedelta(days=1)` recomputed the same day forever instead of stepping
from `current_date`. It **hung** rather than returning a wrong answer, because the condition
depended on state that stopped changing. A hang is worse than a wrong answer: no traceback, no
output, a pinned CPU — and in a web handler (Phase 4) it takes down the worker, not just the
request. A `for` loop can't fail this way: it drains a finite iterator, so termination is
guaranteed by the iterator protocol rather than by my code. **Prefer `for`; when `while` is
genuinely needed, check that the loop variable actually advances.**

**3. Dead code still executes.**
A leftover debug `print` — diagnosing a bug I'd *already fixed* — crashed a correct function
with `ZeroDivisionError`, because it still had the old buggy expression and a single-day range
made the divisor 0. **Code isn't dead until it's deleted. Remove the scaffolding as part of
fixing the bug, not afterwards.**

**4. Duplicated expressions drift.**
I fixed the precedence bug in the `return` but not in the `print` above it, because the same
formula existed twice. The fix that makes this impossible: **compute once, bind to a name, use
the name.** `denominator = (end - start).days + 1` — then there's only one thing to get right
and the two uses can't disagree.

**5. Operator precedence.**
`days_completed / (end - start).days + 1` parses as `(days_completed / (end - start).days) + 1`
— `/` binds tighter than `+`. It *read* as correct because I'd been thinking of
`(end - start).days + 1` as a single unit ("the number of days"). **When an expression is a
concept in my head, give it a name in the code** — that's lesson 4 again, from the other side.

**6. Passing cases can hide two bugs.**
My `gap of one day` case passed while `current_streak` was badly broken — an off-by-one and a
missing consecutiveness check cancelled out. **One passing example proves nothing.** Cases need
to isolate each dimension: empty, single, boundary, and specifically an input where the two
suspected bugs would disagree.

**7. Off-by-one: fenceposts.**
**(mine, sharpened)** `(end - start).days` is the *gap* between two dates — the number of
intervals — and it excludes one endpoint. An inclusive day count needs `+ 1`. Six fenceposts,
seven panels. Aug 1 → Aug 7 is 7 days, not 6.

**8. Bare annotations in a plain class create nothing.**

```python
class HabitStore:
    habits: dict[int, Habit]      # declares a TYPE. Allocates NO attribute.
```

`HabitStore().habits` → `AttributeError`. It reads exactly like a dataclass, but there the
**decorator** was the mechanism — it read `__annotations__` and generated an `__init__` that
assigns them. Without it, this is pure documentation. Either write `__init__` explicitly, or add
`@dataclass` with `field(default_factory=dict)`.

**And pyright stayed silent**, because the annotations *promise* the attributes exist and it
believes them. **Type checkers verify consistency, not existence at runtime.** This is exactly
the class of bug tests catch and types don't.

**9. An annotation is a promise about behaviour, not just shape.**
Widening `longest_streak` to `Iterable[date]` would have advertised "I accept generators" from a
function that was *wrong* for them: `if not check_ins` is always False for a generator object
(no `__len__`, no `__bool__`), so the empty-guard never fired and an empty generator returned
`1` instead of `0`. The annotation would have been a lie pyright happily certifies — **worse
than a narrow but honest type.**

Root cause: **consuming an iterable twice.** Fix: materialize at the top, then work with that.
`days = sorted(set(check_ins))` first, `if not days: return 0` second.

**10. Shadowing a builtin is silent.**
`self.id = id` assigned the **builtin `id()` function** — no error, no pyright complaint. LEGB:
`__init__` had no `id` parameter, so lookup went Local → Enclosing → Global → **Builtins** and
found `id()`. In JS this is a `ReferenceError`; Python's builtins are a real, always-present
scope, so shadowing one is legal and invisible.

Dangerous names: `id`, `list`, `dict`, `type`, `str`, `sum`, `input`, `filter`. `list = [1,2]`
works and then `list(...)` fails 200 lines later with an unrelated-looking `TypeError`.
Convention when I truly need the name: a trailing underscore, `id_`.

**11. Truthiness answers the wrong question for "was this provided?"**
`if not id: raise Exception("You must provide an id")` fires for `id=0` — and 0 *was* provided.
`not 0` is `True`. Truthiness asks "is this empty/zero/None?". For validity, say what I mean:
`if self.id < 1`.

**12. A key and the object's own id must not disagree.**
`self.habits[latest_id] = habit` while `habit.id == latest_id + 1` — so it overwrote the
previous habit *and* `get_habit(habit.id)` raised `HabitNotFound`. When a dict is keyed by an
object's field, **key it by that field**: `self.habits[habit.id] = habit`.

**13. `max()` on an empty sequence raises.**
`max(self.habits.keys())` → `ValueError: max() arg is an empty sequence` on the very first
`add_habit`. `max(..., default=0)` is the fix. Empty is always the first case to test.

**14. A no-op `try/except` is worse than none.**
```python
try:
    self.get_habit(habit_id)
except HabitNotFound:
    raise HabitNotFound(habit_id)     # catches X, raises identical X
```
Just call it and let the exception propagate. Catching only to re-raise the same thing adds
noise and hides the real control flow.
