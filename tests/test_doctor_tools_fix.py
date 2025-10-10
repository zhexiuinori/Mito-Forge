import json
import types
from pathlib import Path
from click.testing import CliRunner
from mito_forge.cli.commands.doctor import doctor

def test_doctor_tools_fix_installs(monkeypatch, tmp_path):
    # 准备 sources.json
    proj_root = Path.cwd()
    tools_dir = proj_root / "mito_forge" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "sources.json").write_text(json.dumps({
        "fastqc": {
            "repo": "https://github.com/example/fastqc",
            "version": "v0.11.9",
            "assets": {"win": {"pattern": "fastqc-.*-win.zip"}, "linux": {"pattern": "fastqc-.*-linux.tar.gz"}, "mac": {"pattern": "fastqc-.*-mac.zip"}}
        }
    }, ensure_ascii=False), encoding="utf-8")

    # mock check_tools 结果：缺失 fastqc
    def _fake_check_tools(names):
        return {"present": [], "missing": ["fastqc"], "detail": {"fastqc": {"found": False, "suggest": ""}}, "summary": {"total": 1, "present": 0, "missing": 1}}
    monkeypatch.setattr("mito_forge.cli.commands.doctor.check_tools", _fake_check_tools)

    # mock ToolsManager.install 行为：创建可执行占位文件
    from mito_forge.utils import tools_manager as tm_mod
    calls = {}
    def _fake_install(self, name, force=False):
        calls["installed"] = name
        bin_dir = (self.project_root / "mito_forge" / "tools" / "bin" / name / "v0.11.9")
        bin_dir.mkdir(parents=True, exist_ok=True)
        exe = bin_dir / (f"{name}.cmd" if tm_mod.os.name == "nt" else name)
        exe.write_text("echo ok" if tm_mod.os.name == "nt" else "#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
        if tm_mod.os.name != "nt":
            import stat
            exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
        return str(exe)
    monkeypatch.setattr("mito_forge.utils.tools_manager.ToolsManager.install", _fake_install)

    # 扩展 doctor：临时加入 --fix 处理（如果已实现则直接使用）
    runner = CliRunner()
    res = runner.invoke(doctor, ["--tools", "fastqc", "--fix"])
    assert res.exit_code == 0
    assert calls.get("installed") == "fastqc"