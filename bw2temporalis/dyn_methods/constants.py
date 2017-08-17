# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from .metrics import AGTP,RadiativeForcing
import numpy as np

#create AGTP timeline (add other gasses)
co2_agtp_ar5_td = AGTP("co2", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
co2bio_agtp_ar5_td = AGTP("co2_biogenic", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
ch4_agtp_ar5_td = AGTP("ch4", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
ch4_fossil_agtp_ar5_td = AGTP("ch4_fossil", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
n2o_agtp_ar5_td = AGTP("n2o", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
sf6_agtp_ar5_td = AGTP("sf6", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)

co2_agtp_base_td = AGTP("co2", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_base")
co2bio_agtp_base_td = AGTP("co2_biogenic", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_base")
ch4_agtp_base_td = AGTP("ch4", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_base")
ch4_fossil_agtp_base_td = AGTP("ch4_fossil", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_base")
n2o_agtp_base_td = AGTP("n2o", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_base")
sf6_agtp_base_td = AGTP("sf6", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_base")

co2_agtp_low_td = AGTP("co2", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_low")
co2bio_agtp_low_td = AGTP("co2_biogenic", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_low")
ch4_agtp_low_td = AGTP("ch4", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_low")
ch4_fossil_agtp_low_td = AGTP("ch4_fossil", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_low")
n2o_agtp_low_td = AGTP("n2o", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_low")
sf6_agtp_low_td = AGTP("sf6", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_low")

co2_agtp_high_td = AGTP("co2", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_high")
co2bio_agtp_high_td = AGTP("co2_biogenic", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_high")
ch4_agtp_high_td = AGTP("ch4", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_high")
ch4_fossil_agtp_high_td = AGTP("ch4_fossil", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_high")
n2o_agtp_high_td = AGTP("n2o", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_high")
sf6_agtp_high_td = AGTP("sf6", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000, "op_high")

#create RF timeline (add other gasses)
co2_rf_td = RadiativeForcing("co2", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
co2bio_rf_td = RadiativeForcing("co2_biogenic", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
ch4_rf_td = RadiativeForcing("ch4", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
ch4_fossil_rf_td = RadiativeForcing("ch4_fossil", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
n2o_rf_td = RadiativeForcing("n2o", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
sf6_rf_td = RadiativeForcing("sf6", np.array((1.,)), np.array((0,),dtype=('timedelta64[Y]')), 'Y', 1000)
