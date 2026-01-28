# Copyright (c) 2025
# This is a proprietary solution. Redistribution of modified versions is prohibited.
# Open-source dependency licenses are documented in the README table.

import os
from typing import List, Dict, Optional

try:
    from simple_salesforce import Salesforce
except Exception:  # pragma: no cover - optional dependency for test mode
    Salesforce = None


class SalesforceClient:
    def __init__(self, *, username: str, password: str, security_token: str, domain: str = "login", test_mode: bool = False, mock_data: Optional[dict] = None):
        self.test_mode = test_mode
        self.mock_data = mock_data or {}
        if not self.test_mode:
            if Salesforce is None:
                raise ImportError("simple_salesforce is required for non-test mode")
            self.sf = Salesforce(
                username=username,
                password=password,
                security_token=security_token,
                domain=domain,
            )
        else:
            self.sf = None

    def query(self, soql: str) -> List[Dict]:
        if self.test_mode:
            return self.mock_data.get("query", [])
        result = self.sf.query_all(soql)
        return result.get("records", [])

    def get_content_document_links(self, record_id: str) -> List[Dict]:
        if self.test_mode:
            return self.mock_data.get("links", {}).get(record_id, [])
        soql = f"SELECT ContentDocumentId, LinkedEntityId FROM ContentDocumentLink WHERE LinkedEntityId = '{record_id}'"
        records = self.sf.query_all(soql)["records"]
        return records

    def get_latest_content_version(self, content_document_id: str) -> Optional[Dict]:
        if self.test_mode:
            return self.mock_data.get("versions", {}).get(content_document_id)
        soql = (
            "SELECT Id, Title, FileExtension, VersionData "
            "FROM ContentVersion WHERE ContentDocumentId = '{}' ORDER BY VersionNumber DESC LIMIT 1".format(content_document_id)
        )
        records = self.sf.query_all(soql)["records"]
        return records[0] if records else None

    def download_content_version_data(self, version: Dict) -> bytes:
        data = version.get("VersionData")
        if self.test_mode:
            return data if isinstance(data, bytes) else (data or "").encode()

        if not isinstance(data, str):
            return b""

        # 絶対 URL を合成
        base = self.sf.base_url.split("/services")[0]
        url  = data if data.startswith("http") else base + data

        # ★ simple-salesforce のリフレッシュ機構付きで呼び出す
        resp = self.sf._call_salesforce("GET", url)
        return resp.content
