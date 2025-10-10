from pathlib import Path
import json
import os
import sys

from mito_forge.utils.tools_manager import ToolsManager

def test_where_finds_nested_executable_and_creates_launcher(tmp_path: Path, monkeypatch):
    # 假项目根
    proj = tmp_path
    tools_dir = proj / "mito_forge" / "tools"
    bin_root = tools_dir / "bin"
    name = "pmat2"
    ver = "vX"
    version_dir = bin_root / name / ver
    nested_dir = version_dir / "PMAT2-2.1.5" / "bin" / "deep"
    nested_dir.mkdir(parents=True, exist_ok=True)

    # 在嵌套目录放置“可执行”占位文件
    if os.name == "nt":
        target = nested_dir / f"{name}.exe"
        target.write_bytes(b"")  # 存在即可
    else:
        target = nested_dir / name
        target.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        mode = target.stat().st_mode
        target.chmod(mode | 0o111)

    # 写 sources.json，提供版本信息
    sources = {
        name: {
            "repo": "local-test",
            "version": ver,
            "assets": {
                ("win" if os.name == "nt" else "linux"): {"url": "file:///dev/null"},
                "mac": {"pattern": "unused"}
            }
        }
    }
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "sources.json").write_text(json.dumps(sources), encoding="utf-8")

    # where 应该递归找到 target，并在版本目录创建启动器
    tm = ToolsManager(project_root=proj)
    launcher = tm.where(name)
    assert launcher is not None, "should find launcher path"
    launcher = Path(launcher)

    if os.name == "nt":
        assert launcher.name == f"{name}.cmd"
        content = launcher.read_text(encoding="utf-8")
        # 启动器应转发到相对路径中包含嵌套目录和目标名
        assert f"{name}.exe" in content
    else:
        assert launcher.name == name
        content = launcher.read_text(encoding="utf-8")
        assert "#!/usr/bin/env bash" in content
        # 目标名应在脚本的相对路径中
        assert name in content

    # 启动器文件必须存在于版本目录下
    assert launcher.parent == version_dir