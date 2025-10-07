from typing import Optional, Mapping, Sequence

from .base import DevToolAdapter, CommandResult
from .runner import run_command
from .adapters import FoundryAdapter, HardhatAdapter, TruffleAdapter


DEFAULT_ADAPTERS: list[DevToolAdapter] = [
    FoundryAdapter(),
    HardhatAdapter(),
    TruffleAdapter(),
]


class DevToolsService:
    def __init__(self, adapters: Optional[list[DevToolAdapter]] = None):
        self.adapters = adapters or DEFAULT_ADAPTERS

    def detect(self, project_dir: str) -> DevToolAdapter:
        candidates: list[DevToolAdapter] = [
            a for a in self.adapters if a.is_applicable(project_dir)
        ]
        if not candidates:
            raise RuntimeError("No supported dev tool detected in project directory")
        # Deterministic precedence: Foundry > Hardhat > Truffle (based on DEFAULT_ADAPTERS)
        return candidates[0]

    def _exec(self, command: Sequence[str], project_dir: str, env: Optional[Mapping[str, str]]) -> CommandResult:
        code, out, err = run_command(command, cwd=project_dir, env=env)
        return CommandResult(ok=(code == 0), code=code, stdout=out, stderr=err, command=command)

    def _get_adapter(self, project_dir: str, tool: Optional[str]) -> DevToolAdapter:
        if tool:
            for adapter in self.adapters:
                if adapter.name.lower() == tool.lower():
                    return adapter
            raise ValueError(f"Unknown tool '{tool}'. Supported: {[a.name for a in self.adapters]}")
        return self.detect(project_dir)

    def build(self, project_dir: str, tool: Optional[str] = None, env: Optional[Mapping[str, str]] = None) -> CommandResult:
        adapter = self._get_adapter(project_dir, tool)
        return self._exec(adapter.build_command(project_dir), project_dir, env)

    def test(self, project_dir: str, tool: Optional[str] = None, env: Optional[Mapping[str, str]] = None) -> CommandResult:
        adapter = self._get_adapter(project_dir, tool)
        return self._exec(adapter.test_command(project_dir), project_dir, env)


