import logging

import parkit

from parkit import (
    Array,
    Dict,
    task,
    wait
)

from underdog.functions import market
from underdog.tasks.logging import add_logger
from underdog.tasks.polygon import polygon

logger = logging.getLogger(__name__)

@task
def nightly_update():
    try:
        add_logger(logger, 'nightly_update')

        logger.info('start nightly update')

        execution = polygon()
        wait(lambda: execution.done)

        logger.info(execution)

        if execution.result:
            df = market()
            symbols = sorted(
                df[df['date'] == df['date']\
                .max()]\
                .sort_values('volume', ascending = False)\
                .head(1000)['symbol']\
                .to_list()
            )
            logger.info('finished successfully')
            # logger.info(symbols)
            #Dict('settings')['symbols'] = symbols
            # remove data not in symbols
            # run tdahistoric
    finally:
        logger.info('stop nightly update')
