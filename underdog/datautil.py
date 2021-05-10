import datetime
import logging

from typing import (
    List, Optional, Union
)

import numpy as np
import pandas as pd

from underdog.utility import (
    datestr_from_date,
    nth_next_trading_date,
    nth_previous_trading_date
)

logger = logging.getLogger(__name__)

def datestr_from_key(
    key: Optional[Union[str, datetime.date, int]],
    dates: Optional[List[Union[str, datetime.date]]]
) -> Optional[str]:
    if key is None:
        return None
    if isinstance(key, datetime.date):
        return datestr_from_date(key)
    if isinstance(key, str):
        return key
    if key >= 0 and dates:
        return datestr_from_date(nth_next_trading_date(key, anchor = dates[0]))
    if key < 0 and dates:
        return datestr_from_date(nth_previous_trading_date(abs(key + 1), anchor = dates[-1]))
    raise KeyError()

def twap(df: pd.DataFrame) -> pd.DataFrame:
    oh = np.abs(df['open'] - df['high'])
    ol = np.abs(df['open'] - df['low'])
    hl = np.abs(df['high'] - df['low'])
    lc = np.abs(df['low'] - df['close'])
    hc = np.abs(df['high'] - df['close'])
    ohlc = oh + hl + lc
    olhc = ol + hl + hc
    ohmean = (df['open'] + df['high']) / 2
    olmean = (df['open'] + df['low']) / 2
    hlmean = (df['high'] + df['low']) / 2
    lcmean = (df['low'] + df['close']) / 2
    hcmean = (df['high'] + df['close']) / 2
    ohlctwap = (oh / ohlc) * ohmean + (hl / ohlc) * hlmean + (lc / ohlc) * lcmean
    olhctwap = (ol / olhc) * olmean + (hl / olhc) * hlmean + (hc / olhc) * hcmean
    df['twap'] = (ohlctwap + olhctwap) / 2
    df['twap'] = np.where(
        df['twap'].isnull(),
        df['close'], df['twap']
    )
    return df
