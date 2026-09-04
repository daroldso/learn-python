# Python Notes

Reference for reloading the mental model. One file per phase, plus a running list of
mistakes. Drafted with Claude at the end of each phase; answers marked **(mine)** are ones
I worked out myself.

Format throughout: `>` is the question, prose below is the answer.

| | File | Covers |
|---|---|---|
| **0** | [How Python runs](notes/phase-0-setup.md) | venvs and why Python needs them, the uv ↔ npm map |
| **1** | [Syntax, by contrast with JS](notes/phase-1-syntax.md) | truthiness vs equality, `bool` is an `int`, `/` vs `//`, f-strings, `__main__`, comprehensions, chained comparisons, `set` vs `list`, `pairwise`, the three streak algorithms |
| **2** | [Types, classes, exceptions](notes/phase-2-types-and-classes.md) | hints not enforced at runtime, pyright strict, variance, `TypedDict`, dataclasses, hashability, `__str__` vs `__repr__`, custom exceptions, EAFP, exception chaining, layering |
| — | [**Hard-won lessons**](notes/lessons.md) | Every bug I actually shipped into my own code, and what I now know. **The reread-me file.** |

## Quick commands

```bash
uv run python habits/streaks.py     # run a file
uv run pytest                       # tests            (Phase 3)
uv run ruff check . --fix           # lint + autofix
uv run ruff format .                # format
uv run pyright                      # type check (strict)
```
