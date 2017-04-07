# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from ..dynamic_ia_methods import DynamicIAMethod, dynamic_methods
from ..dynamic_lca import DynamicLCA
from bw2data import Database, Method, databases, methods
from bw2calc import LCA
from bw2data.tests import BW2DataTest as BaseTestCase
import numpy as np


class DynamicLCATestCase(BaseTestCase):
    def create_methods(self):
        gw = [
            [("b", "bad"), 1],
        ]
        method = Method(("foo",))
        method.register()
        method.write(gw)
        method.process()

        fake_dynamic_method = DynamicIAMethod("Dynamic foo")
        fake_dynamic_method.register()
        fake_dynamic_method.write({x[0]: x[1] for x in gw})

    def get_static_score(self, fu, dmethod, method):
        dynamic_lca = DynamicLCA(
            demand=fu,
            worst_case_method=method,
            # now=arrow.now(),
        )
        dynamic_lca.calculate()
        dynamic_lca.timeline.characterize_static(method)

        # print(dynamic_lca.gt_edges)
        print(dynamic_lca.timeline.raw)

        return sum([x.amount for x in dynamic_lca.timeline.characterized])

    def get_lca_score(self, fu, method):
        lca = LCA(fu, method)
        lca.lci()
        lca.lcia()
        return lca.score

    def create_database(self, name, data):
        db = Database(name)
        db.register()
        db.write(data)
        db.process()

    def test_simple_system_no_temporal_distribution(self):
        """test total impact db without temporal distribution"""
        data = {
            ("b", "bad"): {
                'type': 'emission'
            },
            ('b', 'first'): {
                'exchanges': [
                    {
                        'amount': 1,
                        'input': ('b', 'second'),
                        'type': 'technosphere'
                    },
                ],
                'type': 'process',
            },
            ('b', 'second'): {
                'exchanges': [
                    {
                        'amount': 2,
                        'input': ('b', 'bad'),
                        'type': 'biosphere'
                    },
                ],
                'type': 'process',
            }
        }
        self.create_database("b", data)
        self.create_methods()

        method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

        self.assertTrue(np.allclose(
            self.get_static_score(fu, dmethod, method),
            self.get_lca_score(fu, method)
        ))

    def test_simple_system_temporal_distribution(self):
        """test total impact db with temporal distribution"""
        data = {
            ("b", "bad"): {
                'type': 'emission'
            },
            ('b', 'first'): {
                'exchanges': [
                    {
                        'amount': 10,
                        'input': ('b', 'second'),
                        "temporal distribution": [(x, 1) for x in range(10)],
                        'type': 'technosphere'
                    },
                ],
                'type': 'process',
            },
            ('b', 'second'): {
                'exchanges': [
                    {
                        'amount': 2,
                        'input': ('b', 'bad'),
                        "temporal distribution": [(x, 0.5) for x in range(4)],
                        'type': 'biosphere'
                    },
                ],
                'type': 'process',
            }
        }
        self.create_database("b", data)
        self.create_methods()

        method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

        self.assertTrue(np.allclose(
            self.get_static_score(fu, dmethod, method),
            self.get_lca_score(fu, method)
        ))
        
        
    def test_non_unitary_production_amount(self):
        data = {
            ("b", "bad"): {
                'type': 'emission'
            },
            ('b', 'first'): {
                'exchanges': [
                    {
                        'amount': 1,
                        'input': ('b', 'second'),
                        'type': 'technosphere'
                    },
                ],
                'type': 'process',
            },
            ('b', 'second'): {
                'exchanges': [
                    {
                        'amount': 2,
                        'input': ('b', 'bad'),
                        'type': 'biosphere'
                    },
                    {
                        'amount': 10,
                        'input': ('b', 'second'),
                        'type': 'production'
                    },
                ],
                'type': 'process',
            }
        }
        self.create_database("b", data)
        self.create_methods()

        method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

        self.assertTrue(np.allclose(self.get_static_score(fu, dmethod, method), 0.2))
        self.assertTrue(np.allclose(
            self.get_static_score(fu, dmethod, method),
            self.get_lca_score(fu, method)
        ))



    def test_coproducts_and_substitution(self):
        """test coproducts substitution """
        data = {
            ("b", "bad"): {
                'type': 'emission'
            },
            ('b', 'first'): {
                'exchanges': [
                    {
                        'amount': 1,
                        'input': ('b', 'second'),
                        'type': 'technosphere'
                    },
                    {
                        'amount': 1,
                        'input': ('b', 'first'),
                        'type': 'production'
                    },
                ],
                'type': 'process',
                'name': 'first',
            },
            ('b', 'second'): {
                'exchanges': [
                    {
                        'amount': 2,
                        'input': ('b', 'bad'),
                        'type': 'biosphere'
                    },
                    {
                        'amount': 4,
                        'input': ('b', 'second'),
                        'type': 'production'
                    },
                    {
                        'amount': 5,
                        'input': ('b', 'third'),
                        'type': 'production'
                    },
                ],
                'type': 'process',
                'name': 'second',
            },
            ('b', 'third'): {
                'exchanges': [
                    {
                        'amount': 10,
                        'input': ('b', 'bad'),
                        'type': 'biosphere'
                    },
                    {
                        'amount': 20,
                        'input': ('b', 'third'),
                        'type': 'production'
                    },
                ],
                'type': 'process',
                'name': 'third',
            }
        }
        self.create_database("b", data)
        self.create_methods()

        method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

        dynamic_score = self.get_static_score(fu, dmethod, method),
        static_score = self.get_lca_score(fu, method)

        print(static_score, dynamic_score)

        self.assertTrue(np.allclose(static_score, 2 / 4. - 5 / 4. * 10. / 20.))
        self.assertTrue(np.allclose(static_score, dynamic_score))
        
        
    def test_substitution_exchange(self):
        """test that exchange of type substitution gives correct results"""
        data = {
            ("b", "bad"): {
                'type': 'emission'
            },
            ('b', 'first'): {
                'exchanges': [
                    {
                        'amount': 1,
                        'input': ('b', 'second'),
                        'type': 'technosphere'
                    },
                    {
                        'amount': 1,
                        'input': ('b', 'first'),
                        'type': 'production'
                    },
                ],
                'type': 'process',
                'name': 'first',
            },
            ('b', 'second'): {
                'exchanges': [
                    {
                        'amount': 2,
                        'input': ('b', 'bad'),
                        'type': 'biosphere'
                    },
                    {
                        'amount': 4,
                        'input': ('b', 'second'),
                        'type': 'production'
                    },
                    #substitution
                    {
                        'amount': 5,
                        'input': ('b', 'third'),
                        'type': 'substitution'
                    },
                ],
                'type': 'process',
                'name': 'second',
            },
            ('b', 'third'): {
                'exchanges': [
                    {
                        'amount': 10,
                        'input': ('b', 'bad'),
                        'type': 'biosphere'
                    },
                    {
                        'amount': 20,
                        'input': ('b', 'third'),
                        'type': 'production'
                    },
                ],
                'type': 'process',
                'name': 'third',
            }
        }
        self.create_database("b", data)
        self.create_methods()

        method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

        dynamic_score = self.get_static_score(fu, dmethod, method),
        static_score = self.get_lca_score(fu, method)

        print(static_score, dynamic_score)

        self.assertTrue(np.allclose(static_score, 2 / 4. - 5 / 4. * 10. / 20.))
        self.assertTrue(np.allclose(static_score, dynamic_score))
        
        
    def test_loop(self):
        """test that database with loop stop the traversal"""
        data = {
            ("b", "bad"): {
                'type': 'emission'
            },
            ('b', 'first'): {
                'exchanges': [
                    {
                        'amount': 1,
                        'input': ('b', 'second'),
                        'type': 'technosphere'
                    },
                    {
                        'amount': 1,
                        'input': ('b', 'first'),
                        'type': 'production'
                    },
                ],
                'type': 'process',
                'name': 'first',
            },
            ('b', 'second'): {
                'exchanges': [
                    {
                        'amount': 2,
                        'input': ('b', 'bad'),
                        'type': 'biosphere'
                    },
                    {
                        'amount': 4,
                        'input': ('b', 'second'),
                        'type': 'production'
                    },
                    #loop
                    {
                        'amount': 5,
                        'input': ('b', 'first'),
                        'type': 'technosphere'
                    },
                ],
                'type': 'process',
                'name': 'second',
            },
            ('b', 'third'): {
                'exchanges': [
                    {
                        'amount': 10,
                        'input': ('b', 'bad'),
                        'type': 'biosphere'
                    },
                    {
                        'amount': 20,
                        'input': ('b', 'third'),
                        'type': 'production'
                    },
                ],
                'type': 'process',
                'name': 'third',
            }
        }
        self.create_database("b", data)
        self.create_methods()

        method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

        dynamic_score = self.get_static_score(fu, dmethod, method),
        static_score = self.get_lca_score(fu, method)

        print(static_score, dynamic_score)

        # self.assertTrue(np.allclose(static_score, 2 / 4. - 5 / 4. * 10. / 20.))
        self.assertTrue(np.allclose(static_score, dynamic_score))

    def test_double_exchange(self):
        """test dataset that has the same exchange that occurs two times """
        data = {
            ("b", "bad"): {
                'type': 'emission'
            },
            ('b', 'first'): {
                'exchanges': [
                    {
                        'amount': 1,
                        'input': ('b', 'second'),
                        'type': 'technosphere'
                    },
                    {
                        'amount': 1,
                        'input': ('b', 'first'),
                        'type': 'production'
                    },
                ],
                'type': 'process',
                'name': 'first',
            },
            ('b', 'second'): {
                'exchanges': [
                    {
                        'amount': 2,
                        'input': ('b', 'bad'),
                        'type': 'biosphere'
                    },
                    {
                        'amount': 4,
                        'input': ('b', 'second'),
                        'type': 'production'
                    },
                    #duplicate exc
                    {
                        'amount': 2,
                        'input': ('b', 'third'),
                        'type': 'technosphere'
                    },
                    {
                        'amount': 3,
                        'input': ('b', 'third'),
                        'type': 'technosphere'
                    },
                ],
                'type': 'process',
                'name': 'second',
            },
            ('b', 'third'): {
                'exchanges': [
                    {
                        'amount': 10,
                        'input': ('b', 'bad'),
                        'type': 'biosphere'
                    },
                    {
                        'amount': 20,
                        'input': ('b', 'third'),
                        'type': 'production'
                    },
                ],
                'type': 'process',
                'name': 'third',
            }
        }
        self.create_database("b", data)
        self.create_methods()

        method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

        dynamic_score = self.get_static_score(fu, dmethod, method),
        static_score = self.get_lca_score(fu, method)

        print(static_score, dynamic_score)

        # self.assertTrue(np.allclose(static_score, 2 / 4. - 5 / 4. * 10. / 20.))
        self.assertTrue(np.allclose(static_score, dynamic_score))
