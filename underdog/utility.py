import bisect
import datetime
import functools
import struct
import time
import typing

from typing import (
    Generator, List, Optional, Tuple, Union
)

import bitarray
import bitarray.util
import numba
import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
import parkit.constants

from parkit import (
    Dict,
    get_site_uuid,
    getenv,
    import_site,
    Frequency
)

import underdog.constants as constants

import_site(
    getenv(parkit.constants.GLOBAL_SITE_STORAGE_PATH_ENVNAME, str),
    create = True
)

cache = Dict(
    'memory/underdog/cache',
    create = True, bind = True,
    site_uuid = get_site_uuid(
        getenv(parkit.constants.GLOBAL_SITE_STORAGE_PATH_ENVNAME, str)
    )
)

@functools.lru_cache(None)
def market_dates() -> List[datetime.date]:
    if 'market_dates' not in cache:
        cache['market_dates'] = [
            date.date()
            for date in mcal.get_calendar('NYSE').valid_days(
                start_date = constants.MARKET_CALENDAR_START_DATE,
                end_date = constants.MARKET_CALENDAR_END_DATE
            )
        ]
    return cache['market_dates']

def as_pandas(
    array: Optional[np.ndarray],
    human: bool = False
) -> Optional[pd.DataFrame]:
    if array is not None:
        assert array.dtype == np.float64
        if array.shape[1] == 9:
            df = pd.DataFrame(columns = [
                'symbol', 'volume', 'vwap',
                'open', 'close', 'high', 'low',
                'date', 'twap'
            ], data = array)
        elif array.shape[1] == 8:
            df = pd.DataFrame(columns = [
                'timeslot', 'open', 'high', 'low', 'close', 'volume',
                'twap', 'date'
            ], data = array)
        elif array.shape[1] == 7:
            df = pd.DataFrame(columns = [
                'open', 'high', 'low', 'close', 'volume',
                'date', 'twap',
            ], data = array)
        else:
            return None
        if human:
            columns = df.columns.to_list()
            if 'date' in columns:
                df['date'] = df['date'].apply(datetime.datetime.fromtimestamp)
            if 'symbol' in columns:
                df['symbol'] = df['symbol'].apply(decode_symbol)
        return df
    return None

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

@functools.lru_cache(None)
def early_closes() -> typing.Dict[Tuple[datetime.date, int], int]:
    if 'early_closes' not in cache:
        nyse = mcal.get_calendar('NYSE')
        early_schedule = nyse.schedule(
            start_date = constants.MARKET_CALENDAR_START_DATE,
            end_date = constants.MARKET_CALENDAR_END_DATE
        )
        df = nyse.early_closes(schedule = early_schedule).copy()
        df['market_close_tzconvert'] = \
        df['market_close'].apply(lambda x: x.tz_convert(tz = 'US/Eastern'))
        irregular_closes = {}
        for timestamp in df['market_close_tzconvert'].to_list():
            date = timestamp.date()
            irregular_closes[date] = timestamp
        result = {}
        for period in [1, 5]:
            for date in market_dates():
                if date not in irregular_closes:
                    result[(date, period)] = timestamp_to_timeslot(
                        pd.Timestamp(
                            year = date.year,
                            month = date.month,
                            day = date.day,
                            hour = 16, minute = 0, second = 0, tz = 'US/Eastern'
                        ),
                        frequency = Frequency.MINUTE,
                        period = period
                    )
                else:
                    result[(date, period)] = timestamp_to_timeslot(
                        irregular_closes[date],
                        frequency = Frequency.MINUTE,
                        period = period
                    )
        cache['early_closes'] = result
    return cache['early_closes']

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

def resolve_date(when: Optional[Union[str, datetime.date, np.datetime64]] = None) -> datetime.date:
    if not when:
        return datetime.datetime.today().date()
    if isinstance(when, str):
        return datetime.datetime.strptime(when, '%Y-%m-%d').date()
    if isinstance(when, np.datetime64):
        return pd.Timestamp(when).date()
    return when

