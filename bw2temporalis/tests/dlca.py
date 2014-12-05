from ..dynamic_ia_methods import DynamicIAMethod, dynamic_methods
from ..dynamic_lca import DynamicLCA
from brightway2 import Database, Method, LCA, config, databases, methods
from bw2data.tests import BW2DataTest as BaseTestCase
import arrow
import numpy as np


class DynamicLCATestCase(BaseTestCase):
    def extra_setup(self):
        dynamic_methods.__init__()

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
            dynamic_method=dmethod,
            worst_case_method=method,
            now=arrow.now(),
        )
        dynamic_lca.calculate()
        dynamic_lca.timeline.characterize_static(method)

        print dynamic_lca.gt_edges

        print dynamic_lca.timeline.raw

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
        data = {
            ("b", "bad"): {
                'type': 'emission'
            },
            (u'b', u'first'): {
                u'exchanges': [
                    {
                        u'amount': 1,
                        u'input': (u'b', u'second'),
                        u'type': u'technosphere'
                    },
                ],
                'type': 'process',
            },
            (u'b', u'second'): {
                u'exchanges': [
                    {
                        u'amount': 2,
                        u'input': (u'b', u'bad'),
                        u'type': u'biosphere'
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
        data = {
            ("b", "bad"): {
                'type': 'emission'
            },
            (u'b', u'first'): {
                u'exchanges': [
                    {
                        u'amount': 10,
                        u'input': (u'b', u'second'),
                        u"temporal distribution": [(x, 1) for x in range(10)],
                        u'type': u'technosphere'
                    },
                ],
                'type': 'process',
            },
            (u'b', u'second'): {
                u'exchanges': [
                    {
                        u'amount': 2,
                        u'input': (u'b', u'bad'),
                        u"temporal distribution": [(x, 0.5) for x in range(4)],
                        u'type': u'biosphere'
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
            (u'b', u'first'): {
                u'exchanges': [
                    {
                        u'amount': 1,
                        u'input': (u'b', u'second'),
                        u'type': u'technosphere'
                    },
                ],
                'type': 'process',
            },
            (u'b', u'second'): {
                u'exchanges': [
                    {
                        u'amount': 2,
                        u'input': (u'b', u'bad'),
                        u'type': u'biosphere'
                    },
                    {
                        u'amount': 10,
                        u'input': (u'b', u'second'),
                        u'type': u'production'
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
        data = {
            ("b", "bad"): {
                'type': 'emission'
            },
            (u'b', u'first'): {
                u'exchanges': [
                    {
                        u'amount': 1,
                        u'input': (u'b', u'second'),
                        u'type': u'technosphere'
                    },
                ],
                'type': 'process',
                'name': 'first',
            },
            (u'b', u'second'): {
                u'exchanges': [
                    {
                        u'amount': 2,
                        u'input': (u'b', u'bad'),
                        u'type': u'biosphere'
                    },
                    {
                        u'amount': 4,
                        u'input': (u'b', u'second'),
                        u'type': u'production'
                    },
                    {
                        u'amount': 5,
                        u'input': (u'b', u'third'),
                        u'type': u'production'
                    },
                ],
                'type': 'process',
                'name': 'second',
            },
            (u'b', u'third'): {
                u'exchanges': [
                    {
                        u'amount': 10,
                        u'input': (u'b', u'bad'),
                        u'type': u'biosphere'
                    },
                    {
                        u'amount': 20,
                        u'input': (u'b', u'third'),
                        u'type': u'production'
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

        print static_score, dynamic_score

        self.assertTrue(np.allclose(static_score, 2 / 4. - 5 / 4. * 10. / 20.))
        self.assertTrue(np.allclose(static_score, dynamic_score))
