# Phase 1 — Syntax, by contrast with JS

> Part of [Python Notes](../NOTES.md). Answers marked **(mine)** are ones I worked out
> myself. Format: `>` is the question, prose below is the answer.

### Truthiness is not equality

```python
[] == False   # False
[] == True    # False
bool([])      # False
```

> What question does `==` ask? What question does `bool()` ask? Why does JS answer
> `true` to `[] == false`?

`==` asks **"do these represent the same value?"** Python tries `list.__eq__(bool)`, gets
`NotImplemented`, tries the reflected `bool.__eq__(list)`, also `NotImplemented`, and falls
back to identity — which is `False`. A list is not equal to a boolean, in either direction.
There's no third answer; both comparisons are just false.

`bool(x)` asks a different question — **"is this truthy?"** — and it's a conversion, not a
comparison. It calls `__bool__`, or `__len__` if there's no `__bool__` (which is why empty
containers are falsy: their length is 0).

JS conflates the two because `==` **coerces**: `[]` → `""` → `0`, `false` → `0`, `0 == 0` →
`true`. That coercion is also why JS is *asymmetric* here — `[] == false` is `true` but
`[] == true` is `false`. Python refuses to coerce across unrelated types, so it gives the
boring symmetric answer.

> When do I write `if x:` vs `if x == something`?

- `if x:` — truthiness. **The default.** Use for "is this list non-empty", "did I get a value".
- `if x == value:` — only when you genuinely care about equality with a specific value.
- `if x is None:` — identity, for `None` specifically. Never `== None`.
- **Never `if x == True`.** It asks the wrong question and gives wrong answers for `None`,
  `""`, `[]` — all of which are falsy but not equal to `False`.

### `bool` is a subclass of `int`

> Why is `0 == False` True when `[] == False` is False?

Because `bool` genuinely inherits from `int`, and `True` *is* the value `1`. So `0 == False`
and `1 == True` are ordinary numeric equality, not coercion. `isinstance(True, int)` is `True`.
(But `True is 1` is `False` — equal value, different object.)

```python
sum([True, True, False])   # 2
```

`sum` just adds ints, and `True` is 1. This makes **counting a one-liner** — no accumulator,
no `+= 1`:

```python
# the loop I wrote in completion_rate...
days_completed = 0
for check_in in set(check_ins):
    if start <= check_in <= end:
        days_completed += 1

# ...is the same as
days_completed = sum(start <= c <= end for c in set(check_ins))
```

### `/` vs `//`

```python
7 / 2     # 3.5    true division — ALWAYS a float
7 // 2    # 3      floor division
4 / 2     # 2.0    <- still a float, even though it divides evenly
-7 // 2   # -4     <- floors toward -infinity, does NOT truncate
```

**(mine)** The first three. The trap for a JS dev is that JS has one number type, so `/` never
surprises you; in Python the operator you pick decides the *type* of the result. `//` returning
`0` instead of `0.14` is how a completion rate silently becomes 0%.

`-7 // 2` is the subtler one: Python **floors** (`-4`), JS's `Math.trunc(-7/2)` **truncates**
(`-3`). They differ for negatives.

### Empty containers are falsy

Falsy in Python: `False`, `None`, `0`, `0.0`, `""`, `[]`, `()`, `{}`, `set()`, `range(0)`, and
any object whose `__bool__` returns `False` or `__len__` returns `0`. Everything else is truthy.

Differences from JS worth memorizing:

