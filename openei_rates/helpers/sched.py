import numpy as np
import numba as nb
from ..data_objects import Interval

@nb.jit(nopython=True, nogil=False)
def get_tou(interval: Interval, struct: np.array, schedule_a: np.array, schedule_b: np.array=np.array([], dtype=np.uint8) ):
    """Returns the rate information for the supplied TOU.

    :param month: Integer in the range [1,12] representing the month.
    :param hour: Integer in the range [0,23] representing the hour of the day.
    :param schedule: A Numpy array containing the time of use period indexes.
    :param struct: A Numpy array containing the associated rate information.
    :returns: A Numpy array of the are information for the current month and hour.
            The array will have a minimum length of 1.
            Returns *None* if either **struct** or **schedule** are *None*.
    :raises IndexError: If either **month** or **hour** are out of range.
    """
    if interval.hour < 0 or interval.hour > 23:
        raise IndexError('Supplied hour is out of range')
    
    if interval.month < 1 or interval.month > 12:
        raise IndexError('Supplied month is out of range')

    out = None
    month_index = interval.month - 1
    hour_index = interval.hour
    sched = schedule_a

    if schedule_b.size > 0 and interval.weekend:    
        sched = schedule_b
    
    # We have a 2-D array with months and hours
    if sched.ndim == 2:
        out = struct[sched[month_index,hour_index]]
    # We have a struct of just months
    elif sched.ndim == 1:
        out = struct[sched[month_index]]
    else:
        raise ValueError('Struct has wrong number of dimensions. Must be of dimension 1 or 2.')
        
    return out
