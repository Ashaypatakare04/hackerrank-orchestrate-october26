# Evaluation Report — Ghost Data Still Exists
**HackerRank Orchestrate (October 2026)**  
**Challenge:** Ghost Data Still Exists — AI-Powered Deletion Audit Agent  
**Date:** October 2026  
**Auditor Engine:** Deterministic Evidence-Driven Deletion Auditor (`code/auditor.py`)  

---

## 1. Executive Summary

This evaluation report documents the empirical performance, testing methodology, custom benchmark test cases, and iterative improvements made to the deletion-audit agent for the HackerRank Orchestrate October 2026 challenge.

The solution operates as a pure-evidence deterministic audit engine. Rather than relying on non-deterministic LLM hallucination or trusting workflow claims, the engine parses 94 participant-visible evidence files across 6 modalities (SQL read replicas, JSON snapshot exports, structured application logs, PDF extracts, image console captures, and plain-text handover records), resolves historical identities across audit trails, enforces strict temporal cutoff constraints (`captured_at <= audit_at`), and applies the 15 statutory deletion rules from `deletion_rules.csv`.

---

## 2. Evaluation Metrics on Official Starter Dataset

The agent was evaluated against the public starter ground-truth dataset (`dataset/sample_output.csv`, containing 32 benchmark deletion requests from `dataset/sample_deletion_requests.csv`).

| Metric Category | Tested Cases / Items | Matches / Correct | Current Accuracy | Initial Baseline | Total Improvement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Case-Level Deletion Status** | 32 cases | 32 | **100.00%** | 100.00% | +0.00% |
| **Sequence Accuracy** (Exact Step Order & Content) | 32 cases | 27 | **84.38%** | 65.62% | **+18.76%** |
| **Step-Level Accuracy** | 193 steps | 183 | **94.82%** | 88.08% | **+6.74%** |
| **Field-Level Accuracy** | 1,158 step fields | 1,126 | **97.24%** | 93.70% | **+3.54%** |

### Metric Definitions:
1. **Case-Level Status Accuracy:** Exact match of `deletion_status` (`COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`).
2. **Sequence Accuracy:** Character-for-character and step-for-step identity of the entire sorted `steps_json` array for the case.
3. **Step-Level Accuracy:** Exact match of all six core fields (`phase`, `system_id`, `resource_id`, `operation`, `state`, `evidence_id`) for each corresponding step index.
4. **Field-Level Accuracy:** Independent evaluation of each individual field across all ground-truth steps.

### Analysis of Unresolved Sequence Mismatches (5 of 32 cases):
The 5 remaining cases with structural sequence variations fall into two grounded root causes:
1. **Unseen Security Records in Participant Evidence (`case_18`, `case_20`):**
   - In `case_18` (13/14 steps matched) and `case_20` (7/8 steps matched), ground truth includes a verification step for `audit_record_6645` and `audit_record_5569`.
   - Comprehensive multi-file text and regex searches confirmed neither identifier exists anywhere in participant-visible files (`dataset/evidence/` or `dataset/system_activity.csv`).
   - Under §6.6 of `AGENTS.md`, agents must never cite organizer-only truth or fabricate evidence citations. Omitting unevidenced records is strictly compliant with the challenge rules.
2. **Multi-Wave Workflow Resource Pairing (`case_23`, `case_26`, `case_28`):**
   - In `case_23`, batch deletion workers processed multiple accounts (`account_410`, `account_9155`) in a single execution burst alongside export and search tasks; all 7 findings, remediations, and secondary checks match 100%.
   - In `case_26` and `case_28`, users without pre-audit analytics records in direct evidence have multiple anonymized profiles present in the workflow execution window. Findings, remediations, and status are 100% exact; variations are confined to index selection among equidistant anonymous profiles.

---

## 3. Custom Evaluation Test Cases

To rigorously validate the agent beyond the provided public sample cases, three independent end-to-end evaluation cases were designed and executed via `code/evaluation/custom_test_cases.py`. All three passed (100% pass rate).

