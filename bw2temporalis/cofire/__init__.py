# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

"""cofire is a library built by Greg Schively. It can be downloaded from https://github.com/gschivley/co-fire.

We wrap this library to provide dynamic LCIA methods that fit the Temporalis data model."""

from ..dynamic_ia_methods import DynamicIAMethod
from .constants import co2_gtp_td, ch4_gtp_td
from bw2data import config, Database
import itertools


co2_gtp_function = """def co2_gtp_function(datetime):
    from bw2temporalis.cofire import co2_gtp_td
    from datetime import timedelta
    import collections
    return_tuple = collections.namedtuple('return_tuple', ['dt', 'amount'])
    return [return_tuple(datetime + timedelta(days=365.24 * x), y) for x, y in co2_gtp_td]"""

ch4_gtp_function = """def ch4_gtp_function(datetime):
    from bw2temporalis.cofire import ch4_gtp_td
    from datetime import timedelta
    import collections
    return_tuple = collections.namedtuple('return_tuple', ['dt', 'amount'])
    return [return_tuple(datetime + timedelta(days=365.24 * x), y) for x, y in ch4_gtp_td]"""


def create_temperature_method(name="GTP", worst_case=("GTP", "worst case")):
    """Create an LCIA method temperature change due to GHG emissions.

    Temperature change is calculated every year over 250 years.

    `name` is name of new method to create."""
    db = Database(config.biosphere)

    method = DynamicIAMethod(name)

    cf_data = {}

    for ds in itertools.chain(db.search("'carbon dioxide, fossil'"),
                              db.search("'carbon dioxide, in air'")):
        cf_data[ds.key] = co2_gtp_function

    for ds in db.search("'methane fossil'"):
        cf_data[ds.key] = ch4_gtp_function

    method.register()
    method.write(cf_data)
    method.to_worst_case_method(worst_case, dynamic=False)
    return method
