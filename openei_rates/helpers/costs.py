import numba as nb
import numpy as np
import pandas as pd

from .sched import get_flat_month
from .sched import get_tou_info
from .demand import get_interval_max_demand
from ..rateschedule import RateIndex


@nb.njit
def get_tou_tier(qty: float, tou: np.array):

    # Find the Tier, if there is one.
    tou_tiers = tou.shape[0]

    current_tier = tou[0]
    i = 0
    while tou[i][RateIndex.MAX_USE] > 0 and qty <= tou[i][RateIndex.MAX_USE] and i < tou_tiers:
        current_tier = tou[i]

    return current_tier


@nb.njit
def calculate_tou_cost(qty: float, month: int, hour: int, schedule: np.array, struct: np.array):
    """Calculate the cost of the energy for the interval.
    """
    tou = get_tou_info(month, hour, schedule, struct)

    tier = get_tou_tier(qty, tou)
    
    rate_price = 0.0

    # If we're positive, we use the rate
    if qty >= 0:
        rate_price = qty * tier[RateIndex.RATE]

    # If we're negative, we use the sell price. This is what will happen under NEM 2.0 in Califoirnia.
    else:
        rate_price = qty * tier[RateIndex.SELL]
    
    adj_price = abs(qty) * tier[RateIndex.ADJ]
    
    return adj_price + rate_price

@nb.njit
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





    

