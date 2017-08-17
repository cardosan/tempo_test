# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from .dynamic_ia_methods import DynamicIAMethod, dynamic_methods
from bw2data import Method, methods, get_activity
import collections
import itertools
import numpy as np
import datetime
import os
import gzip
try:
    import cPickle as pickle
except ImportError:
    import pickle

data_point = collections.namedtuple('data_point', ['dt', 'flow', 'ds', 'amount'])
grouped_dp=collections.namedtuple('grouped_dp', ['dt', 'flow', 'amount']) #groups by flow and datetime

class EmptyTimeline(Exception):
    pass


class Timeline(object):
    """Sum and group elements over time.
    Timeline calculations produce a list of [(datetime, amount)] tuples."""

    def __init__(self, data=None):
        self.raw = data or []
        self.characterized = []
        self.dp_groups=[]

    def sort(self):
        """Sort the raw timeline data. Characterized data is already sorted."""
        self.raw.sort(key=lambda x: x.dt)

    def add(self, dt, flow, ds, amount):
        """Add a new flow from a dataset at a certain time."""
        self.raw.append(data_point(dt, flow, ds, amount))

    def flows(self):
        """Get set of flows in timeline"""
        return {pt.flow for pt in self.raw}

    def processes(self):
        """Get set of processes in timeline"""
        return {pt.ds for pt in self.raw}

    def timeline_for_flow(self, flow):
        """Create a new Timeline for a particular flow."""
        return Timeline([x for x in self.raw if x.flow == flow])

    def timeline_for_activity(self, activity):
        """Create a new Timeline for a particular activity."""
        return Timeline([x for x in self.raw if x.ds == activity])

    def total_flow_for_activity(self, flow, activity):
        """Return cumulative amount of the flow passed for the activity passed"""
        return sum([x.amount for x in self.raw if x.ds == activity and x.flow == flow])
        
    def total_amount_for_flow(self, flow):
        """Return cumulative amount of the flow passed"""
        return sum([x.amount for x in self.raw if x.flow == flow])

    def characterize_static(self, method, data=None, cumulative=True, stepped=False):
        """Characterize a Timeline object with a static impact assessment method.
        
        Args:
            * *method* (tuple): The static impact assessment method.
            * *data* (Timeline object; default=None): ....
            * *cumulative* (bool; default=True): when True return cumulative impact over time.
            * *stepped* (bool; default=True):...
        """
        if method not in methods:
            raise ValueError(u"LCIA static method %s not found" % method)
        if data is None and not self.raw:
            raise EmptyTimeline("No data to characterize")
        self.method_data = {x[0]: x[1] for x in Method(method).load()}    
        self.dp_groups=self._groupby_sum_by_flow(self.raw if data is None else data)
        
        self.characterized = [
                    grouped_dp(nt.dt, nt.flow, nt.amount * self.method_data.get(nt.flow, 0))
                    # grouped_dp(nt.dt, nt.flow, nt.amount * method_data.get(nt.flow, 0))
                    for nt in self.dp_groups
                ]
        self.characterized.sort(key=lambda x: x.dt)
        return self._summer(self.characterized, cumulative, stepped)


    def characterize_dynamic(self, method, data=None, cumulative=True, stepped=False):
        """Characterize a Timeline object with a dynamic impact assessment method.
        Return a nested list of year and impact
        Args:
            * *method* (tuple): The dynamic impact assessment method.
            * *data* (Timeline object; default=None): ....
            * *cumulative* (bool; default=True): when True return cumulative impact over time.
            * *stepped* (bool; default=True):...
        """
        if method not in dynamic_methods:
            raise ValueError(u"LCIA dynamic method %s not found" % method)
        if data is None and not self.raw:
            raise EmptyTimeline("No data to characterize")
        method = DynamicIAMethod(method)
        self.method_data = method.load()
        method_functions = method.create_functions(self.method_data)

        self.characterized = []
        self.dp_groups=self._groupby_sum_by_flow(self.raw if data is None else data)

        for obj in self.dp_groups:
            # if obj.flow in method_functions:
            self.characterized.extend([
                grouped_dp(
                    item.dt,
                    obj.flow,
                    item.amount * obj.amount
                ) for item in method_functions[obj.flow](obj.dt)
            ])
            # else:
                # continue
                #GIU: I would skipe this,we save time plus memory, in groupby_sum_by_flow already skips datapoint not in method_data
                #also more consistent in my opinion (the impact is not 0 but is simply not measurable)
                
                # self.characterized.append(grouped_dp(
                    # obj.dt,
                    # obj.flow,
                    # obj.amount * method_data.get(obj.flow, 0)
                # ))
                
        self.characterized.sort(key=lambda x: x.dt)

        return self._summer(self.characterized, cumulative, stepped)
        
    def characterize_static_by_process(self, method, characterize_static_kwargs={}):
        """Characterize a Timeline object with a static impact assessment method separately by process
        Return a dictionary with process name as key and a nested list of year and impact as value
        Args:
            * *method* (tuple): The static impact assessment method.
            * *characterize_static_kwargs* (dictionary; default={}): optional arguments (passed as key=argument name, value= argument value) passed to the called function `characterize_static` (e.g.'cumulative':True). See `characterize_static` for the possible arguments to pass
        """
        #skip None that is returned from DynamicLCA when the overlall LCA impact of the demand is==0
        return {get_activity(process)['name']:[self.timeline_for_activity(process).characterize_static(method,**characterize_static_kwargs)] for process in self.processes() if process is not None} 
        
    def characterize_dynamic_by_process(self, method, characterize_dynamic_kwargs={}):
        """Characterize a Timeline object with a static impact assessment method separately by process
        Return a dictionary with process name as key and a nested list of year and impact as value
        Args:
            * *method* (tuple): The dynamic impact assessment method.
            * *characterize_dynamic_kwargs* (dictionary; default={}): optional arguments (passed as key=argument name, value= argument value) passed to the called function `characterize_dynamic` (e.g. 'cumulative':True). See `characterize_dynamic` for the possible arguments to pass
        """
        
        #skip None that is returned from DynamicLCA when the overla LCA impact of the demand is==0
        return {get_activity(process)['name']:[self.timeline_for_activity(process).characterize_dynamic(method,**characterize_dynamic_kwargs)] for process in self.processes() if process is not None} 

    def characterize_static_by_flow(self, method, characterize_static_kwargs={}):
        """Characterize a Timeline object with a static impact assessment method separately by flow
        Return a dictionary with flow name as key and a nested list of year and impact as value
        Args:
            * *method* (tuple): The static impact assessment method.
            * *characterize_static_kwargs* (dictionary; default={}): optional arguments (passed as key=argument name, value= argument value) passed to the called function `characterize_static` (e.g.'cumulative':True). See `characterize_static` for the possible arguments to pass
        """
        #skip None that is return from DynamicLCA when the overla LCA impact of the demand is==0
        return {get_activity(flow)['name']:[self.timeline_for_flow(flow).characterize_static(method,**characterize_static_kwargs)] for flow in self.flows() if flow is not None} 
        
    def characterize_dynamic_by_flow(self, method, characterize_dynamic_kwargs={}):
        """Characterize a Timeline object with a static impact assessment method separately by flow
        Return a dictionary with flow name as key and a nested list of year and impact as value
        Args:
            * *method* (tuple): The dynamic impact assessment method.
            * *characterize_dynamic_kwargs* (dictionary; default={}): optional arguments (passed as key=argument name, value= argument value) passed to the called function `characterize_dynamic` (e.g. 'cumulative':True). See `characterize_dynamic` for the possible arguments to pass
        """
        
        #skip None that is return from DynamicLCA when the overla LCA impact of the demand is==0
        return {get_activity(flow)['name']:[self.timeline_for_flow(flow).characterize_dynamic(method,**characterize_dynamic_kwargs)] for flow in self.flows() if flow is not None} 
        
