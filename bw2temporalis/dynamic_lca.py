# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from .temporal_distribution import TemporalDistribution
from .timeline import Timeline
from bw2calc import LCA
from bw2data import Database, get_activity, databases
from bw2data.logs import get_logger
from heapq import heappush, heappop
import numpy as np
import pprint
import warnings

#########
# import collections

class FakeLog(object):
    """Like a log object, but does nothing"""
    def fake_function(cls, *args, **kwargs):
        return

    def __getattr__(self, attr):
        return self.fake_function


class DynamicLCA(object):
    """Calculate a dynamic LCA, where processes, emissions, and CFs can vary throughout time.If an already (statically) characterized LCA object is passed calculate its dynamic LCA (useful when doing several dynamic LCA for same database but different the FUs)

Args:
    * *demand* (dict): The functional unit. Same format as in LCA class.
    * *worst_case_method* (tuple): LCIA method. Same format as in LCA class.
    * *cutoff* (float, default=0.005): Cutoff criteria to stop LCA calculations. Relative score of total, i.e. 0.005 will cutoff if a dataset has a score less than 0.5 percent of the total.
    * *max_calc_number* (int, default=10000): Maximum number of LCA calculations to perform.
    * *now* (datetime, default=np.datetime64('now')): `datetime` of the year zero (i.e. the one of the functional unit). 
    * *log* (int, default=False): If True to make log file
    * *lca_object* (LCA object,default=None): do dynamic LCA for the object passed (must have "characterized_inventory" i.e. LCA_object.lcia() has been called)
    """
    def __init__(self, demand, worst_case_method, now=None, max_calc_number=1e4, cutoff=0.001, log=False, lca_object=None):
        self.demand = demand
        self.worst_case_method = worst_case_method
        self.now=np.datetime64('now', dtype="datetime64[s]") if now is None else np.datetime64(now).astype("datetime64[s]")
        self.max_calc_number = max_calc_number
        self.cutoff_value = cutoff
        self.log = get_logger("dynamic-lca.log") if log else FakeLog()
        self.lca_object=lca_object
        
        #return static db and create set where will be added nodes as traversed
        all_databases = set.union(*[Database(key[0]).find_graph_dependents() for key in self.demand])
        self.static_databases = {name for name in all_databases if databases[name].get('static')}
        self.nodes=set()
        self.edges=[]
        
        #########
        #to test total for processes
        # self.test=collections.defaultdict(int)
        ########
        
        
