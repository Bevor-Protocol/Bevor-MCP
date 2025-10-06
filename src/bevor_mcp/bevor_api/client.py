import requests
import json
from typing import Any, Dict, Optional
import os
import asyncio
from pathlib import Path
import uuid


class BevorApiClient:
    """Bevor API client wrapper.

    Initialize with an API key. Optionally set an existing project id or a contracts folder path.
    """

    def __init__(self, bevor_api_key: str, project_id: Optional[str] = None, contracts_folder_path: Optional[str] = None) -> None:
        self.base_url = (os.getenv("BEVOR_API_URL") or "http://localhost:8000").rstrip("/")
        # Read API key from BEVOR_API_KEY (fallback to provided arg)
        self.bevor_api_key = os.getenv("BEVOR_API_KEY") or bevor_api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.bevor_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        # Prefer explicit project_id, else environment override if provided
        self.project_id = project_id or os.getenv("BEVOR_PROJECT_ID")
        self.contracts_folder_path = contracts_folder_path
        self.version_mapping_id: Optional[str] = None
        self.chat_id: Optional[str] = None
        # Debug fields for integration visibility
        self.last_project_response: Optional[Dict[str, Any]] = None
        self.last_version_response: Optional[Dict[str, Any]] = None
        self.last_chat_response: Optional[Dict[str, Any]] = None


    async def create(
        self,
    ) -> "BevorApiClient":
        """Async factory that performs network/file I/O without blocking __init__."""

        # Ensure project exists
        if not self.project_id:
            project_resp = await self._create_project()
            self.last_project_response = project_resp if isinstance(project_resp, dict) else {"_raw": str(project_resp)}
            self.project_id = (
                (project_resp or {}).get("id")
                or (project_resp or {}).get("project_id")
                or self.project_id
            )

        if self.contracts_folder_path:
            contracts_map = self.pull_in_solidity_test_folder(self.contracts_folder_path)
            version_resp = self.versions_create_folder(contracts_map, self.project_id or "")
            self.last_version_response = version_resp if isinstance(version_resp, dict) else {"_raw": str(version_resp)}
            # Robust extraction of a version/ mapping id from varied response shapes
            vr = version_resp or {}
            self.version_mapping_id = (
                vr.get("version_mapping_id")
                or vr.get("version_id")
                or vr.get("id")
                or (vr.get("data", {}) or {}).get("version_mapping_id")
                or (vr.get("data", {}) or {}).get("version_id")
                or (vr.get("data", {}) or {}).get("id")
            )
            if self.version_mapping_id:
                chat_resp = self.chat_with_version(self.version_mapping_id)
                self.last_chat_response = chat_resp if isinstance(chat_resp, dict) else {"_raw": str(chat_resp)}
                if isinstance(chat_resp, dict):
                    self.chat_id = chat_resp.get("id") or chat_resp.get("chat_id")

        return self


    def create_sync(
        self,
    ) -> "BevorApiClient":
        """Synchronous convenience wrapper for environments without an event loop."""
        return asyncio.run(self.create())


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

    
    async def _create_project(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project with the given name or auto-generated name if none provided."""
        if project_name is None:
            project_name = f"MCP Chat | {uuid.uuid4()}"
        
        payload = {
            "name": project_name,
            "description": f"Project created via Bevor API client",
            "tags": ["bevor-api", "client"]
        }
        response = await self._request(
            method="POST",
            path="/projects",
            json=payload
        )
        try:
            return response.json()
        except ValueError:
            return {"status_code": response.status_code, "text": response.text}


    def pull_in_solidity_test_folder(self, folder_path: str = "contracts") -> Dict[str, bytes]:
        """Recursively read all .sol files under a folder; return mapping of relative_path -> bytes.

        Only Solidity sources are included. Nested directories are supported.
        Paths are recorded relative to the provided folder to preserve structure.
        """
        contracts_dict: Dict[str, bytes] = {}
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            return contracts_dict
        for file_path in folder.rglob("*.sol"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(folder))
                with open(file_path, 'rb') as f:
                    contracts_dict[rel_path] = f.read()
        return contracts_dict


    def versions_create_folder(self, file_map: Dict[str, bytes], project_id: str) -> Dict[str, Any]:
        """Create a new contract scan/version by sending contracts as multipart/form-data.

        Tries multiple endpoint variants to accommodate backend differences.
        """
        # For multipart, don't set Content-Type; requests sets boundary automatically
        headers = {
            "Authorization": self.session.headers.get("Authorization", ""),
            "Accept": "application/json",
        }
        data = {"project_id": project_id, "projectId": project_id}

        # Build alternative files payloads with different field names
        files_variants = [
            [("files", (relative_path, content, "application/octet-stream")) for relative_path, content in file_map.items()],
            [("contracts", (relative_path, content, "application/octet-stream")) for relative_path, content in file_map.items()],
            [("sources", (relative_path, content, "application/octet-stream")) for relative_path, content in file_map.items()],
        ]

        candidate_paths = [
            "/versions/create/folder",
            "/versions/create",
            f"/projects/{project_id}/versions",
            "/versions",
        ]

        last_resp: Optional[requests.Response] = None
        for path in candidate_paths:
            url = f"{self.base_url}{path}"
            for files in files_variants:
                try:
                    resp = requests.post(url, headers=headers, data=data, files=files)
                except requests.RequestException as e:
                    return {"error": str(e)}
                last_resp = resp
                # Accept 200-299, and also 201/202 etc; skip 404s to try next variant
                if resp.status_code >= 200 and resp.status_code < 300 and resp.status_code != 204:
                    try:
                        return resp.json()
                    except ValueError:
                        return {"status_code": resp.status_code, "text": resp.text}
                if resp.status_code == 404:
                    continue
                # For other statuses, return the response as-is
                try:
                    return resp.json()
                except ValueError:
                    return {"status_code": resp.status_code, "text": resp.text}

        if last_resp is not None:
            try:
                return last_resp.json()
            except ValueError:
                return {"status_code": last_resp.status_code, "text": last_resp.text}
        return {"error": "No response from versions endpoint"}


    def chat_with_version(self, version_mapping_id: str) -> Dict[str, Any]:
        """Create a chat session for a given version mapping id.

        Tries multiple endpoints to handle backend variations.
        """
        payload = {"version_mapping_id": version_mapping_id, "versionMappingId": version_mapping_id}
        candidate_paths = [
            "/chats",
            "/chats/create",
            f"/versions/{version_mapping_id}/chats",
        ]
        last_resp: Optional[requests.Response] = None
        for path in candidate_paths:
            url = f"{self.base_url}{path}"
            try:
                response = self.session.post(url, json=payload)
            except requests.RequestException as e:
                return {"error": str(e)}
            last_resp = response
            if response.status_code >= 200 and response.status_code < 300 and response.status_code != 204:
                try:
                    return response.json()
                except ValueError:
                    return {"status_code": response.status_code, "text": response.text}
            if response.status_code == 404:
                continue
            try:
                return response.json()
            except ValueError:
                return {"status_code": response.status_code, "text": response.text}
        if last_resp is not None:
            try:
                return last_resp.json()
            except ValueError:
                return {"status_code": last_resp.status_code, "text": last_resp.text}
        return {"error": "No response from chats endpoint"}

    
    def chat_contract(self, chat_id: str, message: str) -> Dict[str, Any]:
        """Send a chat message to a specific chat session and return the final response.

        This calls POST /chats/{chat_id} with a JSON body {"message": message}.
        The endpoint streams Server-Sent Events; we accumulate the content and
        return the final combined text once streaming completes.
        """
        url = f"{self.base_url}/chats/{chat_id}"
        # Use session headers which already include Authorization and JSON defaults
        headers = {
            "Authorization": self.session.headers.get("Authorization", ""),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {"message": message}

        try:
            response = requests.post(url, headers=headers, json=payload, stream=True)
        except requests.RequestException as e:
            return {"error": str(e)}

        if response.status_code != 200:
            # Try to surface JSON error if available
            try:
                return {"error": response.json()}
            except ValueError:
                return {"error": f"HTTP {response.status_code}: {response.text}"}

        # Handle streaming SSE/plain text
        full_response = ""
        try:
            for line in response.iter_lines():
                if not line:
                    continue
                line_text = line.decode("utf-8", errors="ignore")
                if line_text.startswith("data: "):
                    data_content = line_text[6:]
                    if data_content.strip() == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data_content)
                        if isinstance(chunk_data, dict):
                            content = (
                                chunk_data.get("content")
                                or chunk_data.get("text")
                                or chunk_data.get("message")
                                or chunk_data.get("response")
                            )
                            if content:
                                full_response += str(content)
                    except json.JSONDecodeError:
                        full_response += data_content
                else:
                    full_response += line_text
        except Exception as e:
            return {"error": f"Error processing stream: {str(e)}"}

        if full_response.strip():
            return {"response": full_response.strip()}

        # Fallback: attempt to parse standard JSON response
        try:
            return response.json()
        except ValueError:
            return {"error": "No valid response received"}
