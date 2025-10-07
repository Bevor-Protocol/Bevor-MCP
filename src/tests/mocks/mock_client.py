from typing import Any, Dict, Optional
import asyncio
from pathlib import Path
import uuid


class MockBevorApiClient:
    """In-memory mock of BevorApiClient for tests.

    Provides the same public interface but avoids any network I/O.
    """

    def __init__(self, bevor_api_key: str, project_id: Optional[str] = None, contracts_folder_path: Optional[str] = None) -> None:
        self.bevor_api_key = bevor_api_key
        self.project_id = project_id
        self.contracts_folder_path = contracts_folder_path
        self.version_mapping_id: Optional[str] = None
        self.chat_id: Optional[str] = None

        # Debug/trace fields to mirror the real client
        self.last_project_response: Optional[Dict[str, Any]] = None
        self.last_version_response: Optional[Dict[str, Any]] = None
        self.last_chat_response: Optional[Dict[str, Any]] = None

        # In-memory stores
        self._projects: Dict[str, Dict[str, Any]] = {}
        self._versions: Dict[str, Dict[str, Any]] = {}
        self._chats: Dict[str, Dict[str, Any]] = {}

    async def create(self) -> "MockBevorApiClient":
        if not self.project_id:
            project_resp = await self._create_project()
            self.last_project_response = project_resp
            self.project_id = project_resp.get("id")

        if self.contracts_folder_path:
            contracts_map = self.pull_in_solidity_test_folder(self.contracts_folder_path)
            version_resp = self.versions_create_folder(contracts_map, self.project_id or "")
            self.last_version_response = version_resp
            self.version_mapping_id = version_resp.get("version_mapping_id")
            if self.version_mapping_id:
                chat_resp = self.chat_with_version(self.version_mapping_id)
                self.last_chat_response = chat_resp
                self.chat_id = chat_resp.get("id")

        return self

    def create_sync(self) -> "MockBevorApiClient":
        return asyncio.run(self.create())

    async def _create_project(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        name = project_name or f"MCP Chat | {uuid.uuid4()}"
        pid = str(uuid.uuid4())
        project = {"id": pid, "name": name, "description": "Mock project", "tags": ["mock"]}
        self._projects[pid] = project
        return project

    def pull_in_solidity_test_folder(self, folder_path: str = "contracts") -> Dict[str, bytes]:
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
        if not project_id:
            return {"error": "project_id required"}
        vmid = str(uuid.uuid4())
        version = {
            "id": vmid,
            "version_mapping_id": vmid,
            "project_id": project_id,
            "files": list(file_map.keys()),
            "count": len(file_map),
        }
        self._versions[vmid] = version
        return version

    def chat_with_version(self, version_mapping_id: str) -> Dict[str, Any]:
        if version_mapping_id not in self._versions:
            return {"error": "unknown version"}
        cid = str(uuid.uuid4())
        chat = {"id": cid, "version_mapping_id": version_mapping_id, "messages": []}
        self._chats[cid] = chat
        return chat

    def chat_contract(self, message: str) -> str:
        if not self.chat_id:
            return "Error: No chat initialized"
        chat = self._chats.get(self.chat_id)
        if not chat:
            return "Error: Chat not found"
        chat["messages"].append({"role": "user", "content": message})
        # Deterministic mock response
        reply = f"[mock] Received {len(message)} chars for version {chat.get('version_mapping_id')}"
        chat["messages"].append({"role": "assistant", "content": reply})
        return reply
