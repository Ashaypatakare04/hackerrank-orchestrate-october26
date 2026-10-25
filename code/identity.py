"""
Identity resolution module.
Recovers current and historical identifiers using user_identities.csv and user_audit_log.csv.
"""
import csv
from typing import Dict, Optional, Set
from models import UserProfile


class IdentityResolver:
    def __init__(self, identities_path: str, audit_log_path: str):
        self.users_by_id: Dict[str, UserProfile] = {}
        self.email_to_uid: Dict[str, str] = {}
        self._load_identities(identities_path)
        self._load_audit_log(audit_log_path)

    def _load_identities(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row["user_id"]
                email = row["email"].strip().lower()
                profile = UserProfile(
                    user_id=uid,
                    primary_email=email,
                    all_emails={email},
                    all_phones={row["phone"].strip()} if row.get("phone") else set(),
                    all_names={row["name"].strip().lower()} if row.get("name") else set(),
                    all_hashes={row["email_hash"].strip().lower()} if row.get("email_hash") else set(),
                )
                self.users_by_id[uid] = profile
                self.email_to_uid[email] = uid

    def _load_audit_log(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row["user_id"]
                if uid not in self.users_by_id:
                    continue
                profile = self.users_by_id[uid]
                field_name = row["field_name"]
                old_val = (row["old_value"] or "").strip()
                new_val = (row["new_value"] or "").strip()

                if field_name == "email":
                    if old_val:
                        low_old = old_val.lower()
                        profile.all_emails.add(low_old)
                        self.email_to_uid[low_old] = uid
                    if new_val:
                        low_new = new_val.lower()
                        profile.all_emails.add(low_new)
                        self.email_to_uid[low_new] = uid
                elif field_name == "phone":
                    if old_val:
                        profile.all_phones.add(old_val)
                    if new_val:
                        profile.all_phones.add(new_val)
                elif field_name == "name":
                    if old_val:
                        profile.all_names.add(old_val.lower())
                    if new_val:
                        profile.all_names.add(new_val.lower())
                elif field_name == "email_hash":
                    if old_val:
                        profile.all_hashes.add(old_val.lower())
                    if new_val:
                        profile.all_hashes.add(new_val.lower())

    def resolve(self, email_or_uid: str) -> Optional[UserProfile]:
        key = email_or_uid.strip().lower()
        if key in self.users_by_id:
            return self.users_by_id[key]
        uid = self.email_to_uid.get(key)
        if uid:
            return self.users_by_id.get(uid)
        return None
