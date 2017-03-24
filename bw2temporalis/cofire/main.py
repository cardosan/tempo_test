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

import numpy as np
import numexpr as ne
from scipy.interpolate import interp1d
from scipy.signal import fftconvolve
from scipy.integrate import cumtrapz
from ..temporal_distribution import TemporalDistribution


RADIATIVE_EFFICIENCIES = {
    'co2': 1.7517e-15,        # AR5-SM, p. 8SM-16,
    'ch4': 1.277E-13 * 1.65,  # Source?
    'n2o': 3.845E-13,         # Source?
    'sf6': 2.01e-11           # Source?
}


class _GlobalTemperaturePotential(object):
    """Calculate global temperature potential change for a unit forcing.

    `times` is a number or numpy array of relative years, starting from zero.

    Returns a numpy array with shape `time`, with units of degrees kelvin per (watt/square meter)."""

    def ar5_boucher(self, times):
        """Equation and constants from AR5-SM, p. 8SM-15, equation 8.SM.13 and table 8.SM.9.

        Equilibrium climate response (how much temperature would change if CO2 levels doubled)
        is 3.9 degrees kelvin."""
        times = np.array(times)
        return ne.evaluate("0.631 / 8.4 * exp(-times / 8.4) + 0.429 / 409.5 * exp(-times / 409.5)")

    def op_base(self, times):
        """Taken from Olivie and Peters (2013) (need citation), Table 4, using the CMIP5 data.

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

GlobalTemperaturePotential = _GlobalTemperaturePotential()


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

    def methane_to_co2(times, alpha=0.51):
        """As methane decays some fraction is converted to CO2.

        This function is from Boucher, O.; Friedlingstein, P.; Collins, B.;
        Shine, K. P. The indirect global warming potential and global temperature
        change potential due to methane oxidation. Environmental Research Letters
        2009, 4 (4), 044007.

        12.4 is the lifetime of methane, found in Boucher and AR5.

        `times` is a numpy array of relative years, starting at zero.
        `alpha` is the fraction of methane converted to CO2; default is 51%.

        Returns an array of shape `times` with fraction of methane converted to CO2.

        """
        return 1 / 12.4 * alpha * np.exp(-times / 12.4)

AtmosphericDecay = _AtmosphericDecay()


class _RadiativeForcing(object):
    def __call__(self, gas, emissions, emission_times, time_step=0.1, cutoff=100):
        """Calculate the radiative forcing due to continuous emissions of `gas`.

        `emissions` is a 1D numpy array of emission amounts.
        `emission_times` is a 1D numpy array of relative years, starting at zero.

        `emissions` and `emission_times` should have the same shape, and element of
        `emissions` to correspond to the element in `emissions_times` with the same
        index.

        `emission_times` do not have to be regularly spaced.

        """
        if gas == "ch4":
            return self.pulsed_emissions_ch4(emissions, emission_times, time_step, cutoff)
        elif gas not in RADIATIVE_EFFICIENCIES:
            raise ValueError("Unknown gas")
        else:
            times = np.linspace(0, cutoff, cutoff / time_step + 1)
            emission_td = TemporalDistribution(
                emission_times,
                emissions * RADIATIVE_EFFICIENCIES[gas]
            )
            decay_td = TemporalDistribution(
                times,
                AtmosphericDecay(gas, times)
            )
            return emission_td * decay_td

    def pulsed_emissions_ch4(self, emissions, emission_times, time_step, cutoff):
        """Special handling - do we need to include decay to CO2?

        TODO: This should not need a special method"""
        times = np.linspace(0, cutoff, cutoff / time_step + 1)
        emission_td = TemporalDistribution(
            emission_times,
            emissions * RADIATIVE_EFFICIENCIES['ch4']
        )
        decay_td = TemporalDistribution(
            times,
            AtmosphericDecay("ch4", times)
        )
        return emission_td * decay_td

RadiativeForcing = _RadiativeForcing()


def gtp(gas, emissions, times, time_step=0.1, cutoff=100, method="ar5_boucher"):
    assert method in {'ar5_boucher', 'op_base', 'op_low', 'op_high'}
    forcing_td = RadiativeForcing(gas, emissions, times, time_step, cutoff)
    times_2 = np.linspace(0, cutoff, cutoff / time_step + 1)
    temperature_td = TemporalDistribution(
        times_2,
        getattr(GlobalTemperaturePotential, method)(times_2)
    )
    return forcing_td * temperature_td


def rf(gas, emissions, times, time_step=0.1, cutoff=100):
    return RadiativeForcing(gas, emissions, times, time_step, cutoff)


# def CH4_rf(emission, years, tstep=0.01, kind='linear',
#              decay=True, emiss_type='sustained'):
#     """Transforms an array of methane emissions into radiative forcing with user-defined
#     time-step.

