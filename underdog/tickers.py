import json
import logging
import math

import aiohttp
import pandas as pd

from parkit import getenv

import underdog.constants as constants

from underdog.asyncthread import AsyncThread
from underdog.dataframedict import DataFrameDict
from underdog.utility import date_from_datestr

logger = logging.getLogger(__name__)

async def _fetch_tickers(api_key: str):
    results = []
    page = 1
    last_page = None
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(
                'https://api.polygon.io/v2/reference/tickers',
                params = {
                    'perpage': '50', 'page': str(page), 'market': 'STOCKS',
                    'locale': 'us', 'sort': 'ticker',
                    'apiKey': api_key
                }
            ) as response:
                if response.status == 200:
                    result = json.loads(await response.text())
                    if last_page is None:
                        last_page = int(math.ceil(result['count'] / 50))
                    if result['status'] == 'OK':
                        results.extend(result['tickers'])
                        page += 1
                        if page > last_page:
                            return results
                    else:
                        raise RuntimeError('Response status is {0}'.format(result['status']))
                else:
                    raise RuntimeError('Server response code {0}'.format(response.status))

def tickers(update: bool = False):
    thread = None
    try:
        datadict = DataFrameDict(constants.GENERIC_PATH)

        if update:
            thread = AsyncThread()
            thread.start()
            api_key = getenv(constants.POLYGON_API_KEY_ENVNAME)
            results = thread.run_task(_fetch_tickers(api_key))
            df = pd.DataFrame(results)
            df = df.drop(['url'], axis = 1)
            df = df.rename(dict(ticker = 'symbol', primaryExch = 'exchange'), axis = 1)
            df['updated'] = df['updated'].apply(
                lambda x: pd.Timestamp(date_from_datestr(x))
            )
            df = df.sort_values('ticker').reset_index(drop = True)
            datadict['tickers'] = df

        if 'tickers' in datadict:
            return datadict['tickers']
        return None
    finally:
        if thread:
            thread.stop()
