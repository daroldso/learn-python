from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class HabitIn(BaseModel):
    name: str = Field(min_length=1)
    timezone: str = "UTC"


class HabitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    archived: bool
    timezone: str = "UTC"


class CheckInIn(BaseModel):
    at: AwareDatetime
    note: str | None = None


class CheckInOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    habit_id: int
    at: AwareDatetime
    note: str | None = None


class StatsOut(BaseModel):
    current_streak: int
    longest_streak: int
    completion_rate: float
