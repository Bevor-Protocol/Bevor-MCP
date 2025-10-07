import unittest
import tempfile
import os
from pathlib import Path
import shutil
from utils.solidity_etl import find_contracts_folder_in_directory

class TestFindContractsFolder(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for each test
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        # Clean up temporary directory after each test
        shutil.rmtree(self.test_dir)

    def test_contracts_folder_at_root(self):
        # Create contracts folder with .sol file at root
        contracts_dir = self.test_dir / "contracts"
        contracts_dir.mkdir()
        (contracts_dir / "Token.sol").touch()

        result = find_contracts_folder_in_directory(self.test_dir)
        self.assertEqual(result, contracts_dir)

    def test_contracts_nested_in_src(self):
        # Create nested contracts folder structure
        src_dir = self.test_dir / "src"
        contracts_dir = src_dir / "contracts"
        src_dir.mkdir()
        contracts_dir.mkdir()
        (contracts_dir / "Token.sol").touch()

        result = find_contracts_folder_in_directory(self.test_dir)
        self.assertEqual(result, contracts_dir)

    def test_src_folder_at_root(self):
        # Create src folder with .sol files
        src_dir = self.test_dir / "src"
        src_dir.mkdir()
        (src_dir / "Token.sol").touch()
        (src_dir / "Vault.sol").touch()

        result = find_contracts_folder_in_directory(self.test_dir)
        self.assertEqual(result, src_dir)

    def test_nested_sol_files(self):
        # Create complex nested structure
        main_dir = self.test_dir / "main"
        sub1_dir = main_dir / "sub1"
        sub2_dir = main_dir / "sub2"
        
        for dir in [main_dir, sub1_dir, sub2_dir]:
            dir.mkdir(parents=True)
        
        # Add more .sol files in sub2
        (sub1_dir / "Token1.sol").touch()
        (sub2_dir / "Token2.sol").touch()
        (sub2_dir / "Token3.sol").touch()

        result = find_contracts_folder_in_directory(self.test_dir)
        self.assertEqual(result, sub2_dir)  # Should return sub2 as it has most .sol files

    def test_mixed_file_types(self):
        # Create folder with mixed file types
        contracts_dir = self.test_dir / "contracts"
        contracts_dir.mkdir()
        
        # Create various file types
        (contracts_dir / "Token.sol").touch()
        (contracts_dir / "readme.md").touch()
        (contracts_dir / "config.json").touch()
        (contracts_dir / "test.js").touch()
        (contracts_dir / "Vault.sol").touch()

        result = find_contracts_folder_in_directory(self.test_dir)
        self.assertEqual(result, contracts_dir)

    def test_no_sol_files(self):
        # Test with directory containing no .sol files
        other_dir = self.test_dir / "other"
        other_dir.mkdir()
        (other_dir / "readme.md").touch()
        (other_dir / "config.json").touch()

        result = find_contracts_folder_in_directory(self.test_dir)
        self.assertIsNone(result)
