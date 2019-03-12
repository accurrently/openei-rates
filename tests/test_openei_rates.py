#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `openei_rates` package."""


import unittest
from click.testing import CliRunner
from openei_rates import logger
from openei_rates import openei_rates
from openei_rates import cli

class TestOpenEIRates(unittest.TestCase):
    """Tests for `openei_rates` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        # This is a testing key, and keys are free.
        # Also, the API is rate-limited, so there's very little reason to abuse this.
        self.api_key = '2iG9VxVZJYGKRagpaqdxzhiCdgYbbtlkpfYXdUfa'       

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_class_construction(self):
        """Test whether the OpenEIRates class can be constructed."""

        ei_rates = openei_rates.OpenEIRates(self.api_key)

        assert ei_rates.api.api_key == self.api_key

    def test_bad_label_query(self):
        """Tests a bad query for a rate
        """
        ei_rates = openei_rates.OpenEIRates(self.api_key)

        assert ei_rates.get_rate_by_label('thisisnotareal_label') is None

    def test_good_label_query(self):
        """Test a valid query
        """
        ei_rates = openei_rates.OpenEIRates(self.api_key)

        rate = ei_rates.get_rate_by_label(u'5c488ad2b718b378f4caf7ea')

        assert rate.label == u'5c488ad2b718b378f4caf7ea'
        assert rate.sector == 'Residential'
        assert rate.name == 'Residential TOD (Option A)'
        assert rate.utility == 'Sacramento Municipal Utility District'
        
        logger.info(rate)

    def test_get_rate_by_url(self):
        """Looking to see if we can grab the rate from the URL
        """

        ei_rates = openei_rates.OpenEIRates(self.api_key)

        rate = ei_rates.get_rate_by_label(u'5c488ad2b718b378f4caf7ea')

        url_rate = ei_rates.get_rate_by_url('https://openei.org/apps/IURDB/rate/view/5c488ad2b718b378f4caf7ea#1__Basic_Information')

        assert url_rate.label == u'5c488ad2b718b378f4caf7ea'
        assert url_rate.sector == 'Residential'
        assert url_rate.name == 'Residential TOD (Option A)'
        assert url_rate.utility == 'Sacramento Municipal Utility District'
        assert url_rate.label == rate.label

        logger.info(url_rate)


    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'openei_rates.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output


from . import test_rateschedule

if __name__ == '__main__':
    unittest.main()