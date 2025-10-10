import json
from pathlib import Path
from mito_forge.utils.tools_manager import ToolsManager

def test_sources_override(tmp_path, monkeypatch):
    # 临时复制一份 sources.json
    proj_root = Path.cwd()
    tools_dir = proj_root / "mito_forge" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    sources_path = tools_dir / "sources.json"
    sources_path.write_text(json.dumps({
        "fastqc": {
            "repo": "https://github.com/example/fastqc",
            "version": "v0.11.9",
            "assets": {
                "win": {"pattern": "fastqc-.*-win.zip", "sha256": "dummy"},
                "linux": {"pattern": "fastqc-.*-linux.tar.gz", "sha256": "dummy"},
                "mac": {"pattern": "fastqc-.*-mac.zip", "sha256": "dummy"}
            }
        }
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    tm = ToolsManager(project_root=proj_root)
    cfg = tm.get_tool_config("fastqc")
    assert cfg["repo"].startswith("https://github.com/example/fastqc")
    assert cfg["version"] == "v0.11.9"
    assert "assets" in cfg and "win" in cfg["assets"] and "linux" in cfg["assets"]