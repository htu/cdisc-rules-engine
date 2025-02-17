from typing import List
from unittest.mock import patch

import pandas as pd
import pytest
from cdisc_rules_engine.services.cache.in_memory_cache_service import (
    InMemoryCacheService,
)
from cdisc_rules_engine.utilities.data_processor import DataProcessor


@pytest.mark.parametrize(
    "data",
    [
        (
            pd.DataFrame.from_dict(
                {
                    "RDOMAIN": ["AE", "EC", "EC", "AE"],
                    "IDVAR": ["AESEQ", "ECSEQ", "ECSEQ", "AESEQ"],
                    "IDVARVAL": [1, 2, 1, 3],
                }
            )
        ),
        (pd.DataFrame.from_dict({"RSUBJID": [1, 4, 6000]})),
    ],
)
def test_preprocess_relationship_dataset(data):
    datasets: List[dict] = [
        {
            "domain": "AE",
            "filename": "ae.xpt",
        },
        {
            "domain": "EC",
            "filename": "ec.xpt",
        },
        {
            "domain": "SUPP",
            "filename": "supp.xpt",
        },
        {
            "domain": "DM",
            "filename": "dm.xpt",
        },
    ]
    ae = pd.DataFrame.from_dict(
        {
            "AESTDY": [4, 5, 6],
            "STUDYID": [101, 201, 300],
            "AESEQ": [1, 2, 3],
        }
    )
    ec = pd.DataFrame.from_dict(
        {
            "ECSTDY": [500, 4],
            "STUDYID": [201, 101],
            "ECSEQ": [2, 1],
        }
    )
    dm = pd.DataFrame.from_dict({"USUBJID": [1, 2, 3, 4, 5, 6000]})
    path_to_dataset_map: dict = {
        "path/ae.xpt": ae,
        "path/ec.xpt": ec,
        "path/dm.xpt": dm,
        "path/data.xpt": data,
    }
    with patch(
        "cdisc_rules_engine.services.data_services.LocalDataService.get_dataset",
        side_effect=lambda dataset_name: path_to_dataset_map[dataset_name],
    ):
        data_processor = DataProcessor(cache=InMemoryCacheService())
        reference_data = data_processor.preprocess_relationship_dataset(
            "path", data, datasets
        )
        if "IDVAR" in data:
            idvars = data["IDVAR"]
            domains = data["RDOMAIN"]
            for i, idvar in enumerate(idvars):
                assert idvar in reference_data[domains[i]]
        elif "RSUBJID" in data:
            assert "RSUBJID" in reference_data["DM"]
            assert pd.np.array_equal(reference_data["DM"]["RSUBJID"], dm["USUBJID"])


def test_filter_dataset_columns_by_metadata_and_rule():
    """
    Unit test for DataProcessor.filter_dataset_columns_by_metadata_and_rule function.
    """
    columns: List[str] = ["STUDYID", "DOMAIN", "AESEV", "AESER"]
    define_metadata: List[dict] = [
        {
            "define_variable_name": "AESEV",
            "define_variable_origin_type": "Collected",
        },
        {
            "define_variable_name": "AESER",
            "define_variable_origin_type": "Collected",
        },
    ]
    library_metadata: dict = {
        "STUDYID": {
            "core": "Exp",
        },
        "DOMAIN": {
            "core": "Exp",
        },
        "AESEV": {
            "core": "Perm",
        },
        "AESER": {
            "core": "Perm",
        },
        "AESEQ": {
            "core": "Exp",
        },
    }
    rule: dict = {
        "variable_origin_type": "Collected",
        "variable_core_status": "Perm",
    }
    filtered_columns: List[
        str
    ] = DataProcessor.filter_dataset_columns_by_metadata_and_rule(
        columns, define_metadata, library_metadata, rule
    )
    assert filtered_columns == [
        "AESEV",
        "AESER",
    ]


