import logging

from underdog.polygon import fetch_market

logger = logging.getLogger(__name__)

def polygon():
    try:
        logger.info('start polygon')
        fetch_market()
    finally:
        logger.info('stop polygon')