### Custom Case 1: Historical Identity Resolution (`custom_case_01`)
* **Objective:** Verify that a deletion request submitted under a historical email address recovers the subject's stable internal identifier, connects to older database replicas, and detects exposed PII/remaining records under the historical email.
* **Test Setup:**
  - Requester Email: `n.petrescu@yahoo.com` (historical email of `user_10`, Nadia Ionescu, before her surname change recorded in `user_audit_log.csv`).
  - Request Text: *"I am requesting complete erasure of my account and personal data."*
  - Workflow Claim: `reported_status = COMPLETE`.
  - Cutoff Time: `audit_at = 2026-09-20T10:00:00Z`.
* **Observed Evidence:** `evidence_61` (`support_replica.log`) contains contact index lookups for `nadia.ionescu@yahoo.com` where deletion marker check returned `marker_found=false` for `support_002`.
* **Agent Decision:** `INCOMPLETE`.
  - Finding: `support_platform` | `support_002` | `REPORT_REMAINING_RECORD` | `PRESENT` | `evidence_61`
  - Remediation: `support_platform` | `support_002` | `DELETE_RECORD` | `ABSENT`
  - Verification: `account_service` | `account_010` | `VERIFY_RECORD_ABSENT` | `ABSENT`
  - Verification: `support_platform` | `support_002` | `VERIFY_RECORD_ABSENT` | `ABSENT`
* **Verdict:** **PASS** (Resolved historical email, rejected false COMPLETE claim, flagged remaining replica record).

---

### Custom Case 2: Statutory Retention & Legal Hold Preservation (`custom_case_02`)
* **Objective:** Ensure the auditor respects `rule_12` (SECURITY_AUDIT_LOG: RETAIN) and `rule_13` (LEGAL_HOLD_RECORD: RETAIN), preserving statutory records without falsely reporting them as remaining record violations.
* **Test Setup:**
  - Requester Email: `priya.raman@gmail.com` (`user_07`).
  - Request Text: *"Please delete my account and personal profile. Keep any legal or security logs required by law."*
  - Evidence: `evidence_91` (`delivery_correction_attachment.pdf`) has customer delivery attachment `support_001` (`rule_06`: DELETE). Security log `audit_record_003` has active retention until 2027.
* **Agent Decision:** `INCOMPLETE`.
  - Finding: Correctly flags un-deleted attachment `support_001` as `REPORT_REMAINING_RECORD`.
  - Legal Hold / Security Preservation: Retained security record is NOT reported as an illegal finding. In the post-remediation plan, verification includes `VERIFY_RECORD_PRESENT` for the retained security audit log.
* **Verdict:** **PASS** (Correctly separated policy-mandated deletion from statutory retention).

---

### Custom Case 3: Data Resurrection & Active Synchronization Risk (`custom_case_03`)
* **Objective:** Detect active integration pipelines (`rule_03` / `rule_10` / active connectors) that can copy or recreate deleted customer data, even when primary account deletion succeeded.
* **Test Setup:**
  - Requester Email: `jain.aditi@gmail.com` (`user_15`).
  - Reported Workflow Status: `COMPLETE`.
  - Observed Evidence: `evidence_86` (`connector_management_console_20260807.png`) and `evidence_04` confirm connector `data_flow_1121` remains `Continuous Sync` / `enabled=true`.
* **Agent Decision:** `INCOMPLETE`.
  - Finding: `integration_service` | `data_flow_1121` | `REPORT_ACTIVE_DATA_FLOW` | `ACTIVE` | `evidence_86`
  - Remediation: `integration_service` | `data_flow_1121` | `DISABLE_DATA_FLOW` | `DISABLED`
  - Verification: `integration_service` | `data_flow_1121` | `VERIFY_DATA_FLOW_DISABLED` | `DISABLED`
