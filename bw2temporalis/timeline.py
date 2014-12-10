from .dynamic_ia_methods import DynamicIAMethod, dynamic_methods
from bw2data import Method, methods
import collections
import itertools
import numpy as np


data_point = collections.namedtuple('data_point', ['dt', 'flow', 'ds', 'amount'])


class Timeline(object):
    """Sum and group elements over time.

    Timeline calculations produce a list of [(datetime, amount)] tuples."""

    def __init__(self, data=None):
        self.raw = data or []
        self.characterized = []

    def add(self, dt, flow, ds, amount):
        """Add a new flow from a dataset at a certain time."""
        self.raw.append(data_point(dt, flow, ds, amount))

    def timeline_for_flow(self, flow):
        """Create a new Timeline for a particular flow."""
        return Timeline([x for x in self.raw if x.flow == flow])

    def timeline_for_activity(self, activity):
        """Create a new Timeline for a particular activity."""
        return Timeline([x for x in self.raw if x.ds == activity])

    def characterize_static(self, method, data=None, cumulative=True, stepped=False):
        if method not in methods:
            raise ValueError(u"LCIA static method %s not found" % unicode(method))
        method_data = {x[0]: x[1] for x in Method(method).load()}
        self.characterized = [
            data_point(nt.dt, nt.flow, nt.ds, nt.amount * method_data.get(nt.flow, 0))
            for nt in (data if data is not None else self.raw)
        ]
        self.characterized.sort(key=lambda x: x.dt)
        return self._summer(self.characterized, cumulative, stepped)

    def characterize_dynamic(self, method, data=None, cumulative=True, stepped=False):
        if method not in dynamic_methods:
            raise ValueError(u"LCIA dynamic method %s not found" % unicode(method))
        method = DynamicIAMethod(method)
        method_data = method.load()
        method_functions = method.create_functions(method_data)
        self.characterized = []

        for obj in (data if data is not None else self.raw):
            if obj.flow in method_functions:
                self.characterized.extend([
                    data_point(
                        item.dt,
                        obj.flow,
                        obj.ds,
                        item.amount * obj.amount
                    ) for item in method_functions[obj.flow](obj.dt)
                ])
            else:
                self.characterized.append(data_point(
                    obj.dt,
                    obj.flow,
                    obj.ds,
                    obj.amount * method_data.get(obj.flow, 0)
                ))

        self.characterized.sort(key=lambda x: x.dt)
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
