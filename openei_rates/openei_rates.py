# -*- coding: utf-8 -*-

from .api import OpenEIApi
from .rate import Rate
import datetime
import re
from urllib import parse
from . import logger

class OpenEIRates(object):

    allowed_sectors = ['Residential', 'Commercial', 'Industrial', 'Lighting']

    def __init__(self, api_key):

        self.api = OpenEIApi(api_key)

        self.rates = []

        self.utility_filter = ''
        self.rate_name_filter = ''
        self.active_date = datetime.datetime.now()
    

    def _sectors(self, sector_str: str):
        possible_sectors = list(map(lambda x: x.title(), re.findall(r'[\w]+', sector_str)))
        return [s for s in possible_sectors if s in self.allowed_sectors]

    
    def filter_rates(
            self,
            rates: list = [],
            utility: str = '',
            name: str = '',
            active: bool = True,
            approved: bool = True,
            sector: str = '',
            replace = False,
            active_date: datetime.datetime = None
        ):


        if not active_date:
            active_date = self.active_date

        newlist = []
        rlist = rates if rates else self.rates
        
        sectors = self._sectors(sector)

        rate: Rate
        for rate in rlist:
            add_status = []

            # If utility is blank, default to True
            # Otherwise, see if the string is in the field
            if utility:
                add_status.append(utility in rate.utility)

            # Same as utility, but with name
            if name:
                add_status.append(name in rate.name)

            # Get approval status equality
            add_status.append(rate.approved == approved)

            # See if the rate's sector is in of the allowed sectors of the filter
            if sectors:
                add_status.append(rate.sector in sectors)

            if active and active_date:
                add_status.append( rate.is_active(active_date) )

            if all(add_status):
                newlist.append(rate)
        
        if replace or not rates:
            self.rates = newlist
        
        return newlist         

    def get_rates_geocoded(
        self,
        address: str,
        active: bool = True,
        approved: bool = True,
        sector: str = '',
        active_date: datetime.datetime = datetime.datetime.now(),
        replace = True,
        ):
        """Looks up rates based on a a geocoded address.
        This uses the [Google geocoding API](https://developers.google.com/maps/documentation/geocoding/) in OpenEi's backend.

        :param  address: A location to look for rates.
        :type   address: ``str``
        """
        params = {
            'address': address.title(),
            'approved': approved
        }
        if sector and sector.title() in ['Residential', 'Lighting', 'Commercial', 'Industrial']:
            params['sector'] = sector.title()

        code, j = self.api.rate_query(params)

        if code == 200 and j:
            rates = []
            for item in j.get('items'):
                rates.append(Rate(item))

            return self.filter_rates(
                rates,
                active = active,
                approved = approved,
                sector = sector,
                replace = replace
            )

        return []

    def get_rate_by_label(self, label: str, replace = False, append=False, use_cached=False):
        """Looks up rates based onthe rate's label.

        :param  label: An OpenEI rate label
        :type   label: ``str``

        :param  replace:    Determines if the found rate should replace the current list of rates. Defaults to ``False``.
        :type   replace: ``bool``

        :param  append:     Determines if the rate should be appended to the current rate list. Defaults to ``False``.
        :type   append:     ``bool``

        :param  use_cached: If set to ``True``, looks in current list of rates before attempting to fetch a new one.
                            Defaults to ``False``.
        :type   use_cached: ``bool``

        :return:    A `Rate` if found, ``None`` if not found.
        """

        if use_cached:
            for rate in self.rates:
                if rate.label == label:
                    return Rate

        params = {
            'getpage': label
        }
        code, j = self.api.rate_query(params)

        if code == 200 and j:
            items = j.get('items')
            if items:
                rate = Rate(items[0])
                if rate:
                    if replace:
                        self.rates = [rate]
                    elif append:
                        self.rates.append(rate)
                    return rate
        return None


    def get_rate_by_url(self, url: str, replace = False, append=False):
        """Looks up rates based onthe URL for the rate.
        [OpenEI provides an online search tool](https://openei.org/apps/USURDB/) to locate rate information. 
        You can simply paste a rate's url into this function, and it should be found.

        :param  url: A valid OpenEI rate URL
        :type   url: ``str``

        :param  replace:    Determines if the found rate should replace the current list of rates. Defaults to ``False``.
        :type   replace: ``bool``

        :param  append:     Determines if the rate should be appended to the current rate list. Defaults to ``False``.
        :type   append:     ``bool``

        :return:    A `Rate` if found, ``None`` if not found.
        """
        try:
            parsed = parse.urlparse(url)
            label = parsed.path.split('/')[-1]
            rate = self.get_rate_by_label(label, replace=replace, append=append, use_cached=False)
            if not rate:
                logger.warn('The URL specified wa snot a valid OpenEI rate URL.')
            return rate
        except:
            logger.warn('A malformed URL was provided')
        return None






