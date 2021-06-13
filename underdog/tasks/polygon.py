import logging

from parkit import task

from underdog.polygon import fetch_market
from underdog.tasks.logging import add_logger

logger = logging.getLogger(__name__)

@task
def polygon():
    try:
        add_logger(logger, 'polygon')
        logger.info('start polygon')
        fetch_market()
        return True
    finally:
        logger.info('stop polygon')
