import csv
import json
from typing import Dict, List, Any, Tuple

def load_ground_truth(path: str) -> Dict[str, Dict[str, Any]]:
    cases = {}
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["case_id"]
            cases[cid] = {
                "case_id": cid,
                "deletion_status": row["deletion_status"],
                "steps": json.loads(row["steps_json"])
            }
    return cases

def evaluate_predictions(predictions: Dict[str, Dict[str, Any]], ground_truth: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    total_cases = len(ground_truth)
    if total_cases == 0:
        return {"error": "Ground truth is empty"}

    correct_status = 0
    exact_sequence_matches = 0
    total_steps_expected = 0
    total_steps_matched = 0
    total_fields_expected = 0
    total_fields_matched = 0

    mismatches = []

    fields_to_check = ["phase", "system_id", "resource_id", "operation", "state", "evidence_id"]

    for cid, gt in ground_truth.items():
        pred = predictions.get(cid)
        if not pred:
            mismatches.append({"case_id": cid, "error": "Missing prediction"})
            continue

        # Status check
        status_match = (pred["deletion_status"] == gt["deletion_status"])
        if status_match:
            correct_status += 1

        pred_steps = pred.get("steps", [])
        gt_steps = gt.get("steps", [])

        # Sequence check
        seq_match = False
        if len(pred_steps) == len(gt_steps):
            step_matches = True
            for p_step, g_step in zip(pred_steps, gt_steps):
                for fld in fields_to_check:
                    if str(p_step.get(fld, "")) != str(g_step.get(fld, "")):
                        step_matches = False
                        break
                if not step_matches:
                    break
            if step_matches:
                seq_match = True
                exact_sequence_matches += 1

        if not (status_match and seq_match):
            mismatches.append({
                "case_id": cid,
                "expected_status": gt["deletion_status"],
                "predicted_status": pred["deletion_status"],
                "expected_steps_count": len(gt_steps),
                "predicted_steps_count": len(pred_steps),
                "gt_steps": gt_steps,
                "pred_steps": pred_steps
            })

        # Step and Field-level metrics
        total_steps_expected += len(gt_steps)
        for i, g_step in enumerate(gt_steps):
            total_fields_expected += len(fields_to_check)
            if i < len(pred_steps):
                p_step = pred_steps[i]
                step_exact = True
                for fld in fields_to_check:
                    if str(p_step.get(fld, "")) == str(g_step.get(fld, "")):
                        total_fields_matched += 1
                    else:
                        step_exact = False
                if step_exact:
                    total_steps_matched += 1

    return {
        "total_cases": total_cases,
        "status_accuracy": correct_status / total_cases if total_cases else 0.0,
        "correct_status_count": correct_status,
        "sequence_accuracy": exact_sequence_matches / total_cases if total_cases else 0.0,
        "exact_sequence_count": exact_sequence_matches,
        "step_accuracy": total_steps_matched / total_steps_expected if total_steps_expected else 1.0,
        "total_steps_expected": total_steps_expected,
        "total_steps_matched": total_steps_matched,
        "field_accuracy": total_fields_matched / total_fields_expected if total_fields_expected else 1.0,
        "total_fields_expected": total_fields_expected,
        "total_fields_matched": total_fields_matched,
        "mismatches": mismatches
    }


if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from auditor import Auditor
    from models import DeletionRequest

    dataset_dir = "dataset"
    gt_path = os.path.join(dataset_dir, "sample_output.csv")
    samples_path = os.path.join(dataset_dir, "sample_deletion_requests.csv")

    gt = load_ground_truth(gt_path)
    auditor = Auditor(dataset_dir)

    preds = {}
    with open(samples_path, "r", encoding="utf-8") as fp:
        for row in csv.DictReader(fp):
            req = DeletionRequest(
                case_id=row["case_id"],
                email=row["email"],
                requested_at=row["requested_at"],
                reported_status=row["reported_status"],
                reported_at=row["reported_at"],
                audit_at=row["audit_at"],
                request_text=row["request_text"],
            )
            status, steps = auditor.audit_case(req)
            preds[row["case_id"]] = {
                "case_id": row["case_id"],
                "deletion_status": status,
                "steps": [s.to_dict() for s in steps]
            }

    metrics = evaluate_predictions(preds, gt)
    print("=" * 60)
    print(f"Sample Evaluation Results ({metrics['total_cases']} cases)")
    print("=" * 60)
    print(f"Status Accuracy:    {metrics['status_accuracy']*100:.2f}% ({metrics['correct_status_count']}/{metrics['total_cases']})")
    print(f"Sequence Accuracy:  {metrics['sequence_accuracy']*100:.2f}% ({metrics['exact_sequence_count']}/{metrics['total_cases']})")
    print(f"Step Accuracy:      {metrics['step_accuracy']*100:.2f}% ({metrics['total_steps_matched']}/{metrics['total_steps_expected']})")
    print(f"Field Accuracy:     {metrics['field_accuracy']*100:.2f}% ({metrics['total_fields_matched']}/{metrics['total_fields_expected']})")
    print("=" * 60)
    if metrics["mismatches"]:
        print(f"Mismatches ({len(metrics['mismatches'])} cases):")
        for m in metrics["mismatches"][:5]:
            print(f"  {m['case_id']}: Expected {m['expected_status']} ({m['expected_steps_count']} steps), Got {m['predicted_status']} ({m['predicted_steps_count']} steps)")
