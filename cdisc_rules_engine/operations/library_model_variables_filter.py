import copy
import json
import pandas as pd 
from typing import Any
from rulebuilder.echo_msg import echo_msg

from typing import List, Optional, Tuple

from cdisc_rules_engine.enums.variable_roles import VariableRoles

from cdisc_rules_engine.constants.classes import (
    DETECTABLE_CLASSES,
)
from cdisc_rules_engine.operations.base_operation import BaseOperation
from cdisc_rules_engine.utilities.utils import (
    get_model_details_cache_key,
    get_standard_details_cache_key,
    search_in_list_of_dicts,
    convert_library_class_name_to_ct_class,
)
from collections import OrderedDict


class LibraryModelVariablesFilter(BaseOperation):
    def _execute_operation(self):
        """
        Fetches column order for a given domain from the CDISC library.
        Returns it as a Series of lists like:
        0    ["STUDYID", "DOMAIN", ...]
        1    ["STUDYID", "DOMAIN", ...]
        2    ["STUDYID", "DOMAIN", ...]
        ...

        Length of Series is equal to the length of given dataframe.
        The lists with column names are sorted
        in accordance to "ordinal" key of library metadata.
        """
        echo_msg("_execute_operation", 1.001, self.params,1)
        echo_msg("_execute_operation", 1.002, self.params.key_name,1)
        echo_msg("_execute_operation", 1.003, self.params.key_value,1)

        return self._get_variable_names_list(self.params.domain, self.params.dataframe,
                                             self.params.key_name, self.params.key_value)
    
    
    def _get_variable_names_list(self, domain, dataframe, key_name, key_value):
        
        v_prg = f"get_variable_names_list"
        v_stp = 1.0
        v_msg = "Get variable name list..."
        echo_msg(v_prg, v_stp, v_msg,1)
        echo_msg(v_prg, 1.01, domain,1)
        echo_msg(v_prg, 1.02, dataframe,1)
        echo_msg(v_prg, 1.03, key_name,1)
        echo_msg(v_prg, 1.04, key_value,1)

        # get variables metadata from the standard model
        variables_metadata: List[
            dict
        ] = self._get_variables_metadata_from_standard_model(domain, dataframe,key_name,key_value)

        echo_msg(v_prg, 1.05, variables_metadata,1)
        
        # create a list of variable names in accordance to the "ordinal" key
        variable_names_list = self._replace_variable_wildcards(
            variables_metadata, domain
        )
        echo_msg(v_prg, 1.06, variable_names_list,1)

        r_list = list(OrderedDict.fromkeys(variable_names_list))
        echo_msg(v_prg, 1.07, r_list,1)
        return r_list
    
    def get_dataset_variables(self, metadata, domain_name, key, val):
        dataset_variables = []
        for dataset in metadata['datasets']:
            if dataset['name'] == domain_name:
                dataset_variables = dataset['datasetVariables']
                break

        class_variables = []
        for class_ in metadata['classes']:
            for var in class_['classVariables']:
                if var.get(key) == val:
                    class_variables.append(var.get("name"))

        variable_names = []
        for variable in dataset_variables:
            variable_name = variable['name']
            if variable_name in class_variables:
                variable_names.append(variable_name)

        return variable_names

    def get_dataset_component(self, datasets, dataset_name, var_list):
        dataset_component = None

        # for dataset in datasets:
        if datasets['name'] == dataset_name:
            dataset_component = copy.deepcopy(datasets)

        if dataset_component:
            dv = []
            dataset_variables = dataset_component.get('datasetVariables', [])
            for variable in dataset_variables:
                if variable.get("name") in var_list:
                    dv.append(variable)
            dataset_component["datasetVariables"] = dv

        return dataset_component

    def get_class_variables(self, metadata, class_name, key, val):
        class_variables = []
        if metadata["name"] != class_name:
            return class_variables
        for var in metadata['classVariables']:
            if var.get(key) == val:
                class_variables.append(var.get("name"))
        return class_variables

    def get_class_component(self, datasets, class_name, var_list):
        class_component = None

        # for dataset in datasets:
        if datasets['name'] != class_name:
            return class_component
        class_component = copy.deepcopy(datasets)

        if class_component:
            dv = []
            class_variables = class_component.get('classVariables', [])
            for variable in class_variables:
                if variable.get("name") in var_list:
                    dv.append(variable)
            class_component["classVariables"] = dv

        return class_component


    def _get_variables_metadata_from_standard_model(
        self, domain, dataframe, key_name, key_value
    ) -> List[dict]:
        """
        Gets variables metadata for the given class and domain from cache.
        The cache stores CDISC Library metadata.

        Return example:
        [
            {
               "label":"Study Identifier",
               "name":"STUDYID",
               "ordinal":"1",
               "role":"Identifier",
               ...
            },
            {
               "label":"Domain Abbreviation",
               "name":"DOMAIN",
               "ordinal":"2",
               "role":"Identifier"
            },
            ...
        ]
        """
        v_prg = f"get_variables_metadata_from_standard_model"
        # if key_name and key_value:
        #     variable_role = VariableRoles[key_value.upper()]
        # else:
        #     variable_role = None

        # get model details from cache
        cache_key: str = get_standard_details_cache_key(
            self.params.standard, self.params.standard_version
        )


        standard_details: dict = self.cache.get(cache_key) or {}
        model = standard_details.get("_links", {}).get("model")
        model_type, model_version = self._get_model_type_and_version(model)
        model_cache_key = get_model_details_cache_key(model_type, model_version)
        model_details = self.cache.get(model_cache_key) or {}


        echo_msg(v_prg, 2.077, model_details, 1)


        domain_details = self._get_model_domain_metadata(model_details, domain)

        echo_msg(v_prg,2.01, cache_key, 1)
        echo_msg(v_prg,2.02, standard_details, 1)
        echo_msg(v_prg,2.03, model, 1)
        echo_msg(v_prg,2.04, model_type, 1)
        echo_msg(v_prg,2.05, model_version, 1)
        echo_msg(v_prg,2.06, model_cache_key, 1)
        echo_msg(v_prg,2.07, model_details, 1)
        echo_msg(v_prg,2.08, domain_details, 1)
        
        variables_metadata = []

        if domain_details:
            var_list = self.get_dataset_variables(
                model_details, domain, key_name, key_value)
            echo_msg(v_prg, 2.11, f"Domain Name: {domain}", 1)
            echo_msg(v_prg, 2.12, model_details, 1)
            echo_msg(v_prg, 2.13, var_list, 1)
            r_domain_details = self.get_dataset_component(
                domain_details, domain, var_list)

            # Domain found in the model
            class_name = convert_library_class_name_to_ct_class(
                r_domain_details["_links"]["parentClass"]["title"]
            )
            class_details = self._get_class_metadata(model_details, class_name)
            variables_metadata = r_domain_details.get("datasetVariables", [])
            variables_metadata.sort(key=lambda item: item["ordinal"])
            return variables_metadata
        else:
            # Domain not found in the model. Detect class name from data
            class_name = self.data_service.get_dataset_class(
                dataframe, self.params.dataset_path, self.params.datasets
            )
            class_name = convert_library_class_name_to_ct_class(class_name)
            class_details = self._get_class_metadata(model_details, class_name)

            echo_msg(v_prg, 2.21, f"Class Name: {class_name}", 1)
            echo_msg(v_prg, 2.22, class_details, 1)

            var_list = self.get_class_variables(
                class_details, class_name, key_name, key_value)
            
            echo_msg(v_prg, 2.23, var_list, 1)
            r_class_details = self.get_class_component(
                class_details, class_name, var_list)

            echo_msg(v_prg, 2.24, r_class_details, 1)
            class_metadata = r_class_details.get("classVariables", [])
            class_metadata.sort(key=lambda item: item["ordinal"])
            echo_msg(v_prg, 2.25, class_metadata, 1)


        
        echo_msg(v_prg, 2.33, variables_metadata, 1)
        
        
        # if class_name in DETECTABLE_CLASSES:
        #     (
        #         identifiers_metadata,
        #         variables_metadata,
        #         timing_metadata,
        #     ) = self.get_allowed_class_variables(model_details, class_details)
        #     if not domain_details: 
        #         # Identifiers are added to the beginning and Timing to the end
        #         if identifiers_metadata:
        #             variables_metadata = identifiers_metadata + variables_metadata
        #         if timing_metadata:
        #             variables_metadata = variables_metadata + timing_metadata
        
        echo_msg(v_prg, 2.12, "Variable Metadata\n-----------------------------",1)
        # echo_msg(v_prg, 2.13, identifiers_metadata, 1)
        # echo_msg(v_prg, 2.14, timing_metadata, 1)
        echo_msg(v_prg, 2.15, variables_metadata, 1)

        return class_metadata



    def _get_model_domain_metadata(self, model_details, domain_name) -> Tuple:

        v_prg = f"get_model_domain_metadata"
        echo_msg(v_prg, 3.1, model_details, 1)

        
        echo_msg(v_prg, 3.11, f"Domain Name: {domain_name}", 1)
        echo_msg(v_prg, 3.12, model_details, 1)

        # Get domain metadata from model
        domain_details: Optional[dict] = search_in_list_of_dicts(
            model_details.get(
                "datasets", []), lambda item: item["name"] == domain_name 
        )
        
        echo_msg(v_prg, 3.2, domain_details, 1)

        return domain_details

    @staticmethod
    def _replace_variable_wildcards(variables_metadata, domain):
        return [var["name"].replace("--", domain) for var in variables_metadata]
