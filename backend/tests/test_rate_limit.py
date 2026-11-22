import pytest
from fastapi import HTTPException
from app.config import settings
from app.models import User
from app.rate_limit import rate_limit

class FakeRedis:
    def __init__(self):
        self.store: dict[str, int] = {}

    def set(self, key, value, ex=None, nx=None):
        if nx and key in self.store:
            return None
        self.store[key] = value
        return True

    def incr(self, key):
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    def ttl(self, key):
        return 60


def test_requests_over_the_limit_are_rejected(monkeypatch):
    monkeypatch.setattr("app.rate_limit.redis_client", FakeRedis())
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    check = rate_limit("test", limit=3, window_seconds=60)
    user = User(id=1, email="a@example.com", hashed_password="x")

    for _ in range(3):
        assert check(current_user=user) is user

    with pytest.raises(HTTPException) as error:
        check(current_user=user)

    assert error.value.status_code == 429
    assert error.value.headers["Retry-After"] == 60


def test_limits_are_counted_separately_per_user(monkeypatch):
    monkeypatch.setattr("app.rate_limit.redis_client", FakeRedis())
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    check = rate_limit("test", limit=1, window_seconds=60)

    check(current_user=User(id=1, email="a@example.com", hashed_password="x"))
    check(current_user=User(id=2, email="b@example.com", hashed_password="x"))