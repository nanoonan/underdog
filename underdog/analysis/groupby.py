import logging

import numpy as np

from numba.typed import List

logger = logging.getLogger(__name__)

def groupby_date(array: np.ndarray) -> List:
    if array.shape[1] == 8:
        return List(
            np.split(array[:, :], np.unique(array[:,7], return_index = True)[1])[1:]
        )
    raise NotImplementedError()
