# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

import numpy as np
from ..dynamic_lca import DynamicLCA
from .constants import co2_agtp_ar5_td,co2_rf_td

# from .dynamic_ia_methods import dynamic_methods, DynamicIAMethod
# from .temporal_distribution import TemporalDistribution
# from .timeline import Timeline, data_point



def time_dependent_LCA(FU,dynIAM='GWP',TH_start=None,TH_end=None,DynamicLCA_kwargs={},characterize_dynamic_kwargs={}):
    """calculate dynamic GWP or GTP for the functional unit and the time horizon
    indicated following the approach of Levausseur (2010, doi: 10.1021/es9030003).
    It also consider climate effect of forest regrowth of biogenic CO2 (Cherubini 2011  doi: 10.1111/j.1757-1707.2011.01102.x)
    assuming a rotation lenght of 100 yrs.

    
Args:
    * *FU* (dict):  The functional unit. Same format as in LCA.
    * *TH_start* (datetime,default = now): year 0 of the time horizon considered.
    * *TH_end* (datetime,default = now + 100 years): final year of the time horizon considered.
    * *dynIAM* (string, default='GWP'): Dynamic IA Method, can be 'GWP' or 'GTP'.
    * *DynamicLCA_kwargs* (dict, default=None): optional argument to be passed for DynamicLCA.
    * *characterize_dynamic_kwargs* (dict, default=None): optional arguments to be passed for characterize_dynamic.
    """
    
    dyn_m={'GWP':"RadiativeForcing",'GTP':'AGTP'}
    assert dynIAM in dyn_m, "DynamicIAMethod not present"
    
    #set defaul start and end if not passed
    th_zero=np.datetime64('now') if TH_start is None else np.datetime64(TH_start)
    th_end=np.datetime64('now').astype('datetime64[Y]')+np.timedelta64(100,'Y') if TH_end is None else np.datetime64(TH_end)

    #calculate time horizon
    TH=(th_end-th_zero).astype('timedelta64[Y]').astype(int)
    #calculate lca
    dlca = DynamicLCA(FU, (dyn_m[dynIAM] , "worst case"),
                      th_zero,
                      **DynamicLCA_kwargs
                     )
    dyn_lca= dlca.calculate().characterize_dynamic(dyn_m[dynIAM],cumulative=False, **characterize_dynamic_kwargs)

    #pick denominator based on metric
    if dyn_m[dynIAM]=='GWP':co2=co2_rf_td
    if dyn_m[dynIAM]=='GTP':co2=co2_agtp_ar5_td

        

    #calculate 
    res=np.trapz(x=dyn_lca[0][:TH] , y=dyn_lca[1][:TH]) / np.trapz(
                 x=(co2_rf_td.times.astype('timedelta64[Y]').astype('float')+dyn_lca[0][0])[:TH],
                 y=co2_rf_td.values[:TH])
    
    return res
