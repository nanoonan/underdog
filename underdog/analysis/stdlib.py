import logging
import math
import mmap

from itertools import zip_longest
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Optional
)

import cardinality
import numpy as np
import pandas as pd

from parkit import (
    asyncable,
    File,
    get_concurrency,
    wait
)

from underdog.analysis.table import Table

logger = logging.getLogger(__name__)

@asyncable
def frame_mapper(
    fn: Callable[..., Optional[pd.DataFrame]],
    items: Iterable[Any],
    file: File,
    **kwargs
):
    logger.info('frame mapper started')
    cache = {}
    buffer = mmap.mmap(-1, 2147483648)
    for item in items:
        if item is not None:
            df = fn(item, cache, **kwargs)
            if df is not None:
                if len(df) > 0:
                    if file.columns is None:
                        file.columns = df.columns.to_list()
                    else:
                        assert file.columns == df.columns.to_list()
                    buffer.write(np.ascontiguousarray(df.to_numpy()).data.cast('B'))
    file.set_content(memoryview(buffer[0:buffer.tell()]))
    del buffer

@asyncable
def table_mapper(
    fn: Callable[..., None],
    items: Iterable[Any],
    table: Optional[Table]
):
    logger.info('frame mapper started')
    cache = {}
    if table is not None:
        with table as view:
            for item in items:
                if item is not None:
                    fn(item, view, cache)
    else:
        for item in items:
            if item is not None:
                fn(item, cache)

def chunks(
    size: int,
    iterable: Iterable[Any],
    padvalue: Any = None
) -> Iterable[Any]:
    return zip_longest(*[iter(iterable)]*size, fillvalue = padvalue)

def maptable(
    fn: Callable[..., None],
    items: Iterable[Any],
    /, *,
    transform: Optional[
        Callable[[pd.DataFrame], pd.DataFrame]
    ] = None,
    columns: Optional[Iterable[str]] = None
) -> Optional[pd.DataFrame]:
    tasks = {}
    tables: Optional[List[Table]] = [] if columns is not None else None
    try:
        size = cardinality.count(items)
        for chunk in chunks(
            int(math.ceil(size / get_concurrency())) if size > get_concurrency() else 1,
            items
        ):
            if tables is not None:
                assert columns is not None
                tables.append(Table(columns = columns))
            tasks[table_mapper(fn, chunk, tables[-1] if tables is not None else None)] = \
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

def mapframe(
    fn: Callable[..., Optional[pd.DataFrame]],
    items: Iterable[Any],
    /, *,
    transform: Optional[
        Callable[[pd.DataFrame], pd.DataFrame]
    ] = None,
    **kwargs
) -> Optional[pd.DataFrame]:
    tasks = {}
    files = []
    try:
        size = cardinality.count(items)
        for chunk in chunks(
            int(math.ceil(size / get_concurrency())) if size > get_concurrency() else 1,
            items
        ):
            file = File()
            file.columns = None
            files.append(file)
            tasks[frame_mapper(fn, chunk, files[-1], **kwargs)] = files[-1]
        results = []
        while True:
            if len(tasks) == 0:
                break
            wait(lambda: any(task.done for task in tasks))
            for task in [task for task in tasks if task.done]:
                file = tasks[task]
                del tasks[task]
                task.drop()
                data = file.get_content()
                if data is not None and file.columns is not None:
                    shape = (
                        int(len(data) / (8 * len(file.columns))),
                        len(file.columns)
                    )
                    strides = (8 * len(file.columns), 8)
                    df = pd.DataFrame(
                        columns = file.columns,
                        data = np.lib.stride_tricks.as_strided(
                            np.frombuffer(
                                file.get_content(), dtype = np.float64
                            ),
                            shape,
                            strides
                        )
                    )
                    if transform is not None:
                        df = transform(df)
                    results.append(df)
        if len(results) > 0:
            return pd.concat(
                results,
                ignore_index = True
            )
        return None
    finally:
        for file in files:
            file.drop()
        for task in tasks:
            task.drop()
