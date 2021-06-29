import logging

from itertools import zip_longest
from typing import (
    Any,
    Callable,
    cast,
    Iterable,
    List,
    Optional
)

import cardinality
import pandas as pd

from parkit import (
    asyncable,
    get_concurrency,
    wait
)

from underdog.analysis.table import Table

logger = logging.getLogger(__name__)

@asyncable
def mapper(
    fn: Callable[..., Optional[int]],
    items: Iterable[Any],
    table: Optional[Table]
):
    if table is not None:
        rows = 0
        with table as results:
            for item in items:
                if item is not None:
                    rows = cast(int, fn(item, rows, results))
            table.rows = rows
    else:
        for item in items:
            if item is not None:
                fn(item)

def chunks(
    size: int,
    iterable: Iterable[Any],
    padvalue: Any = None
) -> Iterable[Any]:
    return zip_longest(*[iter(iterable)]*size, fillvalue = padvalue)

def mapresult(
    fn: Callable[..., Optional[int]],
    items: Iterable[Any],
    /, *,
    transform: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
    result_columns: Optional[Iterable[str]] = None,
) -> Optional[pd.DataFrame]:
    tasks = {}
    tables: Optional[List[Table]] = [] if result_columns is not None else None
    try:
        for chunk in chunks(
            int(cardinality.count(items) / get_concurrency()),
            items
        ):
            if tables is not None:
                assert result_columns is not None
                tables.append(Table(result_columns))
            tasks[mapper(fn, chunk, tables[-1] if tables is not None else None)] = \
            tables[-1] if tables is not None else None
        results = []
        while True:
            if len(tasks) == 0:
                break
            wait(lambda: any(task.done for task in tasks))
            for task in [task for task in tasks if task.done]:
                table = tasks[task]
                del tasks[task]
                if table is not None and transform is not None:
                    results.append(transform(table.as_pandas()))
                elif table is not None:
                    results.append(table.as_pandas())
        if len(results) > 0:
            return pd.concat(
                results,
                ignore_index = True
            )
        return None
    finally:
        if tables is not None:
            for table in tables:
                table.drop()
