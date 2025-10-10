import io
import os
import stat
import json
import hashlib
import tarfile
import zipfile
from pathlib import Path
from mito_forge.utils.tools_manager import ToolsManager

def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def test_install_from_file_url_zip(tmp_path, monkeypatch):
    # 准备一个本地zip包，内含可执行文件 fastqc（或 fastqc.exe）
    bin_name = "fastqc.exe" if os.name == "nt" else "fastqc"
    payload_dir = tmp_path / "payload"
    payload_dir.mkdir()
    exe_path = payload_dir / bin_name
    exe_path.write_text("echo ok\n" if os.name == "nt" else "#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    if os.name != "nt":
        exe_path.chmod(exe_path.stat().st_mode | stat.S_IXUSR)

    zip_path = tmp_path / "fastqc-test.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(exe_path, arcname=bin_name)
    sha = _sha256(zip_path)

    # 写 sources.json，提供 file:// URL
    proj_root = Path.cwd()
    tools_dir = proj_root / "mito_forge" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    url = zip_path.as_uri()  # file://...
    sources = {
        "fastqc": {
            "repo": "file-local",
            "version": "vtest",
            "assets": {
                ("win" if os.name == "nt" else "linux"): {"url": url, "sha256": sha},
                "mac": {"pattern": "unused"}  # 占位
            }
        }
    }
    (tools_dir / "sources.json").write_text(json.dumps(sources), encoding="utf-8")

    tm = ToolsManager(project_root=proj_root)
    out = tm.install("fastqc")
    assert Path(out).exists(), "installed executable should exist"
    # 可执行文件应在目标目录下
    assert Path(out).name in (bin_name, "fastqc.cmd")

def test_install_from_file_url_targz(tmp_path, monkeypatch):
    # 准备一个本地tar.gz包
    bin_name = "fastqc.exe" if os.name == "nt" else "fastqc"
    payload_dir = tmp_path / "payload2"
    payload_dir.mkdir()
    exe_path = payload_dir / bin_name
    exe_path.write_text("echo ok\n" if os.name == "nt" else "#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    if os.name != "nt":
        exe_path.chmod(exe_path.stat().st_mode | stat.S_IXUSR)

    tgz_path = tmp_path / "fastqc-test.tar.gz"
    with tarfile.open(tgz_path, "w:gz") as tf:
        tf.add(exe_path, arcname=bin_name)
    sha = _sha256(tgz_path)

    proj_root = Path.cwd()
    tools_dir = proj_root / "mito_forge" / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    url = tgz_path.as_uri()
    sources = {
        "fastqc": {
            "repo": "file-local",
            "version": "vtest2",
            "assets": {
                ("win" if os.name == "nt" else "linux"): {"url": url, "sha256": sha},
                "mac": {"pattern": "unused"}
            }
        }
    }
    (tools_dir / "sources.json").write_text(json.dumps(sources), encoding="utf-8")

    tm = ToolsManager(project_root=proj_root)
    out = tm.install("fastqc")
    assert Path(out).exists()
    assert Path(out).name in (bin_name, "fastqc.cmd")