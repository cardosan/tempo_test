# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from .main import gtp, rf
import numpy as np


co2_gtp_td_ar5 = gtp("co2", np.array((1.,)), np.array((0.,)), 1., 250)
ch4_gtp_td_ar5 = gtp("ch4", np.array((1.,)), np.array((0.,)), 1., 250)

co2_rf = rf("co2", np.array((1.,)), np.array((0.,)), 1., 250)
ch4_rf = rf("ch4", np.array((1.,)), np.array((0.,)), 1., 250)

co2_gtp_td_base = gtp("co2", np.array((1.,)), np.array((0.,)), 1., 250, "op_base")
ch4_gtp_td_base = gtp("ch4", np.array((1.,)), np.array((0.,)), 1., 250, "op_base")

co2_gtp_td_low = gtp("co2", np.array((1.,)), np.array((0.,)), 1., 250, "op_low")
ch4_gtp_td_low = gtp("ch4", np.array((1.,)), np.array((0.,)), 1., 250, "op_low")

co2_gtp_td_high = gtp("co2", np.array((1.,)), np.array((0.,)), 1., 250, "op_high")
ch4_gtp_td_high = gtp("ch4", np.array((1.,)), np.array((0.,)), 1., 250, "op_high")
