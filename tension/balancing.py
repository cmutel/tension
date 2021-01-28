from .brightway_utils import get_bio, DATABASE
from bw2data.backends.peewee.proxies import Exchange
from bw2data.backends.peewee.schema import ExchangeDataset as ED
import bw2data as bd
import pandas as pd


bio = get_bio()


def get_sign(exc):
    exc_mapping = {
        'technosphere': -1,
        'production': 1,
        'substitution': 1,
    }
    if exc.type in exc_mapping:
        return exc_mapping[exc.type]
    else:
        assert exc.type == 'biosphere'

    bio_mapping = {
        'air': 1,
        'economic': 0,
        'natural resource': -1,
        'social': 0,
        'soil': 1,
        'water': 1
    }
    return bio_mapping[bio[(exc.input_database, exc.input_code)]['categories'][0]]


def get_property(ed, label):
    try:
        return next(v for k, v in ed.data['properties'].items() if k == label)
    except StopIteration:
        pass


def get_carbon_content(ed):
    carbon = get_property(ed, 'carbon content')
    if carbon is not None:
        return carbon['amount']

    fc, nfc = get_property(ed, 'carbon content, fossil'), get_property(ed, 'carbon content, non-fossil')
    if fc is not None:
        return fc['amount'] + nfc['amount']

    return None


def get_mass(ed):
    if ed.data['unit'] == 'kilogram':
        return ed.data['amount']

    wet_mass = get_property(ed, 'wet mass')
    if wet_mass is not None and wet_mass['unit'] in ('kilogram', 'kg'):
        return wet_mass['amount']

    return None


def get_carbon_mass(ed):
    assert isinstance(ed, ED)

    cc = get_carbon_content(ed)
    mass = get_mass(ed)

    if cc is not None and mass is not None:
        return cc * mass
    else:
        return None


class Balancer:
    def __init__(self, act):
        if isinstance(act, tuple):
            act = bd.get_activity(act)
        assert isinstance(act, bd.backends.peewee.Activity)
        self.obj = act
        self.key = self.obj.key

    def exchanges(self):
        return ED.select().where(ED.output_database == self.key[0], ED.output_code == self.key[1])

    def calculate_carbon(self):
        """Calculate actual carbon flows.

        Creates ``self.report``, which has data format:

            [(sign, amount of carbon (kg) or None, exchange object)]

        """
        self.report = [
            (get_sign(ed), get_carbon_mass(ed), ed)
            for ed in self.exchanges()
        ]

    def filtered_report(self):
        for x, y, z in self.report:
            if x is not None and y is not None:
                yield x, y, z

    def positive(self):
        return sum(x * y for x, y, z in self.filtered_report() if x > 0)

    def negative(self):
        return sum(x * y for x, y, z in self.filtered_report() if x < 0)

    def write_results(self):
        p, n = self.positive(), -1 * self.negative()
        try:
            difference = (p - n) / p
        except ZeroDivisionError:
            difference = -1 * n
        self.obj.setdefault('balances', {})['carbon'] = {
                'in': n,
                'out': p,
                'difference': difference
            }
        self.obj.save()


def get_report_for_code(code):
    act = bd.get_activity((DATABASE, code))
    b = Balancer(act)
    b.calculate_carbon()

    data = []

    def try_attribute(obj, key, missing=None):
        try:
            return obj[key]
        except KeyError:
            return missing

    for sign, amount, ed in b.report:
        exc = Exchange(ed)
        data.append({
            'sign': sign,
            'carbon': amount,
            'amount': exc['amount'],
            'type': exc['type'],
            'name': exc.input['name'],
            'unit': exc.input['unit'],
            'location': try_attribute(exc.input, 'location'),
            'product': try_attribute(exc.input, 'reference product'),
            'url': '/activity/' + exc.input['code'],
            'properties': try_attribute(exc, 'properties', []),
        })
    return act, data
