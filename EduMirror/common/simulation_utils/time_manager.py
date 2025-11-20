from datetime import datetime, timedelta
from typing import Sequence

from concordia.clocks.game_clock import FixedIntervalClock, MultiIntervalClock


def create_fixed_interval_clock(start: datetime | None = None, step_minutes: int = 10) -> FixedIntervalClock:
    step_size = timedelta(minutes=step_minutes)
    return FixedIntervalClock(start=start, step_size=step_size)


def create_multi_interval_clock(start: datetime | None = None, step_sizes: Sequence[timedelta] = (timedelta(minutes=10),)) -> MultiIntervalClock:
    return MultiIntervalClock(start=start, step_sizes=tuple(step_sizes))


def advance(clock) -> None:
    clock.advance()


def set_time(clock, time: datetime) -> None:
    clock.set(time)


def now(clock) -> datetime:
    return clock.now()


def current_interval_str(clock) -> str:
    return clock.current_time_interval_str()