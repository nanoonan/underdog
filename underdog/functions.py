import logging

from typing import (
    Any, Dict, List, Optional, Union
)

import pandas as pd

from parkit import (
    directory,
    File
)

from underdog.finviz import (
    fetch_ticker_details,
    fetch_ticker_news
)

from underdog.tda import (
    fetch_daily,
    fetch_intraday
)

from underdog.utility import (
    get_trading_segment,
    timestamp_to_timeslot,
    twap
)

logger = logging.getLogger(__name__)

def ticker_details(symbol: str) -> Dict[str, Optional[Union[float, bool, int]]]:
    return fetch_ticker_details(symbol)

def ticker_news(symbol: str) -> List[Dict[str, Any]]:
    return fetch_ticker_news(symbol)

def resample(
    df: pd.DataFrame,
    period: int
) -> pd.DataFrame:
    if period not in [1, 5, 30]:
        df = df.set_index('timestamp')
        rule = '{0}T'.format(period)
        df = df.resample(rule).aggregate(dict(
            open = 'first',
            close = 'last',
            low = 'min',
            high = 'max',
            volume = 'sum',
            date = 'first',
            symbol = 'first'
        )).dropna().reset_index(drop = False)
        df = twap(df)
        df['trading_segment'] = df['timestamp'] \
        .apply(lambda x: get_trading_segment(x))
        df['timeslot'] = df['timestamp'] \
        .apply(lambda x: timestamp_to_timeslot(x, period = period))
    return df

def intraday(
    symbol: str,
    period: int = 1
) -> pd.DataFrame:
    sample_period = period
    if sample_period % 30 == 0:
        source_period = 30
    elif sample_period % 5 == 0:
        source_period = 5
    else:
        source_period = 1
    if symbol.upper() not in directory('tdahistoric/intraday/{0}'.format(source_period)).names():
        df = fetch_intraday(symbol, period = source_period)
        if df is None:
            raise ValueError()
        return resample(df, sample_period)
    with File(
        'tdahistoric/intraday/{0}/{1}'.format(source_period, symbol.upper()),
        mode = 'rb'
    ) as file:
        return resample(pd.read_feather(file), sample_period)

def market() -> pd.DataFrame:
    if 'market' not in directory('polygon').names():
        raise ValueError()
    with File('polygon/market', mode = 'rb') as file:
        return pd.read_feather(file)

def daily(symbol: str) -> pd.DataFrame:
    if symbol.upper() not in directory('tdahistoric/daily').names():
        df = fetch_daily(symbol)
        if df is None:
            raise ValueError()
        return df
    with File('tdahistoric/daily/{0}'.format(symbol.upper()), mode = 'rb') as file:
        return pd.read_feather(file)
