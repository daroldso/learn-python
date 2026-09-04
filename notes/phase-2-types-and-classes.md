# Phase 2 — Types, classes, and exceptions

> Part of [Python Notes](../NOTES.md). Answers marked **(mine)** are ones I worked out
> myself. Format: `>` is the question, prose below is the answer.

### Type hints are not enforced at runtime

```python
def add(a: int, b: int) -> int:
    return a + b

add("hello", "world")     # runs fine. Prints "helloworld".
```

> If Python ignores them, what are they for?

Nothing checks annotations unless I run a checker. **In TypeScript the checker is a gate** —
you can't run `.ts` without `tsc`/esbuild, so type errors block execution by construction.
Python has no build step: `uv run python` goes straight to the interpreter. `pyright` runs only
because I ran it. **So the types are only real once they're in CI.**

But they aren't erased either — TS strips types at compile time, Python **keeps** them:

```python
add.__annotations__     # {'a': int, 'b': int, 'return': int}
```

That single fact is the foundation of the whole stack ahead. `@dataclass` reads annotations to
generate `__init__`. Pydantic reads them to generate runtime validators. FastAPI reads them to
generate parsing, validation and OpenAPI docs. **Annotations do nothing alone and everything in
the hands of a library that inspects them.**

### pyright strict: read the error names

- `reportUnknownParameterType` — a parameter has no annotation.
- `reportUnknownVariableType` — a type couldn't be inferred *because something upstream was
  unknown*.

The second kind is **contagious**: one unannotated parameter made `habit` unknown, which made
`names` unknown, which made the return unknown — 4 errors from 1 cause. 16 errors usually have
about 4 causes. **Fix the source, watch the cascade vanish.**