#     emission: an array of emissions, should be same size as years
#     years: an array of years at which the emissions take place
#     : time step to be used in the calculations
#     kind: the type of interpolation to use; can be linear or cubic
#     emiss_type: 'sustained' or 'pulse' - if 'pulse', then the emission values are
#     divided by . this allows a pulse of 1 kg in the first value of the array to
#     represent a full kg of emission, and 1 kg in all values associated with the first
#     year to also represent a full kg when 'sustained'.
#     """
# #emission is a series of emission numbers, years should match up with it
#     if min(years) > 0:
#         years = years - min(years)

#     if emiss_type == 'pulse':
#         emission /= tstep

#     end = max(years)
#     # fch4 = interp1d(years, emission, kind=kind)
#     time = np.linspace(years[0], end, end/ + 1)
#     ch4_inter_emissions = fch4(time)
#     ch4_atmos = np.resize(fftconvolve(CH4_AR5(time), ch4_inter_emissions),
#                           time.size) * tstep
#     co2 = np.resize(fftconvolve(ch42co2(time), ch4_inter_emissions),
#                     time.size) * tstep
#     co2_atmos = np.resize(fftconvolve(CO2_AR5(time), co2),
#                           time.size) * tstep

#     if decay == True:
#          rf = ch4_atmos * ch4_re + co2_atmos * co2_re
#     else:
#         rf = ch4_atmos * ch4_re
#     fil = np.zeros_like(time, dtype=bool)
#     for i in time:
#         if i == int(i):
#             fil[i/tstep] = True

#     return rf[fil]


#             pass


# def CH4_rf_cc(emission, years, tstep=0.01, kind='linear',
#              decay=True, emiss_type='sustained'):
#     """Transforms an array of methane emissions into radiative forcing with user-defined
#     time-step, accounting for climate-carbon feedbacks.

#     emission: an array of emissions, should be same size as years
#     years: an array of years at which the emissions take place
#     : time step to be used in the calculations
#     kind: the type of interpolation to use; can be linear or cubic
#     emiss_type: 'sustained' or 'pulse' - if 'pulse', then the emission values are
#     divided by . this allows a pulse of 1 kg in the first value of the array to
#     represent a full kg of emission, and 1 kg in all values associated with the first
#     year to also represent a full kg when 'sustained'.
#     """
#     gamma = (44.0/12.0) * 10**12

# #emission is a series of emission numbers, years should match up with it
#     if min(years) > 0:
#         years = years - min(years)

#     if emiss_type == 'pulse':
#         emission /= tstep

#     end = max(years)
#     fch4 = interp1d(years, emission, kind=kind)
#     time = np.linspace(years[0], end, end/ + 1)
#     ch4_inter_emissions = fch4(time)
#     ch4_atmos = np.resize(fftconvolve(CH4_AR5(time), ch4_inter_emissions),
#                           time.size) * tstep
#     co2 = np.resize(fftconvolve(ch42co2(time), ch4_inter_emissions),
#                     time.size) * tstep
#     co2_atmos = np.resize(fftconvolve(CO2_AR5(time), co2),
#                           time.size) * tstep
#     cc_co2 = CH4_cc_tempforrf(emission, years) * gamma
#     cc_co2_atmos = np.resize(fftconvolve(CO2_AR5(time), cc_co2),
#                           time.size) * tstep

#     if decay == True:
#          rf = ch4_atmos * ch4_re + (co2_atmos +cc_co2_atmos) * co2_re
#     else:
#         rf = ch4_atmos * ch4_re + (cc_co2_atmos) * co2_re
#     fil = np.zeros_like(time, dtype=bool)
#     for i in time:
#         if i == int(i):
#             fil[i/tstep] = True

