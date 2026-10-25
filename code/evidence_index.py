"""
Evidence indexing module.
Loads, parses, and indexes all evidence files with temporal filtering (captured_at <= audit_at).
"""
import csv
import os
from typing import List, Dict, Any, Optional
from models import UserProfile
from parsers.sql_parser import parse_sql_evidence
from parsers.json_parser import parse_json_evidence
from parsers.log_parser import parse_log_evidence
from parsers.pdf_parser import parse_pdf_document
from parsers.image_parser import parse_image_evidence
from parsers.txt_parser import parse_txt_evidence


class EvidenceIndex:
    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir
        self.manifest_path = os.path.join(dataset_dir, "evidence_files.csv")
        self.manifest: Dict[str, Dict[str, Any]] = {}
        self.all_records: List[Dict[str, Any]] = []
        self._load_and_index()

    def _load_and_index(self) -> None:
        if not os.path.exists(self.manifest_path):
            print(f"Warning: Manifest {self.manifest_path} does not exist.")
            return

        with open(self.manifest_path, "r", encoding="utf-8") as fp:
            manifest_rows = list(csv.DictReader(fp))

        for row in manifest_rows:
            file_id = row["file_id"]
            rel_path = row["file_path"].replace("/", os.sep)
            abs_path = os.path.join(self.dataset_dir, rel_path)
            captured_at = row["captured_at"]

            self.manifest[file_id] = {
                "file_id": file_id,
                "path": abs_path,
                "captured_at": captured_at,
                "origin": row.get("origin", ""),
            }

            if not os.path.exists(abs_path):
                continue

            ext = os.path.splitext(abs_path)[1].lower()
            recs = []
            if ext == ".sql":
                recs = parse_sql_evidence(abs_path, file_id, captured_at)
            elif ext == ".json":
                recs = parse_json_evidence(abs_path, file_id, captured_at)
            elif ext == ".log":
                recs = parse_log_evidence(abs_path, file_id, captured_at)
            elif ext == ".pdf":
                recs = parse_pdf_document(abs_path, file_id, captured_at)
            elif ext == ".png":
                recs = parse_image_evidence(abs_path, file_id, captured_at)
            elif ext == ".txt":
                recs = parse_txt_evidence(abs_path, file_id, captured_at)

            self.all_records.extend(recs)

    def get_latest_evidence_before(
        self, audit_at: str, origin_keyword: str = ""
    ) -> Optional[str]:
        """Returns the file_id of the latest captured evidence before audit_at matching origin."""
        best_id = None
        best_time = None
        for fid, meta in self.manifest.items():
            cap = meta["captured_at"]
            if cap <= audit_at:
                if origin_keyword and origin_keyword not in meta["origin"] and origin_keyword not in meta["path"]:
                    continue
                if best_time is None or cap > best_time:
                    best_time = cap
                    best_id = fid
        return best_id

    def query_for_user(self, profile: UserProfile, audit_at: str) -> List[Dict[str, Any]]:
        """
        Returns all records associated with the user captured at or before audit_at.
        """
        matched = []
        uid = profile.user_id
        emails = profile.all_emails

        for r in self.all_records:
            if r["captured_at"] > audit_at:
                continue

            r_uid = r.get("user_id")
            r_email = r.get("email")
            r_phone = r.get("phone")
            r_hash = r.get("email_hash")

            is_match = False
            if r_uid and r_uid == uid:
                is_match = True
            elif r_email and r_email in emails:
                is_match = True
            elif r_hash and r_hash in profile.all_hashes:
                is_match = True
            elif r_phone and r_phone in profile.all_phones:
                is_match = True

            if is_match:
                matched.append(r)

        return matched

    def query_by_resource(self, resource_id: str, audit_at: str) -> Optional[Dict[str, Any]]:
        """
        Returns the latest evidence record for resource_id captured at or before audit_at.
        """
        latest = None
        for r in self.all_records:
            if r.get("resource_id") == resource_id:
                if r["captured_at"] <= audit_at:
                    if latest is None or r["captured_at"] > latest["captured_at"]:
                        latest = r
        return latest
