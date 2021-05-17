import datetime
import logging

from typing import (
    List, Optional, Union
)

import numpy as np
import pandas as pd

from underdog.utility import (
    date_from_datestr,
    nth_next_trading_date,
    nth_previous_trading_date
)

logger = logging.getLogger(__name__)

def date_from_key(
    key: Optional[Union[str, datetime.date, int]],
    dates: List[datetime.date]
) -> Optional[datetime.date]:
    if key is None:
        return None
    if isinstance(key, datetime.date):
        return key
    if isinstance(key, str):
        return date_from_datestr(key)
    if key >= 0 and dates:
        return nth_next_trading_date(key, anchor = dates[0])
    if key < 0 and dates:
        return nth_previous_trading_date(abs(key + 1), anchor = dates[-1])
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

def twap_(o, h, l, c):
    oh = np.abs(o - h)
    ol = np.abs(o - l)
    hl = np.abs(h - l)
    lc = np.abs(l - c)
    hc = np.abs(h - c)
    ohlc = oh + hl + lc
    olhc = ol + hl + hc
    ohmean = (o + h) / 2
    olmean = (o + l) / 2
    hlmean = (h + l) / 2
    lcmean = (l + c) / 2
    hcmean = (h + c) / 2
    ohlctwap = (oh / ohlc) * ohmean + (hl / ohlc) * hlmean + (lc / ohlc) * lcmean
    olhctwap = (ol / olhc) * olmean + (hl / olhc) * hlmean + (hc / olhc) * hcmean
    return (ohlctwap + olhctwap) / 2
