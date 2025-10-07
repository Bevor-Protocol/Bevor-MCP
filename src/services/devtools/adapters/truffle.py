from pathlib import Path
from typing import Sequence


class TruffleAdapter:
    name = "truffle"

    def is_applicable(self, project_dir: str) -> bool:
        root = Path(project_dir)
        if (root / "truffle-config.js").exists() or (root / "truffle.js").exists():
            return True
        return (root / "node_modules" / ".bin" / "truffle").exists()

    def build_command(self, project_dir: str) -> Sequence[str]:
        return ["npx", "truffle", "build"]

    def test_command(self, project_dir: str) -> Sequence[str]:
        return ["npx", "truffle", "test"]


