"""Test suite for the devtools service."""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Sequence

from services.devtools.base import CommandResult, DevToolAdapter
from services.devtools.service import DevToolsService
from services.devtools.adapters import FoundryAdapter, HardhatAdapter, TruffleAdapter
from services.devtools.runner import run_command


class MockAdapter(DevToolAdapter):
    """Mock adapter for testing."""
    name = "mock"
    
    def __init__(self, applicable: bool = True, build_cmd: Sequence[str] = None, test_cmd: Sequence[str] = None):
        self.applicable = applicable
        self.build_cmd = build_cmd or ["mock", "build"]
        self.test_cmd = test_cmd or ["mock", "test"]
    
    def is_applicable(self, project_dir: str) -> bool:
        return self.applicable
    
    def build_command(self, project_dir: str) -> Sequence[str]:
        return self.build_cmd
    
    def test_command(self, project_dir: str) -> Sequence[str]:
        return self.test_cmd


class TestCommandResult(unittest.TestCase):
    """Test CommandResult dataclass."""
    
    def test_command_result_creation(self):
        result = CommandResult(
            ok=True,
            code=0,
            stdout="success",
            stderr="",
            command=["test", "command"]
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.code, 0)
        self.assertEqual(result.stdout, "success")
        self.assertEqual(result.stderr, "")
        self.assertEqual(list(result.command), ["test", "command"])


class TestFoundryAdapter(unittest.TestCase):
    """Test Foundry adapter detection and commands."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.adapter = FoundryAdapter()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_foundry_detection_with_config(self):
        """Test detection when foundry.toml exists."""
        config_file = Path(self.temp_dir) / "foundry.toml"
        config_file.write_text("[profile.default]\n")
        
        self.assertTrue(self.adapter.is_applicable(self.temp_dir))
    
    def test_foundry_detection_without_config(self):
        """Test detection when foundry.toml doesn't exist."""
        self.assertFalse(self.adapter.is_applicable(self.temp_dir))
    
    def test_foundry_detection_with_forge_binary_but_no_config(self):
        """Test detection when forge binary is available but no foundry.toml exists."""
        # Even if forge is available, we require foundry.toml for detection
        self.assertFalse(self.adapter.is_applicable(self.temp_dir))
    
    def test_foundry_commands(self):
        """Test command generation."""
        build_cmd = self.adapter.build_command(self.temp_dir)
        test_cmd = self.adapter.test_command(self.temp_dir)
        
        self.assertEqual(list(build_cmd), ["forge", "build"])
        self.assertEqual(list(test_cmd), ["forge", "test"])


class TestHardhatAdapter(unittest.TestCase):
    """Test Hardhat adapter detection and commands."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.adapter = HardhatAdapter()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_hardhat_detection_with_js_config(self):
        """Test detection with hardhat.config.js."""
        config_file = Path(self.temp_dir) / "hardhat.config.js"
        config_file.write_text("module.exports = {};")
        
        self.assertTrue(self.adapter.is_applicable(self.temp_dir))
    
    def test_hardhat_detection_with_ts_config(self):
        """Test detection with hardhat.config.ts."""
        config_file = Path(self.temp_dir) / "hardhat.config.ts"
        config_file.write_text("export default {};")
        
        self.assertTrue(self.adapter.is_applicable(self.temp_dir))
    
    def test_hardhat_detection_with_binary(self):
        """Test detection with node_modules binary."""
        binary_path = Path(self.temp_dir) / "node_modules" / ".bin" / "hardhat"
        binary_path.parent.mkdir(parents=True)
        binary_path.touch()
        
        self.assertTrue(self.adapter.is_applicable(self.temp_dir))
    
    def test_hardhat_detection_without_config(self):
        """Test detection when no config exists."""
        self.assertFalse(self.adapter.is_applicable(self.temp_dir))
    
    def test_hardhat_commands(self):
        """Test command generation."""
        build_cmd = self.adapter.build_command(self.temp_dir)
        test_cmd = self.adapter.test_command(self.temp_dir)
        
        self.assertEqual(list(build_cmd), ["npx", "hardhat", "compile"])
        self.assertEqual(list(test_cmd), ["npx", "hardhat", "test"])


class TestTruffleAdapter(unittest.TestCase):
    """Test Truffle adapter detection and commands."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.adapter = TruffleAdapter()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_truffle_detection_with_config_js(self):
        """Test detection with truffle-config.js."""
        config_file = Path(self.temp_dir) / "truffle-config.js"
        config_file.write_text("module.exports = {};")
        
        self.assertTrue(self.adapter.is_applicable(self.temp_dir))
    
    def test_truffle_detection_with_truffle_js(self):
        """Test detection with truffle.js."""
        config_file = Path(self.temp_dir) / "truffle.js"
        config_file.write_text("module.exports = {};")
        
        self.assertTrue(self.adapter.is_applicable(self.temp_dir))
    
    def test_truffle_detection_with_binary(self):
        """Test detection with node_modules binary."""
        binary_path = Path(self.temp_dir) / "node_modules" / ".bin" / "truffle"
        binary_path.parent.mkdir(parents=True)
        binary_path.touch()
        
        self.assertTrue(self.adapter.is_applicable(self.temp_dir))
    
    def test_truffle_detection_without_config(self):
        """Test detection when no config exists."""
        self.assertFalse(self.adapter.is_applicable(self.temp_dir))
    
    def test_truffle_commands(self):
        """Test command generation."""
        build_cmd = self.adapter.build_command(self.temp_dir)
        test_cmd = self.adapter.test_command(self.temp_dir)
        
        self.assertEqual(list(build_cmd), ["npx", "truffle", "build"])
        self.assertEqual(list(test_cmd), ["npx", "truffle", "test"])


