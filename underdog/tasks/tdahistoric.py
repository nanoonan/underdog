import logging

import pandas as pd

from parkit import (
    Dict,
    File,
    polling_loop
)

from underdog.tda import (
    fetch_daily,
    fetch_intraday
)
from underdog.utility import (
    nth_next_trading_date,
    nth_previous_trading_date,
)

logger = logging.getLogger(__name__)

def tdahistoric():
    try:
        logger.info('start tdahistoric')
        if 'symbols' not in Dict('settings'):
            logger.info('no symbols found')
            return
        logger.info('fetch historic ticker data')
        symbols = Dict('settings')['symbols']
        for _ in polling_loop(61):

            for symbol in symbols[0:30]:
                agg_df = None
                with File('tdahistoric/daily/{0}'.format(symbol.upper()), mode = 'rb') as file:
                    if not file.empty:
                        agg_df = pd.read_feather(file)
                start = None if agg_df is None else \
                nth_next_trading_date(1, anchor = agg_df['date'].max().date())
                if start > nth_previous_trading_date(1):
                    continue
                logger.info('fetch %s daily', symbol)
                df = fetch_daily(symbol, start = start)
                if df is not None:
                    if agg_df is None:
                        agg_df = df
                    else:
                        agg_df = pd.concat([agg_df, df])
                    agg_df = agg_df.sort_values('date').reset_index(drop = True)
                    with File(
                        'tdahistoric/daily/{0}'.format(symbol.upper()),
                        mode = 'wb'
                    ) as file:
                        agg_df.to_feather(file)

                for period in [1, 5, 30]:
                    agg_df = None
                    with File(
                        'tdahistoric/intraday/{0}/{1}'.format(period, symbol.upper()),
                        mode = 'rb'
                    ) as file:
                        if not file.empty:
                            agg_df = pd.read_feather(file)
                    start = None if agg_df is None else \
                    nth_next_trading_date(1, anchor = agg_df['date'].max().date())
                    logger.info('fetch %s intraday %i', symbol, period)
                    df = fetch_intraday(symbol, start = start, period = period)
                    if df is not None:
                        if agg_df is None:
                            agg_df = df
                        else:
                            agg_df = pd.concat([agg_df, df])
                        agg_df = agg_df.sort_values('timestamp').reset_index(drop = True)
                        with File(
                            'tdahistoric/intraday/{0}/{1}'.format(period, symbol.upper()),
                            mode = 'wb'
                        ) as file:
                            agg_df.to_feather(file)

            symbols = symbols[30:]
            if len(symbols) == 0:
                break
    finally:
        logger.info('stop tdahistoric')
