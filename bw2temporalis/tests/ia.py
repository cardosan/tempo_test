# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from ..dynamic_ia_methods import DynamicIAMethod, dynamic_methods
from ..utils import get_function_name
# from bw2data import Database, Method, databases, methods
# from bw2calc import LCA
from bw2data.tests import BW2DataTest as BaseTestCase
import arrow
import numpy as np
import warnings


valid_func = """def f(x):
    return x
"""

deprecated_func = """def %s(x):
    return x
"""


class DynamicIATestCase(BaseTestCase):
    def test_valid_function_name(self):
        self.assertEqual(get_function_name("def wow(foo, bar):\nsome other stuff"), "wow")
        self.assertEqual(get_function_name("def wow_wee(foo, bar):\nsome other stuff"), "wow_wee")
        self.assertEqual(get_function_name("def wow_wee (foo, bar):\nsome other stuff"), "wow_wee")
        self.assertEqual(get_function_name("def wow_WEE ():\nsome other stuff"), "wow_WEE")
        self.assertEqual(get_function_name("def     む䩎():\nsome other stuff"), "む䩎")

    def test_invalid_function_name(self):
        self.assertEqual(get_function_name("def wow(:\nsome other stuff"), None)
        self.assertEqual(get_function_name("defwow():\nsome other stuff"), None)
        self.assertEqual(get_function_name("de wow():\nsome other stuff"), None)
        self.assertEqual(get_function_name("def wow()\nsome other stuff"), None)

    def test_parsing_dynamic_function(self):
        method = DynamicIAMethod("a test method")
        method.write({
            "foo": valid_func
        })
        functions = method.create_functions()
        self.assertEqual(list(functions.keys()), ['foo'])
        self.assertEqual(functions['foo'](42), 42)

    def test_dynamic_function_deprecation(self):
        method = DynamicIAMethod("a test method")
        method.write({
            "foo": deprecated_func
        })

        with warnings.catch_warnings(record=True) as wrn:
            functions = method.create_functions()
            self.assertTrue(wrn)
            self.assertEqual(list(functions.keys()), ['foo'])
            self.assertEqual(functions['foo'](42), 42)

    # def create_methods(self):
    #     gw = [
    #         [("b", "bad"), 1],
    #     ]
    #     method = Method(("foo",))
    #     method.register()
    #     method.write(gw)
    #     method.process()

    #     fake_dynamic_method = DynamicIAMethod("Dynamic foo")
    #     fake_dynamic_method.register()
    #     fake_dynamic_method.write({x[0]: x[1] for x in gw})

    # def get_static_score(self, fu, dmethod, method):
    #     dynamic_lca = DynamicLCA(
    #         demand=fu,
    #         worst_case_method=method,
    #         now=arrow.now(),
    #     )
    #     dynamic_lca.calculate()
    #     dynamic_lca.timeline.characterize_static(method)

    #     print(dynamic_lca.gt_edges)
    #     print(dynamic_lca.timeline.raw)

    #     return sum([x.amount for x in dynamic_lca.timeline.characterized])

    # def get_lca_score(self, fu, method):
    #     lca = LCA(fu, method)
    #     lca.lci()
    #     lca.lcia()
    #     return lca.score

    # def create_database(self, name, data):
    #     db = Database(name)
    #     db.register()
    #     db.write(data)
    #     db.process()

    # def test_simple_system_no_temporal_distribution(self):
    #     data = {
    #         ("b", "bad"): {
    #             'type': 'emission'
    #         },
    #         ('b', 'first'): {
    #             'exchanges': [
    #                 {
    #                     'amount': 1,
    #                     'input': ('b', 'second'),
    #                     'type': 'technosphere'
    #                 },
    #             ],
    #             'type': 'process',
    #         },
    #         ('b', 'second'): {
    #             'exchanges': [
    #                 {
    #                     'amount': 2,
    #                     'input': ('b', 'bad'),
    #                     'type': 'biosphere'
    #                 },
    #             ],
    #             'type': 'process',
    #         }
    #     }
    #     self.create_database("b", data)
    #     self.create_methods()

    #     method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

    #     self.assertTrue(np.allclose(
    #         self.get_static_score(fu, dmethod, method),
    #         self.get_lca_score(fu, method)
    #     ))

    # def test_simple_system_temporal_distribution(self):
    #     data = {
    #         ("b", "bad"): {
    #             'type': 'emission'
    #         },
    #         ('b', 'first'): {
    #             'exchanges': [
    #                 {
    #                     'amount': 10,
    #                     'input': ('b', 'second'),
    #                     "temporal distribution": [(x, 1) for x in range(10)],
    #                     'type': 'technosphere'
    #                 },
    #             ],
    #             'type': 'process',
    #         },
    #         ('b', 'second'): {
    #             'exchanges': [
    #                 {
    #                     'amount': 2,
    #                     'input': ('b', 'bad'),
    #                     "temporal distribution": [(x, 0.5) for x in range(4)],
    #                     'type': 'biosphere'
    #                 },
    #             ],
    #             'type': 'process',
    #         }
    #     }
    #     self.create_database("b", data)
    #     self.create_methods()

    #     method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

    #     self.assertTrue(np.allclose(
    #         self.get_static_score(fu, dmethod, method),
    #         self.get_lca_score(fu, method)
    #     ))

    # def test_non_unitary_production_amount(self):
    #     data = {
    #         ("b", "bad"): {
    #             'type': 'emission'
    #         },
    #         ('b', 'first'): {
    #             'exchanges': [
    #                 {
    #                     'amount': 1,
    #                     'input': ('b', 'second'),
    #                     'type': 'technosphere'
    #                 },
    #             ],
    #             'type': 'process',
    #         },
    #         ('b', 'second'): {
    #             'exchanges': [
    #                 {
    #                     'amount': 2,
    #                     'input': ('b', 'bad'),
    #                     'type': 'biosphere'
    #                 },
    #                 {
    #                     'amount': 10,
    #                     'input': ('b', 'second'),
    #                     'type': 'production'
    #                 },
    #             ],
    #             'type': 'process',
    #         }
    #     }
    #     self.create_database("b", data)
    #     self.create_methods()

    #     method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

    #     self.assertTrue(np.allclose(self.get_static_score(fu, dmethod, method), 0.2))
    #     self.assertTrue(np.allclose(
    #         self.get_static_score(fu, dmethod, method),
    #         self.get_lca_score(fu, method)
    #     ))

    # def test_coproducts_and_substitution(self):
    #     data = {
    #         ("b", "bad"): {
    #             'type': 'emission'
    #         },
    #         ('b', 'first'): {
    #             'exchanges': [
    #                 {
    #                     'amount': 1,
    #                     'input': ('b', 'second'),
    #                     'type': 'technosphere'
    #                 },
    #                 {
    #                     'amount': 1,
    #                     'input': ('b', 'first'),
    #                     'type': 'production'
    #                 },
    #             ],
    #             'type': 'process',
    #             'name': 'first',
    #         },
    #         ('b', 'second'): {
    #             'exchanges': [
    #                 {
    #                     'amount': 2,
    #                     'input': ('b', 'bad'),
    #                     'type': 'biosphere'
    #                 },
    #                 {
    #                     'amount': 4,
    #                     'input': ('b', 'second'),
    #                     'type': 'production'
    #                 },
    #                 {
    #                     'amount': 5,
    #                     'input': ('b', 'third'),
    #                     'type': 'production'
    #                 },
    #             ],
    #             'type': 'process',
    #             'name': 'second',
    #         },
    #         ('b', 'third'): {
    #             'exchanges': [
    #                 {
    #                     'amount': 10,
    #                     'input': ('b', 'bad'),
    #                     'type': 'biosphere'
    #                 },
    #                 {
    #                     'amount': 20,
    #                     'input': ('b', 'third'),
    #                     'type': 'production'
    #                 },
    #             ],
    #             'type': 'process',
    #             'name': 'third',
    #         }
    #     }
    #     self.create_database("b", data)
    #     self.create_methods()

    #     method, dmethod, fu = ("foo",), "Dynamic foo", {("b", "first"): 1}

    #     dynamic_score = self.get_static_score(fu, dmethod, method),
    #     static_score = self.get_lca_score(fu, method)

    #     print(static_score, dynamic_score)

    #     self.assertTrue(np.allclose(static_score, 2 / 4. - 5 / 4. * 10. / 20.))
    #     self.assertTrue(np.allclose(static_score, dynamic_score))
