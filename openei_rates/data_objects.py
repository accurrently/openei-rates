from typing import NamedTuple

TierIndex = NamedTuple(
    'TierIndexNT',
    [
        ('MAX', int),
        ('RATE', int),
        ('ADJ', int),
        ('SELL', int),
        ('ARRAY_LENGTH', int)
    ]
)(0, 1, 2, 3, 4)


class DemandResult(NamedTuple):
    normalized: bool
    peak_index: int
    qty: float
    span: int
    net_metered: bool




class Period(NamedTuple):

    interval_hours: float
    span: int
    month: int
    hour: int
    weekend: bool


class Tier(NamedTuple):

    max: float
    price: float
    adj: float
    sell: float

    def isin(self, qty: float):
        return qty <= self.max if self.max > 0.0 else True


class Peak(NamedTuple):

    index: int
    qty: float
    hour: int
    weekend: bool
    peak_interval_index: int
    peak_interval_qty: float

    def clip(self, ceiling: float = None, floor: float = None):
        a = self.qty
        if floor is not None:
            a = max(floor, a)
        if ceiling is not None:
            a = min(ceiling, a)
        return a