#     return rf[fil]

# def CO2_rf(emission, years, tstep=0.01, kind='linear', emiss_type='sustained'):
#     """Transforms an array of CO2 emissions into radiative forcing with user-
#     defined time-step.

#     emission: an array of emissions, should be same size as years
#     years: an array of years at which the emissions take place
#     : time step to be used in the calculations
#     kind: the type of interpolation to use; can be linear or cubic
#     emiss_type: 'sustained' or 'pulse' - if 'pulse', then the emission values are
#     divided by . this allows a pulse of 1 kg in the first value of the array to
#     represent a full kg of emission, and 1 kg in all values associated with the first
#     year to also represent a full kg when 'sustained'.
#     """
# #emission is a series of emission numbers, years should match up with it
#     if min(years) > 0:
#         years = years - min(years)

#     if emiss_type == 'pulse':
#         emission /= tstep

#     end = max(years)
#     f = interp1d(years, emission, kind=kind)
#     time = np.linspace(years[0], end, end/tstep + 1)
#     inter_emissions = f(time)
#     atmos = np.resize(fftconvolve(CO2_AR5(time), inter_emissions), time.size) * tstep
#     rf = atmos * co2_re
#     fil = np.zeros_like(time, dtype=bool)
#     for i in time:
#         if i == int(i):
#             fil[i/tstep] = True

#     return rf[fil]


# ### Replaced

# def CO2_AR5(t):
#     return f0(t) + f1(t) + f2(t) + f3(t)

# def CH4_AR5(t):
#     return np.exp(-t/CH4tau)

# def N2O_AR5(t):
#     return np.exp(-t/CH4tau)

# def SF6_AR5(t):
#     return np.exp(-t/CH4tau)

# def AR5_GTP(t):
#     c1, c2, d1, d2 = 0.631, 0.429, 8.4, 409.5
#     return c1/d1*np.exp(-t/d1) + c2/d2*np.exp(-t/d2)

# def Alt_GTP(t):
#     c1, c2, d1, d2 = 0.43, 0.32, 2.57, 82.24
#     """ The response function for radiative forcing. Taken from Olivie and Peters (2013),
#     Table 4, using the CMIP5 data. This has a slightly lower climate response value than
#     Boucher (2008), which is used in AR5.

#     Convolve with radiative forcing to get temperature.
#     """
#     return c1/d1*np.exp(-t/d1) + c2/d2*np.exp(-t/d2)













# def CH4_rate(emission, years, tstep=0.01, kind='linear', emiss_type='sustained'):
#     """Transforms an array of methane emissions into radiative forcing with user-defined
#     time-step, accounting for climate-carbon feedbacks.

#     emission: an array of emissions, should be same size as years
#     years: an array of years at which the emissions take place
#     : time step to be used in the calculations
#     kind: the type of interpolation to use; can be linear or cubic
#     emiss_type: 'sustained' or 'pulse' - if 'pulse', then the emission values are
#     divided by . this allows a pulse of 1 kg in the first value of the array to
#     represent a full kg of emission, and 1 kg in all values associated with the first
#     year to also represent a full kg when 'sustained'.
#     """
#     gamma = (44.0/12.0) * 10**12

# #emission is a series of emission numbers, years should match up with it
#     if min(years) > 0:
#         years = years - min(years)

#     if emiss_type == 'pulse':
#         emission /= tstep

#     end = max(years)
#     fch4 = interp1d(years, emission, kind=kind)
#     time = np.linspace(years[0], end, end/ + 1)
#     ch4_inter_emissions = fch4(time)
#     ch4_atmos = np.resize(fftconvolve(CH4_AR5(time), ch4_inter_emissions),
#                           time.size) * tstep
#     co2 = np.resize(fftconvolve(ch42co2(time), ch4_inter_emissions),
#                     time.size) * tstep
#     co2_atmos = np.resize(fftconvolve(CO2_AR5(time), co2),
#                           time.size) * tstep
#     cc_co2 = CH4_cc_tempforrf(emission, years) * gamma
#     cc_co2_atmos = np.resize(fftconvolve(CO2_AR5(time), cc_co2),
#                           time.size) * tstep

