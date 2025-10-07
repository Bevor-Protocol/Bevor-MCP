from pathlib import Path
from shutil import which
from typing import Sequence


class FoundryAdapter:
    name = "foundry"

    def is_applicable(self, project_dir: str) -> bool:
        root = Path(project_dir)
        # Only detect Foundry if foundry.toml exists
        return (root / "foundry.toml").exists()

    def build_command(self, project_dir: str) -> Sequence[str]:
        return ["forge", "build"]

    def test_command(self, project_dir: str) -> Sequence[str]:
        return ["forge", "test"]


