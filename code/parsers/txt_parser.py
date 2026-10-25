"""
Text file parser for customer_account_handover shift logs.
"""
from typing import List, Dict, Any


def parse_txt_evidence(file_path: str, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
    """
    Parses shift handover log entries:
    timestamp | system | resource_id | category | status | email_or_uid
    """
    records = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as fp:
        for line in fp:
            line = line.strip()
            if not line.startswith("- "):
                continue
            parts = [p.strip() for p in line[2:].split("|")]
            if len(parts) >= 6:
                ts, svc, res_id, cat, status, ident = parts[:6]
                state = "PRESENT"
                if status in ["NOT_FOUND", "ABSENT"]:
                    state = "ABSENT"
                elif status in ["RETAINED", "VALID"]:
                    state = "PRESENT"
                elif status in ["ANONYMIZED"]:
                    state = "ANONYMIZED"
                elif status in ["REDACTED"]:
                    state = "REDACTED"
                elif status in ["ACTIVE"]:
                    state = "ACTIVE"
                elif status in ["BLOCKED"]:
                    state = "BLOCKED"
                elif status in ["DISABLED"]:
                    state = "DISABLED"
                elif status in ["IDENTIFIABLE", "FOUND"]:
                    state = "PRESENT"

                user_id = None
                email = None
                if ident.startswith("user_"):
                    user_id = ident
                elif "@" in ident:
                    email = ident.lower()

                records.append({
                    "system_id": svc,
                    "resource_id": res_id,
                    "user_id": user_id,
                    "email": email,
                    "state": state,
                    "category": cat,
                    "evidence_id": file_id,
                    "captured_at": captured_at,
                    "raw": line,
                })

    return records
