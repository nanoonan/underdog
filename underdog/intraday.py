# pylint: disable = broad-except
import datetime
import logging

from typing import (
    Any, Dict, List, Optional
)

import pandas as pd

import underdog.constants as constants

from underdog.datautil import twap
from underdog.schema import Timespan
from underdog.tdaclient import tda
from underdog.tdahistoric import TDAHistoric
from underdog.utility import (
    get_trading_segment,
    nth_previous_trading_date,
    timestamp_to_timeslot
)

logger = logging.getLogger(__name__)

def build_dataframe(
    rows: List[Dict[str, Any]],
    period: int = 1
) -> Optional[pd.DataFrame]:
    if not rows:
        return None

    df = pd.DataFrame(rows)

    df = df.rename(
        columns = {
            'datetime':'timestamp',
        }
    )
    df = df.astype({
        'volume': int,
        'open': float,
        'close': float,
        'high': float,
        'low': float,
    })
    df['timestamp'] = df['timestamp'].apply(
        lambda x: pd.Timestamp(x, tz = 'US/Eastern', unit = 'ms')
    )
    df['trading_segment'] = df['timestamp'].apply(
        lambda x: get_trading_segment(x).value
    )
    df['timeslot'] = df['timestamp'].apply(
        lambda x: timestamp_to_timeslot(x, period = period)
    )
    df = twap(df)

    return df.sort_values('timestamp', ascending = True).reset_index(drop = True)

def intraday(symbol: str) -> pd.DataFrame:
    try:
        result = tda.api.get_price_history(
            symbol,
            period_type = tda.api.PriceHistory.PeriodType.DAY,
            frequency_type = tda.api.PriceHistory.FrequencyType.MINUTE,
            frequency = tda.api.PriceHistory.Frequency.EVERY_MINUTE,
            start_datetime = datetime.datetime.combine(datetime.datetime.today(), datetime.time()),
            end_datetime = datetime.datetime.combine(datetime.datetime.today(), datetime.time()),
            need_extended_hours_data = True
        )
        assert result.status_code == 200, result.raise_for_status()
        return build_dataframe(result.json()['candles'])
    except Exception as exc:
        logger.error(str(exc))
        return None

class IntraDay(TDAHistoric):

    def __init__(
        self,
        symbol: str,
        period: int = 1
    ):
        sample_period = period
        if sample_period % 30 == 0:
            source_period = 30
        elif sample_period % 5 == 0:
            source_period = 5
        else:
            source_period = 1
        super().__init__(
            symbol, '{0}/{1}'.format(constants.INTRADAY_PATH, source_period), 'timestamp',
            Timespan.Minute, source_period, sample_period
        )

    def _fetch(
        self,
        start: Optional[datetime.date] = None,
        end: Optional[datetime.date] = None
    ) -> Optional[pd.DataFrame]:
        try:
            if start is None:
                start = nth_previous_trading_date(252)
            if end is None:
                end = nth_previous_trading_date(1)
            if self._source_period == 1:
                frequency = tda.api.PriceHistory.Frequency.EVERY_MINUTE
            elif self._source_period == 5:
                frequency = tda.api.PriceHistory.Frequency.EVERY_FIVE_MINUTES
            else:
                frequency = tda.api.PriceHistory.Frequency.EVERY_THIRTY_MINUTES
            result = tda.api.get_price_history(
                self._symbol,
                period_type = tda.api.PriceHistory.PeriodType.DAY,
                frequency_type = tda.api.PriceHistory.FrequencyType.MINUTE,
                frequency = frequency,
                start_datetime = datetime.datetime.combine(start, datetime.time()) \
                if start else None,
                end_datetime = datetime.datetime.combine(end, datetime.time()) \
                if end else None,
                need_extended_hours_data = True
            )
            assert result.status_code == 200, result.raise_for_status()
            return build_dataframe(result.json()['candles'], self._source_period)
        except Exception as exc:
            logger.error(str(exc))
            return None

    def _resample(self):
        if self._dataframe is not None:
            if self._sample_period not in [1, 5, 30]:
                self._dataframe = self._dataframe.set_index('timestamp')
                rule = '{0}T'.format(str(self._sample_period))
                self._dataframe = self._dataframe.resample(rule).aggregate(dict(
                    open = 'first',
                    close = 'last',
                    low = 'min',
                    high = 'max',
                    volume = 'sum',
                    trading_segment = 'first'
                )).dropna().reset_index(drop = False)
                self._dataframe = twap(self._dataframe)
                self._dataframe['trading_segment'] = self._dataframe['timestamp'] \
                .apply(lambda x: get_trading_segment(x).value)
                self._dataframe['timeslot'] = self._dataframe['timestamp'] \
                .apply(lambda x: timestamp_to_timeslot(x, period = self._sample_period))
