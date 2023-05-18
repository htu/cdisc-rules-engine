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
                                "name": "USUBJID",
                                "ordinal": 2,
                            },
                            {
                                "name": "AESEQ",
                                "ordinal": 3,
                            },

                            {
                                "name": "AETERM",
                                "ordinal": 4,
                            },
                            {
                                "name": "VISITNUM",
                                "ordinal": 17,
                            },
                            {
                                "name": "VISIT",
                                "ordinal": 18,
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
                                "name": "STUDYID",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 1,
                            },
                            {
                                "name": "DOMAIN",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 2,
                            },
                            {
                                "name": "USUBJID",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 3,
                            },
                            {
                                "name": "AETERM",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 4,
                            },
                            {
                                "name": "VISITNUM",
                                "role": VariableRoles.TIMING.value,
                                "ordinal": 17,
                            },
                            {
                                "name": "VISIT",
                                "role": VariableRoles.TIMING.value,
                                "ordinal": 18
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
                                    {"name": "VISITNUM", "ordinal": 3},
                                    {"name": "VISIT", "ordinal": 4},
                                ],
                            }
                        ],
                    }
                ],
            },
        )
    ],
)

def test_get_model_variables_filter1(
    operation_params: OperationParams, model_metadata: dict, standard_metadata: dict
):
    """
    Unit test for DataProcessor.get_column_order_from_library.
    Mocks cache call to return metadata.
    """
    operation_params.dataframe = pd.DataFrame.from_dict(
        {
            "STUDYID": [
                "TEST_STUDY",
                "TEST_STUDY",
                "TEST_STUDY",
            ],
            "AETERM": [
                "test",
                "test",
                "test",
            ],
        }
    )
    # operation_params.dataframe = dat2
    operation_params.domain = "AE"
    operation_params.standard = "sdtmig"
    operation_params.standard_version = "3-4"
    operation_params.key_name = "role"
    # operation_params.key_value = "Identifier"
    operation_params.key_value = "Timing"

    v_prg = f"test_get_model_variables_filter"
    v_stp = 1.0
    os.environ["write2log"] = "1"
    os.environ["g_msg_lvl"] = "2"
    os.environ["g_log_lvl"] = "9"
    os.environ["log_fn"] = "test01.txt"

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


    variables: List[str] = [
        # "STUDYID",
        # "DOMAIN",
        # "USUBJID",
        # "AETERM",
        # "AESEQ",
        "VISITNUM",
        "VISIT",
        # "TIMING_VAR",
    ]
    expected: pd.Series = pd.Series(
        [
            variables,
            variables,
            variables,
        ]
    )
    assert result[operation_params.operation_id].equals(expected)


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
                                "name": "USUBJID",
                                "ordinal": 2,
                            },
                            {
                                "name": "AESEQ",
                                "ordinal": 3,
                            },

                            {
                                "name": "AETERM",
                                "ordinal": 4,
                            },
                            {
                                "name": "VISITNUM",
                                "ordinal": 17,
                            },
                            {
                                "name": "VISIT",
                                "ordinal": 18,
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
                                "name": "STUDYID",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 1,
                            },
                            {
                                "name": "DOMAIN",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 2,
                            },
                            {
                                "name": "USUBJID",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 3,
                            },
                            {
                                "name": "AETERM",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 4,
                            },
                            {
                                "name": "VISITNUM",
                                "role": VariableRoles.TIMING.value,
                                "ordinal": 17,
                            },
                            {
                                "name": "VISIT",
                                "role": VariableRoles.TIMING.value,
                                "ordinal": 18
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
                                    {"name": "VISITNUM", "ordinal": 3},
                                    {"name": "VISIT", "ordinal": 4},
                                ],
                            }
                        ],
                    }
                ],
            },
        )
    ],
)


