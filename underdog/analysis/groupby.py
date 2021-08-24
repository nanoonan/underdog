import logging

import numba
import numpy as np

logger = logging.getLogger(__name__)

def groupby_date(array: np.ndarray) -> numba.typed.List:
    if array.shape[1] == 8:
        return numba.typed.List(
            np.split(array[:, :], np.unique(array[:,7], return_index = True)[1])[1:]
        )
    raise NotImplementedError()
