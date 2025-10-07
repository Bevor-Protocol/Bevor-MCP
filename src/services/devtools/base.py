from dataclasses import dataclass
from typing import Protocol, Sequence, Mapping, Optional


@dataclass
class CommandResult:
    ok: bool
    code: int
    stdout: str
    stderr: str
    command: Sequence[str]


class DevToolAdapter(Protocol):
    name: str

    def is_applicable(self, project_dir: str) -> bool:
        ...

    def build_command(self, project_dir: str) -> Sequence[str]:
        ...

    def test_command(self, project_dir: str) -> Sequence[str]:
        ...


