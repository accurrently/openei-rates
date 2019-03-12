
import unittest
from click.testing import CliRunner
from openei_rates import logger
from openei_rates import openei_rates
from openei_rates.rateschedule import RateSchedule
from openei_rates import cli
import pandas as pd
import numpy as np

class TestRateSchedule(unittest.TestCase):
    """Tests for `openei_rates` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        # This is a testing key, and keys are free.
        # Also, the API is rate-limited, so there's very little reason to abuse this.
        self.api_key = '2iG9VxVZJYGKRagpaqdxzhiCdgYbbtlkpfYXdUfa'
        self.eir = openei_rates.OpenEIRates(self.api_key)

        self.rate = self.eir.get_rate_by_url('https://openei.org/apps/IURDB/rate/view/5c488ad2b718b378f4caf7ea#1__Basic_Information')

    def tearDown(self):
        """Tear down test fixtures, if any."""
        pass

    def test_class_construction(self):
        """Testing the construction of a RateSchedule."""

        rs = self.rate.get_rate_schedule(self.eir.api)

        assert rs is not None
        assert rs.label == self.rate.label
        assert rs.energy_weekend_schedule.shape == (12,24)

        logger.info(str(rs))
    
    def test_energy_cost(self):
        """Testing the energy cost algorithm.
        """
        rs = self.rate.get_rate_schedule(self.eir.api)

        i = pd.date_range(start = '2019-05-01', end='2019-06-30', freq='5min')
        s = pd.Series(data=0, index = i, dtype = np.float32)

        total = 10.0 * .1338
        total += 10.0 * .0969
        total += 10.0 * .1611
        total += 20.3 * 2
        s[pd.Timestamp('2019-05-01T18:00:00')] = 10.0
        s[pd.Timestamp('2019-05-01T06:00:00')] = 10.0
        s[pd.Timestamp('2019-06-05T15:00:00')] = 10.0

        df = rs.get_costs(s)

        print(df.head())






    
