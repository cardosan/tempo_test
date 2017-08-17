# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from .temporal_distribution import TemporalDistribution
from .timeline import Timeline
from .dyn_methods.forest import get_static_forest_keys
from bw2calc import LCA
from bw2data import Database, get_activity, databases
from bw2data.logs import get_logger
from heapq import heappush, heappop
import numpy as np
import pprint
import warnings
import collections
import gzip
import datetime
import os
import pickle
import datetime


class FakeLog(object):
    """Like a log object, but does nothing"""
    def fake_function(cls, *args, **kwargs):
        return

    def __getattr__(self, attr):
        return self.fake_function


class DynamicLCA(object):
    """Calculate a dynamic LCA, where processes, emissions, and CFs can vary throughout time.If an already (statically) characterized LCA object is passed calculate its dynamic LCA (useful when doing several dynamic LCA for same database but different the FUs).

Args:
    * *demand* (dict): The functional unit. Same format as in LCA class.
    * *worst_case_method* (tuple): LCIA method. Same format as in LCA class.
    * *cutoff* (float, default=0.005): Cutoff criteria to stop LCA calculations. Relative score of total, i.e. 0.005 will cutoff if a dataset has a score less than 0.5 percent of the total.
    * *max_calc_number* (int, default=10000): Maximum number of LCA calculations to perform.
    * *loop_cutoff* (int, default=10): Maximum number of times loops encountered will be traversed.
    * *t0* (datetime, default=np.datetime64('now')): `datetime` of the year zero (i.e. the one of the functional unit). 
    #~* *group* (Boolean, default=False: When 'True' groups the impact upstream for each of the processes with the field`grouping_field`==True
    #~* *grouping_field* (string, default='tempo_group': The bw2 field to look for when grouping impacts upstream. When ``group`==True and a process has `grouping_field`==True the impacts are grouped upstream for it untill another  process with `grouping_field`==True is found
    * *group* (Boolean, default=False: When 'True' groups the impact upstream for each of the processes based on the values of `grouping_field`
    * *grouping_field* (string, default='tempo_group': The bw2 field to look for when grouping impacts upstream. When ``group`==True and a process has `grouping_field==whatever` the impacts are grouped upstream with name ``whatever` untill another  process with `grouping_field==another name` is found. If `grouping_field==True` it simply uses the name of the process
    * *log* (int, default=False): If True to make log file
    * *lca_object* (LCA object,default=None): do dynamic LCA for the object passed (must have "characterized_inventory" i.e. LCA_object.lcia() has been called)
    """
    def __init__(self, demand, worst_case_method, t0=None, max_calc_number=1e4, cutoff=0.001,loop_cutoff=10,group=False,grouping_field="tempo_group", log=False, lca_object=None):
        self.demand = demand
        self.worst_case_method = worst_case_method
        self.t0=np.datetime64('now', dtype="datetime64[s]") if t0 is None else np.datetime64(t0).astype("datetime64[s]")
        self.max_calc_number = max_calc_number
        self.cutoff_value = cutoff
        self.loop_cutoff_value = loop_cutoff
        self.log = get_logger("dynamic-lca.log") if log else FakeLog()
        self.lca_object=lca_object
        self.group=group
        self.grouping_field=grouping_field
        self.stat_for_keys=get_static_forest_keys() #return forest processes
        self.loops=collections.Counter() #to count loops iterations

        #return static db and create set where will be added nodes as traversed
        all_databases = set.union(*[Database(key[0]).find_graph_dependents() for key in self.demand])
        self.static_databases = {name for name in all_databases if databases[name].get('static')}
        self.product_amount=collections.defaultdict(int) #to check supply amount calculated for each product
        self.nodes=set()
        self.edges=set()
        
        #self.test_datetime={}    #test for using TD,left for future (potential) development (other parts are commented out below)
        
        
    ###########
    #Traversal#
    ###########


    def calculate(self):
        """Calculate"""
        self.timeline = Timeline()
        self.heap = [] #heap with dynamic exchanges to loop over (impact,edge,datetime, TemporalDistribution)
        self.calc_number = 0
        
        #run worst case LCA if lca_object not passed else redo for demand and worst_case method
        if self.lca_object:
            _redo_lcia(self, self.lca_object, self.demand,self.worst_case_method)
        else:
            self.lca = LCA(self.demand,self.worst_case_method)
            self.lca.lci()
            self.lca.lcia()
        
        #reverse matrix and calculate cutoff
        self.reverse_activity_dict, self.reverse_prod_dict, self.reverse_bio_dict = self.lca.reverse_dict()        
        self.cutoff = abs(self.lca.score) * self.cutoff_value
                
        #logs
        self.log.info("Starting dynamic LCA")
        self.log.info("Demand: %s" % self.demand)
        self.log.info("Worst case method: %s" % str(self.worst_case_method))
        self.log.info("Start datetime: %s" % self.t0)
        self.log.info("Maximum calculations: %i" % self.max_calc_number)
        self.log.info("Worst case LCA score: %.4g." % self.lca.score)
        self.log.info("Cutoff value (fraction): %.4g." % self.cutoff_value)
        self.log.info("Cutoff score: %.4g." % self.cutoff)


        # Initialize heap
        #MAYBE NOT NECESSARY ANYMORE
        heappush(
            self.heap,
            (
                None,
                ("Functional unit","Functional unit",), 
                self.t0,
                TemporalDistribution(
                    np.array([0,],dtype='timedelta64[s]'), # need int
                    np.array((1.,)).astype(float)                     
                ),
                'Functional unit' #with tag
            )
        ) if self.lca.score!=0 else self.timeline.add(self.t0.astype(datetime.datetime) , None, None,0) #deal with demand with no impact (doing so does not return error in LCIA)

        while self.heap:
            if self.calc_number >= self.max_calc_number:
                warnings.warn("Stopping traversal due to calculation count.")
                break
            self._iterate()
        
        self.log.info("NODES: " + pprint.pformat(self.nodes))
        self.log.info("EDGES: " + pprint.pformat(self.edges))    
        
        return self.timeline

    ##############
    #INTERNAL USE#
    ##############

    def _iterate(self):
        """Iterate over the datasets starting from the FU"""
        # Ignore the calculated impact
        # `ed` is the the edge, in the form of (keyto, keyfrom)
        # `dt` is the datetime; GIU: we can also avoid this and use self.t0
        # `td` is a TemporalDistribution instance, which gives
        # how much of the dataset is used over time at
        # this point in the graph traversal
        _, ed, dt, td,ups_tag = heappop(self.heap)  # Don't care about impact #with tag

        #do not remeber what is this, check
        if ed!=("Functional unit","Functional unit",):
            self.product_amount[ed[1]] += td.total
        self.scale_value = self._get_scale_value(ed[1])

        if self.log:
            self.log.info("._iterate(): %s, %s, %s" % (ed, dt, td))
            
        #get bw2 activity for node
        node=get_activity(ed[1]) if ed[1] != "Functional unit" else {'FU':False} #trick to deal with FU in LCA with results==0

        #tag ds with label if present otherwise inherit upstream tag
        ed_tag=ed[1]
        if self.group==True:
            ed_tag=ups_tag if node.get(self.grouping_field,False) == False else ed[1] #with tags ed[0]
        
        #add bio flows (both dynamic and static)
        self._add_biosphere_flows(ed, td,ed_tag) #with tag

        #deal with functional unit
        if ed[1]=="Functional unit":               
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
                    (ed[1],key),
                    dt,
                    new_td,
                    ed_tag #with tag
                ))
            self.calc_number += 1
            
        #for all the other datasets
        else:
            #skip node if part of of a static db or when a loop i traversed loop_cutoff times
            if node['database'] in self.static_databases or self.loops[ed]>=self.loop_cutoff_value or (self.loops[ed]>=1 and td.total>=1): #loop certain amount of time ONLY if exc amoung <=1
                return

            #add to nodes,edges and loops counter
            self.nodes.add(ed[1])
            self.edges.add(ed)
            self.loops[ed]+=1
            
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
                    #~print(exc.get('name'),exc.get('input'),exc.get('system'))
                    dyn_edges[exc['input']] = (
                    self._get_temporal_distribution(exc) +
                    dyn_edges.get(exc['input'], 0))
                    
                #deal with coproducts
                if exc.get('type')=='production' and exc.get('input')!=ed[1]:
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
                
                # Calculate lca and discard if node impact is lower than cutoff
                if self._discard_node(
                        edge,
                        new_td.total):
                    continue
                
                #else add to the heap the ds of this exchange with the new TD
                heappush(self.heap, (
                    abs(1 / self.lca.score),
                    (ed[1],edge),
                    dt,
                    new_td,
                    ed_tag  #with tag          
                ))
            self.calc_number += 1

    def _add_biosphere_flows(self, edge, tech_td,tag): #with tag

        """add temporally distributed biosphere exchanges for this ds to timeline.raw both if ds is static or dynamic"""
        
        ds=edge[1] #fix this (for now done just to avoid changing all the ds below)
        if ds == "Functional unit":
            return
        data = get_activity(ds)
        
        #add biosphere flow for process passed
        #check if new bw2 will need changes cause will differentiate import of products and activity (i.e. process)
        if not data.get('type', 'process') == "process":
            return
            
        #Add cumulated inventory for static database (to make faster calc) and loops (to avoid infinite loops)
        if data['database'] in self.static_databases or self.loops[edge]>=self.loop_cutoff_value or (self.loops[edge]>=1 and tech_td.total>=1): #loop certain amount of time only if exc amoung <=1
                
            self.lca.redo_lci({data: 1})
            
            # #add product amount to product_amount (to be used when background dataset traversal will be implemented )
            # for i,am in np.ndenumerate(self.lca.supply_array):
                # product=self.reverse_prod_dict[i[0]]
                # if product!=ds:
                    # self.product_amount[product] += am*tech_td.total
            
            # #this only foreground
            inventory_vector = np.array(self.lca.inventory.sum(axis=1)).ravel()
            for index, amount in enumerate(inventory_vector):
                if not amount or amount == 0 : #GIU: we can skip also 0 amounts that sometimes occurs right?
                    continue
                flow = self.reverse_bio_dict[index]
                
            ###benchmarked this below, takes the same time of the foreground the problem is the high memory usage that slow things down
            # #this also background
            # coo=self.lca.inventory.tocoo()
            # for i,j,amount in zip(coo.row, coo.col, coo.data):
                # flow = self.reverse_bio_dict[i]
                # pr = self.reverse_prod_dict[j]
        
                
                dt_bio=self._calculate_bio_td_datetime(amount,tech_td)
                for bio_dt, bio_amount_scaled in dt_bio:
                    #TODO: best to use a better container for timeline.
                    #maybe defaultdict with namedtuple as key to group amount when added 
                    #fastest, see among others here https://gist.github.com/dpifke/2244911 (I also tested)
                    if bio_amount_scaled !=0:
                        self.timeline.add(bio_dt, flow, tag,bio_amount_scaled) #only foreground with tag
                        # self.timeline.add(bio_dt, flow, pr,bio_amount_scaled) #with background
                
                #~#test for using TD
                #~dt_bio_test=self._calculate_bio_td_datetime_test_timeline(amount,tech_td)
                #~self.test_datetime[flow, ds] = dt_bio_test+self.test_datetime.get((flow, ds),0) 


            ##deal with co2 biogenic dynamic in installed (static) databases (maybe can avoid this loop and do direclty above) 
            if ('biosphere3', 'cc6a1abb-b123-4ca6-8f16-38209df609be') in self.lca.biosphere_dict:
                row_bioc = self.lca.biosphere_dict[('biosphere3', 'cc6a1abb-b123-4ca6-8f16-38209df609be')] 
                col_cbio = self.lca.biosphere_matrix[row_bioc, :].tocoo() #get coordinates Carbon dioxide, in air
                
                ## find inventory values and sum
                ## in principle `CO2, in air` should have a negative 
                ## but in ei it is positive so no need to change sign in bio_c
                bio_c=sum([self.lca.inventory[row_bioc, index] for index in col_cbio.col if self.reverse_activity_dict[index] in self.stat_for_keys])
                dt_bio_c=self._calculate_bio_td_datetime(bio_c,tech_td)
                for bio_dt, bio_amount_scaled in dt_bio_c:                   
                    if bio_amount_scaled !=0:
                        #~self.timeline.add(bio_dt, ('static_forest','C_biogenic'), ds, bio_amount_scaled)
                        self.timeline.add(bio_dt, ('static_forest','C_biogenic'), tag, bio_amount_scaled) #with tag

                #~#test for using TD
                #~dt_bio_c_test=self._calculate_bio_td_datetime_test_timeline(bio_c,tech_td)
                #~self.test_datetime[('static_forest','C_biogenic'), ds] = dt_bio_c_test+self.test_datetime.get((('static_forest','C_biogenic'), ds),0) 

            return   
    
        #dynamic database
        #get TD of bio exc, spread, convert to datetime and append to timeline.raw
        for exc in data.biosphere():
            bio_td=self._get_temporal_distribution(exc)
            td_bio_new=self._calculate_bio_td_datetime(bio_td,tech_td)
            for bio_dt, bio_amount_scaled in td_bio_new:
                if bio_amount_scaled !=0:
                    #deal with forest biogenic C in dynamic db
                    if exc['input']==('biosphere3', 'cc6a1abb-b123-4ca6-8f16-38209df609be') and ds in self.stat_for_keys:
                        self.timeline.add(bio_dt, ('static_forest','C_biogenic'), tag,bio_amount_scaled) # with tag
                    else:
                        self.timeline.add(bio_dt, exc['input'], tag,bio_amount_scaled) # with tag

            #~#test for using TD
            #~td_bio_new_test=self._calculate_bio_td_datetime_test_timeline(bio_td,tech_td)
            #~if exc['input']==('biosphere3', 'cc6a1abb-b123-4ca6-8f16-38209df609be') and ds in self.stat_for_keys:
                #~self.test_datetime[('static_forest','C_biogenic'), ds] = td_bio_new_test+self.test_datetime.get((('static_forest','C_biogenic'), ds),0) 
            #~else:
                #~self.test_datetime[exc['input'], ds] = td_bio_new_test+self.test_datetime.get((exc['input'], ds),0) 

                    
    def _calculate_bio_td_datetime(self,bio_flows,td_tech):
        """Recalculate bio, both if datetime or timedelta, and add to timedelta.
        td_tech is always timedelta64, bio_flows can be datetime64 or float for static db"""
        #dynamic db with dt for bio_flows, multiply by node total
        if isinstance(bio_flows,TemporalDistribution) and 'datetime64' in str(bio_flows.times.dtype):
            return ( bio_flows * td_tech.total ) / self.scale_value 
        #both static db and dynamic with timedelta for bio_flows
        bio_td_delta = (td_tech * bio_flows) / self.scale_value 
        return bio_td_delta.timedelta_to_datetime(self.t0)
    #~#test for using TD
    #~def _calculate_bio_td_datetime_test_timeline(self,bio_flows,td_tech):
        #~###a test to check `test_datetime` since timeline multiply only with timedelta
        #~"""Recalculate bio, both if datetime or timedelta, and add to timedelta.
        #~td_tech is always timedelta64, bio_flows can be datetime64 or float for static db"""
        #~#dynamic db with dt for bio_flows, multiply by node total
        #~if isinstance(bio_flows,TemporalDistribution) and 'datetime64' in str(bio_flows.times.dtype):
            #~return ( bio_flows * td_tech.total ) / self.scale_value 
        #~#both static db and dynamic with timedelta for bio_flows
        #~bio_td_delta = (td_tech * bio_flows) / self.scale_value 
        #~return bio_td_delta

    def _calculate_new_td(self,edge_td,node_td):
        """Recalculate edge both if datetime or timedelta, return always timedelta.
        node_td is always timedelta64, edge_td can be datetime"""
        if 'datetime64' in str(edge_td.times.dtype):
            #multiply by node.total and convert to timedelta
            new_td=(edge_td * node_td.total) / self.scale_value 
            return new_td.datetime_to_timedelta(self.t0)
        #else just convolute 
        return (node_td * edge_td) / self.scale_value 
        
    ################
    #Data retrieval#
    ################


    def _get_temporal_distribution(self, exc):
        """get 'temporal distribution'and change sing in case of production or substitution exchange"""
        # sign = 1 if exc.get('type') != 'production' else -1
        #deal with exchanges of type production and substititution
        sign = -1 if exc.get('type') in ['production','substitution'] else 1
        
        td=exc.get('temporal distribution', TemporalDistribution(
                np.array([0,], dtype='timedelta64[s]'), # need int
                np.array([exc['amount'],]).astype(float)        )
                   )
        if not isinstance(td,TemporalDistribution):
            #convert old format, not for fractional years
            if any(isinstance(t_v, tuple) and len(t_v)==2 and isinstance(t_v[0], int ) for t_v in td):
                    array = np.array(exc[u'temporal distribution'])
                    td=TemporalDistribution(array[:, 0].astype('timedelta64[Y]'), array[:, 1]) 
                    warnings.warn("The old format for `temporal distribution` is deprecated, now must be a `TemporalDistribution` object instead of a nested list of tuples. The applied convertion might be incorrect in the exchange from {} to {}".format(exc['input'],exc['output']),DeprecationWarning)
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
        
    def save_dLCI(self,folderpath=None):
        """Save the results of DynamicLCA to a (compressed) ``bw2lci`` file containing dictionary like 
        ``'timeline':timeline object,
        'demand':dLCI demand
        'wc_method':dLCI worst_case_method
        The file is saved to the current working directory by default with the filename=demandkey_worstcase_method. Restoration is done using 'bw2temporalis.timeline.load_LCI'. 
        Args:
            * *folderpath* (str, default=None): the filepath of the timeline (without file extension)
        """
        
        assert hasattr(self, "timeline"), "Must do calculate first"
        #make folder if not existing and give name of demand_worstcase_method to the file 
        os.makedirs(folderpath or '.', exist_ok=True) #create folder if not existing yet see  https://stackoverflow.com/a/12517490/4929813     
        tl_path=os.path.join(folderpath or '.','{}_{}.bw2lci'.format(self.demand, self.worst_case_method))
        f = gzip.open(tl_path,'wb')
        pickle.dump({'timeline':self.timeline,'demand':self.demand,'wc_method':self.worst_case_method},f)
        f.close()

