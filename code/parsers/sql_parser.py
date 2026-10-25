"""
SQL snapshot parser using in-memory SQLite.
"""
import sqlite3
import json
from typing import List, Dict, Any

TABLE_SYSTEM_MAP = {
    "customer_profiles": "account_service",
    "customer_profiles_failover_replica": "account_service",
    "customer_profiles_primary": "account_service",
    "customer_data_primary": "account_service",
    "customer_data_read_replica": "account_service",
    "customer_data_replica_ap_south": "account_service",
    "customer_data_replica_eu_west": "account_service",
    "customer_data_failover_replica": "account_service",
    "customer_data_reporting_replica": "account_service",
    "customer_search_documents": "search_service",
    "search_documents_primary": "search_service",
    "customer_analytics_profiles": "analytics_platform",
    "support_records": "support_platform",
    "customer_exports": "export_service",
    "connector_subscriptions": "integration_service",
    "backup_restore_entries": "backup_service",
    "security_audit_records": "security_service",
    "deleted_customer_references": "identity_service",
}


def parse_sql_evidence(file_path: str, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
    """
    Executes a SQL file in an in-memory SQLite database and extracts all resource records.
    """
    with open(file_path, "r", encoding="utf-8") as fp:
        sql_text = fp.read()

    conn = sqlite3.connect(":memory:")
    records = []
    try:
        conn.executescript(sql_text)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]

        for tbl in tables:
            if tbl == "snapshot_scope":
                continue

            system_id = TABLE_SYSTEM_MAP.get(tbl, "unknown_service")
            cur.execute(f"PRAGMA table_info({tbl})")
            columns = [c[1] for c in cur.fetchall()]

            cur.execute(f"SELECT * FROM {tbl}")
            for row in cur.fetchall():
                row_dict = dict(zip(columns, row))
                res_id = row_dict.get("resource_id")
                if not res_id:
                    continue

                uid = (
                    row_dict.get("user_id")
                    or row_dict.get("customer_reference")
                    or row_dict.get("subject_reference")
                )
                email = (
                    row_dict.get("email")
                    or row_dict.get("customer_email")
                    or row_dict.get("requester_email")
                    or row_dict.get("owner_email")
                )
                phone = (
                    row_dict.get("phone")
                    or row_dict.get("requester_phone")
                    or row_dict.get("owner_phone")
                )
                email_hash = row_dict.get("email_hash")

                state = "PRESENT"
                category = "UNKNOWN"

                # Check if row has record_json column
                if "record_json" in row_dict and row_dict["record_json"]:
                    try:
                        parsed = json.loads(row_dict["record_json"])
                        doc = parsed.get("document") if isinstance(parsed.get("document"), dict) else {}
                        uid = (
                            uid
                            or parsed.get("user_id")
                            or parsed.get("customer_reference")
                            or parsed.get("subject_reference")
                            or doc.get("customer_reference")
                            or doc.get("user_id")
                        )
                        email = (
                            email
                            or parsed.get("email")
                            or parsed.get("customer_email")
                            or parsed.get("requester_email")
                            or parsed.get("owner_email")
                            or doc.get("email")
                        )
                        phone = (
                            phone
                            or parsed.get("phone")
                            or parsed.get("requester_phone")
                            or parsed.get("owner_phone")
                            or doc.get("phone")
                        )
                        email_hash = email_hash or parsed.get("email_hash")
                        if "origin_system" in row_dict and row_dict["origin_system"]:
                            system_id = row_dict["origin_system"]
                        
                        col_name = row_dict.get("collection_name", "")
                        if "search" in col_name:
                            category = "SEARCH_INDEX_ENTRY"
                            state = "PRESENT"
                        elif "profile" in col_name:
                            category = "USER_PROFILE"
                            acc_st = parsed.get("account_status", "ACTIVE")
                            state = "PRESENT" if acc_st == "ACTIVE" else "ABSENT"
                        elif "analytics" in col_name:
                            category = "ANALYTICS_PROFILE"
                            is_anon = not (parsed.get("email") or parsed.get("phone") or parsed.get("user_id") or parsed.get("customer_reference"))
                            state = "ANONYMIZED" if is_anon else "PRESENT"
                        elif "deleted" in col_name or "tombstone" in col_name:
                            category = "ACCOUNT_TOMBSTONE"
                            is_redacted = not (parsed.get("email") or parsed.get("phone") or parsed.get("full_name") or parsed.get("name"))
                            state = "REDACTED" if is_redacted else "PRESENT"
                        elif "backup" in col_name:
                            category = "BACKUP_ARCHIVE"
                            state = "ACTIVE" if parsed.get("restore_allowed") in [True, 1, "true", "TRUE"] else "BLOCKED"
                        elif "connector" in col_name:
                            category = "ACTIVE_DATA_FLOW"
                            state = "ACTIVE" if parsed.get("enabled") in [True, 1, "true", "TRUE"] else "DISABLED"
                    except Exception:
                        pass

                if "backup_restore" in tbl:
                    category = "BACKUP_ARCHIVE"
                    restore_allowed = row_dict.get("restore_allowed")
                    if restore_allowed in [True, 1, "true", "TRUE"]:
                        state = "ACTIVE"
                    else:
                        state = "BLOCKED"
                elif "connector_subscriptions" in tbl:
                    category = "ACTIVE_DATA_FLOW"
                    enabled = row_dict.get("enabled")
                    if enabled in [True, 1, "true", "TRUE"]:
                        state = "ACTIVE"
                    else:
                        state = "DISABLED"
                elif "security_audit" in tbl:
                    category = "SECURITY_AUDIT_LOG"
                    state = "PRESENT"
                elif "search" in tbl:
                    category = "SEARCH_INDEX_ENTRY"
                    state = "PRESENT"
                elif "analytics" in tbl:
                    category = "ANALYTICS_PROFILE"
                    if email or phone or uid:
                        state = "PRESENT"
                    else:
                        state = "ANONYMIZED"
                elif "support" in tbl:
                    category = "SUPPORT_MESSAGE"
                    if not (row_dict.get("requester_email") or row_dict.get("requester_phone") or row_dict.get("requester_name")):
                        state = "REDACTED" if row_dict.get("customer_reference") else "PRESENT"
                    else:
                        state = "PRESENT"
                elif "export" in tbl:
                    category = "USER_EXPORT"
                    state = "PRESENT"
                elif "profiles" in tbl or "customer_data" in tbl:
                    if category == "UNKNOWN":
                        category = "USER_PROFILE"
                        state = "PRESENT"

                records.append({
                    "system_id": system_id,
                    "resource_id": res_id,
                    "user_id": uid,
                    "email": email.lower() if email else None,
                    "phone": phone,
                    "email_hash": email_hash,
                    "table": tbl,
                    "state": state,
                    "category": category,
                    "evidence_id": file_id,
                    "captured_at": captured_at,
                    "raw": row_dict,
                })
    except Exception as e:
        print(f"Error parsing SQL file {file_path}: {e}")
    finally:
        conn.close()

    return records
