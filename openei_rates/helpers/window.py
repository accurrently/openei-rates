import numba as nb
import numpy as np
# import pandas as pd

from .sched import get_Tier
from ..data_objects import Tier, Period


@nb.njit
def assign_front(a: np.array, val: float, index: int):
    a[0] = val
    return None


@nb.njit
def assign_end(a: np.array, val: float, index: int):
    a[-1] = val
    return None


@nb.njit
def assign_distribute(a: np.array, val: float, index: int):
    a[:] = val / np.size(a, 0)
    return None


@nb.njit
def assign_at_index(a: np.array, val: float, index: int):
    a[index] = val
    return None


@nb.njit
def _window_cost(
        out_a: np.array,
        qty_total: float,
        tier: Tier,
        index: int,
        retail_net: bool,
        assignment_func):

    total_cost = qty_total * tier.adj

    if qty_total < 0 and not retail_net:
        total_cost += (qty_total * tier.sell)
    else:
        total_cost += qty_total * tier.price

    assignment_func(out_a, total_cost, index)


@nb.njit
def _sched(weekend: bool, wd_a: np.array, we_a: np.array):
    sched = wd_a
    if weekend and we_a.shape[0] > 0:
        sched = we_a
    return sched


@nb.njit
def hour_changed(a: Period, b: Period):
    return not (a.hour == b.hour)


@nb.njit
def month_changed(a: Period, b: Period):
    return not (a.month == b.month)


@nb.njit
def window(
        qty_array: np.array,
        out: np.array,
        price_struct: np.array,
        months: np.array,
        hours: np.array,
        is_weekend: np.array,
        wd_schedule: np.array,
        we_schedule: np.array,
        interval_hours: float,
        net_meter: bool,
        period_change_func,
        demand_func,
        cost_assignment_func,
        demand_agg_func,
        retail_net: bool = False,
        window_span: int = 1):

    num = qty_array.shape[0]

    current_period = Period(
        interval_hours=interval_hours,
        span=window_span,
        month=months[0],
        hour=hours[0],
        weekend=is_weekend[0],
    )

    window_index = 0
    for i in range(num):
        # qty = process_period(qty_array, net_meter, interval_time, avg)
        new_period = Period(
            interval_hours=current_period.interval_hours,
            span=current_period.span,
            month=months[i],
            hour=hours[i],
            weekend=is_weekend[i]
        )

        # Did our interval change?
        if period_change_func(current_period, new_period):

            # Get the window search done
            demand_result = demand_func(
                qty_array[window_index:i],
                current_period,
                net_meter,
                demand_agg_func
            )

            tou_period = Period(
                interval_hours=current_period.interval_hours,
                span=current_period.span,
                month=months[window_index:i][demand_result.index],
                hour=hours[window_index:i][demand_result.index],
                weekend=is_weekend[window_index:i][demand_result.index]
            )

            tier = get_Tier(
                demand_result.qty,
                tou_period,
                price_struct,
                _sched(
                    is_weekend[window_index:i][demand_result.index],
                    wd_schedule,
                    we_schedule
                )
            )

            _window_cost(
                qty_array[window_index:i],
                out[window_index:i],
                demand_result.qty,
                tier,
                demand_result.index,
                retail_net,
                cost_assignment_func
            )

            window_index = i

        # Change the current period every hour
        if not (current_period.hour == new_period.hour):
            current_period = new_period

        # endif
        i += 1

    # Out of loop
    # do the last window
    demand_result = demand_func(
        qty_array[window_index:num],
        current_period,
        net_meter,
        demand_agg_func
    )

    tier = get_Tier(
        demand_result.qty,
        current_period,
        price_struct,
        _sched(
            is_weekend[window_index:num][demand_result.index],
            wd_schedule,
            we_schedule
        )
    )

    _window_cost(
        qty_array[window_index:num],
        out[window_index:num],
        demand_result.qty,
        tier,
        retail_net,
        cost_assignment_func
    )
