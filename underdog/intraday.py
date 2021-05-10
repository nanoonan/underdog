# pylint: disable = broad-except
import datetime
import logging

from typing import (
    Any, Dict, List, Optional
)

import pandas as pd

import underdog.constants as constants

from underdog.datautil import twap
from underdog.tdaclient import tda
from underdog.tdahistoric import TDAHistoric
from underdog.utility import get_trading_segment

logger = logging.getLogger(__name__)

def build_dataframe(rows: List[Dict[str, Any]]) -> Optional[pd.DataFrame]:
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
    df = twap(df)
    df.attrs['type'] = 'intraday'
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
        symbol: str
    ):
        super().__init__(symbol, constants.INTRADAY_PATH, 'timestamp')

    def _fetch(
        self,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None
    ) -> Optional[pd.DataFrame]:
        try:
            if start is None:
                start = datetime.datetime.combine(datetime.datetime.today() - \
                datetime.timedelta(days = 90), datetime.time())
            if end is None:
                end = datetime.datetime.combine(datetime.datetime.today(), datetime.time())
            result = tda.api.get_price_history(
                self._symbol,
                period_type = tda.api.PriceHistory.PeriodType.DAY,
                frequency_type = tda.api.PriceHistory.FrequencyType.MINUTE,
                frequency = tda.api.PriceHistory.Frequency.EVERY_MINUTE,
                start_datetime = start,
                end_datetime = end,
                need_extended_hours_data = True
            )
            assert result.status_code == 200, result.raise_for_status()
            return build_dataframe(result.json()['candles'])
        except Exception as exc:
            logger.error(str(exc))
            return None
