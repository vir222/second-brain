from datetime import datetime, timedelta, timezone

from app.srs import CardSchedule, schedule_review

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

def new_card() -> CardSchedule:
    return CardSchedule(ease_factor=2.5, interval_days=0, repetitions=0, due_at=NOW)

def test_first_good_review_schedules_one_day():
    result = schedule_review(new_card(), "good", NOW)
    assert result.interval_days == 1
    assert result.repetitions == 1
    assert result.due_at == NOW + timedelta(days=1)

def test_intervals_grow_with_ease():
    card = new_card()
    intervals = []
    for _ in range(3):
        card = schedule_review(card, "good", NOW)
        intervals.append(card.interval_days)

    assert intervals == [1,6,15]

def test_again_resets_streak_and_returns_soon():
    card = schedule_review(new_card(), "good", NOW)
    card = schedule_review(new_card(), "again", NOW)

    assert card.repetitions == 0
    assert card.due_at == NOW + timedelta(minutes=10)

def test_ease_never_drops_below_minimum():
    card = new_card()
    for _ in range(10):
        card = schedule_review(card, "again", NOW)

    assert card.ease_factor == 1.3

