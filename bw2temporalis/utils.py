# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from bw2data import Database
from numbers import Number
import arrow
import numpy as np
import warnings
import re


def get_maximum_value(maybe_func, lower=None, upper=None, dynamic=True):
    """Get maximum CF values by calculating each week for 100 years. Poor computers."""
    if lower is None:
        lower = arrow.get(2000, 1, 1)
    if upper is None:
        upper = arrow.get(2100, 1, 1)
    if isinstance(maybe_func, Number):
        return maybe_func
    def _(obj):
        if isinstance(obj, Number):
            return obj
        else:
            return sum([x.amount for x in obj])
    if dynamic:
        return max([_(maybe_func(x))
            for x in arrow.Arrow.range('week', lower, upper)])
    else:
        # If total CF not a function of time of emission,
        # don't need to do all this work...
        return _(maybe_func(lower))


def check_temporal_distribution_totals(name):
    """Check that temporal distributions sum to total `amount` value"""
    data = Database(name).load()
    errors = []
    for key, value in data.items():
        if value.get('type', 'process') != 'process':
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


function_re = re.compile("^def\s+(?P<func_name>\S+)\s*\(\s*\S*\s*(?:,\s*\S+)*\):", re.UNICODE)


def get_function_name(string):
    """Use a regular expression to extract the name of a Python function.

    Returns None is no function is found in ``string``."""
    match = function_re.match(string)
    if not match:
        return None
    else:
        return match.groupdict()['func_name']
