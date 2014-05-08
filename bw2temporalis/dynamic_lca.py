from .timeline import Timeline
from bw2analyzer import GTManipulator
from bw2calc import GraphTraversal
from bw2data import Database
from heapq import heappush, heappop
import arrow
import datetime
import itertools
import logging
import pprint
import warnings

logging.basicConfig(filename="dynamic-lca.log", level=logging.DEBUG)


class DynamicLCA(object):
    """Calculate a dynamic LCA, where processes, emissions, and CFs can vary throughout time."""
    def __init__(self, demand, dynamic_method, worst_case_method, now, max_calc_number=1e4, cutoff = 0.001):
        self.demand = demand
        self.dynamic_method = dynamic_method
        self.worst_case_method = worst_case_method
        self.now = now
        self.max_calc_number = max_calc_number
        self.cutoff_value = cutoff

    def calculate(self):
        self.timeline = Timeline()
        self.gt = GraphTraversal()
        self.heap = []
        self.calc_number = 0

        self.gt_results = self.gt.calculate(self.demand, self.worst_case_method)
        self.lca = self.gt_results['lca']
        self.temporal_edges = self.get_temporal_edges()
        self.cutoff = abs(self.lca.score) * self.cutoff_value
        self.gt_nodes = GTManipulator.add_metadata(
            self.gt_results['nodes'],
            self.lca
        )
        self.gt_edges = self.translate_edges(self.gt_results['edges'])

        logging.debug("NODES: " + pprint.pformat(self.gt_nodes))
        logging.debug("EDGES: " + pprint.pformat(self.gt_edges))

        # Initialize heap
        heappush(
            self.heap,
            (None, "Functional unit", self.now, self.gt_nodes[-1]['amount'])
        )

        while self.heap:
            if self.calc_number >= self.max_calc_number:
                warnings.warn("Stopping traversal due to calculation count.")
                break
            self.iterate()

    def translate_edges(self, edges):
        for edge in edges:
            edge['from'] = self.gt_nodes[edge['from']].get(
                'key', "Functional unit"
            )
            edge['to'] = self.gt_nodes[edge['to']].get(
                'key', "Functional unit"
            )
        return edges

    def get_temporal_edges(self):
        edges = {}
        for database in self.lca.databases:
            db_data = Database(database).load()
            for key, value in db_data.iteritems():
                if value.get("type") != "process":
                    continue
                for exc in value.get("exchanges", []):
                    if "temporal distribution" not in exc:
                        continue
                    else:
                        edges[(exc['input'], key)] = exc['temporal distribution']
        return edges

    def add_biosphere_flows(self, ds, dt, amount):
        if ds == "Functional unit":
            return
        data = Database(ds[0]).load()[ds]
        if not data.get('type') == "process":
            return
        for exc in data.get('exchanges', []):
            if not exc.get("type") == "biosphere":
                continue
            elif "temporal distribution" not in exc:
                self.timeline.add(dt, exc['input'], ds, amount * exc['amount'])
            else:
                for year_delta, subtotal in exc['temporal distribution']:
                    self.timeline.add(
                        dt + self.to_timedelta(year_delta),
                        exc['input'],
                        ds,
                        amount * subtotal
                    )

    def tech_edges_from_node(self, node):
        return itertools.ifilter(
            lambda x: x['to'] == node,
            self.gt_edges
        )

    def discard_node(self, node, amount):
        self.lca.redo_lcia({node: amount})
        return abs(self.lca.score) < self.cutoff

    def to_timedelta(self, years):
        return datetime.timedelta(hours=int(years * 8765.81))

    def check_absolute(self, ds, dt):
        if ds == "Functional unit":
            return dt
        ds_data = Database(ds[0]).load()[ds]
        absolute = "absolute date" in ds_data
        logging.debug("check_absolute: %s (%s)" % (absolute, ds))
        if "absolute date" in ds_data:
            return arrow.get(ds_data['absolute date'])
        else:
            return dt

    def iterate(self):
        _, ds, dt, amount = heappop(self.heap)  # Don't care about impact

        dt = self.check_absolute(ds, dt)

        logging.debug(".iterate(): %s, %s, %s" % (ds, dt, amount))
        self.add_biosphere_flows(ds, dt, amount)
        for edge in self.tech_edges_from_node(ds):
            logging.debug(".iterate:edge: " + pprint.pformat(edge))
            input_amount = amount * edge['exc_amount']
            if self.discard_node(edge['from'], input_amount):
                continue
            try:
                temporal_edges = self.temporal_edges[(edge['from'], edge['to'])]
            except KeyError:
                temporal_edges = [(0, edge['exc_amount'])]

            for year_delta, subtotal in temporal_edges:
                heappush(self.heap, (
                    self.lca.score * subtotal / amount,
                    edge['from'],
                    dt + self.to_timedelta(year_delta),
                    subtotal * amount
                ))
        self.calc_number += 1
