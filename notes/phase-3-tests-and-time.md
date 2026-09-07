# Phase 3 — Tests, and time

> Part of [Python Notes](../NOTES.md). Answers marked **(mine)** are ones I worked out
> myself. Format: `>` is the question, prose below is the answer.

---

## pytest

### Why there's no `expect()`

```python
def test_counts_words():
    assert word_count("a b c") == 4
```

```
>       assert word_count("a b c") == 4
E       AssertionError: assert 3 == 4
E        +  where 3 = word_count('a b c')
```

> Plain `assert` gives a bare `AssertionError` with no detail. Where does that output come from?

**pytest rewrites the bytecode of my test modules at import time.** It imports them through a
custom loader that captures every subexpression, so a plain `assert` reports both the comparison
(`assert 3 == 4`) *and* the intermediate values (`where 3 = word_count('a b c')`).

That's why Python needs no fluent matcher API: **the language's own operator was made
introspective.** Jest needs `expect().toBe()` precisely because JS can't do this — it can only
see the final boolean.

### The Jest map

| Jest | pytest |
|---|---|
| `describe` / `it` | *(nothing)* — files `test_*.py`, functions `test_*` |
| `expect(x).toBe(y)` | `assert x == y` |
| `test.each([...])` | `@pytest.mark.parametrize("a,b", [...])` |
| `expect(fn).toThrow()` | `with pytest.raises(SomeError):` |
| `beforeEach` | a `@pytest.fixture`, injected **by parameter name** |
| temp dirs by hand | the built-in `tmp_path` fixture |

There is **no registration step**. The collector walks `testpaths` (set to `["tests"]` in
`pyproject.toml`) and imports anything matching the naming convention.

### Fixtures are dependency injection

```python
@pytest.fixture
def sample() -> list[str]:
    return ["alpha", "beta"]

def test_uses_fixture(sample: list[str]):   # gets it because the PARAMETER is named `sample`
    assert len(sample) == 2
```

Not a `beforeEach` closure over shared mutable state — each test **declares what it needs** and
pytest constructs it fresh. Closer to React hooks than to Jest's setup blocks.

`tmp_path` is built in: declare `tmp_path: Path` and get a fresh temp directory per test, cleaned
up automatically. **Never write test files into the repo.**

### `parametrize` and generators don't mix

**(mine)** A generator in a `parametrize` list is created **once at collection time** and drained
by the first test that touches it — every later case sees it empty. Anything one-shot needs its
own test function instead of a table row.

### Mutation testing — how to know if a suite is any good

> A green suite proves the code works today. What proves it will keep working?

**Reintroduce a bug on purpose and confirm the suite goes red.** Five bugs from Phase 1 put back
one at a time — all five caught:

| Mutation | Tests that failed |
|---|---|
| drop the fencepost `+ 1` | 6 |
| `start > end` → `>=` | **1** |
| `longest_streak: current = 1` → `0` | 3 |
| `current_streak: streak = 0` → `1` | 3 |
| `/` → `//` | 4 |

**The `>=` row is the lesson.** Exactly one test detects it — the single-day range
(`Sep 5 → Sep 5`), the case I originally got wrong. Delete that one row from `parametrize` and
the bug becomes invisible again. **Edge cases aren't thoroughness theatre; they're often the only
thing standing between me and a regression.**

Any test that never fails under any mutation is decoration. (`mutmut`, `cosmic-ray` automate
this; the manual version is 90% of the value.)

---

## Time

### Naive vs aware

```python
datetime(2026, 9, 5, 8, 0).tzinfo                       # None      <- NAIVE
datetime(2026, 9, 5, 8, 0, tzinfo=ZoneInfo("Asia/Tokyo")).tzinfo   # Asia/Tokyo

datetime.now()      # NAIVE. reads the local clock, then FORGETS where it came from. The trap.
datetime.now(UTC)   # aware

naive < aware       # TypeError: can't compare offset-naive and offset-aware datetimes
```

> Why does Python refuse to compare them?

Because any guess would be wrong somewhere. Loud failure over silent corruption — the same design
choice as `ZeroDivisionError` instead of JS's `Infinity`.

**`datetime.now()` is the single biggest `datetime` trap in Python:** it looks like the obvious
call and yields a value that can't be safely compared, stored, or converted. Always
`datetime.now(UTC)`.

### `.date()` is a lossy, timezone-dependent projection

