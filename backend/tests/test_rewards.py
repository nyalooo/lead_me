"""Tests for rewards service logic."""

from datetime import datetime, timezone

from app.services.rewards.service import (
    calculate_reward,
    get_next_milestone,
    get_streak_multiplier,
)


def test_streak_multiplier_no_streak():
    assert get_streak_multiplier(0) == 1.0
    assert get_streak_multiplier(2) == 1.0


def test_streak_multiplier_3_day():
    assert get_streak_multiplier(3) == 1.5
    assert get_streak_multiplier(6) == 1.5


def test_streak_multiplier_7_day():
    assert get_streak_multiplier(7) == 2.0
    assert get_streak_multiplier(13) == 2.0


def test_streak_multiplier_14_day():
    assert get_streak_multiplier(14) == 2.5


def test_streak_multiplier_30_day():
    assert get_streak_multiplier(30) == 3.0
    assert get_streak_multiplier(100) == 3.0


def test_next_milestone_from_zero():
    milestone = get_next_milestone(0)
    assert milestone == {"days": 3, "multiplier": 1.5}


def test_next_milestone_after_3():
    milestone = get_next_milestone(5)
    assert milestone == {"days": 7, "multiplier": 2.0}


def test_next_milestone_at_max():
    milestone = get_next_milestone(30)
    assert milestone is None


def test_calculate_reward_basic():
    reward = calculate_reward(detour_percent=0, current_streak=0)
    assert reward.base_coins == 10
    assert reward.total_coins == 10


def test_calculate_reward_with_detour():
    reward = calculate_reward(detour_percent=15.0, current_streak=0)
    # detour_multiplier = 1.0 + (15/15) = 2.0
    assert reward.detour_multiplier == 2.0
    assert reward.total_coins == 20


def test_calculate_reward_with_streak():
    reward = calculate_reward(detour_percent=0, current_streak=7)
    assert reward.streak_multiplier == 2.0
    assert reward.total_coins == 20


def test_calculate_reward_peak_hour():
    peak_time = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    reward = calculate_reward(detour_percent=0, current_streak=0, departure_time=peak_time)
    assert reward.peak_multiplier == 2.0
    assert reward.total_coins == 20


def test_calculate_reward_all_multipliers():
    peak_time = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)
    reward = calculate_reward(detour_percent=7.5, current_streak=7, departure_time=peak_time)
    # base=10, detour=1.5, streak=2.0, peak=2.0
    # 10 * 1.5 * 2.0 * 2.0 = 60
    assert reward.total_coins == 60
