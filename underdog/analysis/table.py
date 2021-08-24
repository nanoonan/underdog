import logging

from typing import (
    Any,
    Iterable,
    Optional
)

import cardinality
import numba
import numpy as np
import pandas as pd

from parkit import FileIO

logger = logging.getLogger(__name__)

@numba.experimental.jitclass([
    ('_buffer', numba.typeof(memoryview(bytearray(8)).cast('d',(1,)))),
    ('_columns', numba.types.ListType(numba.types.unicode_type))
])
class RowFloat64():

    def __init__(self, buffer, columns):
        self._columns = columns
        self._buffer = buffer

    @property
    def buffer(self):
        return self._buffer

    @property
    def colsize(self):
        return len(self._columns)

    @property
    def columns(self):
        return self._columns

    def __getitem__(self, key):
        return self._buffer[self._columns.index(key)]

    def __setitem__(self, key, value):
        self._buffer[self._columns.index(key)] = value

@numba.experimental.jitclass([
    ('_table_index', numba.int64),
    ('_row_buffer', numba.typeof(memoryview(bytearray(8)).cast('d', (1,)))),
    ('_table_buffer', numba.typeof(memoryview(bytearray(8)).cast('d', [1,1]))),
    ('_columns', numba.types.ListType(numba.types.unicode_type))
])
class TableView():

    def __init__(self, table_buffer, table_index, row_buffer, columns):
        self._table_buffer = table_buffer
        self._row_buffer = row_buffer
        self._table_index = table_index
        self._columns = columns

    @property
    def rowsize(self):
        return self._table_index

    @property
    def colsize(self):
        return len(self._columns)

    @property
    def columns(self):
        return self._columns

    def row(self, index):
        if index < 0 or index > self._table_index - 1:
            raise ValueError()
        return RowFloat64(self._table_buffer[index], self._columns)

    def newrow(self):
        return RowFloat64(self._row_buffer, self._columns)

    def addrow(self, row):
        self._table_buffer[self._table_index,:] = row.buffer
        self._table_index += 1

class Table(FileIO):

    _view: Optional[TableView] = None

    def __init__(
        self,
        path: Optional[str] = None,
        /, *,
        columns: Optional[Iterable[str]] = None,
        maxrows: int = 1024000,
        create: bool = True,
        bind: bool = False,
        site_uuid: Optional[str] = None
    ):
        self._columns: Iterable[str]
        self._maxrows: int
        self._rows: int

        def on_init(created:bool):
            if created:
                if columns is None or maxrows < 0:
                    raise ValueError()
                self._columns = columns
                self._maxrows = maxrows
                self._rows = 0

        super().__init__(
            path,
            bufsize = maxrows * 8 * cardinality.count(columns),
            create = create,
            bind = bind,
            site_uuid = site_uuid,
            on_init = on_init
        )

        self._view = None

    def __enter__(self):
        self.mode = 'wb'
        super().__enter__()
        table_buffer = memoryview(self._buffer)
        table_buffer = table_buffer.cast(
            'd',
            (
                self._maxrows,
                cardinality.count(self._columns)
            )
        )

        self._rows = 0
        row_buffer = memoryview(bytearray(
            8 * cardinality.count(self._columns)
        )).cast('d')
        self._view = TableView(
            table_buffer, 0, row_buffer, numba.typed.List(self._columns)
        )
        return self._view

    def __exit__(self, error_type: type, error: Optional[Any], traceback: Any):
        assert self._view is not None
        self._rows = self._view.rowsize
        self._view = None
        self._extent = self._rows * 8 * cardinality.count(self._columns)
        super().__exit__(error_type, error, traceback)

    @property
    def rows(self) -> int:
        return self._rows

    @rows.setter
    def rows(self, value: int):
        self._rows = value

    @property
    def columns(self) -> Iterable[str]:
        assert self._columns is not None
        return self._columns

    def as_pandas(self) -> pd.DataFrame:
        if self._rows > 0:
            return pd.DataFrame(
                columns = self._columns,
                data = self.as_numpy()
            )
        raise ValueError()

    def as_numpy(self) -> np.ndarray:
        if self._rows > 0:
            shape = (
                self._rows,
                cardinality.count(self._columns)
            )
            dtype = np.float64
            strides = (
                8 * cardinality.count(self._columns), 8
            )
            return np.lib.stride_tricks.as_strided(
                np.frombuffer(
                    self._content_binary,
                    dtype
                ),
                shape,
                strides
            )
        raise ValueError()
