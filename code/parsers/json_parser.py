"""
JSON evidence parser for service resource exports, snapshot bundles, and manifests.
"""
import json
from typing import List, Dict, Any


def parse_json_evidence(file_path: str, file_id: str, captured_at: str) -> List[Dict[str, Any]]:
    """
    Parses a JSON evidence file and extracts normalized resource records.
    """
    records = []
    with open(file_path, "r", encoding="utf-8") as fp:
        try:
            data = json.load(fp)
        except Exception as e:
            print(f"Error loading JSON {file_path}: {e}")
            return records

    # Format 1: service_resource_export_*.json
    if "service_exports" in data:
        exports = data["service_exports"]

        # 1. account_service
        acc = exports.get("account_service", {})
        for item in acc.get("profile_lookups", []):
            res_id = item.get("resource_id")
            sc = item.get("status_code", 404)
            prof = item.get("profile") or {}
            email = prof.get("email")
            uid = prof.get("customer_reference")
            state = "ABSENT" if sc == 404 else "PRESENT"
            records.append({
                "system_id": "account_service",
                "resource_id": res_id,
                "user_id": uid,
                "email": email.lower() if email else None,
                "state": state,
                "category": "USER_PROFILE",
                "evidence_id": file_id,
                "captured_at": captured_at,
                "raw": item,
            })

        # 2. analytics_platform
        ana = exports.get("analytics_platform", {})
        for item in ana.get("profiles", []):
            res_id = item.get("resource_id")
            uid = item.get("customer_reference")
            email = item.get("email")
            phone = item.get("phone")
            email_hash = item.get("email_hash")
            is_anonymized = not (email or phone or uid or email_hash)
            state = "ANONYMIZED" if is_anonymized else "PRESENT"
            records.append({
                "system_id": "analytics_platform",
                "resource_id": res_id,
                "user_id": uid,
                "email": email.lower() if email else None,
                "phone": phone,
                "state": state,
                "category": "ANALYTICS_PROFILE",
                "evidence_id": file_id,
                "captured_at": captured_at,
                "raw": item,
            })

        # 3. backup_service
        bk = exports.get("backup_service", {})
        for item in bk.get("restore_entries", []):
            res_id = item.get("resource_id")
            uid = item.get("customer_reference")
            email = item.get("customer_email")
            restore_allowed = item.get("restore_allowed", False)
            state = "ACTIVE" if restore_allowed else "BLOCKED"
            records.append({
                "system_id": "backup_service",
                "resource_id": res_id,
                "user_id": uid,
                "email": email.lower() if email else None,
                "state": state,
                "category": "BACKUP_ARCHIVE",
                "evidence_id": file_id,
                "captured_at": captured_at,
                "raw": item,
            })

        # 4. export_service
        exp = exports.get("export_service", {})
        for item in exp.get("exports", []):
            res_id = item.get("resource_id")
            uid = item.get("customer_reference")
            email = item.get("owner_email")
            records.append({
                "system_id": "export_service",
                "resource_id": res_id,
                "user_id": uid,
                "email": email.lower() if email else None,
                "state": "PRESENT",
                "category": "USER_EXPORT",
                "evidence_id": file_id,
                "captured_at": captured_at,
                "raw": item,
            })

        # 5. integration_service
        integ = exports.get("integration_service", {})
        for item in integ.get("connectors", []):
            res_id = item.get("resource_id")
            uid = item.get("customer_reference")
            email = item.get("customer_email")
            enabled = item.get("enabled", False)
            state = "ACTIVE" if enabled else "DISABLED"
            records.append({
                "system_id": "integration_service",
                "resource_id": res_id,
                "user_id": uid,
                "email": email.lower() if email else None,
                "state": state,
                "category": "ACTIVE_DATA_FLOW",
                "evidence_id": file_id,
                "captured_at": captured_at,
                "raw": item,
            })

        # 6. search_service
        srch = exports.get("search_service", {})
        for item in srch.get("index_queries", []):
            res_id = item.get("resource_id")
            query = item.get("query")
            hits = item.get("hits", {}).get("total", 0)
            state = "PRESENT" if hits > 0 else "ABSENT"
            # Extract doc info
            docs = item.get("hits", {}).get("documents", [])
            doc_email = docs[0].get("email") if docs else query
            doc_uid = docs[0].get("customer_reference") if docs else None
            records.append({
                "system_id": "search_service",
                "resource_id": res_id,
                "user_id": doc_uid,
                "email": doc_email.lower() if doc_email else None,
                "state": state,
                "category": "SEARCH_INDEX_ENTRY",
                "evidence_id": file_id,
                "captured_at": captured_at,
                "raw": item,
            })

        # 7. security_service
        sec = exports.get("security_service", {})
        for item in sec.get("audit_records", []):
            res_id = item.get("resource_id")
            uid = item.get("subject_reference")
            records.append({
                "system_id": "security_service",
                "resource_id": res_id,
                "user_id": uid,
                "state": "PRESENT",
                "category": "SECURITY_AUDIT_LOG",
                "evidence_id": file_id,
                "captured_at": captured_at,
                "retention_until": item.get("retention_until"),
                "raw": item,
            })

        # 8. support_platform
        supp = exports.get("support_platform", {})
        for item in supp.get("tickets", []):
            res_id = item.get("resource_id")
            uid = item.get("customer_reference")
            email = item.get("requester_email")
            name = item.get("requester_name")
            phone = item.get("requester_phone")
            is_redacted = not (email or name or phone)
            state = "REDACTED" if is_redacted else "PRESENT"
            records.append({
                "system_id": "support_platform",
                "resource_id": res_id,
                "user_id": uid,
                "email": email.lower() if email else None,
                "state": state,
                "category": "SUPPORT_MESSAGE",
                "evidence_id": file_id,
                "captured_at": captured_at,
                "raw": item,
            })

    # Format 2: customer_data_snapshot_bundle_*.json
    elif "snapshots" in data:
        for snap in data["snapshots"]:
            ds = snap.get("data_store")
            recs = snap.get("records", [])
            if ds == "account_service":
                for r in recs:
                    records.append({
                        "system_id": "account_service",
                        "resource_id": r.get("resource_id"),
                        "user_id": r.get("user_id"),
                        "email": r.get("email").lower() if r.get("email") else None,
                        "state": "PRESENT",
                        "category": "USER_PROFILE",
                        "evidence_id": file_id,
                        "captured_at": captured_at,
                        "raw": r,
                    })
            elif ds == "identity_service":
                for r in recs:
                    res_id = r.get("resource_id")
                    uid = r.get("subject_reference")
                    email = r.get("email")
                    name = r.get("name")
                    phone = r.get("phone")
                    is_redacted = not (email or name or phone)
                    state = "REDACTED" if is_redacted else "PRESENT"
                    records.append({
                        "system_id": "identity_service",
                        "resource_id": res_id,
                        "user_id": uid,
                        "email": email.lower() if email else None,
                        "state": state,
                        "category": "ACCOUNT_TOMBSTONE",
                        "evidence_id": file_id,
                        "captured_at": captured_at,
                        "raw": r,
                    })
            elif ds == "security_service":
                for r in recs:
                    records.append({
                        "system_id": "security_service",
                        "resource_id": r.get("resource_id"),
                        "user_id": r.get("subject_reference"),
                        "state": "PRESENT",
                        "category": "SECURITY_AUDIT_LOG",
                        "evidence_id": file_id,
                        "captured_at": captured_at,
                        "raw": r,
                    })

    # Format 3: Generic collections (customer_export_jobs, customer_analytics_report, etc.)
    elif "records" in data and isinstance(data["records"], list):
        col = data.get("collection", "")
        for r in data["records"]:
            res_id = r.get("resource_id")
            if not res_id:
                continue
            uid = r.get("user_id") or r.get("customer_reference") or r.get("subject_reference")
            email = r.get("email") or r.get("owner_email") or r.get("requester_email") or r.get("customer_email")
            sys_prefix = res_id.split("_")[0]
            sys_id = {
                "export": "export_service",
                "analytics": "analytics_platform",
                "data": "integration_service",
                "backup": "backup_service",
                "audit": "security_service",
                "search": "search_service",
                "support": "support_platform",
                "account": "account_service",
                "tombstone": "identity_service",
            }.get(sys_prefix, "unknown_service")

            state = "PRESENT"
            if "analytics" in sys_id and not (email or uid):
                state = "ANONYMIZED"
            elif "backup" in sys_id:
                restore_allowed = r.get("restore_allowed", False)
                state = "ACTIVE" if restore_allowed else "BLOCKED"
            elif "integration" in sys_id:
                enabled = r.get("enabled", False)
                state = "ACTIVE" if enabled else "DISABLED"

            records.append({
                "system_id": sys_id,
                "resource_id": res_id,
                "user_id": uid,
                "email": email.lower() if email else None,
                "state": state,
                "category": col or sys_id,
                "evidence_id": file_id,
                "captured_at": captured_at,
                "raw": r,
            })

    return records
