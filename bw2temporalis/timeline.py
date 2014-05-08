import itertools
import collections
import numpy as np

data_point = collections.namedtuple('data_point', ['dt', 'flow', 'ds', 'amount'])


class Timeline(object):
    """Sum and group elements over time.

    Timeline calculations produce a list of [(datetime, amount)] tuples."""

    def __init__(self):
        self.raw = []
        self.characterized = []

    def add(self, dt, flow, ds, amount):
        """Add a new flow from a dataset at a certain time."""
        self.raw.append(data_point(dt, flow, ds, amount))

    def timeline_for_flow(self, flow, data=None, cumulative=True):
        """Create a timeline for a particular flow."""
        data = data if data is not None else self.raw
        data.sort(key=lambda x: x.dt)
        return self._summer(
            itertools.ifilter(lambda x: x.flow == flow, data),
            cumulative
        )

    def characterize_static(self, method_dict, data=None, cumulative=True, stepped=False):
        """``method_dict`` should be a dictionary of CFs: ``{flow: cf}``"""
        self.characterized = [
            data_point(nt.dt, nt.flow, nt.ds, nt.amount * method_dict.get(nt.flow, 0))
            for nt in sorted(
                data if data is not None else self.raw,
                key=lambda x: x.dt
            )
        ]
        return self._summer(self.characterized, cumulative, stepped)

    def characterize_dynamic(self, method_dict, data=None, cumulative=True, stepped=False):
        """``method_dict`` should be a dictionary of CFs: ``{flow: cf_function(datetime)}``"""
        self.characterized = [
            data_point(nt.dt, nt.flow, nt.ds, nt.amount *
                       method_dict.get(nt.flow, lambda x: 0)(nt.dt))
            for nt in sorted(
                data if data is not None else self.raw,
                key=lambda x: x.dt
            )
        ]
        return self._summer(self.characterized, cumulative, stepped)

    def _summer(self, iterable, cumulative, stepped=False):
        if cumulative:
            data =  self._cumsum_amount_over_time(iterable)
        else:
            data =  self._sum_amount_over_time(iterable)
        if stepped:
            return self._stepper(data)
        else:
            return data

    def _stepper(self, iterable):
        xs, ys = zip(*iterable)
        xs = list(itertools.chain(*zip(xs, xs)))
        ys = [0] + list(itertools.chain(*zip(ys, ys)))[:-1]
        return xs, ys

    def _sum_amount_over_time(self, iterable):
        return sorted([
            (dt, sum([x.amount for x in res]))
            for dt, res in
            itertools.groupby(iterable, key=lambda x: x.dt)
        ])

    def _cumsum_amount_over_time(self, iterable):
        data = self._sum_amount_over_time(iterable)
        values = [float(x) for x in np.cumsum(np.array([x[1] for x in data]))]
        return zip([x[0] for x in data], values)
