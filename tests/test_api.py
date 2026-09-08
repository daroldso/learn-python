from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from habits.api.main import app, get_store
from habits.store import HabitStore


@pytest.fixture
def client() -> Iterator[TestClient]:
    fresh = HabitStore()
    app.dependency_overrides[get_store] = lambda: fresh
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_habit_returns_201(client: TestClient) -> None:
    response = client.post("/habits", json={"name": "run", "timezone": "Asia/Tokyo"})

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "run",
        "archived": False,
        "timezone": "Asia/Tokyo",
    }


def test_unknown_habit_returns_404(client: TestClient) -> None:
    response = client.get("/habits/999")

    assert response.status_code == 404


def test_create_habit_defaults_timezone(client: TestClient) -> None:
    response = client.post("/habits", json={"name": "run"})

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "run",
        "archived": False,
        "timezone": "UTC",
    }


def test_list_starts_empty(client: TestClient) -> None:
    response = client.get("/habits")

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_created_habits(client: TestClient) -> None:
    client.post("/habits", json={"name": "run"})
    client.post("/habits", json={"name": "swim"})
    response = client.get("/habits")

    assert response.json() == [
        {
            "id": 1,
            "name": "run",
            "archived": False,
            "timezone": "UTC",
        },
        {
            "id": 2,
            "name": "swim",
            "archived": False,
            "timezone": "UTC",
        },
    ]


def test_create_habit_empty_name_returns_422(client: TestClient) -> None:
    response = client.post("/habits", json={"name": ""})

    assert response.status_code == 422


def test_create_check_in_returns_201(client: TestClient) -> None:
    client.post("/habits", json={"name": "run"})
    response = client.post(
        "/habits/1/check-ins",
        json={"at": "2026-09-08T08:00:00+09:00", "note": "morning"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "habit_id": 1,
        "at": "2026-09-08T08:00:00+09:00",
        "note": "morning",
    }


def test_check_in_unknown_habit_returns_404(client: TestClient) -> None:
    response = client.post(
        "/habits/999/check-ins",
        json={"at": "2026-09-08T08:00:00+09:00", "note": "morning"},
    )

    assert response.status_code == 404


def test_stats_unknown_habit_returns_404(client: TestClient) -> None:
    response = client.get(
        "/habits/999/stats",
    )
    assert response.status_code == 404


def test_stats_rejects_invalid_days(client: TestClient) -> None:
    client.post("/habits", json={"name": "run"})
    response = client.get(
        "/habits/1/stats?days=0",
    )

    assert response.status_code == 422


def test_get_stats(client: TestClient) -> None:
    response = client.post("/habits", json={"name": "run"})

    print(
        client.post(
            "/habits/1/check-ins",
            json={"at": "2026-09-07T20:00:00+09:00"},
        ).json()
    )
    client.post(
        "/habits/1/check-ins",
        json={"at": "2026-09-08T20:00:00+09:00"},
    )
    response = client.get("/habits/1/stats?days=4")
    stats = response.json()
    print("stats:", stats)
    assert stats["current_streak"] == 2
    assert stats["longest_streak"] == 2
    assert stats["completion_rate"] == 0.5