```python
aware.date()      # the offset is GONE
```

> "Which calendar day was this instant?" — why is that not a well-formed question?

Because it has no answer until I say **in whose timezone**. The same instant is Sep 4 in London
and Sep 5 in Tokyo. Storing a bare `date` means the answer got baked in at write time, by whichever
server handled the request.

An **instant** is an objective fact. A **calendar day** is a rendering of it.

### The bug this caused

A user in Tokyo, 4-day streak, checks in at 8:00am Sep 5 — and the app says their streak is **0**.

```
user checks in at : 2026-09-05 08:00:00+09:00
same instant, UTC : 2026-09-04 23:00:00+00:00     <- the server stores Sep 4
```

8am JST is 11pm *the previous day* UTC, so every check-in shifted back one calendar day. The
insidious part: `longest_streak` still said 4 and the data looked internally consistent — **only
the anchor disagreed.** This ships, and only overseas users complain.

### The rule

> **Store instants in UTC. Compute calendar days in the user's timezone, at read time.**

- `CheckIn.at: datetime` — an aware instant, the objective fact.
- `Habit.timezone: str` — an IANA name (`"Asia/Tokyo"`), i.e. *whose day we mean*.
- `days_for()` converts: `check_in.at.astimezone(ZoneInfo(habit.timezone)).date()`.

### Where the fix belonged — the payoff of layering

**`streaks.py` did not change. Its 24 tests did not change.**

All three functions still take `Iterable[date]` and remain pure calendar arithmetic. The entire
timezone problem lives in the store — the layer that knows about users and storage.

Had `current_streak` accepted `Iterable[CheckIn]` back in Phase 2, this change would have rippled
through the domain logic and every one of its tests. **Dependency arrows point one way:**
`store.py` may import `streaks.py`; `streaks.py` must never import `store.py`. Pure logic sits at
the bottom with no dependencies; layers that know about storage and HTTP depend *on it*.

---

## Persistence

### pathlib

```python
p = Path("data") / "habits.json"          # `/` joins — no os.path.join
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2))
data = json.loads(p.read_text())
p.exists()
```

Replaces the string-juggling of `os.path`. **A `Path` knows it's a path.**

### JSON has no date type

```python
json.dumps(asdict(check_in))
# TypeError: Object of type datetime is not JSON serializable
```

> Is that a Python limitation?

No — a **format** limitation. JSON's value types are string, number, boolean, null, array, object.
Every date on the wire is a *string by convention*, and I pick the convention:

```python
c.at.isoformat()                          # '2026-09-07T08:00:00+00:00'
datetime.fromisoformat(...) == c.at       # True — round-trips exactly, offset included
```

ISO 8601 preserves the UTC offset and every language parses it. Same choice as when a TS `Date`
crosses `JSON.parse` and comes back a string.

`asdict()` walks a dataclass recursively into plain dicts — most of the work — but leaves
`datetime` in place, so it hands me the problem rather than solving it.

**A serialization boundary is where types get lost.** Inside the program `at` is a `datetime`; on
disk it's a string. Every read must reconstruct it — and forgetting to is how naive datetimes
sneak back in, which is what `CheckIn.__post_init__` now catches.

### `@classmethod` — the alternative constructor

```python
@classmethod
def load(cls, path: Path) -> "HabitStore":
    store = cls()          # `cls` IS the class, not an instance
    ...
    return store

store = HabitStore.load(path)      # called on the CLASS
```

Receives `cls` instead of `self`. Python's spelling of a named constructor — the equivalent of a
`static fromJSON()` factory in TS.

### Round-trip is the assertion that matters

```python
assert loaded.habits    == store.habits
assert loaded.check_ins == store.check_ins
```

Stronger and shorter than checking fields one by one — and it works because `@dataclass` generated
`__eq__` in Phase 2, so equality compares every field recursively. **The property is "everything
survives", so assert exactly that** rather than enumerating the fields I remembered to check.

It catches encode/decode *asymmetry*, which is the whole class of bug here. If `save` writes
something `load` can't read back identically, that test goes red and nothing else will.

### What `load` still doesn't do

It trusts the file completely. A missing key → `KeyError: 'timezone'`. A malformed date → a raw
`ValueError`. A check-in referencing a deleted habit → loads happily.

**This is exactly the problem Pydantic solves in Phase 4**: declare the shape once, get parsing,
validation, and clear error messages generated from it.
