from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

Rating = Literal["again", "hard", "good", "easy"]

Quality: dict[Rating, int] = {"again": 1, "hard": 3, "good": 4, "easy": 5}

MIN_EASE = 1.3
RELEARN_DELAY = timedelta(minutes=10)

@dataclass
class CardSchedule:
    ease_factor: float
    interval_days: int
    repetitions: int
    due_at: datetime

def schedule_review(current: CardSchedule, rating : Rating, now: datetime) -> CardSchedule:
    quality = Quality[rating]

    if quality < 3:
        repetitions = 0
        interval_days = 0
        due_at = now + RELEARN_DELAY
    else:
        if current.repetitions == 0:
            interval_days = 1
        elif current.repetitions == 1:
            interval_days = 6
        else:
            interval_days = round(current.interval_days * current.ease_factor)
        repetitions = current.repetitions + 1
        due_at = now + timedelta(days=interval_days)

    ease_factor = current.ease_factor + (0.1-(5-quality)*(0.08 + (5-quality)*0.02))
    ease_factor = max(MIN_EASE, round(ease_factor, 2))

    return CardSchedule(
        ease_factor=ease_factor,
        interval_days=interval_days,
        repetitions=repetitions,
        due_at=due_at,
    )