import numba as nb
import numpy as np
import pandas as pd

from .sched import get_tou
from .demand import get_Peak
from ..data_objects import Tier, TierIndex, Interval

@nb.njit
def process_period(a: np.array, net: bool, t_coeff: float=1., avg: bool=True):      
    b = a * t_coeff
    c = b
    if not net:
        c = np.maximum(b, 0.)
    
    result = 0.0
    if avg:
        result = np.mean(c)
    else:
        result = np.sum(c)
    
    return result 

@nb.njit
def get_tou_tier(qty: float, tou: np.array):

    if tou is None:
        raise ValueError('Supplied schedule array was None')
    
    if tou.ndim < 3:
        raise ValueError('Incorrectly formed schedule array. Must be of dimension 3.')

    # Find the Tier, if there is one.
    current_tier = None

    if tou is not None:
        tou_tiers = tou.shape[0]

        i = 0       
        while i < tou_tiers and qty < tou[i][TierIndex.MAX]:
            current_tier = tou[i]
            i += 1       

    return current_tier

@nb.njit
def get_Tier(qty: float, tou: np.array):

    # We need a non-none tou
    if tou is None:
        raise ValueError('Supplied schedule array was None')
    
    assert tou.ndim == 2, 'Incorrectly formed schedule array. Must be of dimension 3.'
    assert tou.shape[1] == TierIndex.ARRAY_LENGTH, 'Incorrectly shaped Tier rows.'
    i = 0
    row = np.array([np.inf,0.,0.,0.], dtype=np.float32)
    while i < tou.shape[0]:
        row = tou[i,:]
        if row[TierIndex.MAX] <= 0.:
            break
        elif qty <= row[TierIndex.MAX]:        
            break
        i += 1
    
    return Tier(
        max=row[TierIndex.MAX],
        price=row[TierIndex.RATE],
        adj=row[TierIndex.ADJ],
        sell=row[TierIndex.SELL]
    )



@nb.njit
def period_cost(
        qty_array: np.array,
        price_struct: np.array,
        interval: Interval,
        shedule_a: np.array,
        schedule_b: np.array=np.empty(0,dtype=np.float32),
        net_meter: bool=False,
        t_coeff: float = 1.,
        avg:bool = True,
        retail_net:bool = False ):

    qty = process_period(qty_array, net_meter, t_coeff, avg)

    tou = get_tou(interval, price_struct, )

    tier = get_Tier(qty, )


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





    

