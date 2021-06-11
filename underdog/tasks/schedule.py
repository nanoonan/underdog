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

schedulers = dict(
    polygon = lambda: Periodic(
        'scheduler/overnight',
        frequency = Frequency.Day,
        period = 1
    ),
    tdahistoric = lambda: Periodic(
        'scheduler/overnight',
        frequency = Frequency.Day,
        period = 1
    ),
    tdastream = lambda: Periodic(
        'scheduler/market-open',
        frequency = Frequency.Day,
        period = 1
    )
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
            status.append(dict(
                task = task.name,
                last_run = scheduler.last_run(task),
                next_run = scheduler.next_run(task)
            ))
    return status
