from datetime import datetime, time

from app.services.daily_fetch import parse_local_fetch_time, seconds_until_next_fetch


def test_parse_local_fetch_time():
    assert parse_local_fetch_time("22:30") == time(22, 30)
    assert parse_local_fetch_time("7:05") == time(7, 5)


def test_next_fetch_is_same_day_before_slot():
    # 2026-07-10 21:30 in Los Angeles == 2026-07-11 04:30 UTC (PDT, UTC-7).
    now_utc = datetime(2026, 7, 11, 4, 30)

    delay = seconds_until_next_fetch(now_utc, "America/Los_Angeles", time(22, 30))

    assert delay == 3600


def test_next_fetch_rolls_to_tomorrow_after_slot():
    # 2026-07-10 23:00 in Los Angeles == 2026-07-11 06:00 UTC.
    now_utc = datetime(2026, 7, 11, 6, 0)

    delay = seconds_until_next_fetch(now_utc, "America/Los_Angeles", time(22, 30))

    assert delay == 23.5 * 3600


def test_exact_slot_schedules_next_day():
    now_utc = datetime(2026, 7, 11, 5, 30)  # exactly 22:30 local

    delay = seconds_until_next_fetch(now_utc, "America/Los_Angeles", time(22, 30))

    assert delay == 24 * 3600
