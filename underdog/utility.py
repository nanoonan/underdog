import bisect
import datetime
import math

from typing import (
    Generator, Optional, Union
)

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

from parkit import Frequency

_dates = [
    date.date()
    for date in mcal.get_calendar('NYSE').valid_days(
        start_date = '1990-01-01',
        end_date = '2030-01-01'
    )
]

def symbol_to_float(symbol: str) -> np.float64:
    return np.float64(int.from_bytes(symbol.upper().encode(), 'little'))

def float_to_symbol(encoded: np.float64) -> str:
    value = int(encoded)
    return value.to_bytes(math.ceil(value.bit_length() / 8), 'little').decode()

def twap(df: pd.DataFrame) -> pd.DataFrame:
    oh = np.abs(df['open'] - df['high'])
    ol = np.abs(df['open'] - df['low'])
    hl = np.abs(df['high'] - df['low'])
    lc = np.abs(df['low'] - df['close'])
    hc = np.abs(df['high'] - df['close'])
    ohlc = oh + hl + lc
    olhc = ol + hl + hc
    ohmean = (df['open'] + df['high']) / 2
    olmean = (df['open'] + df['low']) / 2
    hlmean = (df['high'] + df['low']) / 2
    lcmean = (df['low'] + df['close']) / 2
    hcmean = (df['high'] + df['close']) / 2
    ohlctwap = (oh / ohlc) * ohmean + (hl / ohlc) * hlmean + (lc / ohlc) * lcmean
    olhctwap = (ol / olhc) * olmean + (hl / olhc) * hlmean + (hc / olhc) * hcmean
    df['twap'] = (ohlctwap + olhctwap) / 2
    df['twap'] = np.where(
        df['twap'].isnull(),
        df['close'], df['twap']
    )
    return df

def resolve_date(when: Optional[Union[str, datetime.date]] = None) -> datetime.date:
    if not when:
        return datetime.datetime.today().date()
    if isinstance(when, str):
        return datetime.datetime.strptime(when, '%Y-%m-%d').date()
    return when

def is_trading_date(when: Optional[Union[str, datetime.date]] = None) -> bool:
    return resolve_date(when) in _dates

def trading_days_between(
    start: Union[str, datetime.date],
    end: Optional[Union[str, datetime.date]] = None
) -> int:
    start, end = (resolve_date(start), resolve_date(end))
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
    anchor = resolve_date(anchor)
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
    anchor = resolve_date(anchor)
    if n < 0:
        raise ValueError()
    if n == 0:
        return anchor
    start_index = bisect.bisect_left(_dates, anchor)
    return _dates[start_index - n]

def timestamp_to_timeslot(
    timestamp: pd.Timestamp,
    frequency: Frequency = Frequency.MINUTE,
    period: int = 1
) -> int:
    assert frequency in [Frequency.MINUTE, Frequency.HOUR]
    base_timestamp = pd.Timestamp(
        year = timestamp.year,
        month = timestamp.month,
        day = timestamp.day,
        hour = 4, minute = 0, second = 0, tz = 'US/Eastern'
    )
    timeslot = timestamp - base_timestamp
    if frequency.value == Frequency.MINUTE.value:
        seconds_divisor = 60 * period
    else:
        seconds_divisor = 3600 * period
    return int(timeslot.seconds / seconds_divisor)

def timeslot_to_timestamp(
    timeslot: int,
    frequency: Frequency = Frequency.MINUTE,
    period: int = 1,
    date: pd.Timestamp = pd.Timestamp.now()
) -> Optional[pd.Timestamp]:
    if frequency.value != Frequency.MINUTE.value and frequency.value != Frequency.HOUR.value:
        return None
    opents = pd.Timestamp(
        year = date.year,
        month = date.month,
        day = date.day,
        hour = 4, minute = 0, second = 0, tz = 'US/Eastern'
    )
    duration = 60 * period if frequency.value == Frequency.MINUTE.value else 3600 * period
    return opents + pd.Timedelta(timeslot * duration, unit = 'seconds')

def trading_daterange(
    start: Union[str, datetime.date],
    end: Optional[Union[str, datetime.date]] = None
) -> Generator[datetime.date, None, None]:
    start, end = (resolve_date(start), resolve_date(end))
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

def isfinite(x):
    return not np.isnan(x) and not np.isneginf(x) and not np.isposinf(x)

# def twap_(o, h, l, c):
#     oh = np.abs(o - h)
#     ol = np.abs(o - l)
#     hl = np.abs(h - l)
#     lc = np.abs(l - c)
#     hc = np.abs(h - c)
#     ohlc = oh + hl + lc
#     olhc = ol + hl + hc
#     ohmean = (o + h) / 2
#     olmean = (o + l) / 2
#     hlmean = (h + l) / 2
#     lcmean = (l + c) / 2
#     hcmean = (h + c) / 2
#     ohlctwap = (oh / ohlc) * ohmean + (hl / ohlc) * hlmean + (lc / ohlc) * lcmean
#     olhctwap = (ol / olhc) * olmean + (hl / olhc) * hlmean + (hc / olhc) * hcmean
#     return (ohlctwap + olhctwap) / 2

# def resample(
#     df: pd.DataFrame,
#     period: int
# ) -> pd.DataFrame:
#     return df
#     if period not in [1, 5, 30]:
#         df = df.set_index('timestamp')
#         rule = '{0}T'.format(period)
#         df = df.resample(rule).aggregate(dict(
#             open = 'first',
#             close = 'last',
#             low = 'min',
#             high = 'max',
#             volume = 'sum',
#             date = 'first',
#             symbol = 'first'
#         )).dropna().reset_index(drop = False)
#         df = twap(df)
#         df['trading_segment'] = df['timestamp'] \
#         .apply(get_trading_segment)
#         df['timeslot'] = df['timestamp'] \
#         .apply(lambda x: timestamp_to_timeslot(x, period = period))
#     return df