#     rf = ch4_atmos * ch4_re + (co2_atmos +cc_co2_atmos) * co2_re
#     dx = np.gradient(time)
#     rate = np.gradient(rf, dx)
#     fil = np.zeros_like(time, dtype=bool)
#     for i in time:
#         if i == int(i):
#             fil[i/tstep] = True

#     return rate[fil]

# def CH4_crf(emission, years, tstep=0.01, kind='linear',
#              decay=True, emiss_type='sustained'):
#     """Transforms an array of methane emissions into radiative forcing with user-defined
#     time-step.

#     emission: an array of emissions, should be same size as years
#     years: an array of years at which the emissions take place
#     : time step to be used in the calculations
#     kind: the type of interpolation to use; can be linear or cubic
#     emiss_type: 'sustained' or 'pulse' - if 'pulse', then the emission values are
#     divided by . this allows a pulse of 1 kg in the first value of the array to
#     represent a full kg of emission, and 1 kg in all values associated with the first
#     year to also represent a full kg when 'sustained'.
#     """
# #emission is a series of emission numbers, years should match up with it
#     if min(years) > 0:
#         years = years - min(years)

#     if emiss_type == 'pulse':
#         emission /= tstep

#     end = max(years)
#     fch4 = interp1d(years, emission, kind=kind)
#     time = np.linspace(years[0], end, end/ + 1)
#     ch4_inter_emissions = fch4(time)
#     ch4_atmos = np.resize(fftconvolve(CH4_AR5(time), ch4_inter_emissions),
#                           time.size) * tstep
#     co2 = np.resize(fftconvolve(ch42co2(time), ch4_inter_emissions),
#                     time.size) * tstep
#     co2_atmos = np.resize(fftconvolve(CO2_AR5(time), co2),
#                           time.size) * tstep

#     if decay == True:
#          rf = ch4_atmos * ch4_re + co2_atmos * co2_re
#     else:
#         rf = ch4_atmos * ch4_re
#     crf = cumtrapz(rf, dx = tstep, initial = 0)
#     fil = np.zeros_like(time, dtype=bool)
#     for i in time:
#         if i == int(i):
#             fil[i/tstep] = True

#     return crf[fil]

# def CH4_crf_cc(emission, years, tstep=0.01, kind='linear',
#              decay=True, emiss_type='sustained'):
#     """Transforms an array of methane emissions into radiative forcing with user-defined
#     time-step.

#     emission: an array of emissions, should be same size as years
#     years: an array of years at which the emissions take place
#     : time step to be used in the calculations
#     kind: the type of interpolation to use; can be linear or cubic
#     emiss_type: 'sustained' or 'pulse' - if 'pulse', then the emission values are
#     divided by . this allows a pulse of 1 kg in the first value of the array to
#     represent a full kg of emission, and 1 kg in all values associated with the first
#     year to also represent a full kg when 'sustained'.
#     """
#     gamma = (44.0/12.0) * 10**12

# #emission is a series of emission numbers, years should match up with it
#     if min(years) > 0:
#         years = years - min(years)

#     if emiss_type == 'pulse':
#         emission /= tstep

#     end = max(years)
#     fch4 = interp1d(years, emission, kind=kind)
#     time = np.linspace(years[0], end, end/ + 1)
#     ch4_inter_emissions = fch4(time)
#     ch4_atmos = np.resize(fftconvolve(CH4_AR5(time), ch4_inter_emissions),
#                           time.size) * tstep
#     co2 = np.resize(fftconvolve(ch42co2(time), ch4_inter_emissions),
#                     time.size) * tstep
#     co2_atmos = np.resize(fftconvolve(CO2_AR5(time), co2),
#                           time.size) * tstep
#     cc_co2 = CH4_cc_tempforrf(emission, years) * gamma
#     cc_co2_atmos = np.resize(fftconvolve(CO2_AR5(time), cc_co2),
#                           time.size) * tstep

#     if decay == True:
#          rf = ch4_atmos * ch4_re + (co2_atmos +cc_co2_atmos) * co2_re
#     else:
#         rf = ch4_atmos * ch4_re + (cc_co2_atmos) * co2_re
#     crf = cumtrapz(rf, dx = tstep, initial = 0)
#     fil = np.zeros_like(time, dtype=bool)
#     for i in time:
#         if i == int(i):
#             fil[i/tstep] = True

