from ..temporal_distribution import TemporalDistribution as TD
import numpy as np
import unittest


class TemporalDistributionTestCase(unittest.TestCase):
    def create_td(self):
        return TD(np.arange(5), np.ones(5) * 2)

    def test_init(self):
        with self.assertRaises(ValueError):
            TD(None, None)
        with self.assertRaises(ValueError):
            TD(np.arange(5), np.array(2, 2, 2, 2))

    def test_mul_td(self):
        td = self.create_td()
        td2 = TD(np.array((-1., 0, 1.)), np.ones(3).astype(float))
        multiplied = td * td2
        self.assertTrue(np.allclose(
            np.arange(-1, 6),
            multiplied.times
        ))
        self.assertEqual(
            td.values.sum() * td2.values.sum(),
            multiplied.values.sum()
        )
        self.assertTrue(np.allclose(
            np.array((2.,  4.,  6.,  6.,  6.,  4.,  2.)),
            multiplied.values
        ))

    def test_div_td(self):
        td = self.create_td()
        td2 = TD(np.array((-1., 0, 1.)), np.ones(3).astype(float))
        with self.assertRaises(ValueError):
            td / td2

    def test_div_int(self):
        td = self.create_td()
        divided = td / 2.
        self.assertTrue(np.allclose(
            np.arange(5),
            divided.times
        ))
        self.assertTrue(np.allclose(
            np.ones(5),
            divided.values
        ))

    def test_mul_int(self):
        td = self.create_td() * 5
        self.assertTrue(np.allclose(
            td.times,
            np.arange(5)
        ))
        self.assertTrue(np.allclose(
            td.values,
            np.ones(5) * 10
        ))

    def test_add_integer(self):
        td = self.create_td() + 5
        self.assertTrue(np.allclose(
            td.times,
            np.arange(5)
        ))
        self.assertTrue(np.allclose(
            td.values,
            np.ones(5) * 7
        ))

    def test_add_td(self):
        td = self.create_td()
        td2 = TD(np.array((-1., 0, 1.)), np.ones(3).astype(float))
        added = td + td2
        self.assertTrue(np.allclose(
            np.arange(-1, 5),
            added.times
        ))
        self.assertEqual(
            td.values.sum() + td2.values.sum(),
            added.values.sum()
        )
        self.assertTrue(np.allclose(
            np.array((1.,  3.,  3.,  2.,  2.,  2.)),
            added.values
        ))

    def test_iter(self):
        td = iter(self.create_td())
        self.assertEqual(td.next(), (0, 2))
        self.assertEqual(td.next(), (1, 2))
        self.assertEqual(td.next(), (2, 2))
        self.assertEqual(td.next(), (3, 2))
        self.assertEqual(td.next(), (4, 2))
        with self.assertRaises(StopIteration):
            td.next()

    def test_representation(self):
        repr(self.create_td())

    def test_unicode(self):
        unicode(self.create_td())

    def test_str(self):
        str(self.create_td())
