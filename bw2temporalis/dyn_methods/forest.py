# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from bw2data import Database,config,projects
# 
# ##To make get_forest_keys() work the method downstream_bio() below need to be added to bw2data.backends.peewee.proxies
    # def downstream_bio(self):
        # return Exchanges(
            # self.key,
            # ##kind="technosphere",
            # reverse=True
        # )
        # 
        
def get_static_forest_keys():
    """get the key of the forest sequestation processes in the set `forest`.
    Needed to consider forest sequestation dynamic in already installed dbs that 
    are static.
    When unit processes from other databases need to be evaluated dynamically is enough to add their name 
    to the set set `forest` inside the function.
    
    #Wrapped into a function otherwise it points to the default project if temporalis
    is imported before the current project is set """
    #they are all underbark, check if the bark CO2 is considered or not...if needed
    
    
    ei_22 = ["hardwood, Scandinavian, standing, under bark, in forest",
    "hardwood, standing, under bark, in forest",
    "eucalyptus ssp., standing, under bark, u=50%, in plantation",
    "meranti, standing, under bark, u=70%, in rainforest",
    "softwood, standing, under bark, in forest",
    "azobe (SFM), standing, under bark, in rain forest",
    "paraná pine, standing, under bark, in rain forest",
    "softwood, Scandinavian, standing, under bark, in forest"]

    ei_32_33 = ["softwood forestry, paraná pine, sustainable forest management",
     "hardwood forestry, mixed species, sustainable forest management",
     "hardwood forestry, beech, sustainable forest management",
     "softwood forestry, spruce, sustainable forest management",
     "hardwood forestry, meranti, sustainable forest management",
     "hardwood forestry, azobe, sustainable forest management",
     "softwood forestry, pine, sustainable forest management",
     #"import of roundwood, azobe from sustainable forest management, CM, debarked", # no
     #"import of roundwood, meranti from sustainable forest management, MY, debarked", # no
     "softwood forestry, mixed species, sustainable forest management",
     "hardwood forestry, oak, sustainable forest management",
     "hardwood forestry, birch, sustainable forest management",
     "hardwood forestry, eucalyptus ssp., sustainable forest management"]
     
    forest = set( ei_22 + ei_32_33 )
    projects.set_current("{}".format(projects.current)) #need to do this otherwise uses default project if imported before setting the proj
    db = Database(config.biosphere)
    
    #search 'Carbon dioxide, in air' sequestered from processes in `forest` (empty set when biopshere not existing like in tests)
    return set() if not db else \
           set([x.output.key for x in db.get('cc6a1abb-b123-4ca6-8f16-38209df609be').downstream_bio() if x.output['name'] in forest])
