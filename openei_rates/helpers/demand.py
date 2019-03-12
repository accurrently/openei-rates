
import numpy as np
import numba as nb

from ..data_objects import Peak

@nb.njit
def get_Peak(qty_array: np.array, n_intervals: int=3):
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
    if qty_array is None:
        raise ValueError('None was supplied instead of an array.')
    
    assert qty_array.ndem == 1, 'qty_array is of an incorrect dimension.'
    
    if n_intervals <= 0:
        raise ValueError('Invalid number of intervals for interval length.')
    
    length = qty_array.shape[0]

    if n_intervals > length:
        raise IndexError('qty_array is smaller than the interval window.')

    demand = 0.
    idx = 0
    interval_demand = 0.
    interval_idx = 0
    for i in range(length - n_intervals):
        x = qty_array[i:i+n_intervals].sum()
        y = qty_array[i]
        if x > demand:
            demand = x
            idx = i
        if y > interval_demand:
            interval_demand = y
            interval_idx = i

    return Peak(
        index = idx,
        qty=demand,
        peak_interval_index=interval_idx,
        peak_interval_qty=interval_demand
    )

