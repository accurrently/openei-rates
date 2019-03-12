import numpy as np
import datetime
import pandas as pd
from pandas.tseries.holiday import AbstractHolidayCalendar
from pandas.tseries.holiday import USFederalHolidayCalendar

from .helpers.sched import get_tou
from .helpers.costs import get_tou_tier, get_tou, calculate_flat_cost, calculate_tou_cost, process_period, period_cost

from .helpers.demand import get_Peak

from . import logger

from .data_objects import Peak, Tier

class RateSchedule(object):
    """Contains all the pricing and time-of-use (TOU) information for a particular rate.
    """

    default_start_date = AbstractHolidayCalendar.start_date
    default_end_date = AbstractHolidayCalendar.end_date
    weekmask = [0, 1, 2, 3, 4 ] # Workdays
    default_demand_window = 15

    class SType(object):
        __slots__ = ()
        ENERGY = 'energy'
        TOU_DEMAND = 'tou_demand'
        FLAT_DEMAND = 'flat_demand'
        COINCIDENT = 'coincident'

        DEMANDS = {TOU_DEMAND, FLAT_DEMAND}
        DEMANDS_AND_COI = {TOU_DEMAND, FLAT_DEMAND, COINCIDENT}
        MONTH_ONLY = {FLAT_DEMAND}

        ALL = {ENERGY, TOU_DEMAND, FLAT_DEMAND, COINCIDENT}

        @classmethod
        def is_valid(cls, s: str):
            return s.lower() in cls.SType.ALL

    def __init__(
        self,
        rate_info: dict, 
        default_price: float = .13,
        holiday_calendar: AbstractHolidayCalendar = USFederalHolidayCalendar()
        ):
        """
        Creates a RateSchedule object.

        :param  rate_info: Rate information captured from the json result for a particular Rate.
        :type   rate_info: ``dict``

        :param  default_price:  (Optional) A fallback price that the object should use should no other pricing information be found.
                                This only applies to energy use rates, not demand or coincident charges. Defaults to 13 cents. (0.13)
        :type   default_price:  ``float``

        :param  holiday_calendar:   A Pandas holiday calendar used for calculating holiday times for determining appropiate rates.
                                    Defaults to using the [Pandas US federal holiday calendar](https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html).
        :type   holiday_calendar:   ``pandas.tseries.holiday.AbstractHolidayCalendar``
        """

        logger.info('Loading RateSchedule for {} ({})'.format(rate_info.get('name'), rate_info.get('utility')))

        # Parse the rate information from a dict response
        
        begin_dt = rate_info.get('startdate', None)
        

        end_dt = rate_info.get('enddate', None)

        self.features = set({})
        
        if begin_dt and end_dt:

            self.holidays = holiday_calendar.holidays(
                    start = pd.Timestamp.fromtimestamp(begin_dt),
                    end = pd.Timestamp.fromtimestamp(end_dt)
                )
        else:
            self.holidays = holiday_calendar.holidays()

        self.label = rate_info.get('label')

        # A fallback price in case things get weird.
        self.default_energy_price = default_price
        # Units
        self.flat_demand_unit = rate_info.get('flatdemandunit', 'kW')
        self.demand_rate_unit = rate_info.get('demandrateunit', 'kW')
        self.coincident_rate_unit = rate_info.get('coincidentrateunit', 'kW')
        self.energy_demand_unit = rate_info.get('demandrateunit', 'kWh')
        self.energy_unit = 'kWh'

        # Demand ceiling and floor for demand charges
        self.demand_minimum = rate_info.get('peakkwcapacitymin', 0)
        self.demand_maximum = rate_info.get('peakkwcapacitymax', 0)

        # How long is our window for demand? (in minutes). 
        self.demand_window = rate_info.get('demandratewindow', RateSchedule.default_demand_window)

        # Rate Structures
        # A rate structure is essentially a list of lists with rate information
        # The outer array's indexes refer to the period ID, with Tiers and members
        # The inner array (Tier) is an array of attributes
        # Each rate structure's attributes are a bit different.

        # Demand charges
        d_rate_struct = rate_info.get('demandratestructure')
        self.demand_rates = RateSchedule.build_rate_structure(d_rate_struct)    

        d_flat_struct = rate_info.get('flatdemandstructure')
        self.flat_demand_rates = RateSchedule.build_rate_structure(d_flat_struct)  

        # Coincident
        c_rate_struct = rate_info.get('coincidentratestructure')
        self.coincident_rates = __class__.build_rate_structure(c_rate_struct)  

        # Energy rate
        e_rate_struct = rate_info.get('energyratestructure')
        if not e_rate_struct:
            e_rate_struct = [[{'rate': default_price}]]
            logger.warn('Energy pricing structure not found. Falling back to default price!')
        self.energy_rates = __class__.build_rate_structure(e_rate_struct)

        

        # TOUs
        # Get the TOU schedules
        default_tou = np.zeros((12,24), dtype=np.uint8)
        # Demand
        d_wd_sched = rate_info.get('demandweekdayschedule')
        d_we_sched = rate_info.get('demandweekendschedule')
        d_flat_sched = rate_info.get('flatdemandmonths')
        self.demand_weekday_schedule = np.array(d_wd_sched, dtype=np.uint8) if d_wd_sched else None
        self.demand_weekend_schedule = np.array(d_we_sched, dtype=np.uint8) if d_we_sched else None
        self.flat_demand_months = np.array(d_flat_sched, dtype=np.uint8) if d_flat_sched else None


        e_wd_sched = rate_info.get('energyweekdayschedule')
        e_we_sched = rate_info.get('energyweekendschedule')
        if not e_wd_sched:
            logger.warn('Could not load weekday energy TOU schedule. Falling back to default!')
        if not e_we_sched:
            logger.warn('Could not load weekend energy TOU schedule. Falling back to default!')
        self.energy_weekday_schedule = np.array(e_wd_sched, dtype=np.uint8) if e_wd_sched else np.copy(default_tou)
        self.energy_weekend_schedule = np.array(e_we_sched, dtype=np.uint8) if e_we_sched else np.copy(default_tou)

        c_sched = rate_info.get('coincidentrateschedule')
        self.coincident_schedule = np.array(c_sched, dtype=np.uint8) if c_sched else None


        self.demand_ratchet_pct = np.array(
            rate_info.get('demandrachetpercentage', [0.0 for i in range(12)]),
            dtype = np.float32
        )


        # Fixed monthly charges
        self.fixed_monthly_charge = rate_info.get('fixedmonthlycharge', 0)
        self.monthly_min_charge = rate_info.get('minmonthlycharge', 0)
        self.annual_min_charge = rate_info.get('annualmincharge', 0)

        self.fixed_attrs = rate_info.get('fixedattrs', None)

        # Net metering?
        self.use_net_metering = rate_info.get('usenetmetering', False)
    
    def __str__(self):
        coin_ = 'coincident ' if (self.coincident_rates is not None) and (self.coincident_schedule is not None) else ''
        nrg_ = 'energy ' if (self.energy_rates is not None) and (self.energy_weekday_schedule is not None) and (self.energy_weekend_schedule is not None) else ''
        dem_ = 'tou_demand ' if (self.demand_rates is not None) and (self.demand_weekday_schedule is not None) and (self.demand_weekend_schedule is not None) else ''
        flt_ = 'flat_demand ' if (self.flat_demand_months is not None) and (self.flat_demand_rates is not None) else ''

        return '<RateSchedule {}: {}{}{}{}>'.format(self.label, coin_, nrg_, dem_, flt_)
    
    def __repr__(self):
        return '<RateSchedule({})>'.format(self.label)

    @classmethod
    def build_rate_structure(cls, struct: list):
        """Builds a rate structure Numpy array. The array will always be 3-dimensional.
        Consider the hierarchy of arrays as X-Y-Z, with X being the outer array.
        The Rate Structure (X) n >= 1 Periods.
        Each Period (Y) has n >= 1 Tiers.
        Each Tier (Z) has a length of 4 (n = 4).

        :param  struct: A list of rates and rate information. A 3-dimensional ``list`` (a ``list`` of ``list``s of ``list``s).
        :type   struct: ``list``

        :return:    A 3-dimensional  ``numpy.array`` of type ``numpy.float32``
                    or ``None`` if **struct** is ``None``.
        """
        if struct:
            struct_a = []
            for period in struct:
                period_a = []
                
                for tier in period:
                    tier_a = [0 for i in range(RateIndex.ARRAY_LENGTH)]
                    tier_a[RateIndex.MAX_USE] = tier.get('max', 0.0)
                    tier_a[RateIndex.RATE] = tier.get('rate', 0.0)
                    tier_a[RateIndex.ADJ] = tier.get('rate', 0.0)
                    tier_a[RateIndex.SELL] = tier.get('sell', 0.0)
                    period_a.append(tier_a)
                
                struct_a.append(period_a)
            
            return np.array(struct_a, dtype=np.float32)

        return None
    
    def get_structure_at(self, ts, schedule_type: str = 'energy'):
        """Fetch rate structure information for a given timestamp.

        :param  ts: Timestamp-type. Any time that can be readily converted into a Pandas Timestamp. 
        :type   ts: ``pandas.Timestamp``, ``pandas.DateTimeIndex``, ``numpy.datetime64``, ``datetime.datetime``, or ``str`` 
        
        :param  schedule_type:   Indicates which schedule to use. Values may be "energy", "flat_demand", "demand", or "coincidence". Defaults to "energy".
        :type   schedule_type:  ``str``

        :return:    A rate schedule, or ``None`` if the given schedule or rates are not initialized.
        :rtype:     ``numpy.array``

        :raises:    ``AttributeError`` if **schedule_type** is not a valid option.
        """

        if schedule_type not in ['demand', 'flat_demand', 'coincident', 'energy', 'en', 'fd', 'de', 'co']:
            raise AttributeError

        stamp = pd.Timestamp(ts)

        weekend = stamp.date() in self.holidays or stamp.dayofweek not in __class__.weekmask

        if schedule_type in ['flat_demand', 'fd'] and self.flat_demand_months and self.flat_demand_rates:
            flat_index = get_flat_month(stamp.month, self.flat_demand_months, self.flat_demand_rates)
            return self.flat_demand_rates[flat_index]

        elif schedule_type in ['coincident', 'co'] and self.coincident_schedule and self.coincident_rates:
            return get_tou_info(stamp.month, stamp.hour, self.coincident_schedule, self.coincident_rates)

        elif schedule_type in ['energy', 'en'] and self.energy_rates:
            sched = self.energy_weekend_schedule if weekend else self.energy_weekday_schedule
            return get_tou_info(stamp.month, stamp.hour, sched, self.energy_rates) if sched else None
        
        elif schedule_type in ['demand', 'de'] and self.demand_rates:
            sched = self.demand_weekend_schedule if weekend else self.demand_weekday_schedule
            return get_tou_info(stamp.month, stamp.hour, sched, self.demand_rates) if sched else None
        
        return None

    def _cost(self, s: pd.Series, rtype: str):

        if rtype.lower() not in self.SType.ALL:
            raise ValueError('"{}" is not a valid rate schedule type. rtype must be one of {}'.format(rtype.lower(), self.SType.ALL))
        
        lookup_day_type = (rtype in {self.SType.ENERGY, self.SType.TOU_DEMAND})
        use_flat = rtype == self.SType.FLAT_DEMAND

        # Demand
        if rtype in {self.SType.FLAT_DEMAND, self.SType.TOU_DEMAND}:
            idx, reported_val, max_val = get_interval_max_demand(ser.values, n_intervals=demand_window_intervals)







    def get_costs(
        self,
        demand_series: pd.Series,
        agg: str = 'month',
        distribute_monthly: bool = True,
        ):
        """Calculates the demand charges for a given ``panads.Series``.

        :param  demand_series: A series with a ``pandas.DateTimeInex`` index.
                                Values should reflect average power, not energy.
        :type   demand_series: ``pandas.Series```

        :param  agg:    How to aggregate the costs. Valid values are "day", "week", "month" and "year".
        :type   agg:    ``str``

        :param  distribute_monthly: Whether or not to average monthly charges like demand and
                                    fixed charges oiver every day of the month.
        :type   distribute_monthly: ``bool``

        :return:    A dataframe ahowing the different charges for a given month. 
        :rtype:     ``pandas.DatafRame``

        :raises:    ``IndexError`` if **demand_series** does not have an index of type ``pandas.DatetimeIndex``.
        """

        if (demand_series.empty) or (demand_series.size <= 2):
            return None
        
        if not (isinstance(demand_series.index, pd.DatetimeIndex)):
            raise IndexError


        df = demand_series.to_frame(name='qty')

        group_mode = {
            'day': 'D',
            'week': 'W',
            'month': 'M',
            'quarter': 'Q',
            'year': 'A'
        }.get(agg.lower(), 'D')

        grouper = pd.Grouper(freq=group_mode)
        mg = pd.Grouper(freq='M')

        interval_delta = demand_series.index[1] - demand_series.index[0]

        interval_hours = interval_delta / pd.Timedelta('1h')

        demand_window_intervals = round( interval_delta / pd.Timedelta('{}min'.format(self.demand_window)))

        # First, check out these demand charges
        if (self.demand_rates is not None) and (self.demand_weekday_schedule is not None) and (self.demand_weekend_schedule is not None):

            def get_demand_cost(ser: pd.Series):
                idx, reported_val, max_val = get_interval_max_demand(ser.values, n_intervals=demand_window_intervals)
                ts = ser.reset_index()['index'].iloc[idx]
                cost = 0.0
                try:
                # if we're on a holiday or weekend
                    if ts.date() in self.holidays or ts.dayofweek not in self.weekmask:
                        cost = calculate_tou_cost(reported_val, ts.month, ts.hour, self.demand_weekend_schedule, self.demand_rates)
                    # Otherwise, it's a weekday
                    cost = calculate_tou_cost(reported_val, ts.month, ts.hour, self.demand_weekday_schedule, self.demand_rates)
                except:
                    pass

            if distribute_monthly:
                # Set every interval to have the value evenly distributed
                df['tou_demand_cost'] = df.groupby(mg)['qty'].transform(lambda x: get_demand_cost(x) / x.size)
            else:
                # Assign the value of the charge to the end of the month
                df['tou_demand_cost'] = df.groupby(mg)['qty'].agg(get_demand_cost)

        # Default to zero for the column        
        else:
            df['tou_demand_cost'] = 0
                
        # Now do the same for flat demand
        if (self.flat_demand_months is not None) and (self.flat_demand_rates is not None):

            def get_flat_demand_cost(ser: pd.Series):
                idx, reported_val, max_val = get_interval_max_demand(ser.values, n_intervals=demand_window_intervals)
                ts = ser.reset_index()['index'].iloc[idx]
                # if we're on a holiday or weekend
                if ts in self.holidays or ts.dayofweek not in self.weekmask:
                    return calculate_flat_cost(reported_val, ts.month, self.flat_demand_months, self.flat_demand_rates)
                # Otherwise, it's a weekday
                return calculate_flat_cost(reported_val, ts.month, self.flat_demand_months, self.flat_demand_rates)

            if distribute_monthly:
                # Set every interval to have the value evenly distributed
                df['flat_demand_cost'] = df.groupby(mg)['qty'].transform(lambda x: get_flat_demand_cost(x) / x.size)
            else:
                # Assign the value of the charge to the end of the month
                df['flat_demand_cost'] = df.groupby(mg)['qty'].agg(get_flat_demand_cost)
        else:
            df['flat_demand_cost'] = 0
            
        # Coincident charges
        if (self.coincident_rates is not None) and (self.coincident_schedule is not None):
            c = df.reset_index()
            df['coincident_cost'] = c.apply(lambda x: calculate_tou_cost(
                x['qty'],
                x['index'].month,
                x['index'].hour,
                self.coincident_schedule,
                self.coincident_rates
                )
            )
        else:
            df['coincident_cost'] = 0 # __THAT WAS EASY__
            

        # Energy!
        if (self.energy_rates is not None) and (self.energy_weekday_schedule is not None) and (self.energy_weekend_schedule is not None):

            def get_energy_cost(qty: float, ts: pd.Timestamp):
                # if we're on a holiday or weekend
                cost = 0.0
                try:
                    if ts in self.holidays or ts.dayofweek not in RateSchedule.weekmask:
                        cost = calculate_tou_cost(qty * interval_hours, ts.month, ts.hour, self.energy_weekend_schedule, self.energy_rates)        
                    else:
                        cost = calculate_tou_cost(qty * interval_hours, ts.month, ts.hour, self.energy_weekday_schedule, self.energy_rates)
                except IndexError as ie:
                    logger.error('An IndexError was raised: {}'.format(ie))
                return cost
            
            df['energy_cost'] = df.reset_index().apply(
                (lambda x: get_energy_cost(x['qty'], x['index'])), 
                axis=1
                )
        else:
            df['energy_cost'] = df['qty'].apply(lambda x: x * interval_hours * self.default_energy_price)

        # Monthly fixed costs
        
        fixed_total = self.fixed_monthly_charge

        if distribute_monthly:
            df['fixed_cost'] = df.groupby(mg)['qty'].transform(lambda x: fixed_total / x.size)
        else:
            df['fixed_cost'] = df.groupby(mg).agg(lambda x: fixed_total)
                    
        # If we need to sum everything up, let's do it
        df['total'] = df.apply(
            lambda x: x['energy_cost'] + x['tou_demand_cost'] + x['coincident_cost'] + x['flat_demand_cost'] + x['fixed_cost']
        )

        # Finally, aggregate according to the needed aggregation scheme

        df = df[['qty', 'energy_cost', 'tou_demand_cost', 'coincident_cost', 'flat_demand_cost', 'fixed_cost']]

        return df.groupby(grouper).agg(sum)


                














