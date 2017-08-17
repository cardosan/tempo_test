# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division
from eight import *
from bw2data import methods
from .dynamic_lca import DynamicLCA
from .timeline import load_dLCI
from .dynamic_ia_methods import dynamic_methods
import glob, os
import tarfile
import warnings
try:
    from bw2data import calculation_setups
except ImportError:
    calculation_setups = None
try:
    from bw2data import dynamic_calculation_setups
except ImportError:
    dynamic_calculation_setups = None
    

#TO MAKE IT WORK REMEMBER TO ADD THIS TO BW2DATA.META AND ACCORDINGLY CHANGE ALSO THE __init___ FILE OF BW2DATA
#~@python_2_unicode_compatible
#~class DynamicCalculationSetups(PickledDict):
    #~"""A dictionary for Dynamic calculation setups.
#~
    #~Keys:
    #~* `inv`: List of functional units, e.g. ``[{(key): amount}, {(key): amount}]``
    #~* `ia`: Dictionary of orst case LCIA method and the relative dynamic LCIA method, e.g. `` [{dLCIA_method_1_worstcase:dLCIA_method_1 , dLCIA_method_2_worstcase:dLCIA_method_2}]``.
#~
    #~"""
    #~filename = "dynamicsetups.pickle"


class MultiDynamicLCA(object):
    """Wrapper class for performing dynamic LCI or LCIA with many functional units and IA methods.
    When performing LCA using dynamic LCIA need to pass ``IA='dynamic'`` and a ``dynamic_calculation_setups`` name as ``cs_name`` while when using static LCIA  need ``IA='static'`` and ``calculation_setups`` name again as ``cs_name``.
    
    Args:
        * *cs_name* (string): name of the ``dynamic_calculation_setups`` (when ``IA='dynamic'``) or ``calculation_setup`` (when ``IA='static'``).
        * *IA* (string,default=`static`): if a `static` or a `dynamic` IA will be used.
        * *by_process* (Boolean,default=False): if True return results of LCIA by single process.
        * *dLCA_kwargs* (dict): optional arguments to pass to the class `DynamicLCA` (passed as {argument_name:value} ).
        * *IA_kwargs* (dict): optional arguments for the methods characterize_dynamic and/or characterize_static (passed as {argument_name:value} ).
    """
    
    def __init__(self, cs_name,IA='static',by_process=False,dLCA_kwargs={},IA_kwargs={}):
        
        assert IA in ['static','dynamic'],"IA must be `static` or `dynamic`" 
         
        if IA=='static':
            #check if dynamic_calculation_setups exist
            if not calculation_setups:
                raise ImportError
            assert cs_name in calculation_setups
            try:
                cs = calculation_setups[cs_name]
            except KeyError:
                raise ValueError(
                    "{} is not a known `calculation_setup`.".format(cs_name)
                )   
            #check if methods passed are registered
            self.methods = cs['ia']
            assert set(self.methods).issubset(methods.list), "one of the methods passed does not exist"
            
        if IA=='dynamic':
            #check if dynamic_calculation_setups exist
            if not dynamic_calculation_setups:
                raise ImportError
            assert cs_name in dynamic_calculation_setups
            try:
                cs = dynamic_calculation_setups[cs_name]
            except KeyError:
                raise ValueError(
                    "{} is not a known `dynamic_calculation_setup`.".format(cs_name)
                )
            #check if dynamic methods passed are registered and in correct format
            self.methods = cs['ia']
            assert type(self.methods) is dict,'with dynamic IA you need as IA you need to have a dictionary in the form dynamic_IA:dynamic_IA_worst-case'
            assert set(self.methods.keys()).issubset(methods.list), "one of the dynamic IA passed does not exist"
            assert set(self.methods.values()).issubset(dynamic_methods.list), "one of the dynamic_IA_worst-case passed does not exist"
        
        self.cs_name=cs_name
        self.IA=IA
        self.func_units = cs['inv']
        self.dLCA_kwargs=dLCA_kwargs
        self.IA_kwargs=IA_kwargs
        self.by_process=by_process
            
        
    def multi_lca(self,return_dataframe=False):
        """Method for performing multiple dynamic LCA calculations (both LCI and LCIA) with many functional units and LCIA methods.
        It creates `self.dlca_results`, which is a dictionary with keys=[functional_unit:method] and values = [years,impacts].
        
        If ``to_dataframe=True`` returns the results in the form of a pandas dataframe
        Args:
        * *to_dataframe* (Boolean, default=False): if to return the results in pandas dataframe format

        """
    
        self.dlca_results = {}
                
        #do not do anything fency for now, just loop over fu and ia and run DLCA
        for fu in self.func_units:
            if self.IA=='static':
                for met in self.methods:
                    dynlca = DynamicLCA(fu,met,**self.dLCA_kwargs).calculate()
                    if self.by_process:
                        res_proc=dynlca.characterize_static_by_process(met,self.IA_kwargs)
                        self.dlca_results.update({(list(fu.keys())[0],list(fu.values())[0],met,prod):res[0] for (prod, res) in res_proc.items()})
                    else:
                        yr,imp=dynlca.characterize_static(met,**self.IA_kwargs)
                        self.dlca_results[(list(fu.keys())[0],list(fu.values())[0],met)]=[yr,imp]

            else:
                for wc,dyn in self.methods.items():
                    dynlca = DynamicLCA(fu,wc,**self.dLCA_kwargs).calculate()
                    if self.by_process:
                        res_proc=dynlca.characterize_dynamic_by_process(dyn,self.IA_kwargs)
                        self.dlca_results.update({(list(fu.keys())[0],list(fu.values())[0],wc,dyn,prod):res[0] for (prod, res) in res_proc.items()})
                    else:
                        yr,imp=dynlca.characterize_dynamic(dyn,**self.IA_kwargs)
                        self.dlca_results[(list(fu.keys())[0],list(fu.values())[0],wc,dyn)]=[yr,imp]
        if return_dataframe:
            return self.to_dataframe()
        
        
    def to_dataframe(self,folderpath=None,transpose=True):
        """
        Put the results of `multi_lca` in a pandas dataframe.
        When `transpose=True` columns are FU keys, FU amount, IA and years. When a `filepath_excel` is passed it saves the file as excel file
        
    Args:
        * *transpose* (Boolean,default=True): If to transpose the df with columns as FU keys, FU amount, IA and years.
        * *export* (Boolean,default=False): If to export the dataframe as an xlsx file
        * *folderpath* (string,default=`None`): If a folderpath is provided export the dataframe as an xlsx file
    Returns:
        pandas.Dataframe with the name of the calculation setup and the IA e.g``my_calculation_setups_dynamic``.
        """
        try:
         import pandas as pd
        except ImportError:
            print ('need to have pandas installed')
        assert hasattr(self, "dlca_results"), "Must run multi_lca first"

        #convert dictionary to pandas df (convert cols to string otherwise sometimes gives error when exporting)
        df=pd.DataFrame({tuple(str(y) for y in k):pd.Series(v[1], index=v[0]) for (k,v) in self.dlca_results.items()})# if len(v[0])>0})
        
        #~df.index=df.index.map(int)
        df.index=df.index.astype(int)#to have int in x axis
        
        # # this is to add missing years....to finalize, need to make beaviour correct depending on if it is cumulative or not and check if this is right position to put
        # fill='ffill' if a=1 else None
        # df=df.reindex(range(df.index.min(),df.index.max()),method=fill)
        
        #create columns' name dependng on the type of analysis
        cols=['FU_key','FU_amount','method'] if self.IA=='static' else ['FU_key','FU_amount','worstcase_method','dynamic_method']
        if self.by_process:
            cols+=['process']
        df.columns.names=cols
        
        if transpose:
            df=df.T
        #as it is now export multicolumns or indexes, and nan as empty, check if it is what we want
        if folderpath:
            os.makedirs(folderpath or '.', exist_ok=True) #create folder if not existing yet see  https://stackoverflow.com/a/12517490/4929813     
            xls_path=os.path.join(folderpath or '.','{}_{}{}{}.xlsx'.format(self.cs_name,self.IA,'_T' if transpose else '','_byproc' if self.by_process else ''))  
            df.to_excel(xls_path)            
        return df
            
            
    def save_multi_lci(self,folderpath=None):
        """Method for performing multiple dynamic LCI with many functional units and worst case LCIA methods and save their timelines using ``bw2temporalis.DynamicLCA.save_dLCI``. Usefull when LCA for the same FU need to be performed many time and want to avoid redoing every time also the LCI.
        
        It doesn't return anything but saves all the results in a folder with name ``calculationssetupsname_IA``. The results are bw2lci files with name in the form of `FU key_FU amount` in the passed `folderpath` (or current folder if not passed)
        
        Args:
            * *folderpath* (string,default=None): folder where to save the results. default is current current directory
        """
        wc_methods=self.methods if self.IA=='static' else self.methods.keys()
        
        folder_cs=os.path.join(folderpath or '.','{}_{}'.format(self.cs_name,self.IA))

        #do not do anything fency for now, just loop fu and ia and run DLCA
        for fu in self.func_units:
            for met in wc_methods:
                dynlca = DynamicLCA(fu,met,**self.dLCA_kwargs)
                tl=dynlca.calculate()
                dynlca.save_dLCI(folder_cs)
        
        #save all to tarfile
        #open tar file
        #~os.makedirs(folderpath or '.', exist_ok=True) #create folder if not existing yet see  https://stackoverflow.com/a/12517490/4929813     
        #~tl_path=os.path.join(folderpath or '.','{}_{}.tar.gz'.format(self.cs_name,self.IA))
        #~archive = tarfile.open(tl_path.format(self.cs_name), "w|gz")
        #~for files in glob.glob(os.path.join(folderpath,'*.bw2lci')):
            #~archive.add(files, arcname='{}_{}.tar.gz'.format(self.cs_name,self.IA))
        #~archive.close()
 #~

           
    def multi_lcia_from_saved_LCI(self,folderpath,return_dataframe=False):
        """Method for performing multiple dynamic LCIA using already performed and saved dynamic LCI as results of ``save_multi_lci``. Usefull when LCIA for the same FU need to be performed many time and want to avoid redoing every time also the LCI.
        
        It creates `self.dlca_results`, which is a dictionary with keys=[functional_unit:method] and values = [years,impacts].
        If ``to_dataframe=True`` returns the results in the form of a pandas dataframe     
           
        Args:
            * *folderpath* (string): folder where the ``bw2lci`` files are saved. It must have the name in the form of ``calculationssetupsname_IA`` otherwise an error is  returned
            * *to_dataframe* (Boolean, default=False): if to return the results in pandas dataframe format

        """   
        
        #TODO
        #CHECK IF LENGHT FILE IN FOLDER IS THE SAME OF THE CALCULATIONS SETUP
            
        files=glob.glob(os.path.join(folderpath,'*.bw2lci'))
        assert os.path.isdir(folderpath),'folderpath passed does not exists'
        assert(any(files)),'No bw2lci files in the passed folder'
        
        if os.path.basename(folderpath)!='{}_{}'.format(self.cs_name,self.IA):
            warnings.warn("Loaded results of a calculationas setup that is different from the one instanciated. This might bring to unexpected results.")   
                 
        if len(self.func_units)*len(self.methods) != len(files):
            warnings.warn("Number of file in the folder is {} while for the calculations setups passed should be (). Might have different results from what is expected.".format(len(files),len(self.func_units)*len(self.methods)))
                
        self.dlca_results = {}
        
        for lci_path in files:
            lci=load_dLCI(lci_path)
            if self.IA=='static':
                if self.by_process:
                    res_proc=lci['timeline'].characterize_static_by_process(lci['wc_method'],self.IA_kwargs)
                    self.dlca_results.update({(list(lci['demand'].keys())[0],list(lci['demand'].values())[0],lci['wc_method'],prod):res[0] for (prod, res) in res_proc.items()})
                else:
                    yr,imp=lci['timeline'].characterize_static(lci['wc_method'],**self.IA_kwargs)
                    self.dlca_results[(list(lci['demand'].keys())[0],list(lci['demand'].values())[0],lci['wc_method'])]=[yr,imp]
            else:
                if self.by_process:
                    res_proc=lci['timeline'].characterize_dynamic_by_process(self.methods[lci['wc_method']],self.IA_kwargs)
                    self.dlca_results.update({(list(lci['demand'].keys())[0],list(lci['demand'].values())[0],lci['wc_method'],self.methods[lci['wc_method']],prod):res[0] for (prod, res) in res_proc.items()})
                else:
                    yr,imp=lci['timeline'].characterize_dynamic(self.methods[lci['wc_method']],**self.IA_kwargs)
                    self.dlca_results[(list(lci['demand'].keys())[0],list(lci['demand'].values())[0],lci['wc_method'],self.methods[lci['wc_method']])] = [yr,imp]
        if return_dataframe:
            return self.to_dataframe()
