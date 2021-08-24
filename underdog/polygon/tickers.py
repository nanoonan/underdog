import json
import logging

from typing import (
    Dict,
    List,
    Optional,
    Union
)

import aiohttp
import pandas as pd

from parkit import getenv

import underdog.constants as constants

from underdog.asyncthread import AsyncThread
from underdog.ratelimiter import RateLimiter

logger = logging.getLogger(__name__)

rate_limiter = RateLimiter(
    'polygon_rate_limiter',
    constants.POLYGON_REQUEST_INTERVAL,
    constants.POLYGON_MAX_REQUESTS_PER_INTERVAL
)

def build_dataframe(
    rows: List[Dict[str, Union[str, float, int, bool]]]
) -> Optional[pd.DataFrame]:

    if len(rows) == 0:
        return None

    df = pd.DataFrame(rows)

    df = df.rename(dict(ticker = 'symbol', primary_exchange = 'exchange'), axis = 1)
    df['last_updated_utc'] = df['last_updated_utc'].apply(pd.Timestamp)

    return df.sort_values('symbol').reset_index(drop = True)

async def async_fetch_tickers(
    api_key: str,
    max_attempts: int = constants.POLYGON_FETCH_RETRY_LIMIT
) -> Optional[pd.DataFrame]:
    results = []
    next_url = 'https://api.polygon.io/v3/reference/tickers'
    async with aiohttp.ClientSession() as session:
        while True:
            for context in rate_limiter.try_request(max_attempts):
                with context:
                    async with session.get(
                        next_url,
                        params = {
                            'market': 'stocks',
                            'limit': '1000',
                            'apiKey': api_key
                        }
                    ) as response:
                        if response.status == 200:
                            result = json.loads(await response.text())
                            next_url = result['next_url'] if 'next_url' in result else None
                            if result['status'] == 'OK':
                                results.extend(result['results'])
                                if next_url is None:
                                    if context.attempts > 1:
                                        logger.warning(
                                            '%i attempts fetching ticker data',
                                            context.attempts
                                        )
                                    return build_dataframe(results)
                            else:
                                raise RuntimeError('response status is {0}'.format(result['status']))
                        else:
                            raise RuntimeError('server response code {0}'.format(response.status))
    logger.error('error fetching ticker data')
    return None

def fetch_tickers() -> Optional[pd.DataFrame]:
    thread = None
    try:
        thread = AsyncThread()
        thread.start()
        api_key = getenv(constants.POLYGON_API_KEY_ENVNAME)
        return thread.run_task(async_fetch_tickers(api_key))
    finally:
        if thread:
            thread.stop()
