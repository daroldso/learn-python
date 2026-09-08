# Phase 4 — FastAPI

> Part of [Python Notes](../NOTES.md). Answers marked **(mine)** are ones I worked out
> myself. Format: `>` is the question, prose below is the answer.

---

## Pydantic

### Annotations become validators

```python
class HabitIn(BaseModel):
    name: str = Field(min_length=1)
    timezone: str = "UTC"
```

> A dataclass does no runtime checking — `Habit(id="not-an-int", name=123)` is accepted and
> prints `123 (active)`. What makes the Pydantic version different?

**Pydantic reads the annotations and generates a runtime validator from them.** Same declaration,
but `HabitIn(name="", timezone=123)` raises `ValidationError` with one entry per bad field:

```
('name',):     String should have at least 1 character
('timezone',): Input should be a valid string
```

This only works because **Python keeps annotations as live data** (`__annotations__`) instead of
erasing them like TypeScript. That fact was inert in Phase 2; here it's the entire mechanism.

### Pydantic ≈ Zod, with one difference

| | Zod | Pydantic |
|---|---|---|
| Schema is | a value you build — `z.object({...})` | the class's own annotations |
| Types come | inferred out (`z.infer<>`) | declared in |
| Result | parse → typed value | validate → model instance |

Zod schemas are separate artifacts you keep in sync with your types. Pydantic's *are* the types.

### `AwareDatetime` — the constraint pyright can't express

In Phase 2 I hand-wrote this because no stdlib type distinguishes naive from aware:

```python
def __post_init__(self) -> None:
    if self.at.tzinfo is None:
        raise ValueError("at must be timezone-aware")
```

Pydantic has `AwareDatetime`, which does exactly that check — **and parses ISO strings**:

```python
class CheckInIn(BaseModel):
    at: AwareDatetime

CheckInIn(at="2026-09-07T08:00:00+09:00").at   # -> aware datetime, offset preserved
CheckInIn(at=datetime(2026, 9, 7, 8, 0))       # -> ValidationError: Input should have timezone info
```

Pydantic maintains **its own type layer** on top of Python's, so a constraint a static checker
can't verify becomes a declaration again. That's the same boundary I hand-coded in `load`.

### Structured errors → 422 for free

`ValidationError.errors()` is a list of `{loc, msg, type}` dicts, not a string. FastAPI turns it
straight into an HTTP **422** body with per-field messages. An API error contract, generated.

---

## Domain models vs API schemas

| | `habits/models.py` | `habits/schemas.py` |
|---|---|---|
| What | domain objects | the HTTP contract |
| Now | dataclasses | Pydantic `BaseModel` |
| Phase 5 | SQLAlchemy ORM | **unchanged** |

> Why keep two sets of classes that look almost identical?

Because they differ where it matters. `HabitIn` has **no `id`** — the server assigns it.
`HabitOut` has one. In Phase 6 a `User` will have `password_hash` and its schema must never
expose it. Merging them means the storage shape leaks into the wire format and back.

**This is why the course picked SQLAlchemy over SQLModel** — SQLModel merges the two.

### Getting a Pydantic model from a non-Pydantic object

```python
class HabitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ...
HabitOut.model_validate(habit)      # reads attributes with getattr
```

> Without `from_attributes`, `model_validate(habit)` fails with *"Input should be a valid
> dictionary or instance of HabitOut"*. But the route worked anyway. Why?

**Two different code paths.** In a route, FastAPI runs `jsonable_encoder` on the return value
*before* validating it against the response model, and that encoder knows how to unpack a
dataclass. In my own code there's no encoder, so `model_validate` needs `from_attributes=True`.

Set it anyway: it costs one line, works outside routes (tests, CLI, background jobs), and is the
standard approach for ORM objects in Phase 5 — where betting on the encoder's fallback is a
worse idea.

(`from_attributes` was `orm_mode` / `from_orm()` in Pydantic v1. Older tutorials still say that.)

---

## Routes

### FastAPI infers the source from the type

```python
@app.post("/habits/{habit_id}/check-ins", status_code=201)
def create_check_in(store: StoreDep, habit_id: int, payload: CheckInIn) -> CheckInOut: ...
```

| Parameter | Becomes | Because |
|---|---|---|
| `payload: CheckInIn` | the JSON **body** | it's a `BaseModel` |
| `habit_id: int` | a **path** param | the name matches `{habit_id}` |
| `days: int = 30` | a **query** param | scalar, not in the path |
| `store: StoreDep` | a **dependency** | `Annotated[..., Depends(...)]` |

No decorators per parameter, no manual parsing. Query params validate the same way:
`days: Annotated[int, Query(ge=1, le=365)] = 30` → `?days=0` returns 422.

### One annotation, two consumers

```python
def read_habit(...) -> HabitOut:
    return store.get_habit(habit_id)      # returns a Habit
```

This *runs* — but pyright errors. The `-> HabitOut` annotation is read two ways:

- **FastAPI**: "serialize whatever I return into this shape." Does it.
- **pyright**: "this function returns a `HabitOut`." It doesn't.

`return HabitOut.model_validate(habit)` satisfies both, and shows a reader exactly where the
domain object becomes the HTTP contract. Better than `# type: ignore`.

---

## Dependency injection

```python
def get_store(request: Request) -> HabitStore:
    return request.app.state.store

StoreDep = Annotated[HabitStore, Depends(get_store)]

@app.get("/habits")
def list_habits(store: StoreDep) -> list[HabitOut]: ...
```

> Why not just reference a module-level `store`?

Because the route can't then be given a *different* store. `Depends` is **`useContext`**: the
route declares what it needs by type, the framework supplies it, and a test swaps the provider:

