import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from habits.schemas import CheckInIn, CheckInOut, HabitIn, HabitOut, StatsOut
from habits.store import HabitNotFound, HabitStore
from habits.streaks import completion_rate, current_streak, longest_streak


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    path = Path(os.getenv("HABITS_DB", "data/habits.json"))
    try:
        app.state.store = HabitStore.load(path)
    except FileNotFoundError:
        app.state.store = HabitStore()  # first run: empty is correct
    yield
    app.state.store.save(path)


def get_store(request: Request) -> HabitStore:
    return request.app.state.store


app = FastAPI(title="Habits", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HabitNotFound)
def handle_habit_not_found(request: Request, exc: HabitNotFound) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


StoreDep = Annotated[HabitStore, Depends(get_store)]


@app.get("/habits")
def list_habits(store: StoreDep) -> list[HabitOut]:
    return [HabitOut.model_validate(h) for h in store.habits.values()]


@app.post("/habits", status_code=201)
def create_habit(store: StoreDep, payload: HabitIn) -> HabitOut:
    habit = store.add_habit(name=payload.name, timezone=payload.timezone)
    return HabitOut.model_validate(habit)


@app.get("/habits/{habit_id}")
def read_habit(store: StoreDep, habit_id: int) -> HabitOut:
    return HabitOut.model_validate(store.get_habit(habit_id))


@app.post("/habits/{habit_id}/check-ins", status_code=201)
def create_check_in(store: StoreDep, habit_id: int, payload: CheckInIn) -> CheckInOut:
    return CheckInOut.model_validate(
        store.check_in(habit_id=habit_id, at=payload.at, note=payload.note)
    )


@app.get("/habits/{habit_id}/stats")
def read_stats(
    store: StoreDep, habit_id: int, days: Annotated[int, Query(ge=1, le=365)] = 30
) -> StatsOut:
    check_ins = store.days_for(habit_id=habit_id)
    habit = store.get_habit(habit_id=habit_id)
    today = datetime.now(ZoneInfo(habit.timezone)).date()
    return StatsOut(
        current_streak=current_streak(check_ins=check_ins, today=today),
        longest_streak=longest_streak(check_ins=check_ins),
        completion_rate=completion_rate(
            check_ins=check_ins, end=today, start=today - timedelta(days=days - 1)
        ),
    )
