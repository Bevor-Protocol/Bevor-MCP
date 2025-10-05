
import unittest
import tempfile
import os
from pathlib import Path
from bevor_mcp.bevor_api.client import BevorApiClient

class TestBevorApiClient(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.contracts_dir = Path(self.temp_dir) / "contracts"
        self.contracts_dir.mkdir()

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

    def tearDown(self):
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_client_integration(self):
        api_key = "test_key"  # Replace with actual test key
        project_id = "test_project"  # Replace with actual test project
        
        client = BevorApiClient(
            bevor_api_key=api_key,
            project_id=project_id,
            contracts_folder=str(self.contracts_dir)
        )

        # Verify client initialized correctly
        self.assertIsNotNone(client.version_mapping_id)
        self.assertIsNotNone(client.chat_id)

if __name__ == '__main__':
    unittest.main()
