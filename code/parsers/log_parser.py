"""
Log evidence parser for readback traces, observability events, and audit logs.
"""
import re
import json
from typing import List, Dict, Any


def parse_key_value_line(line: str) -> Dict[str, str]:
    """Parses key=value or JSON object from a log line."""
    idx_brace = line.find('{')
    if idx_brace != -1:
        try:
            data = json.loads(line[idx_brace:])
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    pattern = r'([a-zA-Z0-9_]+)=(?:"([^"]*)"|([^\s]+))'
    matches = re.findall(pattern, line)
    d = {}
    for k, v1, v2 in matches:
        d[k] = v1 if v1 != "" else v2
    return d


def parse_log_evidence(file_path: str, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
    """
    Parses a log file and extracts structured resource records.
    """
    records = []
    trace_to_email = {}
    trace_to_uid = {}
    trace_to_hash = {}

    with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
        lines = fp.readlines()

    # First pass: map trace_id to subject / email / hash
    for line in lines:
        kv = parse_key_value_line(line)
        tid = kv.get("trace_id")
        if not tid:
            continue
        subj = (
            kv.get("subject_ref")
            or kv.get("subject_key")
            or kv.get("lookup_key")
            or kv.get("matched_value")
            or kv.get("correlation_key")
        )
        if subj and subj != "null":
            if "@" in subj:
                trace_to_email[tid] = subj.lower()
            elif subj.startswith("user_"):
                trace_to_uid[tid] = subj
            elif len(subj) == 64 and all(c in "0123456789abcdefABCDEF" for c in subj):
                trace_to_hash[tid] = subj.lower()

    # Second pass: extract resource observations
    for line in lines:
        kv = parse_key_value_line(line)
        res_id = kv.get("resource_id")
        if not res_id:
            continue

        svc = kv.get("service")
        if not svc:
            pfx = res_id.split("_")[0]
            svc = {
                "account": "account_service",
                "analytics": "analytics_platform",
                "backup": "backup_service",
                "export": "export_service",
                "data": "integration_service",
                "search": "search_service",
                "audit": "security_service",
                "support": "support_platform",
                "tombstone": "identity_service",
            }.get(pfx, "unknown_service")

        tid = kv.get("trace_id")
        uid = kv.get("subject_reference") or kv.get("customer_reference")
        email = (
            kv.get("email")
            or kv.get("requester_email")
            or kv.get("customer_email")
            or kv.get("lookup_key")
            or kv.get("matched_value")
            or kv.get("subject_key")
        )
        email_hash = kv.get("email_hash") or kv.get("correlation_key")

        if tid in trace_to_email and not email:
            email = trace_to_email[tid]
        if tid in trace_to_uid and not uid:
            uid = trace_to_uid[tid]
        if tid in trace_to_hash and not email_hash:
            email_hash = trace_to_hash[tid]

        if uid == "null":
            uid = None
        if email == "null":
            email = None
        if email and "@" not in email:
            if email.startswith("user_") and not uid:
                uid = email
            email = None

        event = kv.get("event", "")
        if event.endswith("_started"):
            continue

        state = "PRESENT"
        category = "UNKNOWN"

        # 1. account_service
        if "account" in svc:
            category = "USER_PROFILE"
            rows = kv.get("rows")
            sc = kv.get("http_status")
            if rows == "0" or sc == "404":
                state = "ABSENT"
            else:
                state = "PRESENT"

        # 2. analytics_platform
        elif "analytics" in svc:
            category = "ANALYTICS_PROFILE"
            ana_email = kv.get("email")
            ana_phone = kv.get("phone")
            ana_uid = kv.get("customer_reference")
            is_anon = (
                (ana_email in [None, "null"])
                and (ana_phone in [None, "null"])
                and (ana_uid in [None, "null"])
                and (email in [None, "null"])
                and (email_hash in [None, "null"])
            )
            state = "ANONYMIZED" if is_anon else "PRESENT"

        # 3. backup_service
        elif "backup" in svc:
            category = "BACKUP_ARCHIVE"
            restore_allowed = kv.get("restore_allowed")
            eligible = kv.get("eligible")
            del_block = kv.get("deletion_block")
            if restore_allowed in ["true", "True", "1"] or (eligible == "true" and del_block == "false"):
                state = "ACTIVE"
            else:
                state = "BLOCKED"

        # 4. integration_service
        elif "integration" in svc:
            category = "ACTIVE_DATA_FLOW"
            enabled = kv.get("enabled")
            if enabled in ["true", "True", "1"]:
                state = "ACTIVE"
            else:
                state = "DISABLED"

        # 5. search_service
        elif "search" in svc:
            category = "SEARCH_INDEX_ENTRY"
            hits = kv.get("total_hits") or kv.get("hits") or kv.get("rows")
            if hits == "0":
                state = "ABSENT"
            else:
                state = "PRESENT"

        # 6. security_service
        elif "security" in svc:
            category = "SECURITY_AUDIT_LOG"
            state = "PRESENT"

        # 7. support_platform
        elif "support" in svc:
            source_val = kv.get("source", "")
            if "index" in source_val.lower() or kv.get("event") == "deletion_marker_check":
                category = "SEARCH_INDEX_ENTRY"
                state = "PRESENT"
            else:
                category = "SUPPORT_MESSAGE"
                state = "PRESENT"

        records.append({
            "system_id": svc,
            "resource_id": res_id,
            "user_id": uid,
            "email": email.lower() if email else None,
            "email_hash": email_hash,
            "state": state,
            "category": category,
            "evidence_id": file_id,
            "captured_at": captured_at,
            "retention_until": kv.get("retention_until"),
            "raw": kv,
        })

    return records
