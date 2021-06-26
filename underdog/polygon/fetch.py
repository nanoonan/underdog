import datetime
import json
import logging

from typing import (
    Dict, List, Optional, Union
)

import aiohttp
import numpy as np
import pandas as pd

from parkit import getenv

import underdog.constants as constants

from underdog.asyncthread import AsyncThread
from underdog.ratelimiter import RateLimiter
from underdog.utility import (
    nth_previous_trading_date,
    trading_daterange,
    twap
)

logger = logging.getLogger(__name__)

rate_limiter = RateLimiter(
    'polygon_rate_limiter',
    constants.POLYGON_REQUEST_INTERVAL,
    constants.POLYGON_MAX_REQUESTS_PER_INTERVAL
)

def build_dataframe(
    rows: List[Dict[str, Union[str, float, int, pd.Timestamp]]]
) -> Optional[pd.DataFrame]:

    if len(rows) == 0:
        return None

    df = pd.DataFrame(rows)
    df = df.rename(
        columns = {
            'o':'open',
            'c':'close',
            'h':'high',
            'l':'low',
            'vw':'vwap',
            'v':'volume',
            'T':'symbol'
        }
    )

    with pd.option_context('mode.use_inf_as_null', True):
        df = df.dropna()

    if len(df) == 0:
        return None

    if 'n' in df.columns.to_list():
        df = df.drop('n', axis = 1)
    if 't' in df.columns.to_list():
        df = df.drop('t', axis = 1)
    df = df.astype({
        'volume': np.int64,
        'open': np.float64,
        'close': np.float64,
        'high': np.float64,
        'low': np.float64,
        'vwap': np.float64
    })
    df = df[
        (df['volume'] >= 0) & \
        (df['open'] > 0) & \
        (df['close'] > 0) & \
        (df['high'] > 0) & \
        (df['low'] > 0) & \
        (df['vwap'] > 0)
    ]
    with pd.option_context('mode.use_inf_as_null', True):
        df = df.dropna()

    if len(df) == 0:
        return None

    df = twap(df)
    return df.reset_index(drop = True)

async def async_fetch_grouped_daily(
    session: aiohttp.ClientSession,
    date: datetime.date,
    api_key: str,
    max_attempts: int = constants.POLYGON_FETCH_RETRY_LIMIT
) -> Optional[pd.DataFrame]:
    logger.info('fetch grouped daily %s', str(date))
    context = None
    for context in rate_limiter.try_request(max_attempts):
        with context:
            async with session.get(
                'https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{0}'.format(
                    date.strftime('%Y-%m-%d')
                ),
                params = {'apiKey': api_key}
            ) as response:
                if response.status == 200:
                    result = json.loads(await response.text())
                    if result['status'] == 'OK':
                        if result['resultsCount'] > 0:
                            if context.attempts > 1:
                                logger.warning(
                                    '%i attempts fetching market data for %s',
                                    context.attempts, str(date)
                                )
                            return build_dataframe([
                                {**row, **{'date': pd.Timestamp(date)}}
                                for row in result['results']
                            ])
                        raise RuntimeError('no results returned for {0}'.format(date))
                    raise RuntimeError('response status is {0}'.format(result['status']))
                raise RuntimeError('server response code {0}'.format(response.status))
    logger.error('error fetching market data for %s: %s', str(date), str(context.errors[-1]))
    return None

async def async_fetch_market(
    api_key: str,
    agg_df: Optional[pd.DataFrame]
) -> Optional[pd.DataFrame]:
    async with aiohttp.ClientSession() as session:
        dates = list(trading_daterange(
            nth_previous_trading_date(504),
            nth_previous_trading_date(1)
        ))
        for date in dates:
            if agg_df is None or len(agg_df[agg_df['date'] == str(date)]) == 0:
                df = await async_fetch_grouped_daily(
                    session,
                    date,
                    api_key
                )
                if df is not None:
                    if agg_df is None:
                        agg_df = df
                    else:
                        agg_df = pd.concat([agg_df, df], ignore_index = True)
    if agg_df is not None and len(agg_df) > 0:
        return agg_df.sort_values(['date', 'symbol']).reset_index(drop = True)
    return None

def fetch_market(
    df: Optional[pd.DataFrame]
) -> Optional[pd.DataFrame]:
    thread = None
    try:
        thread = AsyncThread()
        thread.start()
        api_key = getenv(constants.POLYGON_API_KEY_ENVNAME)
        return thread.run_task(async_fetch_market(api_key, df))
    finally:
        if thread:
            thread.stop()
