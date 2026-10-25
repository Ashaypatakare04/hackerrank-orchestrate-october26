"""
Core data structures for HackerRank Orchestrate: Ghost Data Still Exists.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Set, Dict, Any

ALLOWED_STATUSES = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}

# Legal combinations of (phase, operation, state)
LEGAL_STEPS = {
    # Findings
    ("FINDING", "REPORT_REMAINING_RECORD", "PRESENT"),
    ("FINDING", "REPORT_EXPOSED_PII", "PRESENT"),
    ("FINDING", "REPORT_ACTIVE_DATA_FLOW", "ACTIVE"),
    ("FINDING", "REPORT_RESTORE_RISK", "ACTIVE"),
    # Remediation
    ("REMEDIATION", "DISABLE_DATA_FLOW", "DISABLED"),
    ("REMEDIATION", "BLOCK_RESTORE", "BLOCKED"),
    ("REMEDIATION", "DELETE_RECORD", "ABSENT"),
    ("REMEDIATION", "REDACT_RECORD", "REDACTED"),
    ("REMEDIATION", "ANONYMIZE_RECORD", "ANONYMIZED"),
    # Verification
    ("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT"),
    ("VERIFICATION", "VERIFY_RECORD_PRESENT", "PRESENT"),
    ("VERIFICATION", "VERIFY_RECORD_REDACTED", "REDACTED"),
    ("VERIFICATION", "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"),
    ("VERIFICATION", "VERIFY_DATA_FLOW_DISABLED", "DISABLED"),
    ("VERIFICATION", "VERIFY_RESTORE_BLOCKED", "BLOCKED"),
}

OPERATION_ORDER = {
    # Phase order: FINDING=0, REMEDIATION=1, VERIFICATION=2
    "FINDING": [
        "REPORT_REMAINING_RECORD",
        "REPORT_EXPOSED_PII",
        "REPORT_ACTIVE_DATA_FLOW",
        "REPORT_RESTORE_RISK",
    ],
    "REMEDIATION": [
        "DISABLE_DATA_FLOW",
        "BLOCK_RESTORE",
        "DELETE_RECORD",
        "REDACT_RECORD",
        "ANONYMIZE_RECORD",
    ],
    "VERIFICATION": [
        "VERIFY_RECORD_ABSENT",
        "VERIFY_RECORD_PRESENT",
        "VERIFY_RECORD_REDACTED",
        "VERIFY_RECORD_ANONYMIZED",
        "VERIFY_DATA_FLOW_DISABLED",
        "VERIFY_RESTORE_BLOCKED",
    ],
}

SYSTEM_PREFIX_MAP = {
    "account": "account_service",
    "analytics": "analytics_platform",
    "backup": "backup_service",
    "export": "export_service",
    "tombstone": "identity_service",
    "data_flow": "integration_service",
    "search": "search_service",
    "audit_record": "security_service",
    "support": "support_platform",
}


def normalize_system_id(svc_or_res: str) -> str:
    if svc_or_res in [
        "account_service",
        "analytics_platform",
        "backup_service",
        "export_service",
        "identity_service",
        "integration_service",
        "search_service",
        "security_service",
        "support_platform",
    ]:
        return svc_or_res

    for pfx, sys_id in SYSTEM_PREFIX_MAP.items():
        if svc_or_res.startswith(pfx) or pfx in svc_or_res:
            return sys_id
    return svc_or_res


@dataclass
class Step:
    step_no: int
    phase: str
    system_id: str
    resource_id: str
    operation: str
    state: str
    evidence_id: str = ""

    def validate(self) -> None:
        key = (self.phase, self.operation, self.state)
        if key not in LEGAL_STEPS:
            raise ValueError(f"Illegal step tuple: {key}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_no": self.step_no,
            "phase": self.phase,
            "system_id": self.system_id,
            "resource_id": self.resource_id,
            "operation": self.operation,
            "state": self.state,
            "evidence_id": self.evidence_id,
        }


@dataclass
class DeletionRequest:
    case_id: str
    email: str
    requested_at: str
    reported_status: str
    reported_at: str
    audit_at: str
    request_text: str


@dataclass
class UserProfile:
    user_id: str
    primary_email: str
    all_emails: Set[str] = field(default_factory=set)
    all_phones: Set[str] = field(default_factory=set)
    all_names: Set[str] = field(default_factory=set)
    all_hashes: Set[str] = field(default_factory=set)
