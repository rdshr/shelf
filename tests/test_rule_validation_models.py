from __future__ import annotations

import unittest

from frontend_kernel import summarize_frontend_rules, validate_frontend_rules
from knowledge_base_framework import summarize_workbench_rules, validate_workbench_rules
from project_runtime.knowledge_base import load_knowledge_base_project
from rule_validation_models import RuleValidationOutcome, RuleValidationSummary, ValidationReports


class RuleValidationModelsTest(unittest.TestCase):
    def test_frontend_and_workbench_rules_return_dataclass_structures(self) -> None:
        project = load_knowledge_base_project()

        frontend_results = validate_frontend_rules(project)
        workbench_results = validate_workbench_rules(project)

        self.assertTrue(frontend_results)
        self.assertTrue(workbench_results)
        self.assertTrue(all(isinstance(item, RuleValidationOutcome) for item in frontend_results))
        self.assertTrue(all(isinstance(item, RuleValidationOutcome) for item in workbench_results))

        frontend_summary = summarize_frontend_rules(frontend_results)
        workbench_summary = summarize_workbench_rules(workbench_results)

        self.assertIsInstance(frontend_summary, RuleValidationSummary)
        self.assertIsInstance(workbench_summary, RuleValidationSummary)
        self.assertTrue(frontend_summary.passed)
        self.assertTrue(workbench_summary.passed)
        self.assertEqual(frontend_summary.to_dict()["module_id"], "frontend.L2.M0")
        self.assertEqual(workbench_summary.to_dict()["module_id"], "knowledge_base.L2.M0")

    def test_validation_reports_expose_summary_and_dict_views(self) -> None:
        project = load_knowledge_base_project()
        reports = project.validation_reports

        self.assertIsInstance(reports, ValidationReports)
        self.assertTrue(reports.passed)
        self.assertGreater(reports.passed_count, 0)
        self.assertEqual(reports.rule_count, 8)

        payload = reports.to_dict()
        self.assertTrue(payload["overall"]["passed"])
        self.assertEqual(payload["overall"]["rule_count"], 8)
        self.assertEqual(payload["frontend"]["module_id"], "frontend.L2.M0")
        self.assertEqual(payload["knowledge_base"]["module_id"], "knowledge_base.L2.M0")


if __name__ == "__main__":
    unittest.main()
