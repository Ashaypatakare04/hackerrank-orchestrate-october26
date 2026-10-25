"""
Custom Evaluation Test Cases for HackerRank Orchestrate (October 2026).
Implements 3 independent evaluation scenarios:
1. Historical Email & Identity Resolution
2. Legal Hold & Statutory Retention Preservation
3. Data Resurrection & Active Synchronization Risk
"""
import os
import sys
from typing import Dict, Any, List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from auditor import Auditor
from models import DeletionRequest, Step


def run_custom_evaluations(dataset_dir: str = "dataset") -> Dict[str, Any]:
    auditor = Auditor(dataset_dir)

    test_cases = [
        {
            "id": "custom_case_01",
            "name": "Historical Identity Resolution",
            "description": "User requests deletion using an old email address (prior to an update in user_audit_log). "
                           "The auditor must correctly map the historical email to the stable user_id and identify remaining records.",
            "request": DeletionRequest(
                case_id="custom_case_01",
                email="n.petrescu@yahoo.com",  # Historical email of user_10 (Nadia Ionescu)
                requested_at="2026-09-08T10:00:00Z",
                reported_status="COMPLETE",
                reported_at="2026-09-10T10:00:00Z",
                audit_at="2026-09-20T10:00:00Z",
                request_text="I am requesting complete erasure of my account and personal data.",
            ),
            "expected_status": "INCOMPLETE",
            "expected_finding_resource": "support_002",
        },
        {
            "id": "custom_case_02",
            "name": "Statutory Retention & Legal Hold Preservation",
            "description": "User with a legal hold record requests deletion. The auditor must verify the account is removed "
                           "while ensuring the legally held order record is preserved (VERIFY_RECORD_PRESENT), not reported as a violation.",
            "request": DeletionRequest(
                case_id="custom_case_02",
                email="priya.raman@gmail.com",  # user_07
                requested_at="2026-09-01T10:00:00Z",
                reported_status="COMPLETE",
                reported_at="2026-09-03T10:00:00Z",
                audit_at="2026-09-20T10:00:00Z",
                request_text="Please delete my account and personal profile. Keep any legal or security logs required by law.",
            ),
            "expected_status": "INCOMPLETE",  # user_07 has support attachment support_001 still remaining
            "expected_finding_resource": "support_001",
        },
        {
            "id": "custom_case_03",
            "name": "Active Synchronization Connector Resurrection Risk",
            "description": "Workflow reported complete deletion, but an integration connector remains active. "
                           "The auditor must reject the reported COMPLETE claim, flag REPORT_ACTIVE_DATA_FLOW, and propose DISABLE_DATA_FLOW.",
            "request": DeletionRequest(
                case_id="custom_case_03",
                email="jain.aditi@gmail.com",
                requested_at="2026-08-01T10:00:00Z",
                reported_status="COMPLETE",
                reported_at="2026-08-05T10:00:00Z",
                audit_at="2026-08-20T10:00:00Z",
                request_text="Please confirm that all data synchronization and account records for my email are deleted.",
            ),
            "expected_status": "INCOMPLETE",
            "expected_finding_resource": "data_flow_1121",
        },
    ]

    results = []
    passed_count = 0

    for tc in test_cases:
        status, steps = auditor.audit_case(tc["request"])
        finding_res_ids = [s.resource_id for s in steps if s.phase == "FINDING"]
        status_pass = (status == tc["expected_status"])
        finding_pass = (tc["expected_finding_resource"] in finding_res_ids)
        passed = status_pass and finding_pass

        if passed:
            passed_count += 1

        results.append({
            "id": tc["id"],
            "name": tc["name"],
            "description": tc["description"],
            "expected_status": tc["expected_status"],
            "actual_status": status,
            "expected_finding": tc["expected_finding_resource"],
            "actual_findings": finding_res_ids,
            "steps_count": len(steps),
            "passed": passed,
        })

    return {
        "total": len(test_cases),
        "passed": passed_count,
        "results": results,
    }


if __name__ == "__main__":
    eval_res = run_custom_evaluations("dataset")
    print("=" * 60)
    print(f"Custom Test Cases Evaluation ({eval_res['passed']}/{eval_res['total']} Passed)")
    print("=" * 60)
    for r in eval_res["results"]:
        status_icon = "PASS" if r["passed"] else "FAIL"
        print(f"[{status_icon}] {r['id']}: {r['name']}")
        print(f"       Status: Expected {r['expected_status']}, Got {r['actual_status']}")
        print(f"       Finding: Expected {r['expected_finding']}, Found {r['actual_findings']}")
    print("=" * 60)
