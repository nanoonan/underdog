import logging

from typing import (
    Any,
    Iterable,
    Optional
)

import cardinality
import numpy as np
import pandas as pd

from parkit import FileIO

logger = logging.getLogger(__name__)

class Table(FileIO):

    def __init__(
        self,
        columns: Iterable[str],
        /, *,
        rows: int = 1024000
    ):
        super().__init__(
            bufsize = rows * 8 * cardinality.count(columns),
            create = True
        )
        self._columns = columns
        self._rows = rows

    def __enter__(self):
        self.mode = 'wb'
        super().__enter__()
        view = memoryview(self._buffer)
        view = view.cast('d', (self._rows, cardinality.count(self._columns)))
        self._rows = 0
        return view

    def __exit__(self, error_type: type, error: Optional[Any], traceback: Any):
        self._extent = self._rows * (8 * cardinality.count(self._columns))
        super().__exit__(error_type, error, traceback)

    @property
    def rows(self) -> int:
        return self._rows

    @rows.setter
    def rows(self, value: int):
        self._rows = value

    @property
    def columns(self) -> Iterable[str]:
        return self._columns

    def as_pandas(self):
        return pd.DataFrame(
            columns = self._columns,
            data = self.as_numpy()
        )

    def as_numpy(self):
        shape = (self._rows, cardinality.count(self._columns))
        dtype = np.float64
        strides = (8 * cardinality.count(self._columns), 8)
        return np.lib.stride_tricks.as_strided(
            np.frombuffer(
                self._content_binary,
                dtype
            ),
            shape,
            strides
        )
