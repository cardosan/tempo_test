# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from .main import gtp
import numpy as np


co2_gtp_td = gtp("co2", np.array((1.,)), np.array((0.,)), 1., 250)
ch4_gtp_td = gtp("ch4", np.array((1.,)), np.array((0.,)), 1., 250)