```python
app.dependency_overrides[get_store] = lambda: HabitStore()
```

Routes are untouched and don't know the difference. Without this, every test shares one store and
results depend on which tests ran first.

### `Annotated[X, Depends(f)]`, not `x: X = Depends(f)`

The old spelling puts the wiring in the **default value** slot — which lies to pyright (there is
no real default) and can't be reused. `Annotated` attaches metadata to the *type*, so `StoreDep`
is a normal alias written once.

---

## One exception handler beats four `try/except`

```python
@app.exception_handler(HabitNotFound)
def handle_habit_not_found(request: Request, exc: HabitNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})
```

Every `try/except HabitNotFound` in every route deleted itself, and `read_habit` collapsed to one
line. **New routes get correct 404s automatically — including the one I'd already forgotten**
(`/stats` was returning 500).

Two things made this possible:

- **`HabitNotFound` is a specific type**, so the framework can dispatch on it. `raise
  Exception("not found")` would leave nothing to register a handler *for*.
- **`str(exc)` already says the right thing**, because of the `super().__init__(f"No habit with
  id {habit_id}")` written in Phase 2. The message got *better* for free — `"No habit with id
  999"` instead of a hardcoded `"Habit not found"`.

It also enforces the layering: `store.py` raises domain errors and knows nothing about HTTP;
`main.py` owns the error → status mapping, in exactly one place.

---

## `async def` vs `def`

Four concurrent requests, each handler doing a blocking `time.sleep(0.5)`, against real uvicorn:

| Handler | 4 concurrent requests |
|---|---|
| `def` (plain) | **0.54s** — ran in parallel |
| `async def` | **2.03s** — fully serialized |

> Why is the `async` one 4× slower?

**FastAPI runs plain `def` handlers in a threadpool and `async def` handlers directly on the
event loop.** A blocking call inside `async def` stalls *every other request in the process*, so
the four queued at 0.5s each. The same call in a plain `def` was moved off the loop.

**Use `async def` only when the body actually `await`s something.** Blocking work — sync DB
drivers, file I/O, CPU — belongs in a plain `def`, where the threadpool is the safety net.

This is genuinely different from Node, which has one event loop and no escape hatch for your own
code — so everything there is async by necessity. FastAPI picks the execution strategy from the
keyword, which is why "should this be async?" is a real question here and never one in Express.

My routes are plain `def`: `HabitStore` is in-memory and synchronous, so there is nothing to
await. That changes in Phase 5 **only if the driver is async** — driven by the driver, not taste.

---

## Lifecycle

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    path = Path(os.getenv("HABITS_DB", "data/habits.json"))
    try:
        app.state.store = HabitStore.load(path)
    except FileNotFoundError:
        app.state.store = HabitStore()      # first run: empty is correct
    yield
    app.state.store.save(path)

app = FastAPI(title="Habits", lifespan=lifespan)
```

### The same shape, for the third time

| Where | Setup | Teardown |
|---|---|---|
| `with` / `__enter__`/`__exit__` (Phase 2) | before | after |
| `@pytest.fixture` with `yield` (Phase 3) | before `yield` | after `yield` |
| `@asynccontextmanager` lifespan (Phase 4) | before `yield` | after `yield` |

**Setup → hand control away → teardown.** `@asynccontextmanager` builds one from a generator the
same way `@pytest.fixture` does. Recognising this as one pattern rather than three APIs is most
of what "Pythonic" means here.

(`lifespan` replaces the deprecated `@app.on_event("startup")` decorators. Better because setup
and teardown live in one function, so a resource opened at the top is closed where I can see it.)

### `app.state` sidesteps the rebinding trap

`app.state.store = ...` is **attribute assignment on an object**, not a name binding — so the
"assignment makes it local" rule never applies. General escape hatch: **mutate an object instead
of rebinding a name.** See lesson 21.

Starlette's `State` *raises* for a missing attribute rather than returning `None`, so a lifespan
that didn't run fails loudly on the first request instead of silently serving an empty store.

---

## Testing the HTTP layer

### `with` runs the lifespan; the plain constructor doesn't

```python
TestClient(app)              # no lifespan  -> unit-ish, never touches the real data file
with TestClient(app) as c:   # runs startup AND shutdown -> real restart behaviour
```

That's how I verified persistence across a restart without starting a server — and why my 43
existing tests still pass untouched.

### Test what this layer adds, not the domain again

| The HTTP layer's job | Test |
|---|---|
| Parse & validate the body | POST bad input → **422** |
| Map success to a status | POST → **201**, GET → **200** |
| Translate domain errors | GET unknown id → **404** |
| Shape the response JSON | assert `response.json() == {...}` |
| Isolate requests | every test starts from an empty store |

**If a test would still make sense with the web framework deleted, it belongs in
`test_store.py`.** Streak maths and timezone conversion are already covered — don't re-test them
through HTTP.

### Assert the whole body

```python
assert response.json() == {"id": 1, "name": "run", "archived": False, "timezone": "Asia/Tokyo"}
```

One `==` catches a removed key, a renamed key, **and an extra key I didn't mean to expose** —
which is the `password_hash` bug waiting in Phase 6. Field-by-field asserts only check what I
remembered to look at. pytest prints a full dict diff on failure.

For *client errors*, assert the status code only — `detail == "Habit not found"` just pins down
prose I'll want to reword.

### Write the failing test first

`test_stats_unknown_habit_returns_404` was written while `/stats` still returned 500. **A test
I've watched fail for the right reason is proof it's wired to the thing I think it is.** A test
written after the fix only asserts that today's code does what today's code does.
