
import numpy as np
import numba as nb

from ..data_objects import Period, DemandResult


@nb.njit
def peak_period(
        qty_array: np.array,
        period: Period,
        net: bool,
        agg_func: callable,
        ):
    length = qty_array.shape[0]

    if period.span > length:
        raise IndexError('qty_array is smaller than the interval window.')
    if agg_func is None:
        raise ValueError('Cannot have a NoneType callable.')

    peak = 0
    idx = 0
    for i in range(length - period.span):
        x = agg_func(qty_array[i:i + period.span])
        if x > peak:
            peak = x
            idx = i
   
    normalized = False
    if agg_func == np.mean:
        normalized = True

    return DemandResult(
        normalized=normalized,
        index=idx,
        qty=peak,
        span=period.span,
        net_metered=net
    )


@nb.njit
def basic_period(
        qty_array: np.array,
        period: Period,
        net: bool,
        agg_func: callable):

    if agg_func is None:
        raise ValueError('Cannot have a NoneType callable.')

    result = 0.0

    if net:
        result = agg_func(qty_array)
    else:
        result = agg_func(np.maximum(qty_array, 0.))

    normalized = False

    if agg_func == np.mean:
        normalized = True

    return DemandResult(
        normalized=normalized,
        index=0,
        qty=result,
        span=period.span,
        net_metered=net
    )
