import bw2data as bd
import pandas as pd


DATABASE = "Ecoinvent 3.7.1 cutoff"
BIOSPHERE = "biosphere3"


def get_balances(act):
    try:
        return act['balances']
    except KeyError:
        return None


def get_isic(ds):
    try:
        return next(o for o in ds['classifications'] if o[0] == 'ISIC rev.4 ecoinvent')[1]
    except:
        return None


def get_dataframe():
    print("Loading cached data...")
    db = bd.Database(DATABASE)
    data = [o for o in db if get_balances(o)]
    return pd.DataFrame([{
        'unit': o['unit'],
        'location': o['location'],
        'name': o['name'],
        'in': o['balances']['carbon']['in'],
        'out': o['balances']['carbon']['out'],
        'difference': o['balances']['carbon']['difference'],
        'isic': get_isic(o),
        'code': o['code'],
    } for o in data])


def get_bio():
    return {o.key: o for o in bd.Database(BIOSPHERE)}