##############
#INTERNAL USE#
##############

    #~1.5 times faster than using Counter() and ~3 than using groupby that need sorting before but still not great (e.g. pandas ~2 times faster, check if possible to use numpy_groupies somehow )
    #CHECK WHAT IS THIS APPROACH AND IF APPLICABLE http://stackoverflow.com/a/18066479/4929813    
    def _groupby_sum_by_flow(self,iterable):
        """group and sum datapoint by flow, it makes much faster characterization"""
        c = collections.defaultdict(int)
        for dp in iterable:
            c[dp.dt,dp.flow] += dp.amount
        return[grouped_dp(dt_fl[0],dt_fl[1],amount) for dt_fl,amount in c.items() 
                        if dt_fl[1] in self.method_data and amount != 0 ] # skip datapoints with flows without dyn_met and 0 bio_flows  

    def _summer(self, iterable, cumulative, stepped=False):
        if cumulative:
            data =  self._cumsum_amount_over_time(iterable)
        else:
            data =  self._sum_amount_over_time(iterable)
        if stepped:
            return self._stepper(data)
        else:
            return self._to_year([x[0] for x in data]), [x[1] for x in data]

    def _to_year(self, lst):
        """convert datetime to fractional years"""
        to_yr = lambda x: x.year + x.month / 12. + x.day / 365.24
        return [to_yr(obj) for obj in lst]

    def _stepper(self, iterable):
        xs, ys = zip(*iterable)
        xs = list(itertools.chain(*zip(xs, xs)))
        ys = [0] + list(itertools.chain(*zip(ys, ys)))[:-1]
        return self._to_year(xs), ys

    def _sum_amount_over_time(self, iterable):
        """groupby date and sum amount"""
        #GIU: Think here, wiith different data structure we could use consolidate maybe
        return sorted([
            (dt, sum([x.amount for x in res]))
            for dt, res in
            itertools.groupby(iterable, key=lambda x: x.dt.date())
            # itertools.groupby(iterable, key=lambda x: x.dt.astype(object).date()) # to work with numpy datetime. leave for now

        ])

    def _cumsum_amount_over_time(self, iterable):
        """"""
        data = self._sum_amount_over_time(iterable)
        values = [float(x) for x in np.cumsum(np.array([x[1] for x in data]))]
        return list(zip([x[0] for x in data], values))
