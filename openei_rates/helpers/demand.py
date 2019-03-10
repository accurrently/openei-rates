
import numpy as np
import numba as nb

@nb.njit
def get_interval_max_demand(a: np.array, n_intervals: int = 3, floor: float = 0, ceiling: float = 0):
    """Finds the highest interval average that will be used for a demand charge subject to a floor and ceiling.

    When determining n_intervals, it is the responsibility of the calling function or method to supply an appropriate value.
    This function is agnostic about the length of time an interval represents.

    :param a: An array demand intervals
    :param n_intervals: (Optional) The number of intervals to average for the demand charge. Defaults to 3.
    :param floor: (Optional) A minimum quantity demanded for a demand charge. Defaults to 0.
    :param ceiling: (Optional) A maximum quantity demanded. Defaults to 0 (no ceiling).
    :returns: A 3-item tuple with the format (index, reported_maximum, actual_maximum), 
            where reported_maximum is constrained by the floor and ceiling, while the actual_maximum is the maximum found.
    :raises: ValueError if n_intervals is <= 0, the array is empty; IndexError if n_intervals >= len(a).
    """
    if n_intervals <= 0 or not a:
        raise ValueError
    length = a.shape[0]
    if n_intervals > length:
        raise IndexError
    dmax = 0.0
    idx = 0
    for i in range(length - n_intervals):
        x = a[i:i+3].sum()
        if x > dmax:
            dmax = x
            idx = i
    reported = dmax
    if floor > 0:
        reported = max(floor, reported)
    if ceiling > 0:
        reported = min(ceiling, reported)
    return (idx, reported, dmax)

