# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from bw2speedups import consolidate
from future.utils import python_2_unicode_compatible
import numpy as np
import datetime

@python_2_unicode_compatible
class TemporalDistribution(object):
    """A container for a series of values spread over time.
Args:
    * *times* (ndarray): 1D array containg temporal info of `values` with type `timedelta64` or `datetime64` .
    * *values* (ndarray): 1D array containg values with type `float` 
    
    Times and values must have same lenght and element of `values` must correspond to the element of `times`
    with the same index.
    """
    def __init__(self, times, values):
        # #GIU: check if using non numpy datetime and timedelta does not slow down too much        
        try:
            assert isinstance(times, np.ndarray)
            assert isinstance(values, np.ndarray)
            assert times.shape == values.shape
            #nasty but.... http://stackoverflow.com/a/23069878/4929813
            assert 'timedelta64' in str(times.dtype) or \
                   'datetime64' in str(times.dtype) or \
                    isinstance(times[0], datetime.datetime),'times must be of type numpy datetime64 or timedelta64'
            # Type conversion needed for consolidate cython function
            values = values.astype(np.float64)
        except AssertionError:
            raise ValueError(u"Invalid input values")
            
        #use always seconds as resolution (maybe not necessary?)
        if 'datetime64' in str(times.dtype):
            self.times = times.astype("datetime64[s]")
        elif 'timedelta64' in str(times.dtype):
            self.times = times.astype("timedelta64[s]")
        else:
            self.times=times #for datetime
        self.values = values
        
        
    def __getitem__(self, val):
        return TemporalDistribution(np.array(self.times[val]), np.array(self.values[val]))

    def __mul__(self, other):
        if isinstance(other, TemporalDistribution):            
            assert 'timedelta64' in str(self.times.dtype) and 'timedelta64' in str(other.times.dtype),"Multiplication between two TemporalDistribution possible only for timedelta"
            times = (self.times.reshape((-1, 1)) +
                     other.times.reshape((1, -1))).ravel()
            values = (self.values.reshape((-1, 1)) *
                      other.values.reshape((1, -1))).ravel()
            #use array view in consolidate, see http://stackoverflow.com/a/33528073/4929813
            #need to reconvert times.view to timedelta64[s]
            t_view,v=consolidate(times.view('int64'), values) 
            return TemporalDistribution(t_view.astype('timedelta64[s]'),v)
        else:
            try:
                return TemporalDistribution(self.times, self.values * float(other))
            except:
                raise ValueError(u"Can't multiply TemporalDistribution and %s" \
                                 % type(other))

    def __div__(self, other):
        # Python 2
        try:
            other = float(other)
        except:
            raise ValueError(
                u"Can only divide a TemporalDistribution by a number"
            )
        return TemporalDistribution(self.times, self.values / other)

    def __truediv__(self, other):
        # Python 3
        return self.__div__(other)

    def __lt__(self, other):
        # Comparisons in Python 3
        if not isinstance(other, TemporalDistribution):
            return False
        return self.values.sum() < other.values.sum()

    def __cmp__(self, other):
        # Comparisons in Python 2
        if not isinstance(other, TemporalDistribution):
            return -1
        return cmp(self.values.sum(), other.values.sum())

    def __add__(self, other):
        if isinstance(other, TemporalDistribution):
            assert 'timedelta64' in str(self.times.dtype),"sum between two TemporalDistribution possible only for timedelta"
            times = np.hstack((self.times, other.times))
            values = np.hstack((self.values, other.values))
            #same as in __mul__
            t_view,v=consolidate(times.view('int64'), values) 
            return TemporalDistribution(t_view.astype('timedelta64[s]'),v)

        else:
            try:
                return TemporalDistribution(self.times, self.values + float(other))
            except:
                raise ValueError(u"Can't add TemporalDistribution and %s" \
                                 % type(other))        
    def __iter__(self):
        for index in range(self.times.shape[0]):
            yield (self.times[index], float(self.values[index]))

    @property
    def total(self):
        return float(self.values.sum())

    def __str__(self):
        return "TemporalDistribution instance with %s values and total: %.4g" % (
            len(self.values), self.total)

    def __repr__(self):
        return "TemporalDistribution instance with %s values (total: %.4g, min: %.4g, max: %.4g" % (
            len(self.values), self.total, self.values.min(), self.values.max())

    def cumulative(self):
        """Return new temporal distribution with cumulative values"""
        return TemporalDistribution(self.times, np.cumsum(self.values))
        
    def datetime_to_timedelta(self, dt):
        """Convert TD.times of type datetime64 to timedelta64 based on the datetime64 passed
        """
        assert 'datetime64' in str(self.times.dtype),'TemporalDistribution.times must be numpy.datetime64'
        assert isinstance(dt,np.datetime64),'datetime must be numpy.datetime64'
        return  TemporalDistribution(self.times - dt, self.values)
        
    def timedelta_to_datetime(self, dt):
        """Convert TD.times of type timedelta64 to datetime.datetime based on the datetime64 passed
        """
        #converted to datetime.datetime cause timeline._groupby_sum_by_flow is ~5 slower when using np.datetime64
        #while the conversion here to datatime.datetime is almost the same performance wise 
        assert 'timedelta64' in str(self.times.dtype),'TemporalDistribution.times must be numpy.datetime64'
        assert isinstance(dt,np.datetime64),'datetime must be numpy.datetime64'
        return  TemporalDistribution((self.times + dt).astype(datetime.datetime) , self.values)
