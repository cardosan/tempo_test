# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

import numpy as np
from ..dynamic_lca import DynamicLCA
from .constants import co2_agtp_ar5_td,co2_rf_td

# from .dynamic_ia_methods import dynamic_methods, DynamicIAMethod
# from .temporal_distribution import TemporalDistribution
# from .timeline import Timeline, data_point



def time_dependent_LCA(demand,dynIAM='GWP',t0=None,TH=100,DynamicLCA_kwargs={},characterize_dynamic_kwargs={}):
    """calculate dynamic GWP or GTP for the functional unit and the time horizon indicated following the approach of Levausseur (2010, doi: 10.1021/es9030003).
    It also consider climate effect of forest regrowth of biogenic CO2 (Cherubini 2011  doi: 10.1111/j.1757-1707.2011.01102.x)
    assuming a rotation lenght of 100 yrs.

    
Args:
    * *demand* (dict):  The functional unit. Same format as in LCA.
    * *t0* (datetime,default = now): year 0 of the time horizon considered.
    * *TH* (int,default =100): lenght of the time horizon in yearsfinal year of the time horizon considered.
    * *dynIAM* (string, default='GWP'): Dynamic IA Method, can be 'GWP' or 'GTP'.
    * *DynamicLCA_kwargs* (dict, default=None): optional argument to be passed for DynamicLCA.
    * *characterize_dynamic_kwargs* (dict, default=None): optional arguments to be passed for characterize_dynamic.
    """


    dyn_m={'GWP':"RadiativeForcing",'GTP':'AGTP'}
    assert dynIAM in dyn_m, "DynamicIAMethod not present"

    #set default start and calculate year of TH end
    th_zero=np.datetime64('now') if t0 is None else np.datetime64(t0)
    th_end=th_zero.astype('datetime64[Y]').astype(str).astype(int) + TH #convert to string first otherwhise gives years relative to POSIX time

    #calculate lca
    dlca = DynamicLCA(demand, (dyn_m[dynIAM] , "worst case"),
                      th_zero,
                      **DynamicLCA_kwargs
                     )
    dyn_lca= dlca.calculate().characterize_dynamic(dyn_m[dynIAM],cumulative=False, **characterize_dynamic_kwargs)
    #~dyn_lca=([int(x) for x in dyn_lca[0]],dyn_lca[1]) #convert years to int, but better not to be consistent with resolution less than years

    #pick denominator based on metric
    if dyn_m[dynIAM]=='GWP':co2=co2_rf_td
    if dyn_m[dynIAM]=='GTP':co2=co2_agtp_ar5_td

    #calculate lenght of th from first emission occuring
    length=len([int(yr) for yr in dyn_lca[0] if int(yr) <= th_end])


    #calculate agwp for demand and co2 and then gwp
    res=np.trapz(x=dyn_lca[0][:length] , y=dyn_lca[1][:length]) / np.trapz(
                 x=(co2_rf_td.times.astype('timedelta64[Y]').astype('int') + dyn_lca[0][0])[:length],
                 y=co2_rf_td.values[:length])
    
    return res
