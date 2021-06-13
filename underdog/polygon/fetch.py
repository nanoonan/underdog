import datetime
import json
import logging

from typing import (
    Dict, List, Optional, Union
)

import aiohttp
import pandas as pd

from parkit import (
    get_site,
    File,
    getenv,
    polling_loop
)

import underdog.constants as constants

from underdog.asyncthread import AsyncThread
from underdog.utility import (
    nth_previous_trading_date,
    trading_daterange,
    twap
)

logger = logging.getLogger(__name__)

def build_dataframe(
    rows: List[Dict[str, Union[str, float, int, pd.Timestamp]]]
) -> Optional[pd.DataFrame]:
    if not rows:
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
    df = df.dropna()
    if 'n' in df.columns.to_list():
        df = df.drop('n', axis = 1)
    if 't' in df.columns.to_list():
        df = df.drop('t', axis = 1)
    df = df.astype({
        'volume': int,
        'open': float,
        'close': float,
        'high': float,
        'low': float,
        'vwap': float
    })
    df = twap(df)
    return df.reset_index(drop = True)

async def async_fetch_grouped_daily(
    session: aiohttp.ClientSession,
    date: datetime.date,
    api_key: str
) -> Optional[pd.DataFrame]:
    logger.info('fetch grouped daily %s', str(date))
    try:
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
                        return build_dataframe([
                            {**row, **{'date': pd.Timestamp(date)}}
                            for row in result['results']
                        ])
                    raise RuntimeError('no results returned for {0}'.format(date))
                raise RuntimeError('response status is {0}'.format(result['status']))
            raise RuntimeError('server response code {0}'.format(response.status))
    except RuntimeError:
        logger.exception('error fetching polygon market data')
        return None

async def async_fetch_market(
    api_key: str,
    site: str
):
    async with aiohttp.ClientSession() as session:
        agg_df = None
        with File('polygon/market', site = site, mode = 'rb') as file:
            if not file.empty:
                agg_df = pd.read_feather(file)
        dates = list(trading_daterange(
            nth_previous_trading_date(504),
            nth_previous_trading_date(1)
        ))
        for _ in polling_loop(61):
            count = 0
            while count < 5:
                date = dates.pop()
                if agg_df is None or len(agg_df[agg_df['date'] == str(date)]) == 0:
                    count += 1
                    df = await async_fetch_grouped_daily(session, date, api_key)
                    if df is not None:
                        if agg_df is None:
                            agg_df = df
                        else:
                            agg_df = pd.concat([agg_df, df])
                        agg_df = agg_df.sort_values(['date', 'symbol']).reset_index(drop = True)
                if len(dates) == 0:
                    with File('polygon/market', site = site, mode = 'wb') as file:
                        agg_df.to_feather(file)
                    return

def fetch_market():
    thread = None
    try:
        thread = AsyncThread()
        thread.start()
        api_key = getenv(constants.POLYGON_API_KEY_ENVNAME)
        thread.run_task(async_fetch_market(api_key, get_site()))
    finally:
        if thread:
            thread.stop()
