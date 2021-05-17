import enum
import logging
import threading

from typing import (
    Any, List
)

import pandas as pd

from parkit import (
    getenv,
    Log
)
from tda.streaming import StreamClient

import underdog.constants as constants

from underdog.asyncthread import (
    AsyncThread,
    AsyncThreadState
)
from underdog.tdaclient import tda

logger = logging.getLogger(__name__)

class StreamType(enum.Enum):
    Quote = 1
    Chart = 2

class LogProcessorThread(threading.Thread):

    def __init__(
        self,
        log: Log,
        handler: Any
    ):
        super().__init__()
        self._log = log
        self._handler = handler

    def run(self):
        length = 0
        while True:
            self._log.wait(length)
            cache = []
            with snapshot(self._log):
                for obj in self._log[length:]:
                    if obj is None:
                        return
                    cache.append(obj)
                length = len(self._log)
            for obj in cache:
                if not self._handler(obj):
                    return

class StreamReader():
    pass

class StreamWriter(AsyncThread):

    def __init__(
        self,
        name: str,
        config
    ):
        super().__init__()
        self._account_id = int(getenv(constants.TDA_ACCOUNT_ID_ENVNAME))
        self._stream = StreamClient(tda.api, account_id = self._account_id)
        self._log = Log(constants.STREAM_PATH + '/' + name)
        self._log.clear()
        self._config = config

    @property
    def log(self):
        return self._log

    def _log_chart_writer(self, message):
        try:
            if message and 'content' in message:
                timestamp = message['timestamp'] if 'timestamp' in message else None
                for data in message['content']:
                    if 'key' in data:
                        symbol = data['key']
                        candle_timestamp = data['CHART_TIME'] if 'CHART_TIME' in data else None
                        open = data['OPEN_PRICE'] if 'OPEN_PRICE' in data else None
                        close = data['CLOSE_PRICE'] if 'CLOSE_PRICE' in data else None
                        high = data['HIGH_PRICE'] if 'HIGH_PRICE' in data else None
                        low = data['LOW_PRICE'] if 'LOW_PRICE' in data else None
                        volume = int(data['VOLUME']) if 'VOLUME' in data else None
                        self._log.append(
                            (
                                StreamType.Chart.value, timestamp, symbol,
                                candle_timestamp, open, close, high, low, volume
                            )
                        )
        except Exception as exc:
            logger.error('error')

    def _log_quote_writer(self, message):
        try:
            if message and 'content' in message:
                timestamp = message['timestamp'] if 'timestamp' in message else None
                for data in message['content']:
                    if 'key' in data:
                        symbol = data['key']
                        quote_timestamp = data['QUOTE_TIME_IN_LONG'] \
                        if 'QUOTE_TIME_IN_LONG' in data else None
                        bid_price = data['BID_PRICE'] if 'BID_PRICE' in data else None
                        ask_price = data['ASK_PRICE'] if 'ASK_PRICE' in data else None
                        last_price = data['LAST_PRICE'] if 'LAST_PRICE' in data else None
                        last_size = int(data['LAST_SIZE']) if 'LAST_SIZE' in data else None
                        last_timestamp = data['TRADE_TIME_IN_LONG'] \
                        if 'TRADE_TIME_IN_LONG' in data else None
                        self._log.append(
                            (
                                StreamType.Quote.value, timestamp, symbol,
                                quote_timestamp, bid_price, ask_price,
                                last_timestamp, last_price, last_size
                            )
                        )
        except Exception as exc:
            logger.error('error')

    async def _start(self):
        await self._stream.login()
        await self._stream.quality_of_service(StreamClient.QOSLevel.EXPRESS)
        for stream_type, symbols in self._config.items():
            if stream_type.value == StreamType.Quote.value:
                self._stream.add_level_one_equity_handler(self._log_quote_writer)
                await self._stream.level_one_equity_subs(symbols)
            elif stream_type.value == StreamType.Chart.value:
                self._stream.add_chart_equity_handler(self._log_chart_writer)
                await self._stream.chart_equity_subs(symbols)
            else:
                raise RuntimeError()

    async def _handle_messages(self):
        while True:
            await self._stream.handle_message()

    def start(self) -> None:
        super().start()
        super().run_task(self._start(), block = True)
        super().run_task(self._handle_messages(), block = False)

    def add(
        self,
        config
    ) -> None:
        assert self.state == AsyncThreadState.Started
        for stream_type, symbols in config.items():
            if stream_type in self._config:
                difference = list(set(symbols) - set(self._config[stream_type]))
                if difference:
                    if stream_type.value == StreamType.Chart.value:
                        self._stream.chart_equity_add(difference)
                        self._config[stream_type].extend(difference)
