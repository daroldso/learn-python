from typing import TypedDict


def count_done(days: list[bool]) -> int:
    return sum(days)


class DescribeHabitDict(TypedDict):
    name: str
    streak: int


def describe(habit: DescribeHabitDict) -> str:
    return f"{habit['name']}: {habit['streak']} day streak"


def first_or_none(items: list[str]) -> str | None:
    if items:
        return items[0]
    else:
        return None


class HabitDict(TypedDict):
    name: str
    archived: bool


def active_names(habits: list[HabitDict]) -> list[str]:
    names = [habit["name"] for habit in habits if not habit["archived"]]
    return names


if __name__ == "__main__":
    print(count_done([True, False, True]))
    print(describe({"name": "run", "streak": 5}))
    print(first_or_none(["1"]))
    print(first_or_none([]))
    print(
        active_names(
            [
                {"name": "run", "archived": True},
                {"name": "walk", "archived": False},
                {"name": "play", "archived": False},
                {"name": "swim", "archived": True},
            ]
        )
    )
