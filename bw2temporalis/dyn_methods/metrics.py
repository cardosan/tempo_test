# -*- coding: utf-8 -*-
"""
Adapted from https://github.com/gschivley/co-fire, which is licensed:

The MIT License (MIT)

Copyright (c) 2015 Greg Schively

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import print_function, unicode_literals
from eight import *

import numpy as np
import numexpr as ne
from ..temporal_distribution import TemporalDistribution
from .biogenic_carbon import WoodDecay,ForestGrowth

#TODO: all made temporarily compatible with timedelta, but codes need cleaning, did not have time, will do after the paper draft is finished

#Sources # AR5-SM, p. 8SM-16,
RADIATIVE_EFFICIENCIES = {
    'co2': 1.7517e-15,        
    'ch4': 1.277E-13 * 1.65,  
    'n2o': 3.845E-13,        
    'sf6': 2.01e-11,          
}


class _Temperature_IRF_to_RF(object): #GIU:changed name cause this is not GTP
    """Calculate Temperature response function to radiative forcing (i.e. IRF temperature) for a unitary pulse radiative forcing.
    See Chapter 2.1.2 Olivie and Peters (2013, doi:10.5194/esd-4-267-2013) for detailed explanation

    `times` is a number or numpy array of relative years, starting from zero.

    Returns a numpy array with shape `time`, with units of degrees kelvin per watt/square meter (i.e. RF)."""

    def ar5_boucher(self, times):
        """Equation and constants from AR5-SM, p. 8SM-15, equation 8.SM.13 and table 8.SM.9.

        Equilibrium climate response (how much temperature would change if CO2 levels doubled)
        is 3.9 degrees kelvin."""
        #GIU:seems to be unnecessary
        times = np.array(times)
        return ne.evaluate("0.631 / 8.4 * exp(-times / 8.4) + 0.429 / 409.5 * exp(-times / 409.5)")

    def op_base(self, times):
        """Taken from Olivie and Peters (2013, doi:10.5194/esd-4-267-2013), Table 4, using the CMIP5 data.

        This has a slightly lower climate response value than Boucher (2008), which is used in AR5."""
        return ne.evaluate("0.43 / 2.57 * exp(-times / 2.57) + 0.32 / 82.24 * exp(-times / 82.24)")

    def op_low(self, times):
        c1, c2, d1, d2 = 0.43 / (1 + 0.29), 0.32 / (1 + 0.59), 2.57 * 1.46, 82.24 * 2.92
        """ The response function for radiative forcing. Taken from Olivie and Peters (2013),
        Table 4, using the CMIP5 data. This has a lower climate response value than AR5.
        The uncertainty in Table 4 assumes lognormal distributions, which is why values less
        than the median are determined by dividing by (1 + uncertainty).

        Convolve with radiative forcing to get temperature.
        """
        return c1/d1*np.exp(-times/d1) + c2/d2*np.exp(-times/d2)

    def op_high(self, times):
        c1, c2, d1, d2 = 0.43 * 1.29, 0.32 * 1.59, 2.57 / (1 + 0.46), 82.24 / (1 + 1.92)
        """ The response function for radiative forcing. Taken from Olivie and Peters (2013),
        Table 4, using the CMIP5 data. This has a higher climate response value than AR5.
        The uncertainty in Table 4 assumes lognormal distributions, which is why values less
        than the median are determined by dividing by (1 + uncertainty).

        Convolve with radiative forcing to get temperature.
        """
        return c1/d1*np.exp(-times/d1) + c2/d2*np.exp(-times/d2)

Temperature_IRF_to_RF = _Temperature_IRF_to_RF()

class _AtmosphericDecay(object):
    """Vectorized calculations for atmospheric decay curves for various gases.

    Most material from IPCC Assessment Report 5 (2013), working group 1: the physical science basis,
    chapter 8: anthropogenic and natural radiative forcing, hereafter AR5, and its supplementary
    material, hereafter AR5-SM. Reports are available at https://www.ipcc.ch/report/ar5/wg1/.

    Myhre, G.; Shindell, D.; Bréon, F.-M.; Collins, W.; Fuglestvedt, J.; Huang, J.; Koch, D.; Lamarque, J.-F.; Lee, D.; Mendoza, B.; et al. Anthropogenic and Natural Radiative Forcing. In Climate Change 2013: The Physical Science Basis. Contribution of Working Group I to the Fifth Assessment Report of the Intergovernmental Panel on Climate Change; Stocker, T. F., Qin, D., Plattner, G.-K., Tignor, M., Allen, S. K., Boschung, J., Nauels, A., Xia, Y., Bex, V., Midgley, P. M., Eds.; Cambridge University Press: Cambridge, United Kingdom and New York, NY, USA, 2013; pp 659–740.

    """
    LIFETIMES = {
        'ch4': 12.4,  # AR5, p. 675
        'n2o': 121.,  # AR5, p. 675
        'sf6': 3200., # AR5, p. 733
    }
    

    def __call__(self, gas, times):
        """Return fraction of gas emitted still remaining at `times`.

        `times` is relative years, starting at zero.

        Returns 1-d numpy with shape `times.shape`."""
        if gas == 'co2':
            return self.co2_decay_curve(times)
        else:
            #TODO find a way to calculate also these 2 decay
            assert gas not in ['co2_biogenic','ch4_fossil'], "{} only for Radiative_Forcing is calculated".format(gas)
            assert gas in self.LIFETIMES, "This gas is unknown"
            return self.exponential_decay_curve(times, gas)

    def co2_decay_curve(self, times):
        """Decay curve for CO2 from IPCC AR5 (2013).

        Equation and constants from AR5-SM, formula 8.SM.10 and table 8.SM.10.

        The report states that:

        "For CO2, Ri is more complicated because its atmospheric response time
        (or lifetime of a perturbation) cannot be represented by a simple
        exponential decay. The decay of a perturbation of atmospheric CO2
        following a pulse emission at time t is usually approximated by a sum of
        exponentials." (p. 8SM-15)

        Using numexpr is ~twice as fast as plain numpy.

        """
        return ne.evaluate("0.2173 + 0.224 * exp(-times / 394.4) + 0.2824 * "
                           "exp(-times / 36.54) + 0.2763 * exp(-times / 4.304)")

    def exponential_decay_curve(self, times, gas):
        """Decay curve for atmospheric gases other than CO2.

        The atmospheric decay of these gases can be approximated by
        exponential decay, where the IPCC 'lifetime' values can be used
        in the denominator. See AR5-SM p. 8SM-15.

        """
        return np.exp(-times / self.LIFETIMES[gas])

    def methane_to_co2(times,tau=12.4 ,alpha=0.51):
        """As methane decays some fraction (alpha) is converted to CO2.The convolution 
        with the methane emission profile gives the CO2 emission profile.


        This function is from Boucher, O.; Friedlingstein, P.; Collins, B.;
        Shine, K. P. The indirect global warming potential and global temperature
        change potential due to methane oxidation. Environmental Research Letters
        2009, 4 (4), 044007.

        `times` is a numpy array of relative years, starting at zero.
        `tau` is the CH4 lifetime of methane  (from Boucher and AR5)
        `alpha` is the fraction of methane converted to CO2; default is 51%.

        Returns an array of shape `times` with fraction of methane converted to CO2.

        """
        return 1 / 12.4 * alpha * np.exp(-times / tau)

AtmosphericDecay = _AtmosphericDecay()


class _RadiativeForcing(object):
    def __call__(self, gas, emissions, emission_times, time_step='Y', cutoff=100):
        """Calculate the radiative forcing due to pulse emissions of `gas`.

        `emissions` is a 1D numpy array of emission amounts.
        `emission_times` is a 1D numpy array of type `timedelta64` of relative years

        `emissions` and `emission_times` should have the same shape, and element of
        `emissions` to correspond to the element in `emissions_times` with the same
        index.

        `emission_times` do not have to be regularly spaced.
        
        `time_step` must be a `numpy datetime unit <https://docs.scipy.org/doc/numpy/reference/arrays.datetime.html#datetime-units>`_ 

        """
        
        assert emissions.shape==emission_times.shape , "`emissions` and `emission_times` should have the same shape, and element of `emissions` to correspond to the element in `emissions_times` with the same index"
        emission_times=emission_times.astype('timedelta64[{}]'.format(time_step))
        
        #TD.times
        times_TD=np.arange(np.datetime64(0, 'Y'), np.datetime64(cutoff,'Y'), dtype='datetime64[{}]'.format(time_step)).astype('timedelta64[{}]'.format(time_step))
        times_TD=np.append(times_TD,times_TD[-1]+1)
        #for atmospheric decay
        times_decay=np.linspace(0,cutoff,len(times_TD))
        
        if gas == "ch4_fossil":
            return self.fossil_ch4(emissions, emission_times, time_step, cutoff)

        elif gas == "co2_biogenic":     
            emission_RE_td = TemporalDistribution(
                emission_times,
                emissions * RADIATIVE_EFFICIENCIES['co2']
            )
            decay_td = TemporalDistribution(
                times_TD,
                co2bio_stand_decay(cutoff=cutoff,tstep=time_step,bio_emis_yr=emission_times)
            )
            return (emission_RE_td * decay_td)[:cutoff]
                        
        elif gas not in RADIATIVE_EFFICIENCIES:
            raise ValueError("Unknown gas")
        
        else:
            emission_RE_td = TemporalDistribution(
                emission_times,
                emissions * RADIATIVE_EFFICIENCIES[gas]
            )
            decay_td = TemporalDistribution(
                times_TD,
                AtmosphericDecay(gas, times_decay)                
            )
            return (emission_RE_td * decay_td)[:cutoff] 

    def fossil_ch4(self, emissions, emission_times, time_step, cutoff):

        """Calculate radiative forcing for fossil CH4 considering methane oxidation into CO2.
        Implicitly assumes that CO2 produced in the oxidation of CH4 is not already accounted for in the CO2 emission inventories (normal case).         
        """
        ##TODO to include Carbon-climate feedback      
        times_TD=np.arange(np.datetime64(0, 'Y'), np.datetime64(cutoff,'Y'), dtype='datetime64[{}]'.format(time_step)).astype('timedelta64[{}]'.format(time_step))
        times_TD=np.append(times_TD,times_TD[-1]+1)
        times_decay=np.linspace(0,cutoff,len(times_TD))
        
        #CH4 emission and decay TD
        emission_ch4_td = TemporalDistribution(
            emission_times,
            emissions
        )
        decay_ch4_td = TemporalDistribution(
            times_TD,
            AtmosphericDecay('ch4',times_decay)
        )
        
        #CO2 conversion rate from CH4 and CO2 decay TD
        converted_co2_td = TemporalDistribution(
            times_TD,
            _AtmosphericDecay.methane_to_co2(times_decay)

        )
        
        decay_co2_td = TemporalDistribution(
            times_TD,
            AtmosphericDecay('co2',times_decay)

        )
        #radiative forcing of CH4 emission and CO2 oxidated from CH4
        RF_emission_ch4_td = (emission_ch4_td * RADIATIVE_EFFICIENCIES['ch4']) * decay_ch4_td
        RF_converted_co2_td = ((emission_ch4_td * converted_co2_td) * RADIATIVE_EFFICIENCIES['co2']) * decay_co2_td 
        
        return (RF_converted_co2_td + RF_emission_ch4_td)[:len(times_TD)] #otherwise returns TD of len cutoff*2 

RadiativeForcing = _RadiativeForcing()


def AGTP(gas, emissions, times, time_step='Y', cutoff=100, method="ar5_boucher"):
    """Calculate the Absolute Global Temperature change Potential (AGTP) of of x kg of emitted of `gas`. 
    Indicates the impact (in degrees K) of that emission on the global-mean temperature at a certain time. 
    See eq. 9 Olivie and Peters (2013, doi:10.5194/esd-4-267-2013) for detailed explanation

    ### CHECK THIS BELOW###
    `emissions` is a 1D numpy array of emission amounts.
    
    `emission_times` is a 1D numpy array of type `timedelta64` of relative years
    
    `emissions` and `emission_times` should have the same shape, and element of `emissions` to correspond to `the element in `emissions_times` with the same index.
    
    `emission_times` do not have to be regularly spaced.

    `time_step` must be a `numpy datetime unit <https://docs.scipy.org/doc/numpy/reference/arrays.datetime.html#datetime-units>`_
    
    Returns a numpy array  shape `time`, with units of degrees kelvin per kg emitted.

    """
    
    assert method in {'ar5_boucher', 'op_base', 'op_low', 'op_high'}
    forcing_td = RadiativeForcing(gas, emissions, times, time_step, cutoff)
    # times_2 = np.linspace(0, cutoff, cutoff / time_step + 1)
    
    times_TD=np.arange(np.datetime64(0, 'Y'), np.datetime64(cutoff,'Y'), dtype='datetime64[{}]'.format(time_step)).astype('timedelta64[{}]'.format(time_step))
    times_TD=np.append(times_TD,times_TD[-1]+1)
    times_decay=np.linspace(0,cutoff,len(times_TD))
        
    temperature_td = TemporalDistribution(
        # times_2,
        times_TD,
        getattr(Temperature_IRF_to_RF, method)(times_decay) #call the Temperature_IRF_to_RF method "method" and pass "times_2" as argument
    )
    
    return (forcing_td * temperature_td)[:len(times_TD)] #convolution IRF with IRF temperature  (see eq.4 and 0 Olivie and Peters (2013, doi:10.5194/esd-4-267-2013))

#TODO: recode this to deal better with timedelta
def co2bio_stand_decay(cutoff=100,growth_sc_fact=1,tstep='Y',rot=100,NEP=None,bio_decay="delta",bio_emis_yr=np.array([0])):
    """
    Decay curve for a unitary pulse emission of biogenic CO2 (Cherubini 2011  doi: 10.1111/j.1757-1707.2011.01102.x)
    following the single stand approch (Cherubini 2013 doi.org/10.1016/j.jenvman.2013.07.021)
    THIS APPLY ONLY TO SINGLE STAND. For landscape approach the effect of each single stand 
    (i.e. the result of this function) have to be summed over time
    
    NEP= relative Net Ecosystem Productivity profile. By defaul assumes a normal growth and a carbon neutral stand
    IRF= impulse response function profile for carbon
    rot=rotation lenght of forest, default is 100 yrs
    bio_emis_yr= year when the biogenic carbon is emitted, by default at yr=0
    bio_decay= emission profile of biogenic carbon by default delta function (all C emitted at year biog_emis_yr)
    
    the growth scaling factor (see Cherubini 2011 doi:10.1016/j.ecolmodel.2011.06.021)
        if=1 the same C amount is stored compared to previoys rotation; if < 1, a lower amount of C is stored (e.g., conversion of mature forest into managed), when
        > 1 there is an increase C stored (e.g.,a managed forest left to grow up to the mature state)
    
    Note: this does not include changes in land use (see Cherubini 2011 doi:10.1016/j.ecolmodel.2011.06.021, eq. 5)
    
    """
    times_TD=np.arange(np.datetime64(0, 'Y'), np.datetime64(cutoff,'Y'), dtype='datetime64[{}]'.format(tstep)).astype('timedelta64[{}]'.format(tstep))
    times_TD=np.append(times_TD,times_TD[-1]+1)
    times_array=np.linspace(0,cutoff,len(times_TD))
    #TODO; tstep works fine like this, but better rewrite methods to explicity deal with timedelta
    timestep=cutoff/(len(times_TD)-1)
    bio_emis_index=bio_emis_yr.astype('timedelta64[{}]'.format(tstep)).astype('int')[0]
    
    IRF=AtmosphericDecay('co2',times_array)
    #only delta has been updated for now
    assert bio_decay in {'delta'}#, 'uniform', 'exponential', 'chi2'}
    biog_emis_prof=getattr(WoodDecay, bio_decay)(emission_index=bio_emis_index,t_horizon=cutoff,tstep=timestep)
    #old
    # biog_emis_prof=getattr(WoodDecay,bio_decay)(emission_year=bio_emis_yr,t_horizon=cutoff,tstep=timestep)
    
    if NEP is None: 
        NEP=ForestGrowth.normal_growth(rotation=rot,tstep=timestep)
    assert isinstance(NEP, np.ndarray), "NEP must be a numpy array"
    
    conv_emis=np.convolve(biog_emis_prof,IRF,mode='full')[:IRF.size]
        
    #assert growth_sc_fact > 0, maybe can be negative...have to check
    NEP_scaled=NEP*growth_sc_fact #scale forest growth in case of non carbon neutral forests
    conv_gr=np.convolve(NEP_scaled,IRF,mode='full')[:IRF.size]
    decay_bio=(conv_emis-conv_gr) 
    return decay_bio 
    