class TestDevToolsService(unittest.TestCase):
    """Test DevToolsService orchestration."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.service = DevToolsService()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_service_initialization_with_default_adapters(self):
        """Test service initializes with default adapters."""
        self.assertEqual(len(self.service.adapters), 3)
        adapter_names = [adapter.name for adapter in self.service.adapters]
        self.assertIn("foundry", adapter_names)
        self.assertIn("hardhat", adapter_names)
        self.assertIn("truffle", adapter_names)
    
    def test_service_initialization_with_custom_adapters(self):
        """Test service initializes with custom adapters."""
        custom_adapters = [MockAdapter(applicable=True)]
        service = DevToolsService(adapters=custom_adapters)
        
        self.assertEqual(len(service.adapters), 1)
        self.assertEqual(service.adapters[0].name, "mock")
    
    def test_detection_with_applicable_adapter(self):
        """Test detection finds applicable adapter."""
        # Create foundry config
        config_file = Path(self.temp_dir) / "foundry.toml"
        config_file.write_text("[profile.default]\n")
        
        adapter = self.service.detect(self.temp_dir)
        self.assertEqual(adapter.name, "foundry")
    
    def test_detection_with_no_applicable_adapter(self):
        """Test detection raises error when no adapter is applicable."""
        with self.assertRaises(RuntimeError) as context:
            self.service.detect(self.temp_dir)
        
        self.assertIn("No supported dev tool detected", str(context.exception))
    
    def test_detection_precedence(self):
        """Test detection follows precedence order (Foundry > Hardhat > Truffle)."""
        # Create both foundry and hardhat configs
        foundry_config = Path(self.temp_dir) / "foundry.toml"
        foundry_config.write_text("[profile.default]\n")
        
        hardhat_config = Path(self.temp_dir) / "hardhat.config.js"
        hardhat_config.write_text("module.exports = {};")
        
        adapter = self.service.detect(self.temp_dir)
        self.assertEqual(adapter.name, "foundry")
    
    def test_get_adapter_by_name(self):
        """Test getting adapter by explicit name."""
        adapter = self.service._get_adapter(self.temp_dir, "foundry")
        self.assertEqual(adapter.name, "foundry")
    
    def test_get_adapter_by_name_case_insensitive(self):
        """Test getting adapter by name is case insensitive."""
        adapter = self.service._get_adapter(self.temp_dir, "FOUNDRY")
        self.assertEqual(adapter.name, "foundry")
    
    def test_get_adapter_with_unknown_name(self):
        """Test getting adapter with unknown name raises error."""
        with self.assertRaises(ValueError) as context:
            self.service._get_adapter(self.temp_dir, "unknown")
        
        self.assertIn("Unknown tool 'unknown'", str(context.exception))
        self.assertIn("Supported:", str(context.exception))
    
    @patch('services.devtools.service.run_command')
    def test_build_with_auto_detection(self, mock_run_command):
        """Test build command with auto-detection."""
        # Setup foundry config
        config_file = Path(self.temp_dir) / "foundry.toml"
        config_file.write_text("[profile.default]\n")
        
        # Mock successful command execution
        mock_run_command.return_value = (0, "Build successful", "")
        
        result = self.service.build(self.temp_dir)
        
        self.assertTrue(result.ok)
        self.assertEqual(result.code, 0)
        self.assertEqual(result.stdout, "Build successful")
        self.assertEqual(list(result.command), ["forge", "build"])
        mock_run_command.assert_called_once_with(
            ["forge", "build"],
            cwd=self.temp_dir,
            env=None
        )
    
    @patch('services.devtools.service.run_command')
    def test_build_with_explicit_tool(self, mock_run_command):
        """Test build command with explicit tool selection."""
        # Mock successful command execution
        mock_run_command.return_value = (0, "Hardhat build successful", "")
        
        result = self.service.build(self.temp_dir, tool="hardhat")
        
        self.assertTrue(result.ok)
        self.assertEqual(result.code, 0)
        self.assertEqual(result.stdout, "Hardhat build successful")
        self.assertEqual(list(result.command), ["npx", "hardhat", "compile"])
        mock_run_command.assert_called_once_with(
            ["npx", "hardhat", "compile"],
            cwd=self.temp_dir,
            env=None
        )
    
    @patch('services.devtools.service.run_command')
    def test_build_with_custom_env(self, mock_run_command):
        """Test build command with custom environment variables."""
        # Setup foundry config
        config_file = Path(self.temp_dir) / "foundry.toml"
        config_file.write_text("[profile.default]\n")
        
        # Mock successful command execution
        mock_run_command.return_value = (0, "Build successful", "")
        
        custom_env = {"NODE_ENV": "test", "VERBOSE": "1"}
        result = self.service.build(self.temp_dir, env=custom_env)
        
        self.assertTrue(result.ok)
        mock_run_command.assert_called_once_with(
            ["forge", "build"],
            cwd=self.temp_dir,
            env=custom_env
        )
    
    @patch('services.devtools.service.run_command')
    def test_build_with_failure(self, mock_run_command):
        """Test build command with failure."""
        # Setup foundry config
        config_file = Path(self.temp_dir) / "foundry.toml"
        config_file.write_text("[profile.default]\n")
        
        # Mock failed command execution
        mock_run_command.return_value = (1, "", "Compilation failed")
        
        result = self.service.build(self.temp_dir)
        
        self.assertFalse(result.ok)
        self.assertEqual(result.code, 1)
        self.assertEqual(result.stderr, "Compilation failed")
        self.assertEqual(list(result.command), ["forge", "build"])
    
    @patch('services.devtools.service.run_command')
    def test_test_with_auto_detection(self, mock_run_command):
        """Test test command with auto-detection."""
        # Setup hardhat config
        config_file = Path(self.temp_dir) / "hardhat.config.js"
        config_file.write_text("module.exports = {};")
        
        # Mock successful command execution
        mock_run_command.return_value = (0, "All tests passed", "")
        
        result = self.service.test(self.temp_dir)
        
        self.assertTrue(result.ok)
        self.assertEqual(result.code, 0)
        self.assertEqual(result.stdout, "All tests passed")
        self.assertEqual(list(result.command), ["npx", "hardhat", "test"])
        mock_run_command.assert_called_once_with(
            ["npx", "hardhat", "test"],
            cwd=self.temp_dir,
            env=None
        )
    
    @patch('services.devtools.service.run_command')
    def test_test_with_explicit_tool(self, mock_run_command):
        """Test test command with explicit tool selection."""
        # Mock successful command execution
        mock_run_command.return_value = (0, "Truffle tests passed", "")
        
        result = self.service.test(self.temp_dir, tool="truffle")
        
        self.assertTrue(result.ok)
        self.assertEqual(result.code, 0)
        self.assertEqual(result.stdout, "Truffle tests passed")
        self.assertEqual(list(result.command), ["npx", "truffle", "test"])
        mock_run_command.assert_called_once_with(
            ["npx", "truffle", "test"],
            cwd=self.temp_dir,
            env=None
        )


class TestRunCommand(unittest.TestCase):
    """Test command runner functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_run_command_success(self):
        """Test successful command execution."""
        # Use a simple command that should work on all platforms
        if os.name == 'nt':  # Windows
            command = ["cmd", "/c", "echo", "success"]
        else:  # Unix-like
            command = ["echo", "success"]
        
        code, stdout, stderr = run_command(command, cwd=self.temp_dir)
        
        self.assertEqual(code, 0)
        self.assertIn("success", stdout)
        self.assertEqual(stderr, "")
    
    def test_run_command_failure(self):
        """Test failed command execution."""
        # Use a command that should fail
        if os.name == 'nt':  # Windows
            command = ["cmd", "/c", "exit", "1"]
        else:  # Unix-like
            command = ["false"]
        
        code, stdout, stderr = run_command(command, cwd=self.temp_dir)
        
        self.assertNotEqual(code, 0)
    
    def test_run_command_with_custom_env(self):
        """Test command execution with custom environment."""
        custom_env = {"TEST_VAR": "test_value"}
        
        if os.name == 'nt':  # Windows
            command = ["cmd", "/c", "echo", "%TEST_VAR%"]
        else:  # Unix-like
            command = ["sh", "-c", "echo $TEST_VAR"]
        
        code, stdout, stderr = run_command(command, cwd=self.temp_dir, env=custom_env)
        
        self.assertEqual(code, 0)
        self.assertIn("test_value", stdout)
    
    def test_run_command_timeout(self):
        """Test command execution timeout."""
        # Use a command that will hang
        if os.name == 'nt':  # Windows
            command = ["cmd", "/c", "ping", "127.0.0.1", "-n", "10"]
        else:  # Unix-like
            command = ["sleep", "10"]
        
        code, stdout, stderr = run_command(command, cwd=self.temp_dir, timeout=1)
        
        self.assertEqual(code, 124)  # Timeout exit code
        self.assertIn("Timeout", stderr)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete devtools service."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.service = DevToolsService()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow_foundry(self):
        """Test complete workflow with Foundry project."""
        # Create foundry project structure
        config_file = Path(self.temp_dir) / "foundry.toml"
        config_file.write_text("""
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
""")
        
        src_dir = Path(self.temp_dir) / "src"
        src_dir.mkdir()
        
        # Create a simple contract
        contract_file = src_dir / "Test.sol"
        contract_file.write_text("""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Test {
    function test() public pure returns (string memory) {
        return "Hello, Foundry!";
    }
}
""")
        
        # Test detection
        adapter = self.service.detect(self.temp_dir)
        self.assertEqual(adapter.name, "foundry")
        
        # Test build command generation
        build_cmd = adapter.build_command(self.temp_dir)
        self.assertEqual(list(build_cmd), ["forge", "build"])
        
        # Test test command generation
        test_cmd = adapter.test_command(self.temp_dir)
        self.assertEqual(list(test_cmd), ["forge", "test"])
    
    def test_full_workflow_hardhat(self):
        """Test complete workflow with Hardhat project."""
        # Create hardhat project structure
        config_file = Path(self.temp_dir) / "hardhat.config.js"
        config_file.write_text("""
module.exports = {
  solidity: "0.8.0",
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};
""")
        
        contracts_dir = Path(self.temp_dir) / "contracts"
        contracts_dir.mkdir()
        
        # Create a simple contract
        contract_file = contracts_dir / "Test.sol"
        contract_file.write_text("""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Test {
    function test() public pure returns (string memory) {
        return "Hello, Hardhat!";
    }
}
""")
        
        # Test detection
        adapter = self.service.detect(self.temp_dir)
        self.assertEqual(adapter.name, "hardhat")
        
        # Test build command generation
        build_cmd = adapter.build_command(self.temp_dir)
        self.assertEqual(list(build_cmd), ["npx", "hardhat", "compile"])
        
        # Test test command generation
        test_cmd = adapter.test_command(self.temp_dir)
        self.assertEqual(list(test_cmd), ["npx", "hardhat", "test"])


if __name__ == '__main__':
    unittest.main()
