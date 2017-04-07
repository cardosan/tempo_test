# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from ..temporal_distribution import TemporalDistribution as TD
import numpy as np
import unittest


class TemporalDistributionTestCase(unittest.TestCase):
    def create_td(self):
        return TD(np.arange(0,5, dtype='timedelta64[Y]'), np.ones(5) * 2)

    def test_init(self):
        """test TD inizialization"""
        #empty
        with self.assertRaises(ValueError):
            TD(None, None) 
        #uneven lenght
        with self.assertRaises(ValueError):
            TD(np.arange(5), np.array(2, 2, 2, 2))
        #float instead datetime
        with self.assertRaises(ValueError):
            TD(np.arange(5), np.ones(5) * 2)

    def test_mul_td(self):
        """test __mul__ (i.e. convolution)"""
        td = self.create_td()
                
        #test timedelta
        td2 = TD(np.array((-1, 0, 1), dtype='timedelta64[Y]'), np.ones(3).astype(float))
        #test datetime
        td3 = TD(np.array((-1, 0, 1), dtype='datetime64[Y]'), np.ones(3).astype(float))
        #convolution only possible with timedelta
        with self.assertRaises(AssertionError):
            td * td3
        with self.assertRaises(AssertionError):
            td3 * td
        
        multiplied = td * td2
        #check result mul.times (allclose does not work with datetime)
        self.assertTrue(np.array_equal(
            np.arange(-1, 6, dtype='timedelta64[Y]').astype('timedelta64[s]'),
            multiplied.times)
        )
        #check sum of values
        self.assertEqual(
            td.values.sum() * td2.values.sum(),
            multiplied.values.sum()
        )
        #check result array mul.values
        self.assertTrue(np.allclose(
            np.array((2.,  4.,  6.,  6.,  6.,  4.,  2.)),
            multiplied.values
        ))
        
    def test_div_td(self):
        """check unpossible division between tds"""
        td = self.create_td()
        td2 = TD(np.array((-1, 0, 1), dtype='timedelta64[Y]'), np.ones(3).astype(float))
        with self.assertRaises(ValueError):
            td / td2

    def test_div_int(self):
        """check possible division between td and int"""
        td = self.create_td()
        divided = td / 2.
        self.assertTrue(np.array_equal(
            np.arange(0,5, dtype='timedelta64[Y]').astype('timedelta64[s]'),
            divided.times
        ))


    def test_mul_int(self):
        """check mul between td and int"""
        td = self.create_td() * 5
        self.assertTrue(np.array_equal(
            td.times,
            np.arange(0,5, dtype='timedelta64[Y]').astype('timedelta64[s]'),
        ))
        self.assertTrue(np.allclose(
            td.values,
            np.ones(5) * 10
        ))
        
    def test_add_integer(self):
        """check add between td and int"""
        td = self.create_td() + 5
        self.assertTrue(np.array_equal(
            td.times,
            np.arange(0,5, dtype='timedelta64[Y]').astype('timedelta64[s]'),
        ))
        self.assertTrue(np.allclose(
            td.values,
            np.ones(5) * 7
        ))

    def test_add_td(self):
        """check add between tds"""
        td = self.create_td()
        td2 = TD(np.array((-1, 0, 1), dtype='timedelta64[Y]'), np.ones(3).astype(float))
        added = td + td2
        self.assertTrue(np.array_equal(
            np.arange(-1, 5, dtype='timedelta64[Y]').astype('timedelta64[s]'),
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
        self.assertEqual(next(td), (np.timedelta64(0,'Y').astype('timedelta64[s]'), 2))
        self.assertEqual(next(td), (np.timedelta64(1,'Y').astype('timedelta64[s]'), 2))
        self.assertEqual(next(td), (np.timedelta64(2,'Y').astype('timedelta64[s]'), 2))
        self.assertEqual(next(td), (np.timedelta64(3,'Y').astype('timedelta64[s]'), 2))
        self.assertEqual(next(td), (np.timedelta64(4,'Y').astype('timedelta64[s]'), 2))
        with self.assertRaises(StopIteration):
            next(td)

    def test_representation(self):
        repr(self.create_td())

    def test_str(self):
        str(self.create_td())
