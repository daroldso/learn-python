from datetime import date

from habits.models import CheckIn, Habit


class HabitStore:
    habits: dict[int, Habit]
    check_ins: list[CheckIn]

    def __init__(self) -> None:
        self.habits = {}
        self.check_ins = []

    def add_habit(self, name: str) -> Habit:
        latest_id = max(self.habits.keys(), default=0)
        habit = Habit(latest_id + 1, name)
        self.habits[habit.id] = habit
        return habit

    def get_habit(self, habit_id: int) -> Habit:
        try:
            return self.habits[habit_id]
        except KeyError:
            raise HabitNotFound(habit_id) from None

    def check_in(self, habit_id: int, day: date, note: str | None = None) -> CheckIn:
        self.get_habit(habit_id)
        check_in = CheckIn(habit_id, day, note)
        self.check_ins.append(check_in)
        return check_in

    def days_for(self, habit_id: int) -> list[date]:
        return [
            check_in.day for check_in in self.check_ins if check_in.habit_id == habit_id
        ]


class HabitNotFound(Exception):
    def __init__(self, habit_id: int) -> None:
        super().__init__(f"No habit with id {habit_id}")
        self.habit_id = habit_id
