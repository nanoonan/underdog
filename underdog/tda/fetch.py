import datetime
import logging

from typing import (
    Any, Dict, List, Optional, Union
)

import numpy as np
import pandas as pd

from parkit import Frequency

import underdog.constants as constants

from underdog.ratelimiter import RateLimiter
from underdog.tda.tdaclient import tda
from underdog.utility import (
    nth_previous_trading_date,
    resolve_date,
    timeslot_to_timestamp,
    timestamp_to_timeslot,
    twap
)

logger = logging.getLogger(__name__)

rate_limiter: RateLimiter = RateLimiter(
    'tda_rate_limiter',
    constants.TDA_REQUEST_INTERVAL,
    constants.TDA_MAX_REQUESTS_PER_INTERVAL
)

timeslots = {
    1: 960,
    5: 192
}

def fill_missing_intraday(
    df: pd.DataFrame,
    period: int
) -> pd.DataFrame:
    df = df.sort_values('timeslot')
    date = df.iloc[0]['date']
    symbol = df.iloc[0]['symbol']
    df = df.set_index('timeslot')
    added = set(range(timeslots[period])).difference(set(df.index.to_list()))
    df = df.reindex(range(timeslots[period])).reset_index(drop = False)
    df['timestamp'] = df['timeslot'].apply(lambda x: timeslot_to_timestamp(
        x, frequency = Frequency.MINUTE, period = period, date = date
    ))
    df['date'] = date
    df['symbol'] = symbol
    df['volume'] = np.where(
        df.index.isin(added),
        0, df['volume']
    )
    df = df.astype({
        'volume': np.int64
    })
    return df

def normalize_intraday(
    df: pd.DataFrame,
    period: int
) -> Optional[pd.DataFrame]:
    concat = []
    df['date'] = df['timestamp'].apply(lambda x: pd.Timestamp(x.date()))
    for date in df['date'].unique():
        tf = df[df['date'] == date]
        concat.append(fill_missing_intraday(tf, period))
    df = pd.concat(concat, ignore_index = True)
    if len(df) > 0:
        return df.sort_values(['date', 'timeslot']).reset_index(drop = True)
    return None

def fetch_intraday(
    symbol: str,
    /, *,
    period: int = 1,
    start: Optional[Union[str,datetime.date]] = None,
    end: Optional[Union[str, datetime.date]] = None,
    max_attempts: int = constants.TDA_FETCH_RETRY_LIMIT
) -> Optional[pd.DataFrame]:

    def build_dataframe(
        rows: List[Dict[str, Any]],
        period: int = 1
    ) -> Optional[pd.DataFrame]:

        if len(rows) == 0:
            return None

        df = pd.DataFrame(rows)

        df = df.rename(
            columns = {
                'datetime':'timestamp',
            }
        )
        df = df.astype({
            'volume': np.int64,
            'open': np.float64,
            'close': np.float64,
            'high': np.float64,
            'low': np.float64,
        })
        df = df[
            (df['timestamp'] >= 0) & \
            (df['volume'] >= 0) & \
            (df['open'] > 0) & \
            (df['close'] > 0) & \
            (df['high'] > 0) & \
            (df['low'] > 0)
        ]

        with pd.option_context('mode.use_inf_as_null', True):
            df = df.dropna()

        if len(df) == 0:
            return None

        df['symbol'] = symbol
        df['timestamp'] = df['timestamp'].apply(
            lambda x: pd.Timestamp(x, tz = 'US/Eastern', unit = 'ms')
        )
        df['timeslot'] = df['timestamp'].apply(
            lambda x: timestamp_to_timeslot(x, period = period)
        )
        df = df.astype({
            'timeslot': np.int32
        })
        df = twap(df)

        return normalize_intraday(df, period)

    if period not in [1, 5]:
        raise ValueError()

    start = nth_previous_trading_date(252) if start is None else resolve_date(start)
    end = nth_previous_trading_date(1) if end is None else resolve_date(end)

    if period == 1:
        frequency = tda.api.PriceHistory.Frequency.EVERY_MINUTE
    elif period == 5:
        frequency = tda.api.PriceHistory.Frequency.EVERY_FIVE_MINUTES
    else:
        frequency = tda.api.PriceHistory.Frequency.EVERY_THIRTY_MINUTES

    context = None
    for context in rate_limiter.try_request(max_attempts):
        with context:
            result = tda.api.get_price_history(
                symbol.upper(),
                period_type = tda.api.PriceHistory.PeriodType.DAY,
                frequency_type = tda.api.PriceHistory.FrequencyType.MINUTE,
                frequency = frequency,
                start_datetime = datetime.datetime.combine(start, datetime.time()) \
                if start else None,
                end_datetime = datetime.datetime.combine(end, datetime.time()),
                need_extended_hours_data = True
            )
            assert result.status_code == 200, result.raise_for_status()
            if context.attempts > 1:
                logger.warning('%i attempts fetching daily data for %s', context.attempts, symbol)
            return build_dataframe(result.json()['candles'], period)
    logger.error('error fetching intraday data for %s: %s', symbol, str(context.errors[-1]))
    return None

def fetch_daily(
    symbol: str,
    /, *,
    start: Optional[Union[str,datetime.date]] = None,
    end: Optional[Union[str, datetime.date]] = None,
    max_attempts: int = constants.TDA_FETCH_RETRY_LIMIT
) -> Optional[pd.DataFrame]:

    def build_dataframe(rows):

        if len(rows) == 0:
            return None

        df = pd.DataFrame(rows)
        df = df.rename(
            columns = {
                'datetime':'date',
            }
        )
        df = df.astype({
            'volume': np.int64,
            'open': np.float64,
            'close': np.float64,
            'high': np.float64,
            'low': np.float64,
        })
        df = df[
            (df['date'] >= 0) & \
            (df['volume'] >= 0) & \
            (df['open'] > 0) & \
            (df['close'] > 0) & \
            (df['high'] > 0) & \
            (df['low'] > 0)
        ]
        with pd.option_context('mode.use_inf_as_null', True):
            df = df.dropna()

        if len(df) == 0:
            return None

        df['symbol'] = symbol
        df['date'] = df['date'].apply(
             lambda x: pd.Timestamp(pd.Timestamp(x, unit = 'ms').date())
        )
        df = twap(df)
        return df.sort_values('date', ascending = True).reset_index(drop = True)

    start = None if start is None else resolve_date(start)
    end = nth_previous_trading_date(1) if end is None else resolve_date(end)

    context = None
    for context in rate_limiter.try_request(max_attempts):
        with context:
            result = tda.api.get_price_history(
                symbol.upper(),
                period = tda.api.PriceHistory.Period.TWENTY_YEARS,
                period_type = tda.api.PriceHistory.PeriodType.YEAR,
                frequency_type = tda.api.PriceHistory.FrequencyType.DAILY,
                frequency = tda.api.PriceHistory.Frequency.DAILY,
                start_datetime = datetime.datetime.combine(start, datetime.time()) \
                if start else None,
                end_datetime = datetime.datetime.combine(end, datetime.time())
            )
            assert result.status_code == 200, result.raise_for_status()
            if context.attempts > 1:
                logger.warning('%i attempts fetching daily data for %s', context.attempts, symbol)
            return build_dataframe(result.json()['candles'])
    logger.error('error fetching daily data for %s: %s', symbol, str(context.errors[-1]))
    return None
