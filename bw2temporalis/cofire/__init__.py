# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

"""cofire is a library built by Greg Schively. It can be downloaded from https://github.com/gschivley/co-fire.

We wrap this library to provide dynamic LCIA methods that fit the Temporalis data model."""

from ..dynamic_ia_methods import DynamicIAMethod
from bw2data import config, Database
import itertools


def create_cofire_methods():
    """Create LCIA methods for radiative forcing and temperature change due to GHG emissions.

    Effects is calculated every year over 250 years.

    `name` is name of new method to create."""
    function_template = """def ghg_function(datetime):
        from bw2temporalis.cofire.constants import {method}
        from datetime import timedelta
        import collections
        return_tuple = collections.namedtuple('return_tuple', ['dt', 'amount'])
        return [return_tuple(datetime + timedelta(days=365.24 * x), y) for x, y in {method}]"""

    db = Database(config.biosphere)

    to_create = [
        ('GTP', '{flow}_gtp_td_ar5'),
        ('GTP OP base', '{flow}_gtp_td_base'),
        ('GTP OP low', '{flow}_gtp_td_low'),
        ('GTP OP high', '{flow}_gtp_td_high'),
        ('Radiative Forcing', '{flow}_rf'),
    ]

    for name, func in to_create:
        worst_case = (name, "worst case")
        method = DynamicIAMethod(name)
        cf_data = {}

        for ds in itertools.chain(db.search("'carbon dioxide, fossil'"),
                                  db.search("'carbon dioxide, in air'")):
            cf_data[ds.key] = function_template.format(method=func.format(flow="co2"))

        for ds in db.search("'methane fossil'"):
            cf_data[ds.key] = function_template.format(method=func.format(flow="ch4"))

        method.register(
            from_function="create_temperature_methods",
            library="cofire"
        )
        method.write(cf_data)
        method.to_worst_case_method(worst_case, dynamic=False)