###########
#Traversal#
###########

    def calculate(self):
        """Calculate"""
        self.timeline = Timeline()
        self.heap = [] #heap with dynamic exchanges to loop over (impact,dataset,datetime, TemporalDistribution)
        self.calc_number = 0
        
        #run worst case LCA if lca_object not passed else redo for demand and worst_case method if  and 
        if self.lca_object:
            _redo_lcia(self, self.lca_object, self.demand,self.worst_case_method)
        else:
            self.lca = LCA(self.demand,self.worst_case_method)
            self.lca.lci()
            self.lca.lcia()
        
        #reverse matrix and calculate cutoff
        self.reverse_activity_dict, _, self.reverse_bio_dict = self.lca.reverse_dict()        
        self.cutoff = abs(self.lca.score) * self.cutoff_value
                
        #logs
        self.log.info("Starting dynamic LCA")
        self.log.info("Demand: %s" % self.demand)
        self.log.info("Worst case method: %s" % str(self.worst_case_method))
        self.log.info("Start datetime: %s" % self.now)
        self.log.info("Maximum calculations: %i" % self.max_calc_number)
        self.log.info("Worst case LCA score: %.4g." % self.lca.score)
        self.log.info("Cutoff value (fraction): %.4g." % self.cutoff_value)
        self.log.info("Cutoff score: %.4g." % self.cutoff)
        # self.log.debug("NODES: " + pprint.pformat(self.gt_nodes))
        # self.log.debug("EDGES: " + pprint.pformat(self.gt_edges))


        # Initialize heap
        heappush(
            self.heap,
            (
                None,
                "Functional unit", 
                self.now,
                TemporalDistribution(
                    np.array([0,],dtype='timedelta64[s]'), # need int
                    np.array((1.,)).astype(float)                     
                )
            )
        )

        while self.heap:
            if self.calc_number >= self.max_calc_number:
                warnings.warn("Stopping traversal due to calculation count.")
                break
            self._iterate()
        
        self.log.debug("NODES: " + pprint.pformat(self.nodes))
        # self.log.debug("EDGES: " + pprint.pformat(self.gt_edges))    
        
        return self.timeline
        
    def _iterate(self):
        """Iterate over the datasets starting from the FU"""
        # Ignore the calculated impact
        # `ds` is the dataset key
        # `dt` is the datetime; GIU: we can also avoid this and use self.now
        # `td` is a TemporalDistribution instance, which gives
        # how much of the dataset is used over time at
        # this point in the graph traversal
        _, ds, dt, td = heappop(self.heap)  # Don't care about impact
        
        
        # self.test[ds] += td.total#*sig /self.scale_value
        
        self.scale_value = self._get_scale_value(ds)
        
        if self.log:
            self.log.info("._iterate(): %s, %s, %s" % (ds, dt, td))
            
        #add bio flows (both dynamic and static)
        self._add_biosphere_flows(ds, td)
    
        #deal with functional unit
        if ds=="Functional unit":
            dyn_edges={}
            for key, value in self.demand.items():
                dyn_edges[key] = \
                    TemporalDistribution(
                        np.array([0,],dtype='timedelta64[s]'), # need int
                        np.array((value,)).astype(float)
                )
                new_td=self._calculate_new_td(dyn_edges[key],td) 
                # Calculate lca and discard if node impact is lower than cutoff
                if self._discard_node(
                        key,
                        new_td.total):
                    continue
                #else add to the heap the ds of this exchange with the new TD
                heappush(self.heap, (
                    abs(1 / self.lca.score),
                    key,
                    dt,
                    new_td
                ))
            self.calc_number += 1
            
        #for all the other datasets
        else:
            node=get_activity(ds)
            #skip node if a loop or if part of a static db
            if ds in self.nodes or node['database'] in self.static_databases:
                return
            #add to set of nodes
            self.nodes.add(ds)
            #dict with all edges of this node
            dyn_edges={}
            #loop dynamic_technosphere edges for node
            for exc in node.exchanges():
                #deal with technophsere and substitution exchanges
                if exc.get("type") in ["technosphere",'substitution']:
                    if self.log:
                        self.log.info("._iterate:edge: " + pprint.pformat(exc))
                    #Have to be careful here, because can have
                    #multiple exchanges with same input/output
                    #Sum up multiple edges with same input, if present
                    dyn_edges[exc['input']] = (
                    self._get_temporal_distribution(exc) +
                    dyn_edges.get(exc['input'], 0))
                    
                #deal with coproducts
                if exc.get('type')=='production' and exc.get('input')!=ds:
                    if self.log:
                        self.log.info("._iterate:edge: " + pprint.pformat(exc))
                    #Have to be careful here, because can have
                    #multiple exchanges with same input/output
                    #Sum up multiple edges with same input, if present
                    dyn_edges[exc['input']] = (
                    self._get_temporal_distribution(exc) +
                    dyn_edges.get(exc['input'], 0))
            
            #GIU: test if it is necessary all this or just loop all of them
            for edge,edge_td in dyn_edges.items():
                #Recalculate edge TD convoluting its TD with TD of the node consuming it (ds)
                #return a new_td with timedelta as times
                new_td=self._calculate_new_td(edge_td,td)
                
                # print(self.scale_value)#edge,new_td.total,new_td.total/self.scale_value,get_activity(edge).get('type'))
                # self.test[edge] += new_td.total#*sig /self.scale_value

                # Calculate lca and discard if node impact is lower than cutoff
                if self._discard_node(
                        edge,
                        new_td.total):
                    continue
                    
            # #to test total for processes
            # if ds!="Functional unit":
                # print(ds,get_activity(ds).get('type'))
                # sig = -1 if get_activity(ds).get('type') in ['production','substitution'] else 1
                # self.test[ds] += td.total*sig /self.scale_value
            
                #else add to the heap the ds of this exchange with the new TD
                heappush(self.heap, (
                    abs(1 / self.lca.score), # abs(1 / edge['impact'])
                    edge,
                    dt,
                    new_td
                ))
            self.calc_number += 1

    def _add_biosphere_flows(self, ds, tech_td):
        """add temporally distributed biosphere exchanges for this ds to timeline.raw both if ds is static or dynamic"""
        if ds == "Functional unit":
            return
        data = get_activity(ds)
        
        #add biosphere flow for process passed
        #check if new bw2 will need changes cause will differentiate import of products and activity (i.e. process)
        if not data.get('type', 'process') == "process":
            return
            
        #Add cumulated inventory for static database (to make faster calc) and loops (to avoid infinite loops)
        if data['database'] in self.static_databases or ds in self.nodes:
            self.lca.redo_lci({data: 1})
            inventory_vector = np.array(self.lca.inventory.sum(axis=1)).ravel()
            for index, amount in enumerate(inventory_vector):
                if not amount or amount == 0 : #GIU: we can skip also 0 amounts that sometimes occurs right?
                    continue
                flow = self.reverse_bio_dict[index]
                #spread, convert to datetime and append to timeline.raw
                dt_bio=self._calculate_bio_td_datetime(amount,tech_td)
                for bio_dt, bio_amount_scaled in dt_bio:
                    #TODO: best to use a better container for timeline.
                    #maybe defaultdict with namedtuple as key to group amount when added 
                    #fastest, see among others here https://gist.github.com/dpifke/2244911 (I also tested)
                    if bio_amount_scaled !=0:
                        self.timeline.add(bio_dt, flow, ds,bio_amount_scaled)
                # self.c[flow, ds] = dt_bio+self.c.get((flow, ds),0) #test for using TD

            return   
    
        #dynamic database
        for exc in data.exchanges():
            if not exc.get("type") == "biosphere":
                continue
            #get TD of bio exc, spread, convert to datetime and append to timeline.raw
            bio_td = self._get_temporal_distribution(exc)
            td_bio_new=self._calculate_bio_td_datetime(bio_td,tech_td)
            for bio_dt, bio_amount_scaled in td_bio_new:
                if bio_amount_scaled !=0:
                    self.timeline.add(bio_dt, exc['input'], ds,bio_amount_scaled)
            # self.c[exc['input'], ds] = td_bio_new+self.c.get((exc['input'], ds),0)  #test for using TD    
                    
    def _calculate_bio_td_datetime(self,bio_flows,td_tech):
        """Recalculate bio, both if datetime or timedelta, and add to timedelta.
        td_tech is always timedelta64, bio_flows can be datetime64 or float for static db"""
        #dynamic db with dt for bio_flows, multiply by node total
        if isinstance(bio_flows,TemporalDistribution) and 'datetime64' in str(bio_flows.times.dtype):
            return ( bio_flows * td_tech.total ) / self.scale_value
        #both static db and dynamic with timedelta for bio_flows
        bio_td_delta = (td_tech * bio_flows) / self.scale_value
        return bio_td_delta.timedelta_to_datetime(self.now)

    def _calculate_new_td(self,edge_td,node_td):
        """Recalculate edge both if datetime or timedelta, return always timedelta.
        node_td is always timedelta64, edge_td can be datetime"""
        if 'datetime64' in str(edge_td.times.dtype):
            #multiply by node.total and convert to timedelta
            new_td=(edge_td * node_td.total) / self.scale_value
            return new_td.datetime_to_timedelta(self.now)
        #else just convolute 
        return (node_td * edge_td) / self.scale_value
        
