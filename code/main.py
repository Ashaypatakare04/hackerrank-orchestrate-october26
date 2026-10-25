"""
Main entry point for HackerRank Orchestrate (October 2026): Ghost Data Still Exists.
Audits all 518 deletion requests from dataset/deletion_requests.csv and writes root-level output.csv.
"""
import os
import sys
import csv
import json
from typing import List, Dict, Any

from models import DeletionRequest, Step, LEGAL_STEPS
from auditor import Auditor


def run_full_pipeline(dataset_dir: str = "dataset", output_path: str = "output.csv") -> None:
    print(f"Loading deletion requests from {dataset_dir}/deletion_requests.csv...")
    reqs_path = os.path.join(dataset_dir, "deletion_requests.csv")
    if not os.path.exists(reqs_path):
        raise FileNotFoundError(f"Missing dataset file: {reqs_path}")

    requests: List[DeletionRequest] = []
    with open(reqs_path, "r", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            requests.append(DeletionRequest(
                case_id=row["case_id"],
                email=row["email"],
                requested_at=row["requested_at"],
                reported_status=row["reported_status"],
                reported_at=row["reported_at"],
                audit_at=row["audit_at"],
                request_text=row["request_text"],
            ))

    print(f"Loaded {len(requests)} requests.")
    print("Initializing Deletion-Audit Engine...")
    auditor = Auditor(dataset_dir)

    print("Auditing all deletion requests...")
    results = []
    status_counts = {"COMPLETE": 0, "INCOMPLETE": 0, "NOT_APPLICABLE": 0}

    for idx, req in enumerate(requests):
        status, steps = auditor.audit_case(req)
        status_counts[status] = status_counts.get(status, 0) + 1

        # Format steps to dict list
        steps_dicts = [s.to_dict() for s in steps]
        steps_json = json.dumps(steps_dicts, separators=(',', ':'))

        results.append({
            "case_id": req.case_id,
            "deletion_status": status,
            "steps_json": steps_json,
        })

        if (idx + 1) % 50 == 0 or (idx + 1) == len(requests):
            print(f"  Processed {idx + 1}/{len(requests)} cases...")

    # Sort strictly by case_id
    results.sort(key=lambda x: x["case_id"])

    # Write root output.csv
    print(f"Writing {len(results)} rows to {output_path}...")
    fieldnames = ["case_id", "deletion_status", "steps_json"]
    with open(output_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print("Pipeline run completed.")
    print(f"Summary: COMPLETE={status_counts['COMPLETE']}, INCOMPLETE={status_counts['INCOMPLETE']}, NOT_APPLICABLE={status_counts['NOT_APPLICABLE']}")


def validate_output(output_path: str = "output.csv", expected_cases_count: int = 518) -> bool:
    print(f"\n--- Validating {output_path} ---")
    if not os.path.exists(output_path):
        print(f"FAIL: {output_path} does not exist.")
        return False

    with open(output_path, "r", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        header = next(reader, None)
        if header != ["case_id", "deletion_status", "steps_json"]:
            print(f"FAIL: Header mismatch. Got {header}, expected ['case_id', 'deletion_status', 'steps_json']")
            return False

        rows = list(reader)

    if len(rows) != expected_cases_count:
        print(f"FAIL: Row count mismatch. Got {len(rows)}, expected {expected_cases_count}")
        return False

    case_ids = [r[0] for r in rows]
    if len(set(case_ids)) != len(case_ids):
        print("FAIL: Duplicate case_id found in output.")
        return False

    if case_ids != sorted(case_ids):
        print("FAIL: Rows are not sorted by case_id.")
        return False

    allowed_statuses = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}
    for idx, (cid, status, steps_str) in enumerate(rows):
        line_no = idx + 2
        if status not in allowed_statuses:
            print(f"FAIL [Line {line_no}]: Invalid status '{status}' for {cid}")
            return False

        try:
            steps = json.loads(steps_str)
        except Exception as e:
            print(f"FAIL [Line {line_no}]: Invalid JSON for {cid}: {e}")
            return False

        if not isinstance(steps, list):
            print(f"FAIL [Line {line_no}]: steps_json is not an array for {cid}")
            return False

        if status == "NOT_APPLICABLE":
            if steps != []:
                print(f"FAIL [Line {line_no}]: NOT_APPLICABLE case {cid} must have empty steps array [], got {len(steps)} steps")
                return False
            continue

        if status == "COMPLETE":
            for s in steps:
                if s.get("phase") != "VERIFICATION":
                    print(f"FAIL [Line {line_no}]: COMPLETE case {cid} has non-VERIFICATION step: {s}")
                    return False
                if not s.get("evidence_id"):
                    print(f"FAIL [Line {line_no}]: COMPLETE case {cid} verification step has empty evidence_id: {s}")
                    return False

        # Validate step numbering and legal combinations
        phases_seen = []
        for step_idx, s in enumerate(steps, start=1):
            if s.get("step_no") != step_idx:
                print(f"FAIL [Line {line_no}]: Step numbering error in {cid}. Expected {step_idx}, got {s.get('step_no')}")
                return False

            phase = s.get("phase")
            op = s.get("operation")
            state = s.get("state")

            if (phase, op, state) not in LEGAL_STEPS:
                print(f"FAIL [Line {line_no}]: Illegal tuple in {cid}: phase={phase}, op={op}, state={state}")
                return False

            if phase not in phases_seen:
                phases_seen.append(phase)

            # Check evidence_id rules for INCOMPLETE cases
            if status == "INCOMPLETE":
                if phase == "FINDING":
                    if not s.get("evidence_id"):
                        print(f"FAIL [Line {line_no}]: INCOMPLETE case {cid} finding has empty evidence_id: {s}")
                        return False
                else:
                    if s.get("evidence_id") != "":
                        print(f"FAIL [Line {line_no}]: INCOMPLETE case {cid} future step has non-empty evidence_id: {s}")
                        return False

        # Validate phase ordering: FINDING -> REMEDIATION -> VERIFICATION
        valid_phase_orders = [
            [],
            ["VERIFICATION"],
            ["FINDING"],
            ["FINDING", "REMEDIATION"],
            ["FINDING", "REMEDIATION", "VERIFICATION"],
        ]
        if phases_seen not in valid_phase_orders:
            print(f"FAIL [Line {line_no}]: Invalid phase order in {cid}: {phases_seen}")
            return False

    print("SUCCESS: All 518 cases validated successfully.")
    print("  [OK] Exact columns & header order")
    print("  [OK] Exactly 518 rows sorted by case_id")
    print("  [OK] Valid JSON serialization")
    print("  [OK] Legal status, operation, and state combinations")
    print("  [OK] Consecutive step numbering from 1")
    print("  [OK] Strict evidence citation rules (evidence_id requirements)")
    print("  [OK] Phase order: FINDING -> REMEDIATION -> VERIFICATION")
    return True


if __name__ == "__main__":
    dataset_dir = sys.argv[1] if len(sys.argv) > 1 else "dataset"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "output.csv"
    run_full_pipeline(dataset_dir, out_path)
    validate_output(out_path, 518)
