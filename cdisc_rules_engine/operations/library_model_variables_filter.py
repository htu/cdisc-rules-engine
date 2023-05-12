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
        if key_name and key_value:
            variable_role = VariableRoles[key_value.upper()]
        else:
            variable_role = None

        # get model details from cache
        cache_key: str = get_standard_details_cache_key(
            self.params.standard, self.params.standard_version
        )


        standard_details: dict = self.cache.get(cache_key) or {}
        model = standard_details.get("_links", {}).get("model")
        model_type, model_version = self._get_model_type_and_version(model)
        model_cache_key = get_model_details_cache_key(model_type, model_version)
        model_details = self.cache.get(model_cache_key) or {}
        domain_details = self._get_model_domain_metadata(model_details, domain, key_name, key_value)
    
        v_stp = 2.0

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
            # Domain found in the model
            class_name = convert_library_class_name_to_ct_class(
                domain_details["_links"]["parentClass"]["title"]
            )
            class_details = self._get_class_metadata(model_details, class_name)
            variables_metadata = domain_details.get("datasetVariables", [])
            variables_metadata.sort(key=lambda item: item["ordinal"])
        else:
            # Domain not found in the model. Detect class name from data
            class_name = self.data_service.get_dataset_class(
                dataframe, self.params.dataset_path, self.params.datasets
            )
            class_name = convert_library_class_name_to_ct_class(class_name)
            class_details = self._get_class_metadata(model_details, class_name)
        
        echo_msg(v_prg,2.09, class_name, 1)
        echo_msg(v_prg,2.10, class_details, 1)
        
        
        if class_name in DETECTABLE_CLASSES:
            (
                identifiers_metadata,
                variables_metadata,
                timing_metadata,
            ) = self.get_allowed_class_variables(model_details, class_details)
            # Identifiers are added to the beginning and Timing to the end
            if identifiers_metadata:
                variables_metadata = identifiers_metadata + variables_metadata
            if timing_metadata:
                variables_metadata = variables_metadata + timing_metadata
        
        echo_msg(v_prg, 2.11, "Variable Metadata\n-----------------------------",1)
        echo_msg(v_prg, 2.12, identifiers_metadata, 1)
        echo_msg(v_prg, 2.13, variables_metadata, 1)
        echo_msg(v_prg, 2.14, timing_metadata, 1)



        # variables_metadata = [var for var in domain_details.get("datasetVariables", []) 
        #                       if (not variable_role or var.get("role") == variable_role.value)]

        return variables_metadata

    def _get_model_domain_metadata(self, model_details, domain_name, key_name, key_value) -> Tuple:
        # Get domain metadata from model
        domain_details: Optional[dict] = search_in_list_of_dicts(
            model_details.get("datasets", []), lambda item: item["name"] == domain_name
        )
        v_prg = f"get_model_domain_metadata"
        v_stp = 1.1
        echo_msg(v_prg, 3.1, "Variable Metadata\n-----------------------------",1)
        echo_msg(v_prg, 3.2, domain_details, 1)

        return domain_details

    def echo2file(self, v_prg, v_stp, title: str, obj: Any, output_file: str):
        m1 = f"{title}({type(obj)})"
        lb_devider = "-" * (len(m1))
        with open(output_file, "a") as f:
            f.write(f"{m1}\n{lb_devider}\n")
            echo_msg(v_prg, v_stp, obj, 1 )
            f.write("\n\n")


    def echo_to_file(self, output_file: str, *args: Any) -> None:
        # with open(output_file, "w") as f:
        #      f.write("-" * 50 + "\n")
        for i, args in enumerate(args):
            label = args[0]
            arg = args[1]
            self.echo2file("Echo to File", i, label, arg, output_file)

    @staticmethod
    def _replace_variable_wildcards(variables_metadata, domain):
        return [var["name"].replace("--", domain) for var in variables_metadata]
