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
        self.approved_only = False
    
    def rate_query(self, params: dict = {}):

        p = {
            'api_key': self.api_key,
            'format': OpenEIApi.response_format,
            'orderby': 'startdate',
            'direction': 'desc',
            'version': 'latest'         
        }
        if self.approved_only:
            p['approved'] = 'true' if self.approved_only else 'false'

        p.update(params)
        logger.info('Sending request.')

        r = requests.get(OpenEIApi._rate_endpoint, params = p)
        
        
        if r.status_code == 403:
            logger.critical('Invalid API key. Use a valid. key. If you do not have one, get a free one at https://openei.org/services/api/signup/')
            raise ConnectionError('Invalid API key. If you do not have one, get a free one at https://openei.org/services/api/signup/')
        
        logger.info('Response: HTTP {}'.format(r.status_code))

        if r.ok:

            try:
                j = r.json()                
                j_errors = j.get('errors')
                if j_errors:
                    erstr = ''
                    for er in j_errors:
                        erstr += er + '\n'
                    logger.warning(
                        'The server responded with code {}, but there were errors. Translating to 404: {}'.format(r.status_code, erstr)
                    )

                    return (404, None)
                
                items = j.get('items')
                if items:
                    return (r.status_code, items)
            
            except ValueError as ve:
                logger.warning(
                    """There was a bad response.
                    This could be the server, or an application bug.
                    Try ensuring that 'version'='latest'
                    Here's the exception: {}
                    GET request is as follows:
                    {}
                    """.format(ve.with_traceback, r.url )
                )
                return (503, None)
        
        return (r.status_code, None)
    