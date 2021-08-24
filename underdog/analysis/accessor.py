import logging

logger = logging.getLogger(__name__)

INTRADAY_TIMESLOT: int = 0
INTRADAY_OPEN: int = 1
INTRADAY_HIGH: int = 2
INTRADAY_LOW: int = 3
INTRADAY_CLOSE: int = 4
INTRADAY_VOLUME: int = 5
INTRADAY_TWAP: int = 6
INTRADAY_DATE: int = 7

DAILY_OPEN: int = 0
DAILY_HIGH: int = 1
DAILY_LOW: int = 2
DAILY_CLOSE: int = 3
DAILY_VOLUME: int = 4
DAILY_DATE: int = 5
DAILY_TWAP: int = 6