#     return crf[fil]

# def CH4_temp(emission, years, tstep=0.01, kind='linear', source='AR5',
#              decay=True, emiss_type='sustained'):
#     """Transforms an array of methane emissions into temperature with user-defined
#     time-step. Default temperature IRF is from AR5, use 'Alt_low' or 'Alt_high'
#     for a sensitivity test.

#     emission: an array of emissions, should be same size as years
#     years: an array of years at which the emissions take place
#     : time step to be used in the calculations
#     kind: the type of interpolation to use; can be linear or cubic
#     source: the source of parameters for the temperature IRF. default is AR5,
#     'Alt', 'Alt_low', and 'Alt_high' are also options.
#     decay: a boolean variable for if methane decay to CO2 should be included
#     emiss_type: 'sustained' or 'pulse' - if 'pulse', then the emission values are
#     divided by . this allows a pulse of 1 kg in the first value of the array to
#     represent a full kg of emission, and 1 kg in all values associated with the first
#     year to also represent a full kg when 'sustained'.
#     """
# #emission is a series of emission numbers, years should match up with it
#     if min(years) > 0:
#         years = years - min(years)

#     if emiss_type == 'pulse':
#         emission /= tstep

#     end = max(years)
#     f = interp1d(years, emission, kind=kind)
#     time = np.linspace(years[0], end, end/ + 1)
#     ch4_inter_emissions = f(time)
#     ch4_atmos = np.resize(fftconvolve(CH4_AR5(time), ch4_inter_emissions),
#                           time.size) * tstep
#     co2 = np.resize(fftconvolve(ch42co2(time), ch4_inter_emissions),
#                     time.size) * tstep
#     co2_atmos = np.resize(fftconvolve(CO2_AR5(time), co2),
#                           time.size) * tstep
#     if decay == True:
#          rf = ch4_atmos * ch4_re + co2_atmos * co2_re
#     else:
#         rf = ch4_atmos * ch4_re
#     if source == 'AR5':
#         temp = np.resize(fftconvolve(AR5_GTP(time), rf), time.size) * tstep
#     elif source == 'Alt':
#         temp = np.resize(fftconvolve(Alt_GTP(time), rf), time.size) * tstep
#     elif source == 'Alt_low':
#         temp = np.resize(fftconvolve(Alt_low_GTP(time), rf), time.size) * tstep
#     elif source == 'Alt_high':
#         temp = np.resize(fftconvolve(Alt_high_GTP(time), rf), time.size) * tstep

#     fil = np.zeros_like(time, dtype=bool)
#     for i in time:
#         if i == int(i):
#             fil[i/tstep] = True

#     return temp[fil]

# def CH4_cc_tempforrf(emission, years, tstep=0.01, kind='linear', source='AR5',
#              decay=True, emiss_type='sustained'):
#     """Transforms an array of methane emissions into temperature with user-defined
#     time-step. Default temperature IRF is from AR5, use 'Alt_low' or 'Alt_high'
#     for a sensitivity test.

#     emission: an array of emissions, should be same size as years
#     years: an array of years at which the emissions take place
#     : time step to be used in the calculations
#     kind: the type of interpolation to use; can be linear or cubic
#     source: the source of parameters for the temperature IRF. default is AR5,
#     'Alt', 'Alt_low', and 'Alt_high' are also options.
#     decay: a boolean variable for if methane decay to CO2 should be included
#     emiss_type: 'sustained' or 'pulse' - if 'pulse', then the emission values are
#     divided by . this allows a pulse of 1 kg in the first value of the array to
#     represent a full kg of emission, and 1 kg in all values associated with the first
#     year to also represent a full kg when 'sustained'.
#     """
# #emission is a series of emission numbers, years should match up with it
#     if min(years) > 0:
#         years = years - min(years)

#     if emiss_type == 'pulse':
#         emission /= tstep

