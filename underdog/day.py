# pylint: disable = broad-except
import datetime
import logging

from typing import (
   Optional
)

import pandas as pd

import underdog.constants as constants

from underdog.datautil import twap
from underdog.schema import Timespan
from underdog.tdaclient import tda
from underdog.tdahistoric import TDAHistoric
from underdog.utility import (
    nth_next_trading_date,
    nth_previous_trading_date
)

logger = logging.getLogger(__name__)

class Day(TDAHistoric):

    def __init__(
        self,
        symbol: str
    ):
        super().__init__(
            symbol, constants.DAY_PATH, 'date',
            Timespan.Day, 1, 1
        )

    def _fetch(
        self,
        start: Optional[datetime.date] = None,
        end: Optional[datetime.date] = None
    ) -> Optional[pd.DataFrame]:

        def build_dataframe(rows):
            if not rows:
                return None
            df = pd.DataFrame(rows)
            df = df.rename(
                columns = {
                    'datetime':'date',
                }
            )
            df = df.astype({
                'volume': int,
                'open': float,
                'close': float,
                'high': float,
                'low': float,
            })
            df['date'] = df['date'].apply(
                 lambda x: pd.Timestamp(pd.Timestamp(x, unit = 'ms').date())
            )
            df = twap(df)
            return df.sort_values('date', ascending = True).reset_index(drop = True)

        if start is None:
            start = nth_next_trading_date(1, anchor = self._dates[-1]) \
            if self._dates else None
        if end is None:
            end = nth_previous_trading_date(1)

        try:
            result = tda.api.get_price_history(
                self._symbol,
                period = tda.api.PriceHistory.Period.TWENTY_YEARS,
                period_type = tda.api.PriceHistory.PeriodType.YEAR,
                frequency_type = tda.api.PriceHistory.FrequencyType.DAILY,
                frequency = tda.api.PriceHistory.Frequency.DAILY,
                start_datetime = datetime.datetime.combine(start, datetime.time()) \
                if start else None,
                end_datetime = datetime.datetime.combine(end, datetime.time()) \
                if end else None
            )
            assert result.status_code == 200, result.raise_for_status()
            df = build_dataframe(result.json()['candles'])
            if df is not None:
                if self._dataframe is not None:
                    df = pd.concat(
                        [self._dataframe, df],
                        ignore_index = True
                    )
            return df
        except Exception as exc:
            logger.error(str(exc))
            return None
