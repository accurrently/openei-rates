import numpy as np
import datetime
import pandas as pd
import enum
from pandas.tseries.holiday import AbstractHolidayCalendar
from pandas.tseries.holiday import USFederalHolidayCalendar


class RateIndex(enum.IntEnum):
    MAX_USE = 0
    RATE = 1
    ADJ = 2
    SELL = 3

    ARRAY_LENGTH = 4

class PriceSchedule(object):

    default_start_date = AbstractHolidayCalendar.start_date
    default_end_date = AbstractHolidayCalendar.end_date
    weekmask = 'Sat Sun'

    def __init__(
        self,
        rate_info: dict, 
        default_price: float = .13,
        holiday_calendar: AbstractHolidayCalendar = USFederalHolidayCalendar()
        ):

        # Parse the rate information from a dict response
        
        begin_dt = rate_info.get('startdate', None)
        

        end_dt = rate_info.get('enddate', None)
        
        if begin_dt and end_dt:

            self.holidays = holiday_calendar.holidays(
                    start = pd.Timestamp.fromtimestamp(begin_dt),
                    end = pd.Timestamp.fromtimestamp(end_dt)
                )
        else:
            self.holidays = holiday_calendar.holidays()

        # Units
        self.flat_demand_unit = rate_info.get('flatdemandunit', 'kW')
        self.tou_demand_unit = rate_info.get('demandrateunit', 'kW')
        self.coincident_rate_unit = rate_info.get('coincidentrateunit', 'kW')
        self.energy_unit = 'kWh'

        # Demand ceiling and floor for demand charges
        self.demand_minimum = rate_info.get('peakkwcapacitymin', 0)
        self.demand_maximum = rate_info.get('peakkwcapacitymax', 0)

        # Rate Structures
        # A rate structure is essentially a list of lists with rate information
        # The outer array's indexes refer to the period ID, with Tiers and members
        # The inner array (Tier) is an array of attributes
        # Each rate structure's attributes are a bit different.

        # Demand charges
        d_rate_struct = rate_info.get('demandratestructure')
        self.demand_rate_structure = PriceSchedule.build_rate_structure(d_rate_struct)    

        # Energy rate
        e_rate_struct = rate_info.get('energyratestructure', [[{'rate': default_price}]])
        self.energy_rate_struct = PriceSchedule.build_rate_structure(e_rate_struct)

        # Coincident
        c_rate_struct = rate_info.get('coincidentratestructure', [[{'rate': default_price}]])
        self.energy_rate_struct = PriceSchedule.build_rate_structure(c_rate_struct)

        

        self.demand_ratchet_pct = np.array(
            rate_info.get('demandrachetpercentage', [0.0 for i in range(12)]),
            dtype = np.float32
        )

        




        # Fixed monthly charges
        self.fixed_monthly_charge = rate_info.get('fixedmonthlycharge', 0)

        self.fixed_attrs = rate_info.get('fixedattrs', None)

        # Net metering?
        self.use_net_metering = rate_info.get('usenetmetering', False)


 #       self.energy_rates = 

    @classmethod
    def build_rate_structure(cls, struct: list):
        """Builds a rate structure Numpy array. The array will always be 3-dimensional.
        Consider the hierarchy of arrays as X-Y-Z, with X being the outer array.
        The Rate Structure (X) n >= 1 Periods.
        Each Period (Y) has n >= 1 Tiers.
        Each Tier (Z) has a length of 4 (n = 4).
        """
        if struct:
            struct_a = []
            for period in struct:
                period_a = []
                
                for tier in period:
                    tier_a = [0 for i in range(RateIndex.ARRAY_LENGTH)]
                    tier_a[RateIndex.MAX_USE] = tier.get('max', 0)
                    tier_a[RateIndex.RATE] = tier.get('rate', 0)
                    tier_a[RateIndex.ADJ] = tier.get('rate', 0)
                    tier_a[RateIndex.SELL] = tier.get('sell', 0)
                    period_a.append(tier_a)
                
                struct_a.append(period_a)
            
            return np.array(struct_a, dtype=np.float32)

        return None