def test_get_model_variables_filter2(
    operation_params: OperationParams, model_metadata: dict, standard_metadata: dict
):
    """
    Unit test for DataProcessor.get_column_order_from_library.
    Mocks cache call to return metadata.
    """
    operation_params.dataframe = pd.DataFrame.from_dict(
        {
            "STUDYID": [
                "TEST_STUDY",
                "TEST_STUDY",
                "TEST_STUDY",
            ],
            "AETERM": [
                "test",
                "test",
                "test",
            ],
        }
    )
    # operation_params.dataframe = dat2
    operation_params.domain = "AE"
    operation_params.standard = "sdtmig"
    operation_params.standard_version = "3-4"
    operation_params.key_name = "role"
    operation_params.key_value = "Identifier"

    v_prg = f"test_get_model_variables_filter"
    v_stp = 1.0
    os.environ["write2log"] = "1"
    os.environ["g_msg_lvl"] = "2"
    os.environ["g_log_lvl"] = "9"
    os.environ["log_fn"] = "test01.txt"

    echo_msg(v_prg, 0.01, operation_params, 10)

    # save model metadata to cache
    cache = InMemoryCacheService.get_instance()
    echo_msg(v_prg, 0.02, cache, 1)
    cache.add(
        get_standard_details_cache_key(
            operation_params.standard, operation_params.standard_version
        ),
        standard_metadata,
    )
    echo_msg(v_prg, 0.03, cache, 1)
    cache.add(get_model_details_cache_key("sdtm", "1-5"), model_metadata)
    echo_msg(v_prg, 0.04, cache, 1)

    # execute operation
    data_service = LocalDataService.get_instance(cache_service=cache)
    echo_msg(v_prg, 0.05, data_service, 1)

    operation = LibraryModelVariablesFilter(
        operation_params, operation_params.dataframe, cache, data_service
    )
    echo_msg(v_prg, 0.06, operation, 1)

    result: pd.DataFrame = operation.execute()
    echo_msg(v_prg, 0.07, result, 1)

    variables: List[str] = [
        # "STUDYID",
        # "DOMAIN",
        "USUBJID",
        "AETERM",
        # "AESEQ",
        # "VISITNUM",
        # "VISIT",
        # "TIMING_VAR",
    ]
    expected: pd.Series = pd.Series(
        [
            variables,
            variables,
            variables,
        ]
    )
    assert result[operation_params.operation_id].equals(expected)


