# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

"""cofire is a library built by Greg Schively. It can be downloaded from https://github.com/gschivley/co-fire.

We wrap this library to provide dynamic LCIA methods that fit the Temporalis data model."""

from ..dynamic_ia_methods import DynamicIAMethod
from .constants import co2_agtp_td, co2bio_agtp_td, ch4_agtp_td,ch4_fossil_agtp_td,n2o_agtp_td, sf6_agtp_td,co2_rf_td, co2bio_rf_td, ch4_rf_td,ch4_fossil_rf_td,n2o_rf_td, sf6_rf_td

from bw2data import config, Database
import itertools

#TODO: update AGTP

def create_climate_methods():
    
    """Create the dynamic LCIA methods for AGTP and Radiative Forcing that are calculated every year over 500 years for each GHG emissions.
    Gasses from custom biosphere database can be added simpy adding their names to `gas_name_in_biosphere`
    """
    
    bio = Database(config.biosphere)
    
    #from report 'ecoinvent 3.3_LCIA_implementation'
    gas_name_in_biosphere = {
    'co2': [
        "Carbon dioxide, fossil", #fossil fuel emission thus normal CF
        "Carbon dioxide, from soil or biomass stock", # emission from LUC thus normal CF
        "Carbon dioxide, land transformation", #same of above in ei2. bw2 maps to biosphere flow of ei3, left just in case
            #"Carbon dioxide, non-fossil, from calcination" #non characterized in ei 3.3"
            ],
    'ch4_fossil': [
        "Methane", # old fossil ch4 of ei2. bw2 maps to biosphere flow of ei3, left just in case
        "Methane fossil",
        "Methane, from soil or biomass stock"
            ],
    'ch4': [
        "Methane, non-fossil",
        "Methane, biogenic" # old non_fossil ch4 of ei2. bw2 maps to biosphere flow of ei3, left just in case
            ],
    'n2o': ["Dinitrogen monoxide"],
    'sf6': ["Sulfur hexafluoride"],
    'co2bio':
            ('static_forest',"C_biogenic"), #see DynamicLCA.add_biosphere_flows() to understand why this, should be biogenic (ei22) or non-fossil (ei3) technically but used this trick and check if downstream goes to forest
            
    }   
    
    dyn_met={"agtp_ar5":"AGTP",
             "agtp_base":"GTP OP base",
             "agtp_low":"GTP OP low",
             "agtp_high":"GTP OP high",
             "rf":"RadiativeForcing",
             
             }
                 
    function="""def {0}_{1}_function(datetime):
                    from bw2temporalis.dyn_methods.constants import {0}_{1}_td
                    import numpy as np
                    from datetime import timedelta
                    import collections
                    return_tuple = collections.namedtuple('return_tuple', ['dt', 'amount'])
                    return [return_tuple(d,v) for d,v in zip((datetime+{0}_{1}_td.times.astype(timedelta)),{0}_{1}_td.values)]"""

    print('Dynamic IA Methods written:')
    for met_func,met_name in dyn_met.items():

        method = DynamicIAMethod(met_name)

        cf_data = {}

        for gas,gas_bio in gas_name_in_biosphere.items():
            if gas=='co2bio':
                #need again to convert datetime back to numpy
                cf_data[gas_bio] =function.format(gas,met_func)                
                 # """def {0}_{1}_function(datetime):
                                        # from bw2temporalis.dyn_methods.constants import {0}_{1}_td
                                        # import numpy as np
                                        # import collections
                                        # return_tuple = collections.namedtuple('return_tuple', ['dt', 'amount'])
                                        # return [return_tuple(d,v) for d,v in zip(np.datetime64(datetime)+{0}_{1}_td.times,{0}_{1}_td.values)]""".format(gas,met_func) 
            else:
                for gas_n in gas_bio:
                    for bio_key in [ds.key for ds in bio if ds['name']==gas_n]: 
                        cf_data[bio_key] = function.format(gas,met_func)
                        # """def {0}_{1}_function(datetime):
                        # from bw2temporalis.dyn_methods.constants import {0}_{1}_td
                        # import numpy as np
                        # import collections
                        # return_tuple = collections.namedtuple('return_tuple', ['dt', 'amount'])
                        # return [return_tuple(d,v) for d,v in zip(np.datetime64(datetime)+{0}_{1}_td.times,{0}_{1}_td.values)]""".format(gas,met_func)

                        # return [return_tuple(d,v) for d,v in zip(np.datetime64(datetime)+{0}_{1}_td.times,{0}_{1}_td.values)]""".format(gas,met_func)
                            

        method.register()
        method.write(cf_data)
        #GIU:what is this
        # method.register(
            # from_function="create_climate_methods",
            # library="cofire"
        # )        

        method.to_worst_case_method((met_name,"worst case"), dynamic=False)
        print(method)

    #GIU:is the return of method necessary?
    # return method

