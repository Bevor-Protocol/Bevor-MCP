from typing import Optional, Mapping

from services.devtools import DevToolsService


_service = DevToolsService()


def build(project_dir: str, tool: Optional[str] = None, env: Optional[Mapping[str, str]] = None) -> dict:
    res = _service.build(project_dir=project_dir, tool=tool, env=env)
    return {
        "ok": res.ok,
        "code": res.code,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "command": list(res.command),
        "project_dir": project_dir,
        "tool": tool or "auto",
    }


def test(project_dir: str, tool: Optional[str] = None, env: Optional[Mapping[str, str]] = None) -> dict:
    res = _service.test(project_dir=project_dir, tool=tool, env=env)
    return {
        "ok": res.ok,
        "code": res.code,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "command": list(res.command),
        "project_dir": project_dir,
        "tool": tool or "auto",
    }


