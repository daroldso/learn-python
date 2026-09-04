# Phase 0 — How Python runs

> Part of [Python Notes](../NOTES.md). Answers marked **(mine)** are ones I worked out
> myself. Format: `>` is the question, prose below is the answer.

### Virtual environments

> Why does Python need `.venv` when Node just has `node_modules`? What does "activating"
> a venv actually change? Why can `python` and `uv run python` be different programs?

**(mine, sharpened)** Activating a venv prepends `.venv/bin` to `PATH`, so the name `python`
resolves to the venv's interpreter instead of the system one. `uv run` does the same thing
without activation — it locates `.venv` itself and runs the command inside it.

The deeper reason Python needs this and Node doesn't: **Node resolves imports by walking up
the directory tree looking for `node_modules`**, so isolation is automatic and per-directory.
Python has no such search — `import` looks in `sys.path`, which points at *one* global
`site-packages` belonging to whichever interpreter is running. So by default every project on
the machine shares one set of installed packages, and two projects needing different versions
of a library conflict. A venv is a fake Python installation (its own `bin/python`, its own
`site-packages`) that redirects `sys.path`. It's opt-in isolation bolted on, not built in.

Consequence: **"which interpreter am I running?" is always the first debugging question.**
`uv run python -c "import sys; print(sys.executable)"` answers it.

### The uv ↔ npm map

| Python | JS equivalent | Where the analogy breaks |
|---|---|---|
| `pyproject.toml` | `package.json` | Also holds config for ruff/pytest/pyright. It's a language standard (PEP 621), not a tool's private file. |
| `uv.lock` | `package-lock.json` | Resolves for *all* platforms at once, so the same lock works on macOS and the Linux container. Commit it. |
| `uv run <cmd>` | `npx <cmd>` | Runs *any* command in the venv, not just scripts declared in the manifest. Re-syncs from the lock first. |
| `.venv/` | `node_modules/` | Contains a whole Python interpreter, not just packages. And it is **not** auto-discovered — something must put it on `PATH`. |
| `uv add <pkg>` | `npm install <pkg>` | Updates manifest + lock + installs, in one step. |
