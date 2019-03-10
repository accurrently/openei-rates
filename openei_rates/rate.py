import datetime
from .api import OpenEIApi
from .rateschedule import RateSchedule


class Rate(object):
    """A Rate object hold metadat about a rate. It pulls down a new RateSchedule only when needed.
    """
    def __init__(self, d: dict):

        self.sector = d.get('sector')
        self.approved = True
        self.openei_uri = d.get('uri')
        self.name = d.get('name')
        self.label = d.get('label')
        self.utility = d.get('utility')
        self.description = d.get('description')
        self.source = d.get('source')
        self.source_parent_uri = d.get('sourceparent')
        self.wiring = d.get('phasewiring')

        start_d = d.get('startdate')
        self.begin_date = datetime.datetime.utcfromtimestamp(start_d) if start_d else None
        end_d = d.get('enddate')
        self.end_date = datetime.datetime.utcfromtimestamp(end_d) if end_d else None

        self.rate_schedule = None
    
    def is_active(self, dt: datetime.datetime):
        if self.begin_date:
            if self.begin_date <=  dt:
                return dt < self.end_date if self.end_date else True
        return False
    
    def get_rate_schedule(self, api: OpenEIApi):
        params = {
            'label': self.label,
            'detail': 'full',
            'limit': 1
        }
        code, j = api.rate_query(params)
        
        if j:
            self.rate_schedule = RateSchedule(j)

            return self.rate_schedule

