# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

import numpy as np
from numexpr import evaluate
from scipy.stats import expon
from scipy.stats import chi2
# from .import metrics  #to avoid prob in cyclic import of RadiativeForcing, from .metrics import RadiativeForcing does not work


class ForestGrowth(object): 
    """Class containing  methods to estimate forest growth rate"""
    def normal_growth(rotation=100,tstep=0.1):
        """Calculate biomass growth rate (i.e C uptake) a distribution with variance = rotation/4 ,  mean = rotation/2 
        and  a carbon neutral forest (i.e. growth normalized to 1)  (Cherubini 2011  doi: 10.1111/j.1757-1707.2011.01102.x)
        The function  starts at t=0 and ends at t=rotation.
        Arguments:
        rotation=100
        tstep=0.1
        """
        yrs=np.linspace(0, rotation,(rotation/tstep+1))
        pi=np.pi
        growth = evaluate('1/sqrt(2* pi *(rotation/4)**2)*exp(-((yrs-rotation/2)**2)/(2*(rotation/4)**2))')
        growth[int(rotation/tstep):] = 0 # 0 growth after harvesting
        norm_growth=growth/np.trapz(growth) #growth normalized to 1 (i.e. assumes carbon neutrality)
        return norm_growth

    ##########
    #TO CLEAN#
    ##########

    #~ def schnute_growth(t,T2,y2,a,b,Tr,Th=None,T1=0,y1=0,tstep=1):
        #~ """calculate growth for an array of yrs with the param
        #~ t=numpy array with time dimension (i.e. range of years for which to calculate, do not forget python is zero indexed... )
        #~ T1=initial age of the interval(default = 0)
        #~ T2= final age of the interval  (i.e. year when maxium stock is reached, in Cherubini assume Tr*2)
        #~ y1= stock at T1, default = 0
        #~ y2 stock at T2, default = 0
        #~ a=paramater of the schnute model
        #~ b=paramater of the schnute model
        #~ Tr=rotation period (hipotetical)
        #~ Th= time of harvest (default is Tr=Th but real harvest can happen before or after theoretical rotation)
        #~ 
        #~ # need to add tsteps
        #~ 
        #~ """
    #~ #     t = np.linspace(t[0], t[-1], tstep )  
    #~ #     slice_step = int(1/tstep)
        #~ 
        #~ if Th==None:
            #~ Th=Tr
        #~ 
        #~ #stock
        #~ st=evaluate("(( (y1**b) + ((y2**b) - (y1**b)) ) * (( 1- exp( -a* (t - T1 ) ) ) / (1- exp( -a* (T2 - T1 ))))) ** (1/b)") #see Comparison of Schnute’s and Bertalanffy- Richards’ growth function 
        #~ norm_st=st/np.full(len(st), st[Tr]) # calculate normalized growth (divide by stock at Tr)
    #~ 
        #~ #growth
        #~ gr_r=np.diff(st) #calculate growth rate i.e. derivative
        #~ norm_gr_r=np.diff(norm_st) #normalized growth rate i.e. relative to 1 unit sequestered
            #~ #add zero for yr o
        #~ gr_r=np.insert(gr_r, 0, 0) 
        #~ norm_gr_r=np.insert(norm_gr_r, 0, 0) 
    #~ 
    #~ 
        #~ #set to 0 from yr of harvest on
        #~ for arr in [st,norm_st,gr_r,norm_gr_r]:
            #~ arr[Th:]=0
        #~ # norm_st[Th:]=0
        #~ # gr_r[Th:]=0 # 
        #~ # norm_gr_r[Th:]=0 # set to 0 at new rotation
    #~ 
    #~ #     return st[0::1/slice_step],nor_st[0::1/slice_step],rel_gr[0::1/slice_step]
        #~ return st,norm_st,gr_r,norm_gr_r

class WoodDecay(object): 
    """Class containing methods to estimate wood decay rate"""
    #OLD
    # def delta(emission_year=0,t_horizon=100,tstep=.1):
        # """calculate exponential decay
        # """      
        # decay=np.zeros(int( (t_horizon/tstep )+1))
        # decay[ int( (emission_year)/tstep ) ]=1
        # return decay
        
    def delta(emission_index=0,t_horizon=100,tstep=.1):
        """calculate exponential decay
        """      
        decay=np.zeros(int( (t_horizon/tstep )+1))
        decay[emission_index]=1
        return decay
        
#TODO: update them based on timedelta
    # def uniform(emission_year=0,t_horizon=100,tstep=.1):
        # """calculate uniform decay
        # 
        # ###THINK ON WHAT TO DO WHEN EMISSION AFTER TIME HORIZON (E.G. year 150 in default case)
        # ###IF EMISSION OCCUR AFTER t_horizon/2 obviously the sum of yearly emission is not =1
        # 
        # """
        # decay=np.zeros(int(t_horizon/tstep)) #int to avoid np indexing warning
        # if emission_year==0:
            # decay[0]=1
        # else:
            # decay[ :(int(emission_year/tstep)) *2]=1 / ((emission_year/tstep)*2) 
        # return decay
# 
    # def exponential(emission_year=0,t_horizon=100,tstep=.1):
        # """calculate exponential decay
        # """
        # yrs=np.linspace(0, t_horizon,(t_horizon/tstep+1))
        # decay=expon(0,emission_year).pdf(yrs)
        # decay=decay*tstep
        # return decay
# 
    # def chi2(emission_year=0,t_horizon=100,tstep=.1):
        # """
        # use k paramater= t+2 as done in Cherubini (doi: 10.1111/j.1757-1707.2011.01156.x)
        # """
        # yrs=np.linspace(0, t_horizon,(t_horizon/tstep+1))
        # decay=chi2.pdf(yrs,emission_year+2)
        # decay=decay*tstep
        # return decay
