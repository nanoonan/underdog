import logging

import numba
import numpy as np

logger = logging.getLogger(__name__)

@numba.jit(nopython = True, nogil = True, cache = True)
def date_col(array: np.ndarray, timeslot: np.float64):
    if array.shape[1] == 8:
        return array[array[:,0] == timeslot, 7]
    raise NotImplementedError()

@numba.jit(nopython = True, nogil = True, cache = True)
def open_col(array: np.ndarray, timeslot: np.float64):
    if array.shape[1] == 8:
        return array[array[:,0] == timeslot, 1]
    raise NotImplementedError()

@numba.jit(nopython = True, nogil = True, cache = True)
def close_col(array: np.ndarray, timeslot: np.float64):
    if array.shape[1] == 8:
        return array[array[:,0] == timeslot, 4]
    raise NotImplementedError()

@numba.jit(nopython = True, nogil = True, cache = True)
def high_col(array: np.ndarray, timeslot: np.float64):
    if array.shape[1] == 8:
        return array[array[:,0] == timeslot, 2]
    raise NotImplementedError()

@numba.jit(nopython = True, nogil = True, cache = True)
def low_col(array: np.ndarray, timeslot: np.float64):
    if array.shape[1] == 8:
        return array[array[:,0] == timeslot, 3]
    raise NotImplementedError()

@numba.jit(nopython = True, nogil = True, cache = True)
def volume_col(array: np.ndarray, timeslot: np.float64):
    if array.shape[1] == 8:
        return array[array[:,0] == timeslot, 5]
    raise NotImplementedError()

@numba.jit(nopython = True, nogil = True, cache = True)
def twap_col(array: np.ndarray, timeslot: np.float64):
    if array.shape[1] == 8:
        return array[array[:,0] == timeslot, 6]
    raise NotImplementedError()
