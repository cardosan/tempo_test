from bw2speedups import consolidate


class TemporalDistribution(object):
    def __init__(self, times, values):
        self.times = times
        self.values = values

    def convolve(self, other):
        if not isinstance(other, TemporalDistribution):
            raise ValueError(u"Can only convolve other TemporalDistribution objects")
            times = (self.times.reshape((-1, 1)) +
                     other.times.reshape((1, -1))).ravel()
            values = (self.values.reshape((-1, 1)) +
                      other.values.reshape((1, -1))).ravel()
            return TemporalDistribution(*consolidate(times, values))