#     end = max(years)
#     f = interp1d(years, emission, kind=kind)
#     time = np.linspace(years[0], end, end/ + 1)
#     ch4_inter_emissions = f(time)
#     ch4_atmos = np.resize(fftconvolve(CH4_AR5(time), ch4_inter_emissions),
#                           time.size) * tstep
#     co2 = np.resize(fftconvolve(ch42co2(time), ch4_inter_emissions),
#                     time.size) * tstep
#     co2_atmos = np.resize(fftconvolve(CO2_AR5(time), co2),
#                           time.size) * tstep
#     if decay == True:
#          rf = ch4_atmos * ch4_re + co2_atmos * co2_re
#     else:
#         rf = ch4_atmos * ch4_re
#     if source == 'AR5':
#         temp = np.resize(fftconvolve(AR5_GTP(time), rf), time.size) * tstep
#     elif source == 'Alt':
#         temp = np.resize(fftconvolve(Alt_GTP(time), rf), time.size) * tstep
#     elif source == 'Alt_low':
#         temp = np.resize(fftconvolve(Alt_low_GTP(time), rf), time.size) * tstep
#     elif source == 'Alt_high':
#         temp = np.resize(fftconvolve(Alt_high_GTP(time), rf), time.size) * tstep

#     fil = np.zeros_like(time, dtype=bool)
#     for i in time:
#         if i == int(i):
#             fil[i/tstep] = True

#     return temp

# def CH4_temp_cc(emission, years, tstep=0.01, kind='linear', source='AR5',
#              decay=True, emiss_type='sustained'):
#     """Transforms an array of methane emissions into temperature with user-defined
#     time-step. Default temperature IRF is from AR5, use 'Alt_low' or 'Alt_high'
#     for a sensitivity test. Accounts for climate-carbon feedbacks.

#     emission: an array of emissions, should be same size as years
#     years: an array of years at which the emissions take place
#     : time step to be used in the calculations
#     kind: the type of interpolation to use; can be linear or cubic
#     source: the source of parameters for the temperature IRF. default is AR5,
#     'Alt', 'Alt_low', and 'Alt_high' are also options.
#     decay: a boolean variable for if methane decay to CO2 should be included
#     emiss_type: 'sustained' or 'pulse' - if 'pulse', then the emission values are
#     divided by . this allows a pulse of 1 kg in the first value of the array to
#     represent a full kg of emission, and 1 kg in all values associated with the first
#     year to also represent a full kg when 'sustained'.
#     """
#     gamma = (44.0/12.0) * 10**12

# #emission is a series of emission numbers, years should match up with it
#     if min(years) > 0:
#         years = years - min(years)

#     if emiss_type == 'pulse':
#         emission /= tstep

#     end = max(years)
#     f = interp1d(years, emission, kind=kind)
#     time = np.linspace(years[0], end, end/ + 1)
#     ch4_inter_emissions = f(time)
#     ch4_atmos = np.resize(fftconvolve(CH4_AR5(time), ch4_inter_emissions),
#                           time.size) * tstep
#     co2 = np.resize(fftconvolve(ch42co2(time), ch4_inter_emissions),
#                     time.size) * tstep
#     co2_atmos = np.resize(fftconvolve(CO2_AR5(time), co2),
#                           time.size) * tstep
#     cc_co2 = CH4_cc_tempforrf(emission, years) * gamma
#     cc_co2_atmos = np.resize(fftconvolve(CO2_AR5(time), cc_co2),
#                           time.size) * tstep

#     if decay == True:
#          rf = ch4_atmos * ch4_re + (co2_atmos + cc_co2_atmos) * co2_re
#     else:
#         rf = ch4_atmos * ch4_re + cc_co2_atmos * co2_re
#     if source == 'AR5':
#         temp = np.resize(fftconvolve(AR5_GTP(time), rf), time.size) * tstep
#     elif source == 'Alt':
#         temp = np.resize(fftconvolve(Alt_GTP(time), rf), time.size) * tstep
#     elif source == 'Alt_low':
#         temp = np.resize(fftconvolve(Alt_low_GTP(time), rf), time.size) * tstep
#     elif source == 'Alt_high':
#         temp = np.resize(fftconvolve(Alt_high_GTP(time), rf), time.size) * tstep

#     fil = np.zeros_like(time, dtype=bool)
#     for i in time:
#         if i == int(i):
#             fil[i/tstep] = True

#     return temp[fil]
