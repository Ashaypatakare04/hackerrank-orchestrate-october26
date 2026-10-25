# HackerRank Orchestrate (October 2026) — Ghost Data Still Exists
**Challenge:** Ghost Data Still Exists — AI-Powered Deletion Audit Agent
**Contest URL:** https://www.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists

---

## 1. Overview & Architecture

This repository contains the complete, production-grade AI deletion-audit agent for the HackerRank Orchestrate October 2026 challenge.

A deletion workflow can report **Complete** while personal data remains in databases, read replicas, application logs, support attachments, exports, search indexes, analytics records, archives, or backups. Furthermore, active synchronization connectors and restore permissions can recreate data after deletion.

The agent investigates the true state of customer data at each case's `audit_at` timestamp. It resolves historical identity changes, queries grounded participant-visible evidence across 6 distinct formats, enforces the 15 statutory deletion rules, detects policy violations and recreation risks, and outputs ordered findings, remediation plans, and verification checks.

### Architecture Diagram

```
                               ┌────────────────────────────────┐
                               │  dataset/deletion_requests.csv │
                               └──────────────┬─────────────────┘
                                              │
                                              ▼
┌───────────────────────┐      ┌────────────────────────────────┐      ┌─────────────────────────┐
│ user_identities.csv   │────▶ │     IdentityResolver           │ ◀─── │   user_audit_log.csv    │
└───────────────────────┘      │     (code/identity.py)         │      └─────────────────────────┘
                               └──────────────┬─────────────────┘
                                              │ Resolves UserProfile
                                              ▼
┌───────────────────────┐      ┌────────────────────────────────┐      ┌─────────────────────────┐
│ dataset/evidence/     │────▶ │       EvidenceIndex            │ ◀─── │  system_activity.csv    │
│ (SQL, JSON, LOG, PDF, │      │   (code/evidence_index.py)     │      │  (deletion bursts)      │
│  PNG, TXT files)      │      │  Cutoff: captured_at<=audit_at │      └─────────────────────────┘
└───────────────────────┘      └──────────────┬─────────────────┘
                                              │
                                              ▼
                               ┌────────────────────────────────┐      ┌─────────────────────────┐
                               │      Deletion Auditor          │ ◀─── │   deletion_rules.csv    │
                               │      (code/auditor.py)         │      │   (15 statutory rules)  │
                               └──────────────┬─────────────────┘      └─────────────────────────┘
                                              │
                                              ▼
                               ┌────────────────────────────────┐
                               │       Policy & Canonical       │
                               │        Step Sorter             │
                               │       (code/policy.py)         │
                               └──────────────┬─────────────────┘
                                              │
                                              ▼
                               ┌────────────────────────────────┐
                               │      output.csv (Repo Root)    │
                               │   case_id,status,steps_json    │
                               └────────────────────────────────┘
```

---

## 2. Code Structure

All solution source files live under `code/`:

```
code/
├── main.py                     # Primary executable: runs 518 cases & validates output.csv
├── models.py                   # Data models (Step, DeletionRequest, UserProfile, legal tuples)
├── identity.py                 # Historical & current identity resolver
├── evidence_index.py           # Multi-modal evidence manifest indexer with temporal filtering
├── auditor.py                  # Core deletion-audit engine & timeline reconstructor
├── policy.py                   # Statutory deletion rule applicator & canonical step sorter
├── parsers/                    # Deterministic evidence parsers
│   ├── sql_parser.py           # In-memory SQLite read replica parser with JSON document unpacking
│   ├── json_parser.py          # Service resource export & snapshot bundle parser
│   ├── log_parser.py           # Application trace & replica log parser
│   ├── pdf_parser.py           # Pure-Python stream decompressor for compliance PDFs
│   ├── image_parser.py         # Static console screenshot parser
│   └── txt_parser.py           # Shift handover report parser
└── evaluation/                 # Evaluation and benchmark reports
    ├── main.py                 # Evaluation harness for starter benchmark cases
    ├── custom_test_cases.py    # 3 participant-created custom evaluation scenarios
    ├── evaluation_report.md    # Full evaluation report (accuracies, tests, failure analysis)
    └── usage_report.md         # Runtime token & model usage report ($0.00 cost)
```

---

## 3. Environment & Setup

The solution is built using **pure Python standard library modules** (`sqlite3`, `json`, `csv`, `re`, `datetime`, `zlib`, `base64`). It requires **zero external pip dependencies**, ensuring 100% determinism, fast execution, complete data privacy, and zero installation friction across Windows, Linux, and macOS.

### Prerequisites:
- Python 3.10+ (Standard Library)

---

## 4. Execution Commands

### Run Full Dataset Pipeline (All 518 Cases):
```powershell
python code/main.py
```
This generates `output.csv` at the repository root and performs strict automated validation against all 10 grading checks.

### Run Official Benchmark Evaluation (Sample Cases):
```powershell
python code/evaluation/main.py
```
*Current benchmark performance:*
- **Case-Level Status Accuracy:** **100.00%** (32/32)
- **Sequence Accuracy:** **84.38%** (27/32)
- **Step Accuracy:** **94.82%** (183/193)
- **Field Accuracy:** **97.24%** (1126/1158)

### Run Custom Evaluation Test Cases:
```powershell
python code/evaluation/custom_test_cases.py
```
*Executes all 3 custom scenarios: Historical Identity Resolution, Statutory Retention Preservation, and Active Sync Resurrection Risk (100% Pass Rate).*

---

## 5. Official Submission Contract Compliance

The generated root `output.csv` conforms strictly to §6 of `AGENTS.md` and `problem_statement.md`:
1. **Exact Columns & Order:** `case_id,deletion_status,steps_json`
2. **Exactly 518 Rows:** One row per request from `dataset/deletion_requests.csv`, sorted by `case_id`.
3. **Allowed Statuses:** `COMPLETE`, `INCOMPLETE`, `NOT_APPLICABLE`.
4. **NOT_APPLICABLE Contract:** Every non-deletion request outputs `steps_json=[]`.
5. **Phase Ordering:** Strict progression `FINDING` -> `REMEDIATION` -> `VERIFICATION`.
6. **Operation Ordering:** Follows the problem statement ordering within each phase, sorted by `system_id` ASC, then `resource_id` ASC.
7. **Evidence Citations:** Findings cite participant-visible evidence IDs (`file_id`, `activity_id`, `audit_id`). Proposed remediations and future verifications use `evidence_id: ""`.
8. **COMPLETE Cases:** Contain only verification steps proving the compliant state at or before `audit_at`.
9. **No Secrets / Pure Determinism:** All operations run locally with zero API keys or external data transmission.

---

## 6. Packaging `code.zip` for Submission

To package the solution archive for submission without bundling the dataset or cache directories:

### Windows (PowerShell):
```powershell
# Clean any cache folders
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force

# Create submission archive
Compress-Archive -Path README.md, code, evaluation -DestinationPath code.zip -Force
```

### macOS / Linux:
```bash
zip -r code.zip README.md code evaluation -x "*/__pycache__/*" "*/.venv/*" "*/venv/*" "*/.git/*" "*/.DS_Store"
```

The resulting `code.zip` contains all runnable source files, `README.md`, `evaluation/evaluation_report.md`, and `evaluation/usage_report.md`.