@pytest.mark.parametrize(
    "model_metadata, standard_metadata",
    [
        (
            {
                "datasets": [
                    {
                        "_links": {"parentClass": {"title": FINDINGS_ABOUT}},
                        "name": "NOTTHESAME",
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
                        "name": FINDINGS_ABOUT,
                        "label": FINDINGS_ABOUT,
                        "classVariables": [
                            {"name": "--OBJ", "ordinal": 1},
                            {
                                "name": "USUBJID",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 2,
                            },
                            {
                                "name": "IDVAR1",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 3,
                            },
                            {
                                "name": "TIMING_VAR1",
                                "role": VariableRoles.TIMING.value,
                                "ordinal": 31,
                            },
                            {
                                "name": "TIMING_VAR2",
                                "role": VariableRoles.TIMING.value,
                                "ordinal": 32,
                            },
                        ],
                    },
                    {
                        "name": FINDINGS,
                        "label": FINDINGS,
                        "classVariables": [
                            {"name": "--VAR1", "ordinal": 1},
                            {"name": "--TEST", "ordinal": 2},
                            {"name": "--VAR2", "ordinal": 3},
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
                        "name": FINDINGS_ABOUT,
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

def test_get_findings_class_column_order_from_library1(
    operation_params: OperationParams, model_metadata: dict, standard_metadata: dict
):
    """
    Unit test for DataProcessor.get_column_order_from_library.
    Mocks cache call to return metadata.
    """
    v_prg = "test_get_findings_class_column_order_from_library"
    os.environ["write2log"] = "1"
    os.environ["g_msg_lvl"] = "2"
    os.environ["g_log_lvl"] = "9"
    os.environ["log_fn"] = "test01.txt"

    operation_params.dataframe = pd.DataFrame.from_dict(
        {
            "STUDYID": [
                "TEST_STUDY",
                "TEST_STUDY",
                "TEST_STUDY",
            ],
            "DOMAIN": ["AE", "AE", "AE"],
            "AEOBJ": [
                "test",
                "test",
                "test",
            ],
            "AETESTCD": ["test", "test", "test"],
        }
    )
    operation_params.domain = "AE"
    operation_params.standard = "sdtmig"
    operation_params.standard_version = "3-4"
    operation_params.key_name = "role"
    # operation_params.key_value = "Identifier"
    operation_params.key_value = "Timing"

    echo_msg(v_prg, 0.01, operation_params, 1)


    # save model metadata to cache
    cache = InMemoryCacheService.get_instance()
    cache.add(
        get_standard_details_cache_key(
            operation_params.standard, operation_params.standard_version
        ),
        standard_metadata,
    )
    cache.add(get_model_details_cache_key("sdtm", "1-5"), model_metadata)

    echo_msg(v_prg, 0.02, cache, 1)

    # execute operation
    data_service = LocalDataService.get_instance(cache_service=cache)
    operation = LibraryModelVariablesFilter(
        operation_params, operation_params.dataframe, cache, data_service
    )
    echo_msg(v_prg, 0.03, data_service, 1)
    echo_msg(v_prg, 0.04, operation, 1)


    result: pd.DataFrame = operation.execute()

    echo_msg(v_prg, 0.05, result, 1)

    variables: List[str] = [
        # "STUDYID",
        # "DOMAIN",
        # "AEVAR1",
        # "AETEST",
        # "AEOBJ",
        # "AEVAR2",
        "TIMING_VAR1",
        "TIMING_VAR2",
    ]
    expected: pd.Series = pd.Series(
        [
            variables,
            variables,
            variables,
        ]
    )
    assert result[operation_params.operation_id].equals(expected)


@pytest.mark.parametrize(
    "model_metadata, standard_metadata",
    [
        (
            {
                "datasets": [
                    {
                        "_links": {"parentClass": {"title": FINDINGS_ABOUT}},
                        "name": "NOTTHESAME",
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
                        "name": FINDINGS_ABOUT,
                        "label": FINDINGS_ABOUT,
                        "classVariables": [
                            {"name": "--OBJ", "ordinal": 1},
                            {
                                "name": "USUBJID",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 2,
                            },
                            {
                                "name": "IDVAR1",
                                "role": VariableRoles.IDENTIFIER.value,
                                "ordinal": 3,
                            },
                            {
                                "name": "TIMING_VAR1",
                                "role": VariableRoles.TIMING.value,
                                "ordinal": 31,
                            },
                            {
                                "name": "TIMING_VAR2",
                                "role": VariableRoles.TIMING.value,
                                "ordinal": 32,
                            },
                        ],
                    },
                    {
                        "name": FINDINGS,
                        "label": FINDINGS,
                        "classVariables": [
                            {"name": "--VAR1", "ordinal": 1},
                            {"name": "--TEST", "ordinal": 2},
                            {"name": "--VAR2", "ordinal": 3},
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
                        "name": FINDINGS_ABOUT,
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
def test_get_findings_class_column_order_from_library2(
    operation_params: OperationParams, model_metadata: dict, standard_metadata: dict
):
    """
    Unit test for DataProcessor.get_column_order_from_library.
    Mocks cache call to return metadata.
    """
    v_prg = "test_get_findings_class_column_order_from_library"
    os.environ["write2log"] = "1"
    os.environ["g_msg_lvl"] = "2"
    os.environ["g_log_lvl"] = "9"
    os.environ["log_fn"] = "test01.txt"

    operation_params.dataframe = pd.DataFrame.from_dict(
        {
            "STUDYID": [
                "TEST_STUDY",
                "TEST_STUDY",
                "TEST_STUDY",
            ],
            "DOMAIN": ["AE", "AE", "AE"],
            "AEOBJ": [
                "test",
                "test",
                "test",
            ],
            "AETESTCD": ["test", "test", "test"],
        }
    )
    operation_params.domain = "AE"
    operation_params.standard = "sdtmig"
    operation_params.standard_version = "3-4"
    operation_params.key_name = "role"
    operation_params.key_value = "Identifier"

    echo_msg(v_prg, 0.01, operation_params, 1)

    # save model metadata to cache
    cache = InMemoryCacheService.get_instance()
    cache.add(
        get_standard_details_cache_key(
            operation_params.standard, operation_params.standard_version
        ),
        standard_metadata,
    )
    cache.add(get_model_details_cache_key("sdtm", "1-5"), model_metadata)

    echo_msg(v_prg, 0.02, cache, 1)

    # execute operation
    data_service = LocalDataService.get_instance(cache_service=cache)
    operation = LibraryModelVariablesFilter(
        operation_params, operation_params.dataframe, cache, data_service
    )
    echo_msg(v_prg, 0.03, data_service, 1)
    echo_msg(v_prg, 0.04, operation, 1)

    result: pd.DataFrame = operation.execute()

    echo_msg(v_prg, 0.05, result, 1)

    variables: List[str] = [
        # "STUDYID",
        # "DOMAIN",
        # "AEVAR1",
        # "AETEST",
        # "AEOBJ",
        # "AEVAR2",
        "USUBJID",
        "IDVAR1",
    ]
    expected: pd.Series = pd.Series(
        [
            variables,
            variables,
            variables,
        ]
    )
    assert result[operation_params.operation_id].equals(expected)
