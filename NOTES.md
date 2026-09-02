# Python Notes

Reference for reloading the mental model. Written during Phases 0–1, building the habit
tracker. Contrasts are with JS/TS throughout, because that's the intuition being retrained.

---

## Phase 0 — How Python runs

### Virtual environments

**Why they exist:** Node resolves an import by walking up the directory tree looking for
`node_modules`, so isolation is per-project and automatic. Python has no such search — it
has one global list of import paths (`sys.path`), and `pip install` drops packages into
whichever interpreter is first on `$PATH`. Two projects needing different versions of the
same library collide, and the collision can damage the **system Python** that OS tooling
depends on.

**What a venv actually is:** a directory containing its own `bin/python` and its own
`site-packages`. It's a fake Python installation. "Activating" it just prepends `.venv/bin`
to `$PATH` so that `python` resolves *there* instead. That's the entire trick — a `PATH`
manipulation, not a sandbox.

**Why `uv run` beats activating:** it resolves `.venv` per command and syncs from
`uv.lock` first, so activation is never needed. If a tutorial says
`source .venv/bin/activate`, that's the older workflow.

**The consequence that bites:** `python` and `uv run python` are *different programs*.
Mine are 3.11.5 (Homebrew, no project packages) and 3.13.5 (project). When an import
mysteriously fails, the first question is always *which interpreter is this?*

```bash
uv run python -c "import sys; print(sys.executable)"
```

### The uv ↔ npm map

| Python | JS equivalent | Where the analogy breaks |
|---|---|---|
| `pyproject.toml` | `package.json` | Also holds **tool config** — ruff, pytest, pyright all live here. In JS these'd be separate `.eslintrc` / `jest.config.js` files. |
| `uv.lock` | `package-lock.json` | Same idea: exact resolved versions, commit it. |
| `uv run` | `npm run` / `npx` | Syncs the env from the lockfile *before* running. |
| `.venv/` | `node_modules/` | `.venv` contains a **`python` binary**; `node_modules` doesn't contain `node`. And it's not auto-discovered — resolution is by `$PATH`, not by walking up directories. |
| `uv add` | `npm install <pkg>` | Updates `pyproject.toml` + lock + installs, in one step. |

---

## Phase 1 — Syntax, by contrast with JS

### Truthiness is not equality

```python
[] == False   # False
[] == True    # False   <- the one that surprised me
bool([])      # False
```

Two different questions, and JS blends them together:

- **`==` asks "do these compare equal?"** Python does **not** coerce across unrelated
  types. A list compared to a bool is simply not equal — to *either* one. It's not "neither
  true nor false"; it's "you asked whether a list equals a boolean, and it doesn't."
- **`bool(x)` asks "is x truthy?"** — a conversion, defined per type. This is what `if x:`
  calls under the hood.

JS's `==` coerces both sides toward numbers: `[]` → `""` → `0`, `false` → `0`, so
`0 == 0` is `true`. That's why JS produces the genuinely weird **asymmetry** —
`[] == false` is `true` but `[] == true` is `false`. Python's symmetric `False`/`False` is
the *less* surprising answer once you stop expecting coercion.

**The rule:** use `if x:` when asking "is there anything here?" — that's the normal case.
Use `if x == value` only when comparing against a specific value. **Never `if x == True`.**
`ruff` enforces this (E712).

### `bool` is a subclass of `int`

`True` genuinely **is** `1` and `False` **is** `0`, numerically. `isinstance(True, int)`
returns `True`. So:

