import requests
import json


class OpenEI_Api(object):

    _rate_endpoint = 'https://api.openei.org/utility_rates'
    _utility_endpoint = 'https://api.openei.org/utility_companies'

    response_format = 'json'

    def __init__(self, api_key: str, zip_code: str = ''):

        self.api_key = api_key
        self.zip_code = zip_code
        self.preffred_unit = 'kWh'
        self.approved_only = True
    
    def rate_query(self, params: dict = {}):

        p = {
            'api_key': self.api_key,
            'format': OpenEI_Api.response_format,
            'approved': 'true' if self.approved_only else 'false',
            'orderby': 'startdate',
            'direction': 'desc'            
        }
        p.update(params)

        r = requests.get(OpenEI_Api._rate_endpoint, params = p)

        try:

            j = json.loads(r.json())

            if 'error' in j.keys():
                return (None, j['error']['code'])
            
            return j
        
        except ValueError as ve:
            return (None, 'BAD RESPONSE')
        
        return
    
    
        
    
    