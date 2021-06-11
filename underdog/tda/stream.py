import logging

from typing import (
    Any, Dict
)

from parkit import (
    getenv,
    set_site,
)
from tda.streaming import StreamClient

import underdog.constants as constants

from underdog.asyncthread import (
    AsyncThread,
    AsyncThreadState
)
from underdog.tda.tdaclient import tda

logger = logging.getLogger(__name__)

class Stream(AsyncThread):

    def __init__(
        self,
        *,
        site: str,
        config: Dict[str, Dict[str, Any]],
        realtime: bool = True
    ):
        super().__init__()
        set_site(site)
        self._account_id = int(getenv(constants.TDA_ACCOUNT_ID_ENVNAME))
        self._stream = StreamClient(tda.api, account_id = self._account_id)
        self._config = config
        self._realtime = realtime

    def on_chart_event(self, event):
        pass

    def on_quote_event(self, event):
        pass

    def on_trade_event(self, event):
        pass

    def _chart_handler(self, message: Dict[str, Any]) -> None:
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
                        self.on_chart_event(
                            (
                                timestamp, symbol,
                                candle_timestamp, open, close, high, low, volume
                            )
                        )
        except Exception:
            logger.exception('error handling chart event')

    def _trade_handler(self, message: Dict[str, Any]) -> None:
        try:
            if message and 'content' in message:
                timestamp = message['timestamp'] if 'timestamp' in message else None
                for data in message['content']:
                    if 'key' in data:
                        symbol = data['key']
                        trade_timestamp = data['TRADE_TIME'] \
                        if 'TRADE_TIME' in data else None
                        last_price = data['LAST_PRICE'] if 'LAST_PRICE' in data else None
                        last_size = int(data['LAST_SIZE']) if 'LAST_SIZE' in data else None
                        self.on_trade_event(
                            (
                                timestamp, symbol,
                                trade_timestamp, last_price, last_size
                            )
                        )
        except Exception:
            logger.exception('error handling trade event')

    def _quote_handler(self, message: Dict[str, Any]) -> None:
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
                        self.on_quote_event(
                            (
                                timestamp, symbol,
                                quote_timestamp, bid_price, ask_price,
                                last_timestamp, last_price, last_size
                            )
                        )
        except Exception:
            logger.exception('error handling quote event')

    async def _start(self) -> None:
        await self._stream.login()
        if self._realtime:
            await self._stream.quality_of_service(StreamClient.QOSLevel.EXPRESS)
        else:
            await self._stream.quality_of_service(StreamClient.QOSLevel.DELAYED)
        for stream_type, args in self._config.items():
            if stream_type == 'quote':
                self._stream.add_level_one_equity_handler(self._quote_handler)
                await self._stream.level_one_equity_subs(args['symbols'])
            elif stream_type == 'chart':
                self._stream.add_chart_equity_handler(self._chart_handler)
                await self._stream.chart_equity_subs(args['symbols'])
            elif stream_type == 'trade':
                self._stream.add_timesale_equity_handler(self._trade_handler)
                await self._stream.timesale_equity_subs(args['symbols'])
            else:
                raise ValueError()

    async def _handle_messages(self) -> None:
        while True:
            await self._stream.handle_message()

    def start(self) -> None:
        super().start()
        super().run_task(self._start(), block = True)
        super().run_task(self._handle_messages(), block = False)

    def add(
        self,
        config: Dict[str, Dict[str, Any]]
    ) -> None:
        assert self.state == AsyncThreadState.Started
        for stream_type, args in config.items():
            if stream_type in self._config:
                difference = list(set(args['symbols']) - set(self._config[stream_type]['symbols']))
                if difference:
                    if stream_type == 'chart':
                        self._stream.chart_equity_add(difference)
                        self._config[stream_type]['symbols'].extend(difference)
