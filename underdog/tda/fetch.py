import datetime
import logging

from typing import (
    Any, Dict, List, Optional, Union
)

import pandas as pd

from underdog.tda.tdaclient import tda
from underdog.utility import (
    get_trading_segment,
    nth_previous_trading_date,
    resolve_date,
    timestamp_to_timeslot,
    twap
)

logger = logging.getLogger(__name__)

def fetch_intraday(
    symbol: str,
    /, *,
    period: int = 1,
    start: Optional[Union[str,datetime.date]] = None,
    end: Optional[Union[str, datetime.date]] = None
) -> Optional[pd.DataFrame]:

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
        df['symbol'] = symbol
        df['date'] = df['timestamp'].apply(
             lambda x: pd.Timestamp(pd.Timestamp(x, unit = 'ms').date())
        )
        df['timestamp'] = df['timestamp'].apply(
            lambda x: pd.Timestamp(x, tz = 'US/Eastern', unit = 'ms')
        )
        df['trading_segment'] = df['timestamp'].apply(
            lambda x: get_trading_segment(x)
        )
        df['timeslot'] = df['timestamp'].apply(
            lambda x: timestamp_to_timeslot(x, period = period)
        )
        df = df.astype({
            'trading_segment': int,
            'timeslot': int
        })
        df = twap(df)

        return df.sort_values('timestamp', ascending = True).reset_index(drop = True)

    if period not in [1, 5, 30]:
        raise ValueError()

    start = nth_previous_trading_date(252) if start is None else resolve_date(start)
    end = nth_previous_trading_date(1) if end is None else resolve_date(end)
    try:
        if period == 1:
            frequency = tda.api.PriceHistory.Frequency.EVERY_MINUTE
        elif period == 5:
            frequency = tda.api.PriceHistory.Frequency.EVERY_FIVE_MINUTES
        else:
            frequency = tda.api.PriceHistory.Frequency.EVERY_THIRTY_MINUTES
        result = tda.api.get_price_history(
            symbol.upper(),
            period_type = tda.api.PriceHistory.PeriodType.DAY,
            frequency_type = tda.api.PriceHistory.FrequencyType.MINUTE,
            frequency = frequency,
            start_datetime = datetime.datetime.combine(start, datetime.time()) \
            if start else None,
            end_datetime = datetime.datetime.combine(end, datetime.time()),
            need_extended_hours_data = True
        )
        assert result.status_code == 200, result.raise_for_status()
        return build_dataframe(result.json()['candles'], period)
    except Exception:
        logger.exception('error fetching tdahistoric intraday data')
        return None

def fetch_daily(
    symbol: str,
    /, *,
    start: Optional[Union[str,datetime.date]] = None,
    end: Optional[Union[str, datetime.date]] = None
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
        df['symbol'] = symbol
        df['date'] = df['date'].apply(
             lambda x: pd.Timestamp(pd.Timestamp(x, unit = 'ms').date())
        )
        df = twap(df)
        return df.sort_values('date', ascending = True).reset_index(drop = True)

    start = None if start is None else resolve_date(start)
    end = nth_previous_trading_date(1) if end is None else resolve_date(end)
    try:
        result = tda.api.get_price_history(
            symbol.upper(),
            period = tda.api.PriceHistory.Period.TWENTY_YEARS,
            period_type = tda.api.PriceHistory.PeriodType.YEAR,
            frequency_type = tda.api.PriceHistory.FrequencyType.DAILY,
            frequency = tda.api.PriceHistory.Frequency.DAILY,
            start_datetime = datetime.datetime.combine(start, datetime.time()) \
            if start else None,
            end_datetime = datetime.datetime.combine(end, datetime.time())
        )
        assert result.status_code == 200, result.raise_for_status()
        return build_dataframe(result.json()['candles'])
    except Exception:
        logger.exception('error fetching tdahistoric daily data')
        return None
