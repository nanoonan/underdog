import datetime
import logging

from typing import (
    Any, Callable, Dict, List, Set, Union
)

from parkit import (
    bind_task,
    create_task,
    Frequency,
    ObjectNotFoundError,
    Periodic
)

logger = logging.getLogger(__name__)

overnight_scheduler = lambda: Periodic(
    'scheduler/overnight',
    frequency = Frequency.Day,
    period = 1,
    # start = 'tomorrow 1 am'
    start = 'now'
)

market_open_scheduler = lambda: Periodic(
    'scheduler/market-open',
    frequency = Frequency.Day,
    period = 1,
    start = 'tomorrow 3:55 am'
)

schedulers = dict(
    polygon = overnight_scheduler,
    tdahistoric = overnight_scheduler,
    tdastream = market_open_scheduler
)

def schedule(
    target: Callable[..., Any],
    enable: bool = True
):
    scheduler = schedulers[target.__name__]()
    if enable:
        task = create_task(target, name = target.__name__)
        if task not in scheduler:
            logger.info('schedule %s', target.__name__)
            scheduler.schedule(task)
    else:
        try:
            task = bind_task(target.__name__)
            if task in scheduler:
                logger.info('unschedule %s', target.__name__)
                scheduler.unschedule(task)
        except ObjectNotFoundError:
            pass

def get_schedulers() -> List[str]:
    paths = []
    for scheduler in {builder() for builder in schedulers.values()}:
        paths.append(scheduler.path)
    return paths

def scheduled() -> List[Dict[str, Union[None, str, datetime.datetime]]]:
    status = []
    for scheduler in {builder() for builder in schedulers.values()}:
        for task in scheduler.tasks:
            status.append(task.name)
    return status
