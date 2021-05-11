# pylint: disable = unused-argument, assignment-from-none, no-self-use
import datetime
import logging

from typing import (
    cast, Generator, Optional, List, Tuple, Union
)

import pandas as pd

from underdog.dataframedict import DataFrameDict
from underdog.datautil import datestr_from_key
from underdog.schema import Timespan
from underdog.utility import (
    date_from_datestr,
    nth_previous_trading_date
)

logger = logging.getLogger(__name__)

class TDAHistoric():

    def __init__(
        self,
        symbol: str,
        path: str,
        datefield: str,
        timespan: Timespan,
        period: int
    ):
        self._symbol = symbol
        self._datefield = datefield
        self._dataframe = None
        self._dates = None
        self._timespan = timespan
        self._period = period
        self._datadict = DataFrameDict(path)
        if self._symbol in self._datadict:
            df = self._datadict[self._symbol]
            self._dataframe = df
            if df.iloc[-1][self._datefield].date() == nth_previous_trading_date(1):
                self._dates = cast(
                    Optional[List[Union[str, datetime.date]]],
                    sorted(list((self._dataframe[self._datefield].dt.date).unique()))
                )

    @property
    def timespan(self) -> Timespan:
        return self._timespan

    @property
    def period(self) -> int:
        return self._period

    @property
    def symbol(self) -> str:
        return self._symbol

    def __len__(self) -> int:
        if self._load() and self._dates:
            return len(self._dates)
        return 0

    def keys(self) -> Generator[datetime.date, None, None]:
        if self._load() and self._dates:
            for date in self._dates:
                yield cast(datetime.date, date)

    def values(self) -> Generator[pd.DataFrame, None, None]:
        df = self._get_dataframe()
        if df:
            for date in sorted(
                {[timestamp.date() for timestamp in df[self._datefield].to_list()]}
            ):
                yield df[df[self._datefield].dt.date == date].copy().reset_index(drop = True)

    def __iter__(self) -> Generator[datetime.date, None, None]:
        return self.keys()

    def items(self) -> Generator[Tuple[datetime.date, pd.DataFrame], None, None]:
        df = self._get_dataframe()
        if df:
            for date in sorted(
                [timestamp.date() for timestamp in df[self._datefield].to_list()]
            ):
                yield date, df[df[self._datefield].dt.date == date].copy().reset_index(drop = True)

    def __getitem__(
        self,
        key: Union[str, datetime.date, int, slice]
    ) -> Optional[pd.DataFrame]:
        if not isinstance(key, slice):
            return self._get_dataframe(key, key)
        return self._get_dataframe(key.start, key.stop)

    def _get_dataframe(
        self,
        start: Optional[Union[str, datetime.date, int]] = None,
        end: Optional[Union[str, datetime.date, int]] = None
    ) -> Optional[pd.DataFrame]:
        if not self._load():
            return None
        start = datestr_from_key(start, self._dates)
        end = datestr_from_key(end, self._dates)
        if start is None and end is None:
            return self._dataframe
        if start is None:
            return self._dataframe[self._dataframe[self._datefield].dt.date <= \
            date_from_datestr(cast(str, end))].reset_index(drop = True) \
            if self._dataframe is not None else None
        if end is None:
            return self._dataframe[self._dataframe[self._datefield].dt.date >= \
            date_from_datestr(start)].reset_index(drop = True) \
            if self._dataframe is not None else None
        return self._dataframe[
            (self._dataframe[self._datefield].dt.date >= date_from_datestr(start)) &
            (self._dataframe[self._datefield].dt.date <= date_from_datestr(end))
        ].reset_index(drop = True) if self._dataframe is not None else None

    def _load(self) -> bool:
        if self._dates is None:
            self._dataframe = self._fetch(
                end = datetime.datetime.combine(nth_previous_trading_date(1), datetime.time())
            )
            if self._dataframe is None:
                return False
            self._datadict[self._symbol] = self._dataframe
            self._dates = sorted(list((self._dataframe[self._datefield].dt.date).unique()))
        return True

    def _fetch(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None
    ) -> Optional[pd.DataFrame]:
        return None
