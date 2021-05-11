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
        assert period in [1, 5, 30]
        super().__init__(
            symbol, '{0}/{1}'.format(constants.INTRADAY_PATH, period), 'timestamp',
            Timespan.Minute, period
        )

    def _fetch(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None
    ) -> Optional[pd.DataFrame]:
        try:
            if start is None:
                start = datetime.datetime.combine(datetime.datetime.today() - \
                datetime.timedelta(days = 365), datetime.time())
            if end is None:
                end = datetime.datetime.combine(datetime.datetime.today(), datetime.time())
            if self._period == 1:
                frequency = tda.api.PriceHistory.Frequency.EVERY_MINUTE
            elif self._period == 5:
                frequency = tda.api.PriceHistory.Frequency.EVERY_FIVE_MINUTES
            else:
                frequency = tda.api.PriceHistory.Frequency.EVERY_THIRTY_MINUTES
            result = tda.api.get_price_history(
                self._symbol,
                period_type = tda.api.PriceHistory.PeriodType.DAY,
                frequency_type = tda.api.PriceHistory.FrequencyType.MINUTE,
                frequency = frequency,
                start_datetime = start,
                end_datetime = end,
                need_extended_hours_data = True
            )
            assert result.status_code == 200, result.raise_for_status()
            return build_dataframe(result.json()['candles'], self.period)
        except Exception as exc:
            logger.error(str(exc))
            return None
