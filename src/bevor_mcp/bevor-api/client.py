import requests
from typing import Any, Dict, Optional
import os
import asyncio
from pathlib import Path


class BevorApiClient:
    """Bevor API client wrapper.

    Initialize with an API key. Optionally set a base_url.
    """

    def __init__(self, bevor_api_key: str, project_id: str, contracts_folder: str = "contracts") -> None:
        self.base_url = (os.getenv("BEVOR_API_URL") or "http://api.bevor.io").rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {bevor_api_key}",
            "Content-Type": "application/json", 
            "Accept": "application/json",
        })

        self.project_id = project_id

        # 1) Pull contracts from folder
        contracts_map = self.pull_in_solidity_test_folder(contracts_folder)
        # 2) Create version by uploading folder
        version_resp = self.versions_create_folder(contracts_map, self.project_id)
        self.version_mapping_id = (
            (version_resp or {}).get("version_mapping_id")
            or (version_resp or {}).get("version_id")
            or (version_resp or {}).get("id")
        )
        # 3) Create chat for that version mapping
        self.chat_id = None
        if self.version_mapping_id:
            chat_resp = self.chat_with_version(self.version_mapping_id)
            if isinstance(chat_resp, dict):
                self.chat_id = chat_resp.get("id") or chat_resp.get("chat_id")


    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        timeout: Optional[float] = 60.0,
    ) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        # Use asyncio.to_thread to run synchronous requests in a separate thread
        return await asyncio.to_thread(
            self.session.request,
            method=method.upper(),
            url=url,
            params=params,
            json=json,
            stream=stream,
            timeout=timeout,
        )

    def pull_in_solidity_test_folder(self, folder_path: str = "contracts") -> Dict[str, bytes]:
        """Read all files from the contracts folder and return mapping of filename -> bytes."""
        contracts_dict: Dict[str, bytes] = {}
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            return contracts_dict
        for file_path in folder.iterdir():
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    contracts_dict[file_path.name] = f.read()
        return contracts_dict

    def versions_create_folder(self, file_map: Dict[str, bytes], project_id: str) -> Dict[str, Any]:
        """Create a new contract scan/version by sending contracts as multipart/form-data."""
        url = f"{self.base_url}/versions/create/folder"
        # Build files payload
        files = [("files", (relative_path, content, "application/octet-stream")) for relative_path, content in file_map.items()]
        # For multipart, don't set Content-Type; requests sets boundary automatically
        headers = {
            "Authorization": self.session.headers.get("Authorization", ""),
            "Accept": "application/json",
        }
        data = {"project_id": project_id}
        try:
            response = requests.post(url, headers=headers, data=data, files=files)
        except requests.RequestException as e:
            return {"error": str(e)}
        try:
            return response.json()
        except ValueError:
            return {"status_code": response.status_code, "text": response.text}

    def chat_with_version(self, version_mapping_id: str) -> Dict[str, Any]:
        """Create a chat session for a given version mapping id."""
        url = f"{self.base_url}/chats"
        payload = {"version_mapping_id": version_mapping_id}
        try:
            response = self.session.post(url, json=payload)
        except requests.RequestException as e:
            return {"error": str(e)}
        try:
            return response.json()
        except ValueError:
            return {"status_code": response.status_code, "text": response.text}