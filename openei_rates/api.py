import requests
import json

from . import logger

class OpenEIApi(object):

    _rate_endpoint = 'https://api.openei.org/utility_rates'
    _utility_endpoint = 'https://api.openei.org/utility_companies'

    response_format = 'json'

    def __init__(self, api_key: str, zip_code: str = ''):

        self.api_key = api_key
        self.zip_code = zip_code
        self.prefrred_unit = 'kWh'
        self.approved_only = True
    
    def rate_query(self, params: dict = {}):

        p = {
            'api_key': self.api_key,
            'format': __class__.response_format,
            'approved': 'true' if self.approved_only else 'false',
            'orderby': 'startdate',
            'direction': 'desc'            
        }
        p.update(params)
        logger.info('Sending request.')
        r = requests.get(__class__._rate_endpoint, params = p)
        
        
        if r.status_code == 403:
            logger.error('Invalid API key. Use a valid. key. If you do not have one, get a free one at https://openei.org/services/api/signup/')
            exit(1)
        
        logger.info('Response: HTTP {}'.format(r.status_code))

        if r.ok():

            try:

                j = r.json()

                return (r.status_code, j)
            
            except ValueError:
                logger.warn('There was a bad response. This could be the server, or an application bug.')
                return (None, None)
        
        return (r.status_code, j)
    
    
        
    
    