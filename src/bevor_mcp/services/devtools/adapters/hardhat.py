from pathlib import Path
from typing import Sequence


class HardhatAdapter:
    name = "hardhat"

    def is_applicable(self, project_dir: str) -> bool:
        root = Path(project_dir)
        if (root / "hardhat.config.js").exists() or (root / "hardhat.config.ts").exists():
            return True
        return (root / "node_modules" / ".bin" / "hardhat").exists()

    def build_command(self, project_dir: str) -> Sequence[str]:
        return ["npx", "hardhat", "compile"]

    def test_command(self, project_dir: str) -> Sequence[str]:
        return ["npx", "hardhat", "test"]