def test_merge_datasets_on_relationship_columns():
    """
    Unit test for DataProcessor.merge_datasets_on_relationship_columns method.
    """
    # prepare data
    left_dataset: pd.DataFrame = pd.DataFrame.from_dict(
        {
            "USUBJID": [
                "CDISC01",
                "CDISC01",
                "CDISC01",
            ],
            "DOMAIN": [
                "AE",
                "AE",
                "AE",
            ],
            "AESEQ": [
                1,
                2,
                3,
            ],
        }
    )
    right_dataset: pd.DataFrame = pd.DataFrame.from_dict(
        {
            "USUBJID": [
                "CDISC01",
                "CDISC01",
                "CDISC01",
                "CDISC01",
            ],
            "RDOMAIN": [
                "AE",
                "AE",
                "AE",
                "AE",
            ],
            "QNAM": [
                "TEST",
                "TEST",
                "TEST",
                "TEST_1",
            ],
            "IDVAR": [
                "AESEQ",
                "AESEQ",
                "AESEQ",
                "AESEQ",
            ],
            "IDVARVAL": [
                "1.0",
                "2",
                "3.0",
                "3.0",
            ],
        }
    )

    # call the tested function and check the results
    merged_df: pd.DataFrame = DataProcessor.merge_datasets_on_relationship_columns(
        left_dataset=left_dataset,
        right_dataset=right_dataset,
        right_dataset_domain_name="SUPPAE",
        column_with_names="IDVAR",
        column_with_values="IDVARVAL",
    )
    expected_df: pd.DataFrame = pd.DataFrame.from_dict(
        {
            "USUBJID": [
                "CDISC01",
                "CDISC01",
                "CDISC01",
                "CDISC01",
            ],
            "DOMAIN": [
                "AE",
                "AE",
                "AE",
                "AE",
            ],
            "AESEQ": [
                1.0,
                2.0,
                3.0,
                3.0,
            ],
            "USUBJID.SUPPAE": [
                "CDISC01",
                "CDISC01",
                "CDISC01",
                "CDISC01",
            ],
            "RDOMAIN": [
                "AE",
                "AE",
                "AE",
                "AE",
            ],
            "QNAM": [
                "TEST",
                "TEST",
                "TEST",
                "TEST_1",
            ],
            "IDVAR": [
                "AESEQ",
                "AESEQ",
                "AESEQ",
                "AESEQ",
            ],
            "IDVARVAL": [
                1.0,
                2.0,
                3.0,
                3.0,
            ],
        }
    )
    assert merged_df.equals(expected_df)


def test_merge_datasets_on_string_relationship_columns():
    """
    Unit test for DataProcessor.merge_datasets_on_relationship_columns method.
    Test the case when the columns that describe the relation
    are of a string type.
    """
    # prepare data
    left_dataset: pd.DataFrame = pd.DataFrame.from_dict(
        {
            "USUBJID": [
                "CDISC01",
                "CDISC01",
                "CDISC01",
            ],
            "DOMAIN": [
                "AE",
                "AE",
                "AE",
            ],
            "AESEQ": [
                "CDISC_IA",
                "CDISC_IB",
                "CDISC_IC",
            ],
        }
    )
    right_dataset: pd.DataFrame = pd.DataFrame.from_dict(
        {
            "USUBJID": [
                "CDISC01",
                "CDISC01",
                "CDISC01",
                "CDISC01",
            ],
            "RDOMAIN": [
                "AE",
                "AE",
                "AE",
                "AE",
            ],
            "QNAM": [
                "TEST",
                "TEST",
                "TEST",
                "TEST_1",
            ],
            "IDVAR": [
                "AESEQ",
                "AESEQ",
                "AESEQ",
                "AESEQ",
            ],
            "IDVARVAL": [
                "CDISC_IA",
                "CDISC_IB",
                "CDISC_IC",
                "CDISC_IC",
            ],
        }
    )

    # call the tested function and check the results
    merged_df: pd.DataFrame = DataProcessor.merge_datasets_on_relationship_columns(
        left_dataset=left_dataset,
        right_dataset=right_dataset,
        right_dataset_domain_name="SUPPAE",
        column_with_names="IDVAR",
        column_with_values="IDVARVAL",
    )
    expected_df: pd.DataFrame = pd.DataFrame.from_dict(
        {
            "USUBJID": [
                "CDISC01",
                "CDISC01",
                "CDISC01",
                "CDISC01",
            ],
            "DOMAIN": [
                "AE",
                "AE",
                "AE",
                "AE",
            ],
            "AESEQ": [
                "CDISC_IA",
                "CDISC_IB",
                "CDISC_IC",
                "CDISC_IC",
            ],
            "USUBJID.SUPPAE": [
                "CDISC01",
                "CDISC01",
                "CDISC01",
                "CDISC01",
            ],
            "RDOMAIN": [
                "AE",
                "AE",
                "AE",
                "AE",
            ],
            "QNAM": [
                "TEST",
                "TEST",
                "TEST",
                "TEST_1",
            ],
            "IDVAR": [
                "AESEQ",
                "AESEQ",
                "AESEQ",
                "AESEQ",
            ],
            "IDVARVAL": [
                "CDISC_IA",
                "CDISC_IB",
                "CDISC_IC",
                "CDISC_IC",
            ],
        }
    )
    assert merged_df.equals(expected_df)
