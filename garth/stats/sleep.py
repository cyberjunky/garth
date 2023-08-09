from datetime import date, datetime
from typing import ClassVar, Optional

import pytz
from pydantic.dataclasses import dataclass

from .. import http
from ..utils import camel_to_snake_dict, date_range, format_end_date
from ._base import Stats


@dataclass(frozen=True)
class DailySleep(Stats):
    value: int

    _path: ClassVar[
        str
    ] = "/wellness-service/stats/daily/sleep/score/{start}/{end}"
    _page_size: ClassVar[int] = 28


@dataclass(frozen=True)
class Score:
    qualifier_key: str
    optimal_start: Optional[float] = None
    optimal_end: Optional[float] = None
    value: Optional[int] = None
    ideal_start_in_seconds: Optional[float] = None
    ideal_end_in_seconds: Optional[float] = None


@dataclass(frozen=True)
class SleepScores:
    total_duration: Score
    stress: Score
    awake_count: Score
    overall: Score
    rem_percentage: Score
    restlessness: Score
    light_percentage: Score
    deep_percentage: Score


@dataclass(frozen=True)
class DailySleepDTO:
    id: int
    user_profile_pk: int
    calendar_date: date
    sleep_time_seconds: int
    nap_time_seconds: int
    sleep_window_confirmed: bool
    sleep_window_confirmation_type: str
    sleep_start_timestamp_gmt: datetime
    sleep_end_timestamp_gmt: datetime
    sleep_start_timestamp_local: datetime
    sleep_end_timestamp_local: datetime
    unmeasurable_sleep_seconds: int
    deep_sleep_seconds: int
    light_sleep_seconds: int
    rem_sleep_seconds: int
    awake_sleep_seconds: int
    device_rem_capable: bool
    retro: bool
    sleep_from_device: bool
    sleep_version: int
    awake_count: Optional[int] = None
    sleep_scores: Optional[SleepScores] = None
    auto_sleep_start_timestamp_gmt: Optional[datetime] = None
    auto_sleep_end_timestamp_gmt: Optional[datetime] = None
    sleep_quality_type_pk: Optional[int] = None
    sleep_result_type_pk: Optional[int] = None
    average_sp_o2_value: Optional[float] = None
    lowest_sp_o2_value: Optional[int] = None
    highest_sp_o2_value: Optional[int] = None
    average_sp_o2_hr_sleep: Optional[float] = None
    average_respiration_value: Optional[float] = None
    lowest_respiration_value: Optional[float] = None
    highest_respiration_value: Optional[float] = None
    avg_sleep_stress: Optional[float] = None
    age_group: Optional[str] = None
    sleep_score_feedback: Optional[str] = None
    sleep_score_insight: Optional[str] = None

    def __post_init__(self):
        # Calculate timezone offset in minutes from the sleep_start_timestamps
        timedelta_offset_start = (
            self.sleep_start_timestamp_local - self.sleep_start_timestamp_gmt
        )
        offset_minutes_start = int(timedelta_offset_start.total_seconds() / 60)
        fixed_tz_start = pytz.FixedOffset(offset_minutes_start)

        # Calculate timezone offset in minutes from the sleep_end_timestamps
        timedelta_offset_end = (
            self.sleep_end_timestamp_local - self.sleep_end_timestamp_gmt
        )
        offset_minutes_end = int(timedelta_offset_end.total_seconds() / 60)
        fixed_tz_end = pytz.FixedOffset(offset_minutes_end)

        # Use object.__setattr__ since the dataclass is frozen
        object.__setattr__(
            self,
            "sleep_start_timestamp_local",
            self.sleep_start_timestamp_local.replace(tzinfo=fixed_tz_start),
        )
        object.__setattr__(
            self,
            "sleep_end_timestamp_local",
            self.sleep_end_timestamp_local.replace(tzinfo=fixed_tz_end),
        )


@dataclass(frozen=True)
class SleepMovement:
    start_gmt: datetime
    end_gmt: datetime
    activity_level: float


@dataclass(frozen=True)
class SleepData:
    daily_sleep_dto: DailySleepDTO
    sleep_movement: list[SleepMovement]

    @classmethod
    def get(cls, day: date | str, *, client: Optional[http.Client] = None):
        client = client or http.client
        path = (
            f"/wellness-service/wellness/dailySleepData/{client.username}?"
            f"nonSleepBufferMinutes=60&date={day}"
        )
        sleep_data = client.connectapi(path)
        assert sleep_data
        sleep_data = camel_to_snake_dict(sleep_data)
        return cls(**sleep_data)

    @classmethod
    def list(
        cls,
        end: date | str | None = None,
        days: int = 1,
        *,
        client: http.Client | None = None,
    ):
        client = client or http.client
        end = format_end_date(end)
        sleep_data = [
            cls.get(date_, client=client) for date_ in date_range(end, days)
        ]
        return sorted(
            sleep_data, key=lambda x: x.daily_sleep_dto.calendar_date
        )
