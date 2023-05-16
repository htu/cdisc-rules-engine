# python -m pytest tests/unit/test_operations/test_library_model_variables_filter.py

import os 
import pandas as pd
import pytest
import json
import requests
from rulebuilder.echo_msg import echo_msg

from typing import List

from cdisc_rules_engine.constants.classes import (
    GENERAL_OBSERVATIONS_CLASS,
    FINDINGS,
    FINDINGS_ABOUT,
)
from cdisc_rules_engine.enums.variable_roles import VariableRoles
from cdisc_rules_engine.models.operation_params import OperationParams
from cdisc_rules_engine.operations.library_model_variables_filter import (
    LibraryModelVariablesFilter,
)
from cdisc_rules_engine.services.cache import InMemoryCacheService
from cdisc_rules_engine.services.data_services import LocalDataService
from cdisc_rules_engine.utilities.utils import (
    get_standard_details_cache_key,
    get_model_details_cache_key,
)


@pytest.mark.parametrize(
    "model_metadata, standard_metadata",
    [
        (
            {
                "datasets": [
                    {
                        "_links": {"parentClass": {"title": "Events"}},
                        "name": "AE",
                        "datasetVariables": [
                            {
                                "name": "AETERM",
                                "ordinal": 4,
                            },
                            {
                                "name": "AESEQ",
                                "ordinal": 3,
                            },
                        ],
                    }
                ],
                "classes": [
                    {
                        "name": "Events",
                        "label": "Events",
                        "classVariables": [
                            {"name": "--TERM", "ordinal": 1},
                            {"name": "--SEQ", "ordinal": 2},
                        ],
                    },
                    {
                        "name": GENERAL_OBSERVATIONS_CLASS,
                        "label": GENERAL_OBSERVATIONS_CLASS,
                        "classVariables": [
                            {
                                "name": "DOMAIN",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 2,
                            },
                            {
                                "name": "STUDYID",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 1,
                            },
                            {
                                "name": "TIMING_VAR",
                                "role": VariableRoles.TIMING.value,
                                "ordinal": 33,
                            },
                        ],
                    },
                ],
            },
            {
                "_links": {"model": {"href": "/mdr/sdtm/1-5"}},
                "classes": [
                    {
                        "name": "Events",
                        "datasets": [
                            {
                                "name": "AE",
                                "label": "Adverse Events",
                                "datasetVariables": [
                                    {"name": "AETEST", "ordinal": 1},
                                    {"name": "AENEW", "ordinal": 2},
                                ],
                            }
                        ],
                    }
                ],
            },
        )
    ],
)
def test_get_model_variables_filter(
    operation_params: OperationParams, model_metadata: dict, standard_metadata: dict
):
    """
    Unit test for DataProcessor.get_column_order_from_library.
    Mocks cache call to return metadata.
    """

    def find_objects(obj, domain:str=None, key:str="role", val:str=None):
        v_prg="find_objects"
        results = []
        if isinstance(obj, dict):
            dom = obj.get("_links",{}).get("self",{}).get("href")
            dm1 = f"/datasets/{domain}/"
            v1 = obj.get(key)
            echo_msg(v_prg, 1.111, f"{v1}={val},{dm1}={dom}?")
            if v1 == val and dm1 in dom:
                results.append(obj)
            for value in obj.values():
                results += find_objects(value, domain, key, val)
        elif isinstance(obj, list):
            for item in obj:
                results += find_objects(item, domain, key, val)
        return results

    # Open the JSON file
    # https://github.com/cdisc-org/cdisc-library-src-files/blob/master/cdisc-json/products/data-tabulation/
    ifn1 = "./dist/sdtm-2-0.json"
    ifn2 = "./dist/sdtmig-3-4.json"
    with open(ifn1) as f:
        # Load the JSON data into a Python object
        dat1 = json.load(f)
    timing1_objs = find_objects(dat1,'AE', 'role', 'Timing')
    with open(ifn2) as f:
        # Load the JSON data into a Python object
        dat2 = json.load(f)
    timing2_objs = find_objects(dat2,'AE', 'role', 'Timing')

    # Access the data in the object
    # print(data.keys())

    # operation_params.dataframe = pd.DataFrame.from_dict(
    #     {
    #         "STUDYID": [
    #             "TEST_STUDY",
    #             "TEST_STUDY",
    #             "TEST_STUDY",
    #         ],
    #         "AETERM": [
    #             "test",
    #             "test",
    #             "test",
    #         ],
    #     }
    # )
    operation_params.dataframe = dat2
    operation_params.domain = "AE"
    operation_params.standard = "sdtmig"
    operation_params.standard_version = "3-4"
    operation_params.key_name = "role"
    operation_params.key_value = "Timing"

    v_prg = f"test_get_model_variables_filter"
    v_stp = 1.0
    os.environ["write2log"] = "1"
    os.environ["g_msg_lvl"] = "2"
    os.environ["g_log_lvl"] = "9"
    os.environ["log_fn"] = "test01.txt"

    if timing1_objs is not None: 
        echo_msg(v_prg,0.011, timing1_objs, 1)
    if timing2_objs is not None:
        echo_msg(v_prg, 0.012, timing2_objs, 1)
        return

    echo_msg(v_prg,0.01, operation_params, 10)


    # save model metadata to cache
    cache = InMemoryCacheService.get_instance()
    echo_msg(v_prg,0.02, cache, 1)
    cache.add(
        get_standard_details_cache_key(
            operation_params.standard, operation_params.standard_version
        ),
        standard_metadata,
    )
    echo_msg(v_prg,0.03, cache, 1)
    cache.add(get_model_details_cache_key("sdtm", "1-5"), model_metadata)
    echo_msg(v_prg,0.04, cache, 1)


    # execute operation
    data_service = LocalDataService.get_instance(cache_service=cache)
    echo_msg(v_prg,0.05, data_service, 1)

    operation = LibraryModelVariablesFilter(
        operation_params, operation_params.dataframe, cache, data_service
    )
    echo_msg(v_prg,0.06, operation, 1)

    result: pd.DataFrame = operation.execute()
    echo_msg(v_prg,0.07, result, 1)


    # operation.echo_to_file("test01.txt", 
    #     ["Operatioin Parameters", operation_params],
    #     ["Cache",cache], 
    #     ["Data Service", data_service],
    #     ["Operation", operation],
    #     ["Result", result]  
    #     )


    variables: List[str] = [
        "STUDYID",
        "DOMAIN",
        "AETERM",
        "AESEQ",
        "TIMING_VAR",
    ]
    expected: pd.Series = pd.Series(
        [
            variables,
            variables,
            variables,
        ]
    )
    assert result[operation_params.operation_id].equals(expected)


