from bw2speedups import consolidate
import numpy as np


class TemporalDistribution(object):
    """An container for a series of values spread over time."""
    def __init__(self, times, values):
        try:
            assert isinstance(times, np.ndarray)
            assert isinstance(values, np.ndarray)
            assert times.shape == values.shape
            # Type conversion needed for consolidate cython function
            times = times.astype(np.float64)
            values = values.astype(np.float64)
        except AssertionError:
            raise ValueError(u"Invalid input values")
        self.times = times
        self.values = values

    def __mul__(self, other):
        if isinstance(other, TemporalDistribution):
            times = (self.times.reshape((-1, 1)) +
                     other.times.reshape((1, -1))).ravel()
            values = (self.values.reshape((-1, 1)) *
                      other.values.reshape((1, -1))).ravel()
            return TemporalDistribution(*consolidate(times, values))
        else:
            try:
                return TemporalDistribution(self.times, self.values * float(other))
            except:
                raise ValueError(u"Can't multiply TemporalDistribution and %s" \
                                 % type(other))

    def __div__(self, other):
        try:
            other = float(other)
        except:
            raise ValueError(
                u"Can only divide a TemporalDistribution by a number"
            )
        return TemporalDistribution(self.times, self.values / other)

    def __add__(self, other):
        if isinstance(other, TemporalDistribution):
            times = np.hstack((self.times, other.times))
            values = np.hstack((self.values, other.values))
            return TemporalDistribution(*consolidate(times, values))
        else:
            try:
                return TemporalDistribution(self.times, self.values + float(other))
            except:
                raise ValueError(u"Can't add TemporalDistribution and %s" \
                                 % type(other))

    def __iter__(self):
        for index in xrange(self.times.shape[0]):
            yield (float(self.times[index]), float(self.values[index]))

    @property
    def total(self):
        return float(self.values.sum())

    def __unicode__(self):
        return u"TemporalDistribution instance with %s values and total: %.4g" % (
            len(self.values), self.total)

    def __repr__(self):
        return u"TemporalDistribution instance with %s values (total: %.4g, min: %.4g, max: %.4g" % (
            len(self.values), self.total, self.values.min(), self.values.max())

    def __str__(self):
        return unicode(self).encode('utf-8')