@functools.lru_cache(None)
def market_close_table(
    period: int = 1
):
    table = numba.typed.Dict.empty(
        key_type = numba.core.types.float64,
        value_type = numba.core.types.int64
    )
    for (date, period_), timeslot in early_closes().items():
        if period_ == period:
            table[np.float64(time.mktime(date.timetuple()))] = timeslot
    return table

def market_close(
    when: Optional[Union[str, datetime.date, np.datetime64]] = None,
    /, *,
    period: int = 1
) -> Optional[int]:
    assert period in [1, 5]
    try:
        return early_closes()[(resolve_date(when), period)]
    except KeyError:
        return None

def is_trading_date(when: Optional[Union[str, datetime.date, np.datetime64]] = None) -> bool:
    return resolve_date(when) in market_dates()

def trading_days_between(
    start: Union[str, datetime.date, np.datetime64],
    end: Optional[Union[str, datetime.date, np.datetime64]] = None
) -> int:
    dates = market_dates()
    start, end = (resolve_date(start), resolve_date(end))
    start_index = bisect.bisect_right(dates, start) - 1
    end_index = bisect.bisect_left(dates, end)
    if dates[start_index] != start:
        start_index += 1
    if dates[end_index] == end:
        end_index += 1
    return end_index - start_index - 1

def nth_next_trading_date(
    n: int = 1,
    anchor: Optional[Union[str, datetime.date, np.datetime64]] = None
) -> datetime.date:
    anchor = resolve_date(anchor)
    if n < 0:
        raise ValueError()
    if n == 0:
        return anchor
    dates = market_dates()
    start_index = bisect.bisect_left(dates, anchor)
    return dates[start_index + n]

def nth_previous_trading_date(
    n: int = 1,
    anchor: Optional[Union[str, datetime.date, np.datetime64]] = None
) -> datetime.date:
    anchor = resolve_date(anchor)
    if n < 0:
        raise ValueError()
    if n == 0:
        return anchor
    dates = market_dates()
    start_index = bisect.bisect_left(dates, anchor)
    return dates[start_index - n]

def trading_daterange(
    start: Union[str, datetime.date, np.datetime64],
    end: Optional[Union[str, datetime.date, np.datetime64]] = None
) -> Generator[datetime.date, None, None]:
    start, end = (resolve_date(start), resolve_date(end))
    dates = market_dates()
    start_index = bisect.bisect_right(dates, start) - 1
    end_index = bisect.bisect_left(dates, end)
    if dates[start_index] != start:
        start_index += 1
    if dates[end_index] == end:
        end_index += 1
    for i in range(start_index, end_index):
        yield dates[i]

def isfinite(n: np.float64) -> bool:
    return not np.isnan(n) and not np.isneginf(n) and not np.isposinf(n)

def float_to_bin(n: np.float64) -> str:
    return bin(struct.unpack('Q', struct.pack('d', n))[0])[3:]

def bin_to_float(bitstring: str) -> np.float64:
    return np.float64(
        struct.unpack('d',struct.pack('Q', int(''.join(['1', bitstring]), 2)))[0]
    )

@functools.lru_cache(None)
def make_encoding():
    chars = list(range(65, 91))
    chars.extend(list(range(97, 123)))
    chars.append(46)
    symbols = {}
    for i in chars:
        symbols[chr(i)] = 1
    return bitarray.util.huffman_code(symbols)

@functools.lru_cache(None)
def encode_symbol(symbol: str) -> np.float64:
    if len(symbol) > 10:
        raise ValueError()
    a = bitarray.bitarray()
    a.encode(make_encoding(), symbol)
    return np.float64(bin_to_float(a.to01()))

@functools.lru_cache(None)
def decode_symbol(n: np.float64) -> str:
    a = bitarray.bitarray(float_to_bin(n))
    return ''.join(a.decode(make_encoding()))

def encode_date(date):
    return time.mktime(
        resolve_date(date).timetuple()
    )

def decode_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)

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
