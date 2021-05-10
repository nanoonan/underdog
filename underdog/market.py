import bisect
import datetime
import json
import logging

from functools import lru_cache
from typing import (
    Any, cast, Dict, Generator, List, Optional, Tuple,
    Union
)

import aiohttp
import pandas as pd

from parkit import (
    getenv,
    polling_loop
)

import underdog.constants as constants

from underdog.asyncthread import AsyncThread
from underdog.dataframedict import DataFrameDict
from underdog.datautil import (
    datestr_from_key,
    twap
)
from underdog.utility import (
    date_from_datestr,
    datestr_from_date,
    nth_next_trading_date,
    nth_previous_trading_date,
    trading_daterange,
    trading_days_between
)

logger = logging.getLogger(__name__)

class Market():

    def __init__(self, cached: bool = True):
        self._api_key = getenv(constants.POLYGON_API_KEY_ENVNAME)
        self._datadict = DataFrameDict(constants.MARKET_PATH)
        self._dates = cast(
            Optional[List[Union[str, datetime.date]]],
            sorted(list(self._datadict.keys()))
        )
        self._cached = cached
        self.update(True)

    def __len__(self):
        return len(self._dates)

    def keys(self) -> Generator[datetime.date, None, None]:
        for key in self._datadict.keys():
            yield pd.Timestamp(key).date()

    def values(self) -> Generator[pd.DataFrame, None, None]:
        return self._datadict.values()

    def __iter__(self) -> Generator[datetime.date, None, None]:
        return self.keys()

    def items(self) -> Generator[Tuple[datetime.date, pd.DataFrame], None, None]:
        for key, value in self._datadict.items():
            yield pd.Timestamp(key).date(), value

    def __getitem__(
        self,
        key: Union[str, datetime.date, int, slice]
    ) -> Optional[pd.DataFrame]:

        if not isinstance(key, slice):
            datestr = datestr_from_key(key, self._dates)
            if self._dates and datestr in self._dates:
                return self._get_cached_dataframe(datestr) \
                if self._cached else self._datadict[datestr]
            return None

        start_date = datestr_from_key(key.start, self._dates)
        end_date = datestr_from_key(key.stop, self._dates)

        return self._make_dataframe(start_date, end_date)

    def _make_dataframe(
        self,
        start_datestr: Optional[str] = None,
        end_datestr: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        if self._dates:
            dataframes = []
            start_datestr = '0000' if start_datestr is None else start_datestr
            end_datestr = '9999' if end_datestr is None else end_datestr
            for datestr in self._dates[
                bisect.bisect_left(self._dates, start_datestr): \
                bisect.bisect_right(self._dates, end_datestr)
            ]:
                dataframes.append(
                    self._get_cached_dataframe(datestr) \
                    if self._cached else self._datadict[datestr]
                )
            if dataframes:
                return pd.concat(dataframes, ignore_index = True).reset_index(drop = True)
        return None

    @lru_cache
    def _get_cached_dataframe(self, datestr: str):
        return self._datadict[datestr]

    def update(
        self,
        quick_check: bool = False
    ) -> bool:
        thread = None
        try:
            last_date = self._dates[-1] if self._dates else None

            if last_date == datestr_from_date(nth_previous_trading_date(1)):
                return True

            start_date = nth_previous_trading_date(503) if last_date is None else \
            nth_next_trading_date(1, anchor = date_from_datestr(cast(str, last_date)))

            end_date = nth_previous_trading_date(1)

            if quick_check and trading_days_between(start_date, end_date) > 5:
                print('Market data is out of date. Please run update().')
                return False

            thread = AsyncThread()
            thread.start()
            thread.run_task(self._fetchall(start_date, end_date))
        finally:
            self._dates = cast(
                Optional[List[Union[str, datetime.date]]],
                sorted(list(self._datadict.keys()))
            )
            if thread:
                thread.stop()
        return True

    async def _fetchall(
        self,
        start_date: datetime.date,
        end_date: datetime.date
    ):
        args = list(trading_daterange(start_date, end_date))
        interval = 0 if len(args) <= 5 else 12
        async with aiohttp.ClientSession() as session:
            iteration = 0
            while True:
                failed = []
                for index in polling_loop(interval):
                    if index == len(args):
                        break
                    (success, result) = await self._fetchone(session, args[index])
                    if success:
                        self._datadict[str(args[index])] = result
                    else:
                        failed.append(result)
                if not failed:
                    break
                iteration += 1
                interval = 12
                if iteration >= constants.POLYGON_RETRY_LIMIT:
                    raise RuntimeError('Exceeded retry limit ({0})'.format(
                        constants.POLYGON_RETRY_LIMIT)
                    )
                args = failed

    async def _fetchone(
        self,
        session: aiohttp.ClientSession,
        date: datetime.date
    ) -> Tuple[bool, Any]:
        try:
            async with session.get(
                'https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{0}'.format(
                    date.strftime('%Y-%m-%d')
                ),
                params = {'apiKey': self._api_key}
            ) as response:
                if response.status == 200:
                    result = json.loads(await response.text())
                    if result['status'] == 'OK':
                        if result['resultsCount'] > 0:
                            df = _build_dataframe([
                                {**row, **{'date':pd.Timestamp(date)}}
                                for row in result['results']
                            ])
                            return (True, df)
                        raise RuntimeError('No results returned for {0}'.format(date))
                    raise RuntimeError('Response status is {0}'.format(result['status']))
                raise RuntimeError('Server response code {0}'.format(response.status))
        except RuntimeError as exc:
            logger.error(str(exc))
            return (False, date)

def _build_dataframe(
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
    df['twap'] = twap(df)
    df.attrs['type'] = 'market'
    return df.reset_index(drop = True)