################
#Data retrieval#
################


    def _get_temporal_distribution(self, exc):
        """get 'temporal distribution'and change sing in case of production or substitution exchange"""
        # sign = 1 if exc.get('type') != 'production' else -1
        #deal with ds of type production and substititution
        sign = -1 if exc.get('type') in ['production','substitution'] else 1
        
        td=exc.get('temporal distribution', TemporalDistribution(
                np.array([0,], dtype='timedelta64[s]'), # need int
                np.array([exc['amount'],]).astype(float)        )
                   )
        if not isinstance(td,TemporalDistribution):
            # try:
                #convert old format, not for fractional years
            if any(isinstance(t_v, tuple) and len(t_v)==2 and isinstance(t_v[0], int ) for t_v in td):
                    array = np.array(exc[u'temporal distribution'])
                    td=TemporalDistribution(array[:, 0].astype('timedelta64[Y]'), array[:, 1]) 
                    warnings.warn("The old format for `temporal distribution` is deprecated, now must be a `TemporalDistribution` object instead of a nested list of tuples. The applied convertion might be incorrect in the exchange from {} to {}".format(exc['input'],exc['output']),DeprecationWarning)
            # except:
            else:
                raise ValueError("incorrect data format for temporal distribution` from: {} to {}".format(exc['input'],exc['output']))
        if not np.isclose(td.total,exc['amount']):
            raise ValueError("Unbalanced exchanges from {} to {}. Make sure that total of `temporal distribution` is the same of `amount`".format(exc['input'],exc['output']))           
        return td* sign

    def _discard_node(self, node, amount):
        """Calculate lca for {node, amount} passed return True if lca.score lower than cutoff"""
        self.lca.redo_lcia({node: amount})
        discard = abs(self.lca.score) < self.cutoff
        if discard:
            self.log.info(u"Discarding node: %s of %s (score %.4g)" % (
                          amount, node, self.lca.score)
                          )
        return discard

    def _get_scale_value(self, ds):
        """Get production amount (diagonal in matrix A) for the dataset (ds) passed.
        Normally scale_value is 1 but in the case of `non-unitary producitons <https://chris.mutel.org/non-unitary.html>`_ """
        # Each activity must produce its own reference product, but amount
        # can vary, or even be negative.
        # TODO: Do we need to look up the reference product?
        # It is not necessarily the same as the activity,
        # but maybe this breaks many things in the graph traversal
        if ds != "Functional unit":
            scale_value=float(self.lca.technosphere_matrix[
                self.lca.product_dict[ds],
                self.lca.activity_dict[ds]
            ])
            if scale_value == 0:
                raise ValueError(u"Can't rescale activities that produce "
                                 u"zero reference product")
            return scale_value
            
        else:
            return 1

    def _redo_lcia(self, lca_obj, demand, method):
        """
Redo LCA for the same inventory and different method and FU using redo_lcia().Decompose technosphere if it was not factorized in the LCA object passed. Useful when redoing many dynamic LCA for same database
Args:
    * *demand* (dict): The functional unit. Same format as in LCA class.
    * *method* (tuple): LCIA method. Same format as in LCA class.
    * *LCA_object* for which self.characterized_inventory already exists (i.e. LCA_object.lcia() has been called) 
        """
        assert hasattr(lca_obj, "characterized_inventory"), "Must do LCIA first for the LCA object passed"
        self.lca=lca_obj
        self.lca.switch_method(method)
        self.lca.redo_lcia(demand)
        #assumes that this must be reused several times thus better to factorize
        if not hasattr(self.lca, "solver"):
            self.lca.decompose_technosphere()
        return self.lca
