def count_done(days):
    return sum(days)


def describe(habit):
    return f"{habit['name']}: {habit['streak']} day streak"


def first_or_none(items):
    if items:
        return items[0]
    else:
        return None


def active_names(habits):
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
                {"name": "play", "archived": 0},
                {"name": "swim", "archived": 1},
            ]
        )
    )