Strict requires annotations on *parameters* (nothing calls the function at check time, so it
can't infer them) but happily infers *returns*. Annotate returns anyway — an explicit `-> int`
is a claim it verifies against the body, which catches a later branch returning something else.

### Variance: `list` vs `Iterable` vs `Sequence`

> Why did `list[date]` reject callers that `Iterable[date]` accepted?

| Caller passes | `list[date]` | `Iterable[date]` |
|---|---|---|
| `"hello"` | rejected | rejected ✓ |
| `list[datetime]` | **rejected** ✗ | accepted |
| `set[date]` | **rejected** ✗ | accepted |
| a generator | **rejected** ✗ | accepted |

`list` is **invariant**; `Iterable` is **covariant**. **Mutability is why.** If `list[datetime]`
were assignable to `list[date]`, the callee could `.append(date(...))` into it and the caller's
`list[datetime]` would now hold a plain `date`. Unsound. `Iterable` is read-only, so widening
the element type is safe.

**TypeScript gets this wrong on purpose** — TS arrays are covariant, so `Dog[]` passes as
`Animal[]` and you can push a `Cat` in. Python's checker is *stricter* than TS here.

Also: **`datetime` is a subclass of `date`.** Not trivia — Phase 3 brings timezone-aware
timestamps and `list[date]` would reject them.

Rule: **accept the widest input you can actually honour.** Not wider (see lesson 9).

### The `Iterable[str]` trap

```python
def notify(names: Iterable[str]) -> list[str]: ...
notify("ana")     # pyright: 0 errors -> ['hi a', 'hi n', 'hi a']
```

A single string passed where a collection of strings was expected **type-checks clean** and
silently iterates characters, because `str` *is* `Iterable[str]`. Only bites when the element
type is `str` — `Iterable[date]` is safe, since `str` isn't a `date`.

### `dict[K, V]` can't describe a record

> Why is there no correct `dict[str, ...]` annotation for `{"name": "run", "archived": False}`?

`dict[K, V]` is a **homogeneous mapping** — every value has the same type. A habit is a
**heterogeneous record**: `name` is `str`, `archived` is `bool`. The union `dict[str, str | bool]`
throws away *which key has which type*, so `h["name"]` becomes `str | bool` and can't be
returned as `list[str]`.

`TypedDict` describes the shape:

```python
class HabitDict(TypedDict):
    name: str
    archived: bool
```

With that, the function body type-checks clean and the errors move to the **call sites** —
catching a missing key, a typo'd key (`"nmae"`), and `"archived": 0` (int, not bool). A
`dict[str, str]` annotation catches none of those, because every string key is valid in a dict.

Use `TypedDict` for JSON-shaped data from real APIs. For my own domain model, use a class.

### Dataclasses

```python
@dataclass
class Habit:
    id: int
    name: str
    archived: bool = False
```

Generates `__init__`, `__repr__`, and `__eq__` from the annotations alone.

The generated `__eq__` compares **field values** — `Habit(1,"run") == Habit(1,"run")` is `True`,
where JS's `{id:1} === {id:1}` is `false` and I'd reach for lodash. **Value equality is the
Python default.**

**Mutable defaults are refused**, not silently shared:

```python
tags: list[str] = []                              # ValueError at class-definition time
tags: list[str] = field(default_factory=list)     # the fix
```

Plain functions still let `def f(x=[])` through silently. Dataclasses are newer and learned from
the footgun.

> Where does validation go?

`__post_init__`, **not** `__init__`. Writing `__init__` inside a `@dataclass` overrides the
generated one — throwing away the exact thing the decorator existed to provide, and duplicating
the field list so annotations and init body can drift.

```python
def __post_init__(self) -> None:      # runs AFTER the generated __init__ assigns fields
    if self.id < 1:
        raise ValueError(f"id must be positive, got {self.id}")
```

### Hashable requires immutable

```python
{CheckIn(1, day)}     # frozen=True  -> fine
{Habit(1, "run")}     # mutable      -> TypeError: unhashable type: 'Habit'
Habit.__hash__        # is literally None
```

A `set`/`dict` finds items by hash. Mutate an object after inserting it and its hash changes —
the entry becomes permanently unreachable. So `@dataclass` sets `__hash__ = None` when it
generates `__eq__` on a **mutable** class, making the failure loud at insertion rather than
silent at lookup.

Same rule behind `tuple` being a valid dict key and `list` not. And why `frozen=True` "unlocks"
set membership: I promised not to mutate, so hashing is safe again.

JS has no equivalent — a JS `Set` compares by reference, so `new Set([{a:1},{a:1}])` has size 2.
Python's value-hashing is more useful and correspondingly stricter about what qualifies.

Bonus: I made `CheckIn` frozen for *correctness* (a past event shouldn't change) and got
set-membership and dict-key-ability for free. Immutability paying a second dividend is normal.

### `__str__` vs `__repr__`

- `__repr__` — for **developers**. Unambiguous, ideally reconstructible. Dataclass generates it.
- `__str__` — for **users**. `print()` and f-strings use it.

```python
str(h)    # 'run (active)'
repr(h)   # "Habit(id=1, name='run', archived=False)"
```

**If `str(x)` and `repr(x)` say the same thing, one of them is doing no work.**

### Exceptions

```python
class HabitNotFound(Exception):
    def __init__(self, habit_id: int) -> None:
        super().__init__(f"No habit with id {habit_id}")
        self.habit_id = habit_id      # carry DATA, not just a message
```

`raise Exception("...")` is too broad to be catchable — handling it means `except Exception`,
which also swallows `TypeError`, `KeyError`, and every genuine bug in the block. Subclass
something specific.

```python
try:    ...
except HabitNotFound as e:  ...   # e.habit_id is inspectable
else:   ...                       # ran only if NO exception
finally: ...                      # always runs
```

**Raising beats returning `None`.** `get_habit` returns `Habit`, not `Habit | None` — so callers
don't have to check, and can't forget to.

### EAFP vs LBYL

```python
try:                              # EAFP — Pythonic
    return self._habits[habit_id]
except KeyError:
    raise HabitNotFound(habit_id) from None

if habit_id in self._habits:      # LBYL — the defensive JS style
    return self._habits[habit_id]
return None
```

*Easier to ask forgiveness than permission.* Wins because exceptions are cheap, check-then-act
does the lookup **twice**, and returning `None` pushes the problem onto every caller.

### Exception chaining — `from None` vs `from err`

Ruff **B904**. Re-raising inside an `except` without `from` attaches the original as context:

```
KeyError: 42
During handling of the above exception, another exception occurred:
HabitNotFound: No habit with id 42
```

Misleading — the `KeyError` wasn't a failure, it was my deliberate signal.

- `raise X from None` — "the original is an implementation detail, hide it." **Right here:**
  translating `KeyError` → domain error is the method's job; the caller doesn't care a dict
  was involved.
- `raise X from err` — "this was *caused by* that." Keeps the chain when it's genuinely useful.

### Layering: which way the arrows point

`models.py` and `store.py` may import `streaks.py`. **`streaks.py` must never import them.**

> Should `current_streak` take `Iterable[date]` or `Iterable[CheckIn]`?

**(mine)** `current_streak` is a utility, so keep the signature as flexible as possible.
`Iterable[CheckIn]` would restrict it to one class and reject other valid inputs.

The argument that bites hardest is Phase 5: `CheckIn` becomes a **SQLAlchemy ORM model**. If
`streaks.py` took `CheckIn`, my calendar arithmetic would transitively depend on the database —
untestable without a session, and an ORM change would ripple into pure date math. Taking `date`
means **`streaks.py` never changes again**.

The call site is a generator, which only works because I chose `Iterable`:

```python
current_streak((c.day for c in check_ins), today)   # nothing allocated
```

Keep pure logic at the bottom of the stack with no dependencies; let storage and HTTP layers
depend *on it*. Same instinct as keeping React components ignorant of the fetch layer.

### Why `dict[int, Habit]` and not `list[Habit]`

**(mine)** Using a dict makes `get_habit` very efficient — O(1) hash lookup instead of an O(n)
scan. Same instinct that made `set` right in `current_streak`.
