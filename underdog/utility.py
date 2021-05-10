import bisect
import datetime

from typing import (
    Generator, Optional, Union
)

import pandas as pd
import pandas_market_calendars as mcal

from underdog.schema import (
    Timespan,
    TradingSegment
)

_dates = [
    date.date()
    for date in mcal.get_calendar('NYSE').valid_days(
        start_date = '1990-01-01',
        end_date = '2030-01-01'
    )
]

def _resolve_date(when: Optional[Union[str, datetime.date]] = None) -> datetime.date:
    if not when:
        return datetime.datetime.today().date()
    if isinstance(when, str):
        return datetime.datetime.strptime(when, '%Y-%m-%d').date()
    return when

def today() -> datetime.date:
    return datetime.datetime.now().date()

def is_trading_date(when: Optional[Union[str, datetime.date]] = None) -> bool:
    return _resolve_date(when) in _dates

def trading_days_between(
    start: Union[str, datetime.date],
    end: Optional[Union[str, datetime.date]] = None
) -> int:
    start, end = (_resolve_date(start), _resolve_date(end))
    start_index = bisect.bisect_right(_dates, start) - 1
    end_index = bisect.bisect_left(_dates, end)
    if _dates[start_index] != start:
        start_index += 1
    if _dates[end_index] == end:
        end_index += 1
    return end_index - start_index - 1

def nth_next_trading_date(
    n: int = 1,
    anchor: Optional[Union[str, datetime.date]] = None
) -> datetime.date:
    anchor = _resolve_date(anchor)
    if n < 0:
        raise ValueError()
    if n == 0:
        return anchor
    start_index = bisect.bisect_left(_dates, anchor)
    return _dates[start_index + n]

def nth_previous_trading_date(
    n: int = 1,
    anchor: Optional[Union[str, datetime.date]] = None
) -> datetime.date:
    anchor = _resolve_date(anchor)
    if n < 0:
        raise ValueError()
    if n == 0:
        return anchor
    start_index = bisect.bisect_left(_dates, anchor)
    return _dates[start_index - n]

def timestamp_to_timeslot(
    timestamp: pd.Timestamp,
    timespan: Timespan = Timespan.Minute,
    period: int = 1
) -> int:
    assert timespan.value == Timespan.Minute.value or timespan.value == Timespan.Hour.value
    base_timestamp = pd.Timestamp(
        year = timestamp.year,
        month = timestamp.month,
        day = timestamp.day,
        hour = 4, minute = 0, second = 0, tz = 'US/Eastern'
    )
    timeslot = timestamp - base_timestamp
    if timespan.value == Timespan.Minute.value:
        seconds_divisor = 60 * period
    else:
        seconds_divisor = 3600 * period
    return int(timeslot.seconds / seconds_divisor)

def timeslot_to_timestamp(
    timeslot:int,
    timespan: Timespan = Timespan.Minute,
    period: int = 1
) -> Optional[pd.Timestamp]:
    if timespan.value != Timespan.Minute.value and timespan.value != Timespan.Hour.value:
        return None
    current = datetime.datetime.now().date()
    opents = pd.Timestamp(
        year = current.year,
        month = current.month,
        day = current.day,
        hour = 4, minute = 0, second = 0, tz = 'US/Eastern'
    )
    duration = 60 * period if timespan.value == Timespan.Minute.value else 3600 * period
    return opents + pd.Timedelta(timeslot * duration, unit = 'seconds')

def trading_daterange(
    start: Union[str, datetime.date],
    end: Optional[Union[str, datetime.date]] = None
) -> Generator[datetime.date, None, None]:
    start, end = (_resolve_date(start), _resolve_date(end))
    start_index = bisect.bisect_right(_dates, start) - 1
    end_index = bisect.bisect_left(_dates, end)
    if _dates[start_index] != start:
        start_index += 1
    if _dates[end_index] == end:
        end_index += 1
    for i in range(start_index, end_index):
        yield _dates[i]

def datestr_from_date(date: datetime.date) -> str:
    return date.strftime('%Y-%m-%d')

def date_from_datestr(datestr: str) -> datetime.date:
    return datetime.datetime.strptime(datestr, '%Y-%m-%d').date()

def market_open() -> bool:
    return get_trading_segment() != TradingSegment.Closed

def market_closed() -> bool:
    return get_trading_segment() == TradingSegment.Closed

def get_trading_segment(timestamp: Optional[pd.Timestamp] = None) -> TradingSegment:
    if timestamp is None:
        timestamp = pd.Timestamp.now(tz = 'US/Eastern')
    assert str(timestamp.tz) == 'US/Eastern'
    if timestamp.hour >= 16 and timestamp.hour < 20:
        return TradingSegment.ExtendedHours
    if (timestamp.hour >= 4) and (timestamp.hour < 9 or \
    (timestamp.hour == 9 and timestamp.minute < 30)):
        return TradingSegment.PreMarket
    if timestamp.hour < 16 and ((timestamp.hour == 9 and timestamp.minute >= 30) \
    or (timestamp.hour > 9)):
        return TradingSegment.RegularHours
    return TradingSegment.Closed
