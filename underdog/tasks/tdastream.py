import logging
import time
import typing

from typing import (
    Any, Optional
)

import numpy as np
import pandas as pd

from parkit import (
    get_site,
    Dict,
    File
)

import underdog.tda as tda

from underdog.utility import (
    is_trading_date,
    market_open,
    timestamp_to_timeslot,
    today
)

logger = logging.getLogger(__name__)

class Stream(tda.Stream):

    def __init__(
        self,
        *,
        site: str,
        config: typing.Dict[str, typing.Dict[str, Any]],
        realtime: bool = True,
        interrupt: Optional[float] = None
    ):
        super().__init__(site = site, config = config, realtime = realtime, interrupt = interrupt)
        self._config = config
        if 'chart' in self._config.keys():
            self._chart_file = self._config['chart']['file']
            self._chart_symbols = self._config['chart']['symbols']
            assert len(self._chart_file.shape) == 3 and self._chart_file.dtype == np.float64
            assert self._chart_file.shape[0] == 960
            assert self._chart_file.shape[1] == len(self._chart_symbols)
            assert self._chart_file.shape[2] == 6
            self._chart_file.mode = 'rb'
            self._chart_cache = np.ndarray(
                shape = self._chart_file.shape,
                dtype = self._chart_file.dtype,
                buffer = self._chart_file.content
            )
            self._chart_file.mode = 'wb'

    def on_trade_event(self, event):
        pass

    def on_timer_event(self):
        pass

    def on_chart_event(self, event):
        if 'chart' in self._config:
            if isinstance(event, int):
                if event > 0:
                    logger.info('flushing %i events', event)
                    self._chart_file.content = self._chart_cache.data
            else:
                timeslot = timestamp_to_timeslot(
                    pd.Timestamp(pd.Timestamp(event[2], tz = 'US/Eastern', unit = 'ms'))
                )
                logger.info('%i %s', timeslot, str(event))
                index = self._chart_symbols.index(event[1])
                self._chart_cache[timeslot, index, :] = \
                [
                    np.float64(event[3]), np.float64(event[4]), np.float64(event[5]),
                    np.float64(event[6]), np.float64(event[7]), 1.
                ]

#
# Data Format
# shape = (960, num symbols, 6)
# last axis columns = open, close, high, low, volume, filled
#

def tdastream():
    try:
        if not is_trading_date(today()):
            return
        logger.info('start tdastream')
        if 'symbols' not in Dict('settings'):
            logger.info('no symbols found')
            return
        symbols = sorted(Dict('settings')['symbols'])
        data = np.zeros((960, len(symbols), 6), dtype = np.float64)
        chart_file = File('tdastream/chart', mode = 'wb')
        chart_file.content = data.data
        chart_file.shape = data.shape
        chart_file.dtype = data.dtype
        logger.info('file size %i', chart_file.size)
        stream = Stream(
            site = get_site(),
            config = dict(
                chart = dict(symbols = symbols, file = chart_file),
                trade = dict(symbols = symbols)
            )
        )
        stream.start()
        while market_open():
            time.sleep(60)
    finally:
        logger.info('stop tdastream')
