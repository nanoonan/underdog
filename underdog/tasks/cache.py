import logging

from typing import (
    Iterable, Optional, Set
)

import pandas as pd

from parkit import (
    asyncable,
    compactify,
    Directory,
    File,
    ObjectNotFoundError
)

from underdog.finviz.fetch import (
    fetch_ticker_details,
    fetch_ticker_news
)
from underdog.polygon.fetch import fetch_market
from underdog.tda.fetch import (
    fetch_daily,
    fetch_intraday
)
from underdog.utility import (
    nth_next_trading_date,
    nth_previous_trading_date,
)

logger = logging.getLogger(__name__)

def clean_directories(site_uuid: Optional[str]):

    logger.info('cleaning cache')
    for obj in Directory('cache', create = True, site_uuid = site_uuid):
        if obj.name == 'market' and isinstance(obj, File):
            try:
                metadata = obj.metadata
                if metadata['content-type'] == 'application/python-pandas-dataframe' and \
                metadata['content-properties']['type'] == 'pandas.core.frame.DataFrame' and \
                metadata['content-properties']['nrows'] > 0:
                    continue
            except KeyError:
                pass
        logger.info('removing %s from cache', obj.name)
        obj.drop()

    for directory in [
        Directory(path, create = True, site_uuid = site_uuid)
        for path in [
            'cache/daily', 'cache/intraday/5',
            'cache/intraday/1'
        ]
    ]:
        logger.info('cleaning %s', directory.path)
        for obj in directory:
            if isinstance(obj, File):
                try:
                    metadata = obj.metadata
                    if metadata['content-type'] == 'application/python-pandas-dataframe' and \
                    metadata['content-properties']['type'] == 'pandas.core.frame.DataFrame' and \
                    metadata['content-properties']['nrows'] > 0:
                        continue
                except KeyError:
                    pass
            logger.info('removing %s from %s', obj.name, directory.path)
            obj.drop()

    logger.info('cleaning %s', 'cache/tickers')
    for obj in Directory('cache/tickers', create = True, site_uuid = site_uuid):
        if isinstance(obj, File):
            try:
                metadata = obj.metadata
                if metadata['content-type'] == 'application/python-pickle' and \
                metadata['content-properties']['type'] == 'builtins.dict':
                    continue
            except KeyError:
                pass
        logger.info('removing %s from cache/tickers', obj.name)
        obj.drop()

def update_daily(
    symbols: Set[str],
    site_uuid: Optional[str]
):

    for symbol in symbols:

        try:
            agg_df = File(
                'cache/daily/{0}'.format(symbol),
                create = False, bind = True,
                site_uuid = site_uuid
            ).get_content()
        except ObjectNotFoundError:
            agg_df = None

        start = None if agg_df is None else \
        nth_next_trading_date(1, anchor = agg_df['date'].max().date())

        if start is not None and start > nth_previous_trading_date(1):
            continue

        logger.info('fetch %s daily', symbol)

        df = fetch_daily(symbol, start = start)

        if df is not None:
            if agg_df is None:
                agg_df = df
            else:
                agg_df = pd.concat([agg_df, df])
            agg_df = agg_df.sort_values('date').reset_index(drop = True)
            File(
                'cache/daily/{0}'.format(symbol),
                create = True, bind = True, site_uuid = site_uuid
            ).set_content(agg_df)

def update_intraday(
    symbols: Set[str],
    site_uuid: Optional[str]
):

    for period in [1, 5]:

        for symbol in symbols:

            try:
                agg_df = File(
                    'cache/intraday/{0}/{1}'.format(period, symbol),
                    create = False, bind = True,
                    site_uuid = site_uuid
                ).get_content()
            except ObjectNotFoundError:
                agg_df = None

            start = None if agg_df is None else \
            nth_next_trading_date(1, anchor = agg_df['date'].max().date())

            if start is not None and start > nth_previous_trading_date(1):
                continue

            logger.info('fetch %s intraday %i', symbol, period)
            df = fetch_intraday(
                symbol,
                start = start,
                period = period,
            )

            if df is not None:
                if agg_df is None:
                    agg_df = df
                else:
                    agg_df = pd.concat([agg_df, df])
                agg_df = agg_df.sort_values(['date', 'timeslot']).reset_index(drop = True)
                File(
                    'cache/intraday/{0}/{1}'.format(period, symbol),
                    create = True, bind = True, site_uuid = site_uuid
                ).set_content(agg_df)

def update_market(site_uuid: Optional[str]):
    try:
        df = File(
            'cache/market', create = False, bind = True, site_uuid = site_uuid
        ).get_content()
    except ObjectNotFoundError:
        df = None
    df = fetch_market(df)
    if df is not None:
        File(
            'cache/market', create = True, bind = True, site_uuid = site_uuid
        ).set_content(df)

def update_tickers(
    symbols: Set[str],
    site_uuid: Optional[str]
):
    for symbol in symbols:
        try:
            file = File(
                'cache/tickers/{0}'.format(symbol),
                create = False, bind = True,
                site_uuid = site_uuid
            )
            metadata = file.metadata
            if metadata['content-type'] == 'application/python-pickle' and \
            metadata['content-properties']['type'] == 'builtins.dict' and \
            (pd.Timestamp.now() - pd.Timestamp(metadata['last-modified'])).days < 7:
                continue
        except (KeyError, ObjectNotFoundError):
            pass
        data = dict(
            details = fetch_ticker_details(symbol),
            news = fetch_ticker_news(symbol)
        )
        if data['details'] is None and data['news'] is None:
            try:
                File(
                    'cache/tickers/{0}'.format(symbol),
                    create = False, bind = True,
                    site_uuid = site_uuid
                ).drop()
            except ObjectNotFoundError:
                pass
        else:
            logger.info('fetch %s tickers', symbol)
            File(
                'cache/tickers/{0}'.format(symbol),
                create = True, bind = True,
                site_uuid = site_uuid
            ).set_content(data)

@asyncable(
    async_limit = 1,
    disable_sync = True,
    fullpath = True
)
def update_cache(
    symbols: Iterable[str],
    site_uuid: Optional[str] = None
):
    logger.info('start update_cache')

    paths = [
        'cache/daily', 'cache/intraday/1',
        'cache/intraday/5', 'cache/tickers'
    ]

    compactify(site_uuid)

    clean_directories(site_uuid)

    cache_symbols: Set[str] = set()
    for path in paths:
        cache_symbols.update(
            Directory(path, create = True, site_uuid = site_uuid).names()
        )

    include_symbols = set(symbols)
    exclude_symbols = cache_symbols.difference(include_symbols)

    update_market(site_uuid)

    logger.info('cache size is %i symbols', len(cache_symbols))
    logger.info('cache size will be %i symbols', len(include_symbols))
    logger.info('removing %i symbols', len(exclude_symbols))
    logger.info('adding %i symbols', len(include_symbols.difference(cache_symbols)))

    for directory in [
        Directory(path, create = True, site_uuid = site_uuid) for path in paths
    ]:
        for symbol in exclude_symbols:
            try:
                logger.info('removing %s from %s', symbol, directory.path)
                directory[symbol].drop()
            except ObjectNotFoundError:
                pass

    update_tickers(include_symbols, site_uuid)

    update_daily(include_symbols, site_uuid)

    update_intraday(include_symbols, site_uuid)

    logger.info('finish update_cache')
