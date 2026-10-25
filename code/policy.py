"""
Policy engine implementing deletion_rules.csv and step sequencing rules.
"""
from typing import List, Dict, Any, Tuple
from models import Step, OPERATION_ORDER

# Mapping from system/category to policy action
ACTION_MAP = {
    "account_service": "DELETE",
    "search_service": "DELETE",
    "export_service": "DELETE",
    "support_platform": "REDACT",
    "analytics_platform": "ANONYMIZE",
    "identity_service": "REDACT",
    "integration_service": "DISABLE",
    "backup_service": "BLOCK",
    "security_service": "RETAIN",
}

PHASE_RANK = {
    "FINDING": 0,
    "REMEDIATION": 1,
    "VERIFICATION": 2,
}


def sort_steps(steps: List[Step]) -> List[Step]:
    """
    Sorts steps according to official contract:
    1. Phase: FINDING -> REMEDIATION -> VERIFICATION
    2. Operation order within phase (problem_statement.md table)
    3. system_id ascending
    4. resource_id ascending
    Assigns consecutive step_no starting at 1.
    """
    def sort_key(s: Step) -> Tuple[int, int, str, str]:
        p_rank = PHASE_RANK.get(s.phase, 99)
        op_list = OPERATION_ORDER.get(s.phase, [])
        op_rank = op_list.index(s.operation) if s.operation in op_list else 99
        return (p_rank, op_rank, s.system_id, s.resource_id)

    sorted_list = sorted(steps, key=sort_key)
    for idx, s in enumerate(sorted_list, start=1):
        s.step_no = idx
        s.validate()

    return sorted_list
