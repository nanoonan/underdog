import datetime
import logging
import time
import typing

from typing import (
    Any, Iterable, Optional
)

import cardinality
import pandas as pd

from parkit import (
    Array,
    asyncable,
    Dict,
    ObjectNotFoundError,
    transaction
)

import underdog.constants as constants
import underdog.tda.stream as tda

from underdog.tda.fetch import fetch_intraday

logger = logging.getLogger(__name__)

class RealtimeStream(tda.Stream):

    def __init__(
        self,
        *,
        config: typing.Dict[str, typing.Dict[str, Any]],
        realtime: bool = True,
        interrupt: Optional[float] = None
    ):
        super().__init__(config = config, realtime = realtime, interrupt = interrupt)
        self._config = config
        self._nbbo = self._trades = None
        if 'quote' in self._config:
            self._nbbo = self._config['quote']['nbbo']
        if 'trade' in self._config:
            self._trades = self._config['trade']['trades']

    def on_trade_events(self, events):
        if self._trades is not None:
            with transaction(self._trades):
                for event in events:
                    self._trades.append(
                        dict(
                            symbol = event[1],
                            timestamp = event[2],
                            price = event[3],
                            size = event[4]
                        )
                    )

    def on_quote_events(self, events):
        if self._nbbo is not None:
            with transaction(self._nbbo):
                for event in events:
                    if event[1] not in self._nbbo:
                        self._nbbo[event[1]] = dict(bid = event[3], ask = event[4])
                    else:
                        nbbo = self._nbbo[event[1]]
                        nbbo['bid'] = event[3] if event[3] is not None else nbbo['bid']
                        nbbo['ask'] = event[4] if event[4] is not None else nbbo['ask']
                        self._nbbo[event[1]] = nbbo

    def on_interrupt_event(self):
        pass

    def on_chart_events(self, events):
        pass

@asyncable(
    async_limit = 1,
    disable_sync = True,
    fullpath = True
)
def realtime_stream(
    symbols: Iterable[str],
    bufsize: int,
    site_uuid: Optional[str]
):
    if cardinality.count(symbols) == 0 or \
    cardinality.count(symbols) > constants.TDA_MAX_REALTIME_SYMBOLS:
        raise ValueError()

    with transaction('realtime', site_uuid = site_uuid):
        nbbo = Dict(
            'realtime/nbbo',
            create = True, bind = True,
            site_uuid = site_uuid
        )
        nbbo.clear()
        for symbol in symbols:
            nbbo[symbol] = dict(bid = None, ask = None)
        trades = Array(
            'realtime/trades',
            maxsize = bufsize,
            create = True, bind = True
        )
        if trades.maxsize != bufsize:
            trades.drop()
            trades = Array(
                'realtime/trades',
                maxsize = bufsize,
                create = True, bind = True
            )
        else:
            trades.clear()

    stream = RealtimeStream(
        config = dict(
            chart = dict(symbols = symbols),
            trade = dict(symbols = symbols, trades = trades),
            quote = dict(symbols = symbols, nbbo = nbbo)
        )
    )

    stream.start()

    while True:
        time.sleep(60)

def get_intraday(
    symbol: str,
    /, *,
    period: int = 1
) -> pd.DataFrame:
    if period not in [1, 5]:
        raise ValueError()
    sample_period = period
    if sample_period % 5 == 0:
        source_period = 5
    else:
        source_period = 1
    df = fetch_intraday(
        symbol, period = source_period,
        start = datetime.datetime.now().date(),
        end = datetime.datetime.now().date()
    )
    if df is None:
        raise ObjectNotFoundError()
    return df
