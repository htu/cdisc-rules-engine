import os
from unittest.mock import MagicMock

from cdisc_rules_engine.enums.execution_status import ExecutionStatus
from cdisc_rules_engine.models.rule_validation_result import RuleValidationResult
from cdisc_rules_engine.services.reporting.excel_report import ExcelReport
from version import __version__

test_report_template: str = (
    f"{os.path.dirname(__file__)}/../../../../resources/templates/report-template.xlsx"
)

mock_validation_results = [
    RuleValidationResult(
        rule={
            "core_id": "CORE1",
            "executability": "Partially Executable",
            "actions": [{"params": {"message": "TEST RULE 1"}}],
            "authorities": [
                {
                    "Organization": "CDISC",
                    "Standards": [
                        {
                            "References": [
                                {"Rule_Identifier": {"Id": "CDISCRuleID4"}},
                                {"Rule_Identifier": {"Id": "CDISCRuleID3"}},
                            ]
                        },
                        {
                            "References": [
                                {"Rule_Identifier": {"Id": "CDISCRuleID2"}},
                                {"Rule_Identifier": {"Id": "CDISCRuleID1"}},
                            ]
                        },
                    ],
                },
                {
                    "Organization": "FDA",
                    "Standards": [
                        {
                            "References": [
                                {"Rule_Identifier": {"Id": "FDARuleID1"}},
                                {"Rule_Identifier": {"Id": "FDARuleID2"}},
                            ]
                        }
                    ],
                },
                {
                    "Organization": "PMDA",
                    "Standards": [
                        {
                            "References": [
                                {"Rule_Identifier": {"Id": "PMDARuleID1"}},
                                {"Rule_Identifier": {"Id": "PMDARuleID2"}},
                            ]
                        }
                    ],
                },
            ],
        },
        results=[
            {
                "domain": "AE",
                "variables": ["AESTDY", "DOMAIN"],
                "executionStatus": ExecutionStatus.SUCCESS.value,
                "errors": [
                    {
                        "row": 1,
                        "value": {"AESTDY": "test", "DOMAIN": "test"},
                        "USUBJID": "CDISC002",
                        "SEQ": 2,
                    },
                    {
                        "row": 9,
                        "value": {"AESTDY": "test", "DOMAIN": "test"},
                        "USUBJID": "CDISC003",
                        "SEQ": 10,
                    },
                ],
                "message": "AESTDY and DOMAIN are equal to test",
            }
        ],
    ),
    RuleValidationResult(
        rule={
            "core_id": "CORE2",
            "executability": "Fully Executable",
            "actions": [{"params": {"message": "TEST RULE 2"}}],
            "authorities": [
                {
                    "Organization": "CDISC",
                    "Standards": [
                        {
                            "References": [
                                {"Rule_Identifier": {"Id": "CDISCRuleID4"}},
                                {"Rule_Identifier": {"Id": "CDISCRuleID3"}},
                            ]
                        },
                        {
                            "References": [
                                {"Rule_Identifier": {"Id": "CDISCRuleID2"}},
                                {"Rule_Identifier": {"Id": "CDISCRuleID1"}},
                            ]
                        },
                    ],
                },
                {
                    "Organization": "FDA",
                    "Standards": [
                        {
                            "References": [
                                {"Rule_Identifier": {"Id": "FDARuleID1"}},
                                {"Rule_Identifier": {"Id": "FDARuleID2"}},
                            ]
                        }
                    ],
                },
                {
                    "Organization": "PMDA",
                    "Standards": [
                        {
                            "References": [
                                {"Rule_Identifier": {"Id": "PMDARuleID1"}},
                                {"Rule_Identifier": {"Id": "PMDARuleID2"}},
                            ]
                        }
                    ],
                },
            ],
        },
        results=[
            {
                "domain": "TT",
                "variables": ["TTVAR1", "TTVAR2"],
                "executionStatus": ExecutionStatus.SUCCESS.value,
                "errors": [
                    {
                        "row": 1,
                        "value": {"TTVAR1": "test", "TTVAR2": "test"},
                        "USUBJID": "CDISC002",
                        "SEQ": 2,
                    }
                ],
                "message": "TTVARs are wrong",
            }
        ],
    ),
]