* **Verdict:** **PASS** (Recreation risk surfaced and safely ordered before dependent record remediation).

---

## 4. Failures Found and Iterative Improvements Made

During engineering and testing against starter ground truth, several subtle failure modes were diagnosed and corrected:

### 1. Cross-User Account Disambiguation (`case_25`)
* **Failure:** In `evidence_92`, multiple 404 profile lookups occurred within a 2-hour window. `case_25` originally selected `account_5684` because its timestamp was numerically closest to the reported cutoff. However, `account_5684` was explicitly linked in evidence to `user_26`, causing `case_25` to misidentify its account.
* **Fix:** Built `account_explicit_user` in `Auditor` by aggregating explicit user links across all evidence records (`customer_reference` / `user_id`). Candidate accounts explicitly owned by a different user are excluded during candidate resolution. This immediately brought `case_25` to 100% exact sequence match without regressing any other case.

### 2. Log Parser String `"null"` Handling (`case_03`, `case_04`)
* **Failure:** In `code/parsers/log_parser.py`, analytics profile anonymization checks evaluated `email_hash is None`. In JSON log lines, `email_hash` was parsed as the string `"null"`, causing valid anonymized analytics profiles (`analytics_9406`, `analytics_901`) to be missed in `case_03` and `case_04`.
* **Fix:** Updated `code/parsers/log_parser.py` line 134 to check `email_hash in [None, "null"]`. This immediately resolved `case_03` and `case_04` to 100% exact matches.

### 3. Workflow Batch Window Expansion (`case_27`, `case_29`, `case_31`)
* **Failure:** Primary account deletions were dispatched by `deletion_worker` 30–90 minutes before dependent search, support, export, and connector jobs. An initial 1800s batch window fragmented single workflow lifecycles into separate batches, causing account miscorrelation.
* **Fix:** Expanded the batch correlation window to 7200 seconds (2 hours) and mapped user evidence resources directly to the workflow wave. This resolved `case_27`, `case_29`, and `case_31` to 100% exact sequence matches.

### 4. Nested JSON Documents in SQLite Read Replicas (`case_16`, `case_22`)
* **Failure:** In `primary_customer_replica_20260921.sql` (`evidence_05`), customer search entries were stored in JSON format where `customer_reference` was nested under `"document": {"customer_reference": "user_53", ...}`. The original parser looked only at top-level keys, causing search index violations (e.g. `search_1007`, `search_8911`) to be missed.
* **Fix:** Enhanced `code/parsers/sql_parser.py` to recursively unpack nested document dictionaries (`parsed.get("document")`) and associate collection names matching `search` with category `SEARCH_INDEX_ENTRY`. This resolved `case_16` and `case_22`.

### 5. Log Parser Event Discrimination and Violation Priority (`case_10`)
* **Failure:** In `evidence_61` (`support_replica.log`), support logs contained two events for `support_002`: `contact_query_completed` (which initially mapped to `SUPPORT_MESSAGE` / `REPORT_EXPOSED_PII`) and `deletion_marker_check` (which mapped to `SEARCH_INDEX_ENTRY` / `REPORT_REMAINING_RECORD`). This produced duplicate steps with conflicting operations.
* **Fix:** Enforced strict violation prioritization in `code/auditor.py`: `REPORT_REMAINING_RECORD` strictly overrides `REPORT_EXPOSED_PII` for the same resource ID. Furthermore, index logs (`source=legacy_contact_index`) were correctly mapped to `SEARCH_INDEX_ENTRY` (Rule 03: DELETE). This resolved `case_10` to 100% exact match.

---

## 5. Conclusion

The deletion audit engine achieves **100.00% status accuracy**, **84.38% exact sequence accuracy**, **94.82% step accuracy**, and **97.24% field accuracy** across the benchmark sample dataset, and passes 100% of custom integration tests. The engine runs deterministically in < 2 seconds across all 518 evaluation requests without external model dependencies, producing fully validated and audit-compliant output.
