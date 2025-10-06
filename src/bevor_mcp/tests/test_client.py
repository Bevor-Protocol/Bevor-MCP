import unittest
import tempfile
import os
from pathlib import Path
import asyncio
import re
import requests
from bevor_mcp.bevor_api.client import BevorApiClient

class TestBevorApiClient(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.contracts_dir = Path(self.temp_dir) / "contracts"
        self.contracts_dir.mkdir()

        # Ensure tests target the local API server
        os.environ["BEVOR_API_URL"] = os.getenv("BEVOR_API_URL", "http://localhost:8000")
        # Ensure API key is present for auth; use default test key if not provided
        os.environ["BEVOR_API_KEY"] = os.getenv(
            "BEVOR_API_KEY",
            "sk_27d1eb_75b273c4b09760c2a5671e892608729b818385c713504e5a4f111a0aa10b15a6",
        )

        # Create token.sol file
        token_code = '''// SPDX-License-Identifier: MIT

pragma solidity ^0.8.10;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract BevorToken is ERC20 {

    constructor(
        uint256 totalSupply_,
        string memory name_,
        string memory symbol_
    ) ERC20(name_, symbol_) {
        _mint(msg.sender, totalSupply_);
    }

}'''
        
        token_file = self.contracts_dir / "token.sol"
        token_file.write_text(token_code)

        # No mocks for integration tests; requires live backend

    def tearDown(self):
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir)
        # No mocks to stop for integration tests

    async def _client_integration_async(self):
        api_key = os.getenv("BEVOR_API_KEY")
        # project_id = "b626a81b-7279-4ed2-840f-da7f18135ae5"
        
        # Already hit 20 project limit.
        try:
            client = await BevorApiClient(bevor_api_key=api_key, contracts_folder_path=str(self.contracts_dir), project_id="ee5aaf7e-71a5-4c2d-8b20-96af42610367").create()
        except Exception as e:
            print(f"Error initializing BevorApiClient: {e}")
            raise

        # Verify client initialized correctly (live backend expected)
        if not client.version_mapping_id or not client.chat_id:
            # Print debug traces to help diagnose backend responses
            print(f"project_resp: {getattr(client, 'last_project_response', None)}")
            print(f"version_resp: {getattr(client, 'last_version_response', None)}")
            print(f"chat_resp: {getattr(client, 'last_chat_response', None)}")
        self.assertIsNotNone(client.version_mapping_id)
        self.assertIsNotNone(client.chat_id)
        # Save client for use in subsequent tests
        self.client = client
        return client

    def test_client_integration(self):
        # Run async test using sync wrapper
        asyncio.run(self._client_integration_async())

    def test_chat_contract(self):
        # Ensure client is initialized and chat created
        client = asyncio.run(self._client_integration_async())
        self.assertIsNotNone(client)
        self.assertIsNotNone(getattr(client, "chat_id", None))

        # Call chat_contract and assert response is a string
        result = client.chat_contract("Summarize the uploaded contract in one sentence.")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        # Verify response is not a JSON string
        self.assertFalse(result.startswith('{"event_type":'))
        # Enforce no obvious duplicated concatenation from streaming
        # Heuristic: splitting by sentence-ending punctuation shouldn't produce adjacent identical prefixes
        segments = [s.strip() for s in re.split(r'[.!?]+\s*', result) if s.strip()]
        self.assertGreater(len(segments), 0)
        if len(segments) >= 2:
            self.assertNotEqual(segments[0], segments[1])
        # Print so it's visible in test output
        print(f"chat_contract response: {result}")

if __name__ == '__main__':
    unittest.main()