| Value | JS | Python |
|---|---|---|
| `[]`, `{}` | **truthy** | **falsy** |
| `NaN` / `float("nan")` | falsy | **truthy** |
| `"0"` | truthy | truthy |
| `undefined` | falsy | *(doesn't exist — only `None`)* |

The `[]`/`{}` row is the one that causes real bugs, because `if (arr)` in JS and `if arr:` in
Python look identical and mean opposite things for an empty array.

### f-strings

> Equivalent to what in JS? Why does `f"{h["name"]}"` work on 3.13 but not on 3.11?

Template literals — `f"..."` ≈ `` `...` ``, and `{expr}` ≈ `${expr}`. Any expression works
inside the braces.

Before Python 3.12, f-strings were tokenized by a separate mini-parser that couldn't handle the
outer quote character appearing inside the braces — so `f"{h["name"]}"` was a `SyntaxError` and
everyone wrote `f"{h['name']}"`. **PEP 701** (3.12) made f-strings parse with the normal parser,
so nested same-quotes, backslashes, and multi-line expressions are all legal now.

Still prefer the inner-single-quote form: it works everywhere, and most code you'll read uses it.

### `if __name__ == "__main__":`

> What is `__name__` set to, and when? What breaks without the guard?

Python has no separate "script" and "module" concepts — the same `.py` file can be run directly
(`python foo.py`) or imported (`import foo`). `__name__` is how the file tells which happened:

- run directly → `__name__` is `"__main__"`
- imported → `__name__` is the module's name, `"foo"`

Importing a module **executes its entire top level**, once, then caches it in `sys.modules`. So
bare `print(...)` calls at module level fire the moment anything imports the file — including
`pytest` collecting tests. The guard means "only when run directly."

Convention: **definitions at the top, execution behind the guard at the bottom.**

Node's ESM has the same problem and, since Node 24, the same solution: `import.meta.main`.
Older code uses `require.main === module` (CJS) or compares `process.argv[1]` to
`fileURLToPath(import.meta.url)`.

### Comprehensions

```python
[f(x) for x in xs]              # .map(f)
[x for x in xs if pred(x)]      # .filter(pred)
[f(x) for x in xs if pred(x)]   # .filter(pred).map(f)   — one pass, not two

{x for x in xs}                 # set comprehension
{k: v for k, v in pairs}        # dict comprehension
(f(x) for x in xs)              # generator — lazy, no list allocated
```

Idiomatic because it's a single expression producing a value: no accumulator variable, no
`.append`, nothing half-built to misread. Python has no chainable `.map`/`.filter` on lists —
this is the replacement, and it fuses filter+map into one pass.

### Chained comparisons

```python
start <= check_in <= end
```

Real Python: it means `(start <= check_in) and (check_in <= end)`, with `check_in` evaluated
**once**.

In JS this is a bug — `1 <= x <= 3` parses as `(1 <= x) <= 3`, so the boolean gets coerced to
`0`/`1` and compared to `3`. `1 <= 5 <= 3` evaluates to `true` in JS even though 5 > 3.

### Picking the data structure

> `set` vs `list` for `in`? Which edge cases did the set eliminate for free?

`in` on a `list` is **O(n)** — a linear scan. On a `set` (or `dict` key) it's **O(1)** average,
because it hashes. For "have I seen this?", always a set.

In `current_streak`, `set(check_ins)` + anchoring at `today` killed three edge cases with no
code written for any of them:

1. **Duplicates** — the set collapses them.
2. **Unsorted input** — membership doesn't care about order.
3. **Future-dated check-ins** — walking backwards from `today` never visits them.

My first attempt sorted a list and walked forward, and would have needed explicit handling for
all three. **Choosing the right structure removes edge cases instead of adding branches.**

### `itertools.pairwise`

```python
for prev, day in pairwise(sorted(set(check_ins))):
```

**(mine, sharpened)** It solves comparing consecutive values in a sequence — it yields
overlapping pairs `(a,b), (b,c), (c,d)`. It removes the manual "remember the previous item"
bookkeeping and the index arithmetic (`xs[i-1]`), so there's no off-by-one and no way to run off
the end. On a sequence of 1 it yields nothing, which is exactly right for a streak of 1.

---

## The three streak algorithms

Same data, three shapes. The **anchor** — the fixed point the answer is defined relative to —
determines the algorithm.

| Function | Anchor | Shape | Why the anchor forces it |
|---|---|---|---|
| `current_streak` | `today` | walk backwards, `while` + set | "Current" is *defined* relative to today, so you must start there. Length is unknown up front → `while`, not `for`. |
| `longest_streak` | none | sort + scan adjacent pairs | The run can be anywhere, so every run must be examined. Adjacency requires order → `sorted`. |
| `completion_rate` | the `[start, end]` window | no day-by-day iteration at all | Denominator is pure arithmetic on the window; numerator is a membership count. Neither needs to walk days. |

The general lesson: **find the anchor first.** It tells you the shape before you write a line.