- `0 == False` and `1 == True` → `True` (equal numbers)
- `2 == True` → `False` (2 ≠ 1)
- `[] == False` → `False` (a list isn't a number at all)

Which is why this works, and it's genuinely useful:

```python
sum([True, True, False])   # 2
```

"How many days completed this week?" is `sum(...)` over booleans — no counter, no loop.

### `/` vs `//`

```python
7 / 2     # 3.5    true division, ALWAYS returns float
7 // 2    # 3      floor division, int
4 / 2     # 2.0    float even when it divides exactly
-7 // 2   # -4     floors toward negative infinity, not toward zero
```

JS has one number type, so `/` is always float division and the choice never comes up.
Python makes you pick per-operator. **The trap:** `4 // 7` is `0`, so a completion rate
computed with `//` silently reports 0% for everything. And `/` on two ints always yields a
float, which surfaces in JSON as `2.0` instead of `2`.

### Empty containers are falsy

Falsy: `False`, `None`, `0`, `0.0`, `""`, `[]`, `{}`, `set()`, `()`, `range(0)`.
Everything else is truthy.

**Differs from JS:** `[]` and `{}` are **truthy in JS, falsy in Python**. This is the
inversion most likely to cause a silent bug. `"0"` is truthy in both. JS additionally has
`NaN` and `undefined`; Python has `None` and no `undefined` at all.

### f-strings

`f"{x}"` ≈ `` `${x}` ``. The `f` prefix is required; expressions go in braces.

```python
f"{habit['name']}: {streak} day streak"
f"{rate:.1%}"      # 0.5714 -> '57.1%'   format spec after the colon
f"{count:>4}"      # right-align in 4 columns
f"{value=}"        # 'value=42'  — debug shorthand, prints name AND value
```

**Why `f"{h["name"]}"` works on 3.13 but not 3.11:** before PEP 701 (Python 3.12),
f-string bodies were parsed by a separate mini-parser that couldn't handle the same quote
character nested inside — it was a `SyntaxError`. 3.12+ parses f-strings with the real
grammar, so nesting works. Most code online still uses inner single quotes
(`f"{h['name']}"`) because it had to for twenty years, and that form works everywhere.

### `if __name__ == "__main__":`

**`import` in Python RUNS the module** — top to bottom, every top-level statement executes,
and the result is cached in `sys.modules`. There's no separate "definitions only" mode. ESM
evaluates a module once too, but you reach it through exported bindings; in Python a bare
`print()` at module level fires the moment anything imports the file.

`__name__` is a variable Python sets per module: `"__main__"` when the file is run directly
(`python foo.py`), otherwise the module's dotted name (`"habits.streaks"`).

So the guard means **"only when run as a script."** Without it, importing the module prints
things, runs demos, maybe starts a server. Hence the convention: definitions at the top,
execution behind the guard at the bottom.

### Comprehensions

```python
# .map(f)             ->  [f(x) for x in xs]
# .filter(pred)       ->  [x for x in xs if pred(x)]
# .filter().map()     ->  [f(x) for x in xs if pred(x)]
```

Also `{k: v for ...}` (dict), `{x for ...}` (set), and `(x for x in ...)` — parentheses
make it a **generator**, which is lazy and never builds the list.

Idiomatic because it's a single expression with no intermediate list, and it reads in the
order you'd say it aloud. Past two `for`/`if` clauses, use a real loop — nesting is legal
but unreadable.

### Chained comparisons

```python
start <= check_in <= end
```

Real syntax. Means `start <= check_in and check_in <= end`, and `check_in` is evaluated
**once**. In JS, `a <= b <= c` parses as `(a <= b) <= c` — a boolean compared to a number,
coerced to 0/1 — so it's almost always a bug there. Python got this one right.

Using it deleted `days_in_range` entirely: no list of dates needed to ask "is this date in
the window?"

### Picking the data structure

`in` on a **list** is O(n) — a linear scan. `in` on a **set** or **dict** is O(1) — a hash
lookup.

In `current_streak`, one `set(check_ins)` gave three things for free:

1. **Dedup** — duplicate check-ins collapse to one
2. **Order-independence** — no `sorted()` needed
3. **Fast membership** — O(1) instead of O(n)

Choosing the right structure made three edge cases *disappear* instead of requiring three
branches to handle them. That's the general lesson.

Cost: sets are unordered and require hashable elements. `date` is immutable and hashable,
so it qualifies. `longest_streak` needs order, which is why it sorts.

### `itertools.pairwise`

It solves comparing consecutive values in a sequence — it removes the need for an index to
track state.

```python
pairwise([a, b, c])   # -> (a, b), (b, c)
```

Avoids `range(1, len(xs))` plus `xs[i-1]` index arithmetic, which is exactly where
off-by-ones hide. Lazy: yields pairs as it goes rather than building a list.

---

## The three streak algorithms

Same data, three genuinely different shapes. Recognizing which shape a problem has is most
of the skill.

| Function | Anchor | Shape | Why that shape |
|---|---|---|---|
| `current_streak` | `today` — a known endpoint | walk backwards, `while` + set | The run must **end at today**, so start there and step back until the chain breaks. Length is unknown up front → `while`, not `for`. |
| `longest_streak` | none | sort + scan adjacent pairs | No endpoint to anchor to, so **every** run must be examined. Sorting makes runs contiguous; one `pairwise` pass then finds them. O(n log n). |
| `completion_rate` | `start` and `end` — both known | no iteration over days at all | The denominator is pure arithmetic on two dates. The numerator only counts check-ins **inside** the window. Iterating the days would be wasted work. |

Notable: none of these needed a manual index. `sorted`, `set`, `pairwise`, `max`, `sum` did
the work. Reaching for a built-in before writing index arithmetic is the Pythonic default —
shorter, and off-by-ones can't hide in code I didn't write.

---

## Hard-won lessons

**1. A print is not a test.**
My `completion_rate` printed six lines of plausible output while returning the wrong number
**5 times out of 6**. The print was labelled `result:` but printed the *denominator*, and
the actual return value was never printed by anything. A `print` shows what I *chose* to
look at; an `assert` checks what the function actually **returns** and cannot be aimed at
the wrong expression. This is the entire argument for the pytest work in Phase 3.

**2. `while` loops: I own the advance step.**
`current_date = today - timedelta(days=1)` recomputed *yesterday* from a fixed anchor every
pass, so the cursor never moved past it → **infinite loop**. It hung rather than returning
a wrong answer because the exit condition could never become false. A hang is worse than a
wrong answer: no traceback, no output, a pinned CPU — and inside a Phase 4 web handler it
takes out the worker, not just one response. `for x in collection` **cannot** fail this
way; iteration is driven by the iterator, not by me. So `while` deserves more suspicion.

**3. Dead code still executes.**
A leftover debug `print` — diagnosing a bug I had *already fixed* — crashed a correct
function with `ZeroDivisionError` on a single-day range. Deleting scaffolding is part of
finishing, not tidying. Anything that runs can fail.

**4. Duplicated expressions drift.**
The `(end - start).days + 1` formula existed in two places; I fixed the `return` and missed
the `print`. The fix that makes this impossible: **compute once, bind to a name, use the
name.** `denominator = (end - start).days + 1` — then the two can't disagree.

**5. Operator precedence.**
`days_completed / (end - start).days + 1` parses as
`(days_completed / (end - start).days) + 1` — `/` binds tighter than `+`. It *read* as
correct because I'd written the intended grouping in a comment, so the parentheses existed
in my head and not in the code. Same precedence rules as JS; not a Python quirk.

**6. Passing cases can hide two bugs.**
`gap of one day` passed while the function was badly broken — an off-by-one and a missing
consecutiveness check **cancelled each other**. One passing case is evidence of nothing.
Cases have to vary independently: empty, single, boundary, duplicate, unordered,
out-of-range.

**7. Off-by-one: fenceposts.**
`date - date` gives the **gap** (a `timedelta`), not the count of days spanned. Aug 1 → Aug
7 is a gap of 6 but **7 days inclusive**. Six fence panels, seven fenceposts. Inclusive
counts need `+ 1`, and the single-day case (`start == end` → `1`, not `0`) is the one that
proves it's right.
