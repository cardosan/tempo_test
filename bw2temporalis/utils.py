from bw2data import Database
from numbers import Number
import arrow
import numpy as np
import warnings


def get_maximum_value(maybe_func, lower=arrow.get(2000, 1, 1), upper=arrow.get(2100, 1, 1)):
    """Get maximum CF values by calculating each week for 100 years. Poor computers."""
    if isinstance(maybe_func, Number):
        return maybe_func
    def _(obj):
        if isinstance(obj, Number):
            return obj
        else:
            return sum([x.amount for x in obj])
    return max([_(maybe_func(x))
        for x in arrow.Arrow.range('week', lower, upper)])


def check_temporal_distribution_totals(name):
    """Check that temporal distributions sum to total `amount` value"""
    data = Database(name).load()
    errors = []
    for key, value in data.iteritems():
        if value['type'] != 'process':
            continue
        for exchange in value.get('exchanges', []):
            if 'temporal distribution' in exchange:
                amount = exchange['amount']
                total = sum([x[1] for x in exchange['temporal distribution']])
                if not np.allclose(amount, total):
                    errors.append({
                        "output": key,
                        "intput": exchange['input'],
                        "expected": amount,
                        "found": total
                    })
    if errors:
        warnings.warn("Unbalanced exchanges found; see returned errors")
        return errors
    else:
        return True