def test_get_rules_report_data():
    with open(test_report_template, "rb") as f:
        report: ExcelReport = ExcelReport(
            "test", mock_validation_results, 10.1, MagicMock(), f
        )
        report_data = report.get_rules_report_data()
        expected_reports = []
        for result in mock_validation_results:
            expected_reports.append(
                [
                    result.id,
                    "1",
                    result.cdisc_rule_id,
                    result.fda_rule_id,
                    result.pmda_rule_id,
                    result.message,
                    ExecutionStatus.SUCCESS.value.upper(),
                ]
            )
        expected_reports = sorted(expected_reports, key=lambda x: x[0])
        assert len(report_data) == len(expected_reports)
        for i, _ in enumerate(report_data):
            assert report_data[i] == expected_reports[i]


def test_get_detailed_data():
    with open(test_report_template, "rb") as f:
        report: ExcelReport = ExcelReport(
            "test", mock_validation_results, 10.1, MagicMock(), f
        )
        detailed_data = report.get_detailed_data()
        errors = [
            [
                mock_validation_results[0].id,
                "AESTDY and DOMAIN are equal to test",
                "Partially Executable",
                "AE",
                "CDISC002",
                1,
                2,
                "AESTDY, DOMAIN",
                "test, test",
            ],
            [
                mock_validation_results[0].id,
                "AESTDY and DOMAIN are equal to test",
                "Partially Executable",
                "AE",
                "CDISC003",
                9,
                10,
                "AESTDY, DOMAIN",
                "test, test",
            ],
            [
                mock_validation_results[1].id,
                "TTVARs are wrong",
                "Fully Executable",
                "TT",
                "CDISC002",
                1,
                2,
                "TTVAR1, TTVAR2",
                "test, test",
            ],
        ]
        errors = sorted(errors, key=lambda x: (x[0], x[2]))
        assert len(errors) == len(detailed_data)
        for i, error in enumerate(errors):
            assert error == detailed_data[i]


def test_get_summary_data():
    with open(test_report_template, "rb") as f:
        report: ExcelReport = ExcelReport(
            "test", mock_validation_results, 10.1, MagicMock(), f
        )
        summary_data = report.get_summary_data()
        errors = [
            [
                "AE",
                mock_validation_results[0].id,
                "AESTDY and DOMAIN are equal to test",
                2,
            ],
            [
                "TT",
                mock_validation_results[1].id,
                "TTVARs are wrong",
                1,
            ],
        ]
        errors = sorted(errors, key=lambda x: (x[0], x[1]))
        assert len(errors) == len(summary_data)
        for i, error in enumerate(errors):
            assert error == summary_data[i]


def test_get_export():
    with open(test_report_template, "rb") as f:
        mock_args = MagicMock()
        mock_args.meddra = "test"
        mock_args.whodrug = "test"
        report: ExcelReport = ExcelReport(
            ["test"], mock_validation_results, 10.1, mock_args, f
        )
        cdiscCt = ["sdtmct-03-2021"]
        wb = report.get_export(
            define_version="2.1", cdiscCt=cdiscCt, standard="sdtmig", version="3.4"
        )
        assert wb["Conformance Details"]["B3"].value == "10.1 seconds"
        assert wb["Conformance Details"]["B4"].value == __version__
        assert wb["Conformance Details"]["B7"].value == "SDTMIG"
        assert wb["Conformance Details"]["B8"].value == "V3.4"
        assert wb["Conformance Details"]["B9"].value == ", ".join(cdiscCt)
        assert wb["Conformance Details"]["B10"].value == "2.1"