# @pytest.mark.parametrize(
#     "model_metadata, standard_metadata",
#     [
#         (
#             {
#                 "datasets": [
#                     {
#                         "_links": {"parentClass": {"title": FINDINGS_ABOUT}},
#                         "name": "NOTTHESAME",
#                         "datasetVariables": [
#                             {
#                                 "name": "AETERM",
#                                 "ordinal": 4,
#                             },
#                             {
#                                 "name": "AESEQ",
#                                 "ordinal": 3,
#                             },
#                         ],
#                     }
#                 ],
#                 "classes": [
#                     {
#                         "name": FINDINGS_ABOUT,
#                         "label": FINDINGS_ABOUT,
#                         "classVariables": [
#                             {"name": "--OBJ", "ordinal": 1},
#                         ],
#                     },
#                     {
#                         "name": FINDINGS,
#                         "label": FINDINGS,
#                         "classVariables": [
#                             {"name": "--VAR1", "ordinal": 1},
#                             {"name": "--TEST", "ordinal": 2},
#                             {"name": "--VAR2", "ordinal": 3},
#                         ],
#                     },
#                     {
#                         "name": GENERAL_OBSERVATIONS_CLASS,
#                         "label": GENERAL_OBSERVATIONS_CLASS,
#                         "classVariables": [
#                             {
#                                 "name": "DOMAIN",
#                                 "role": VariableRoles.IDENTIFIER.value,
#                                 "ordinal": 2,
#                             },
#                             {
#                                 "name": "STUDYID",
#                                 "role": VariableRoles.IDENTIFIER.value,
#                                 "ordinal": 1,
#                             },
#                             {
#                                 "name": "TIMING_VAR",
#                                 "role": VariableRoles.TIMING.value,
#                                 "ordinal": 33,
#                             },
#                         ],
#                     },
#                 ],
#             },
#             {
#                 "_links": {"model": {"href": "/mdr/sdtm/1-5"}},
#                 "classes": [
#                     {
#                         "name": FINDINGS_ABOUT,
#                         "datasets": [
#                             {
#                                 "name": "AE",
#                                 "label": "Adverse Events",
#                                 "datasetVariables": [
#                                     {"name": "AETEST", "ordinal": 1},
#                                     {"name": "AENEW", "ordinal": 2},
#                                 ],
#                             }
#                         ],
#                     }
#                 ],
#             },
#         )
#     ],
# )
# def test_get_findings_class_column_order_from_library(
#     operation_params: OperationParams, model_metadata: dict, standard_metadata: dict
# ):
#     """
#     Unit test for DataProcessor.get_column_order_from_library.
#     Mocks cache call to return metadata.
#     """
#     operation_params.dataframe = pd.DataFrame.from_dict(
#         {
#             "STUDYID": [
#                 "TEST_STUDY",
#                 "TEST_STUDY",
#                 "TEST_STUDY",
#             ],
#             "DOMAIN": ["AE", "AE", "AE"],
#             "AEOBJ": [
#                 "test",
#                 "test",
#                 "test",
#             ],
#             "AETESTCD": ["test", "test", "test"],
#         }
#     )
#     operation_params.domain = "AE"
#     operation_params.standard = "sdtmig"
#     operation_params.standard_version = "3-4"

#     # save model metadata to cache
#     cache = InMemoryCacheService.get_instance()
#     cache.add(
#         get_standard_details_cache_key(
#             operation_params.standard, operation_params.standard_version
#         ),
#         standard_metadata,
#     )
#     cache.add(get_model_details_cache_key("sdtm", "1-5"), model_metadata)

#     # execute operation
#     data_service = LocalDataService.get_instance(cache_service=cache)
#     operation = LibraryModelVariablesFilter(
#         operation_params, operation_params.dataframe, cache, data_service
#     )
#     result: pd.DataFrame = operation.execute()
#     variables: List[str] = [
#         "STUDYID",
#         "DOMAIN",
#         "AEVAR1",
#         "AETEST",
#         "AEOBJ",
#         "AEVAR2",
#         "TIMING_VAR",
#     ]
#     expected: pd.Series = pd.Series(
#         [
#             variables,
#             variables,
#             variables,
#         ]
#     )
#     assert result[operation_params.operation_id].equals(expected)
