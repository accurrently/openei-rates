import numba as nb
import numpy as np
# import pandas as pd

from typing import Callable

from .sched import get_Tier
from .demand import get_Peak
from ..data_objects import Tier, TierIndex, Period
from .demand import peak_period, basic_period
from .window import (
    window,
    month_changed,
    hour_changed,
    assign_distribute,
    assign_end,
    assign_front,
    assign_at_index
)


@nb.njit
def energy_cost(
        qty_array: np.array,
        price_struct: np.array,
        months: np.array,
        hours: np.array,
        is_weekend: np.array,
        wd_schedule: np.array,
        we_schedule: np.array,
        interval_time: float,
        assignment_func=assign_distribute,
        net_meter: bool = False,
        retail_net: bool = False):
    
    qlen = qty_array.shape[0]

    out = np.zeros(qlen, dtype=np.float32)

    _window(
        qty_array,
        out,
        price_struct,
        months,
        hours,
        is_weekend,
        wd_schedule,
        we_schedule,
        interval_time,
        net_meter,
        hour_changed,
        basic_period,
        assignment_func,
        np.sum
    )

    return out


@nb.njit
def tou_demand_cost(
        qty_array: np.array,
        price_struct: np.array,
        months: np.array,
        hours: np.array,
        is_weekend: np.array,
        window_span: int,
        wd_schedule: np.array,
        we_schedule: np.array,
        interval_hours: float,
        net_meter: bool,
        normalize: bool = False):

    qlen = qty_array.shape[0]

    out = np.zeros(qlen, dtype=np.float32)

    assign_func = assign_distribute
    if normalize:
        assign_func = assign_at_index

    window(
        qty_array,
        out,
        price_struct,
        months,
        hours,
        is_weekend,
        wd_schedule,
        we_schedule,
        interval_hours,
        net_meter,
        month_changed,
        peak_period,
        assignment_func,
        np.sum,
        window_span=window_span
    )

    return out 


@nb.njit
def flat_demand_cost(
        qty_array: np.array,
        price_struct: np.array,
        month_interval: Interval,
        schedule: np.array,

        ):

@nb.njit
def calculate_tou_cost(qty, month, hour, schedule: np.array, struct: np.array):
    """Calculate the cost of the energy for the interval.
    """
    tou = None

    try:
        tou = get_tou(month, hour, schedule, struct)
    except IndexError as ie:
        raise ie

    tier = get_tou_tier(qty, tou)

    rate_price = 0.0
    adj_price = 0.0

    if tier is not None:

        # If we're positive, we use the rate
        if qty >= 0:
            rate_price = qty * tier[RateIndex.RATE]

        # If we're negative, we use the sell price. This is what will happen under NEM 2.0 in Califoirnia.
        else:
            rate_price = qty * tier[RateIndex.SELL]
        
        adj_price = abs(qty) * tier[RateIndex.ADJ]
    
    return adj_price + rate_price

@nb.jit(nopython=True, nogil=False)
def calculate_flat_cost(
    qty: float,
    month: int,
    flat_schedule: np.array,
    flat_struct: np.array,
    ):
    """Calculates the demand charges for a particular quantity of power at a given date and time. 
    """
    flat_price = 0.0
    if flat_schedule and flat_struct:
        # It's a little differnt for flat schedules
        tou = get_flat_month(month, flat_schedule, flat_struct)
        tier = get_tou_tier(qty, tou)
        p = 0.0
        # If we're positive, we use the rate
        if qty >= 0:
            p = qty * tier[RateIndex.RATE]

        # If we're negative, we use the sell price. This is what will happen under NEM 2.0 in Califoirnia.
        else:
            p = qty * tier[RateIndex.SELL]
        
        adj = abs(qty) * tier[RateIndex.ADJ] 

        flat_price = adj + p
    
    return flat_price 





    

