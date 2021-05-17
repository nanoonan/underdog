# pylint: disable = unused-argument, assignment-from-none, no-self-use, too-many-instance-attributes
import datetime
import logging

from typing import (
    Generator, Optional, List, Tuple, Union
)

import pandas as pd

from underdog.dataframedict import DataFrameDict
from underdog.datautil import date_from_key
from underdog.schema import Timespan
from underdog.utility import (
    nth_next_trading_date,
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
        source_period: int,
        sample_period: int
    ):
        self._symbol = symbol
        self._datefield = datefield
        self._dataframe = None
        self._dates: List[datetime.date] = []
        self._timespan = timespan
        self._source_period = source_period
        self._sample_period = sample_period
        self._datadict = DataFrameDict(path)
        self.update()

    @property
    def timespan(self) -> Timespan:
        return self._timespan

    @property
    def period(self) -> int:
        return self._sample_period

    @property
    def symbol(self) -> str:
        return self._symbol

    def __len__(self) -> int:
        return len(self._dates)

    def clear(self) -> None:
        if self._symbol in self._datadict:
            del self._datadict[self._symbol]
        self._dataframe = None
        self._dates = []

    def keys(self) -> Generator[datetime.date, None, None]:
        for date in self._dates:
            yield date

    def values(self) -> Generator[pd.DataFrame, None, None]:
        if self._dataframe is not None:
            for date in self._dates:
                yield self._dataframe[self._dataframe[self._datefield].dt.date == date] \
                .reset_index(drop = True)

    def __iter__(self) -> Generator[datetime.date, None, None]:
        return self.keys()

    def items(self) -> Generator[Tuple[datetime.date, pd.DataFrame], None, None]:
        if self._dataframe is not None:
            for date in self._dates:
                yield (
                    date,
                    self._dataframe[self._dataframe[self._datefield].dt.date == date] \
                    .reset_index(drop = True)
                )

    def __getitem__(
        self,
        key: Union[str, datetime.date, int, slice]
    ) -> Optional[pd.DataFrame]:
        if not isinstance(key, slice):
            return self._make_dataframe(key, key)
        return self._make_dataframe(key.start, key.stop)

    def _make_dataframe(
        self,
        key_start: Optional[Union[str, datetime.date, int]] = None,
        key_end: Optional[Union[str, datetime.date, int]] = None
    ) -> Optional[pd.DataFrame]:
        if not self._dates or self._dataframe is None:
            return None
        start = date_from_key(key_start, self._dates)
        end = date_from_key(key_end, self._dates)
        if start is None and end is None:
            return self._dataframe
        if start is None:
            return self._dataframe[self._dataframe[self._datefield].dt.date <= end] \
            .reset_index(drop = True)
        if end is None:
            return self._dataframe[self._dataframe[self._datefield].dt.date >= start] \
            .reset_index(drop = True)
        return self._dataframe[
            (self._dataframe[self._datefield].dt.date >= start) &
            (self._dataframe[self._datefield].dt.date <= end)
        ].reset_index(drop = True)

    def update(self) -> None:
        if self._symbol in self._datadict:
            self._dataframe = self._datadict[self._symbol]
            if self._dataframe is not None:
                self._dates = sorted(list((self._dataframe[self._datefield].dt.date).unique()))
                if self._dates[-1] == nth_previous_trading_date(1):
                    self._resample()
                    return
        if self._dataframe is None:
            start = None
        else:
            start = nth_next_trading_date(
                1,
                anchor = self._dates[-1]
            )
        df = self._fetch(
            start = start,
            end = nth_previous_trading_date(1)
        )
        if df is None:
            if self._dataframe is not None:
                self._resample()
            return
        if self._dataframe is not None:
            self._dataframe = pd.concat([self._dataframe, df], ignore_index = True)
        else:
            self._dataframe = df
        if self._dataframe is not None:
            self._datadict[self._symbol] = self._dataframe
            self._dates = sorted(list((self._dataframe[self._datefield].dt.date).unique()))
            self._resample()
        return

    def _resample(self):
        pass

    def _fetch(
        self,
        start: Optional[datetime.date] = None,
        end: Optional[datetime.date] = None
    ) -> Optional[pd.DataFrame]:
        return None
