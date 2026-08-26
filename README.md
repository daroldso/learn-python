# Learn Python — by building a habit tracker

Learning **Python** is the goal. The habit tracker is the vehicle: every feature exists
because it forces a Python concept you can't skip.

Backend is Python (FastAPI + Postgres). Frontend is Next.js — already a known quantity,
so 100% of the new learning is Python.

## The rules

**I write the code.** Claude explains the concept and states the target behaviour, then
reviews what I wrote. Claude does not write the solutions. `NOTES.md` is mine, in my own
words — if I can't write it down, I didn't learn it.

## The ladder

| Phase | Topic | App milestone |
|---|---|---|
| 0 | Setup, venvs, how Python runs | toolchain green |
| 1 | Syntax, by contrast with JS/TS | `habits/streaks.py` — pure streak logic |
| 2 | Modules, classes, dunders, type hints | `Habit`/`CheckIn` models + `HabitStore` |
| 3 | stdlib, `datetime`, pytest | JSON persistence + timezone-correct streaks |
| 4 | FastAPI, Pydantic, async | CRUD API + `/habits/{id}/stats` |
| 5 | SQLAlchemy 2.0, Alembic, Postgres | real database + migrations |
| 6 | Auth, config, middleware, decorators | multi-user, JWT login |
| 7 | Next.js + generated TS client | working app in a browser |
| 8 | Docker, CI, deploy | a public URL |

## Commands

```bash
uv run python drills/01_values.py   # run a file
uv run python                       # REPL
uv run pytest                       # tests
uv run ruff check . --fix           # lint (and autofix)
uv run ruff format .                # format
uv run pyright                      # type check
```

No activation needed — `uv run` handles the virtual environment.
