from __future__ import annotations
import os
import json
import platform
from pathlib import Path
from typing import Dict, Any, Optional
from .github_downloader import GitHubDownloader
import subprocess

PLAT = {"Windows": "win", "Linux": "linux", "Darwin": "mac"}[platform.system()]

class ToolsManager:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.tools_dir = self.project_root / "mito_forge" / "tools"
        self.bin_root = self.tools_dir / "bin"

    def load_sources(self) -> Dict[str, Any]:
        p = self.tools_dir / "sources.json"
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def get_tool_config(self, name: str) -> Dict[str, Any]:
        src = self.load_sources()
        cfg = src.get(name)
        if not cfg:
            raise KeyError(f"tool not found in sources: {name}")
        return cfg

    def _target_dir(self, name: str, version: str) -> Path:
        return self.bin_root / name / version

    def where(self, name: str, version: Optional[str] = None) -> Optional[Path]:
        cfg = self.get_tool_config(name)
        ver = version or cfg.get("version", "latest")
        d = self._target_dir(name, ver)
        if not d.exists():
            return None
        # 首选标准启动器位置
        exe = d / (f"{name}.cmd" if os.name == "nt" else name)
        if exe.exists():
            return exe
        # 启动器缺失时：在版本目录内递归查找实际可执行文件（兼容嵌套安装）
        candidates = []
        try:
            for p in d.rglob("*"):
                if not p.is_file():
                    continue
                bn = p.name
                if os.name == "nt":
                    # Windows：按名称优先级和扩展识别
                    if bn.lower() in (f"{name.lower()}.exe", f"{name.lower()}.bat", f"{name.lower()}.cmd", name.lower()):
                        candidates.append(p)
                    elif p.suffix.lower() in (".exe", ".bat", ".cmd"):
                        candidates.append(p)
                else:
                    # POSIX：优先名匹配，其次执行权限
                    if bn == name or bn.lower() == name.lower():
                        candidates.append(p)
                    elif os.access(p, os.X_OK):
                        candidates.append(p)
        except Exception:
            pass
        target = candidates[0] if candidates else None
        if not target:
            return None
        # 生成启动器，转发到找到的目标（相对路径）
        try:
            rel = os.path.relpath(str(target), str(d))
        except Exception:
            rel = target.name
        try:
            if os.name == "nt":
                exe.write_text(f"@echo off\r\n\"%~dp0\\{rel}\" %*\r\n", encoding="utf-8")
            else:
                exe.write_text("#!/usr/bin/env bash\nexec \"$(dirname \"$0\")/%s\" \"$@\"\n" % rel, encoding="utf-8")
                import stat
                exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
            return exe
        except Exception:
            return None

    def verify(self, name: str, version: Optional[str] = None) -> bool:
        return self.where(name, version) is not None

    def remove(self, name: str, version: Optional[str] = None) -> None:
        cfg = self.get_tool_config(name)
        ver = version or cfg.get("version", "latest")
        d = self._target_dir(name, ver)
        if d.exists():
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def install(self, name: str, version: Optional[str] = None, force: bool = False) -> str:
        cfg = self.get_tool_config(name)
        ver = version or cfg.get("version", "latest")
        plat_cfg = (cfg.get("assets", {}) or {}).get(PLAT)
        if not plat_cfg:
            raise RuntimeError(f"no asset config for platform: {PLAT}")
        asset_url = plat_cfg.get("url")
        asset_pat = plat_cfg.get("pattern")
        sha256 = plat_cfg.get("sha256")
        target = self._target_dir(name, ver)
        target.mkdir(parents=True, exist_ok=True)
        if not force and self.verify(name, ver):
            p = self.where(name, ver)
            return str(p) if p else str(target)
        # 下载并解压
        if asset_url:
            GitHubDownloader.download(cfg["repo"], ver, asset_url, target, sha256=sha256)
        else:
            raise RuntimeError("asset url is required in sources.json for current platform; pattern-only not supported yet")
        # 构建（仅 Linux）：若解压根目录含 Makefile，则并行构建，并定位可执行产物
        build_root = None
        try:
            dirs = [p for p in target.iterdir() if p.is_dir() and p.name != "__MACOSX"]
            build_root = dirs[0] if dirs else target
        except Exception:
            build_root = target
        run_target_rel = name
        if os.name != "nt":
            mk = build_root / "Makefile"
            if mk.exists():
                try:
                    jobs = os.cpu_count() or 1
                    subprocess.run(["make", f"-j{jobs}"], cwd=str(build_root), check=True)
                except Exception:
                    # 构建失败不阻断安装流程
                    pass
            # 寻找构建产物作为主可执行（优先 pmat2/PMAT2）
            candidates = ["pmat2", "PMAT2"]
            found = None
            for c in candidates:
                pth = build_root / c
                if pth.exists() and pth.is_file():
                    found = pth
                    break
            if not found:
                try:
                    for pth in build_root.iterdir():
                        if pth.is_file() and os.access(pth, os.X_OK):
                            found = pth
                            break
                except Exception:
                    pass
            if found:
                try:
                    run_target_rel = os.path.relpath(str(found), str(target))
                except Exception:
                    run_target_rel = found.name

        # 规范化主可执行（Windows: .cmd 启动器；POSIX: chmod +x）
        exe = target / (f"{name}.cmd" if os.name == "nt" else name)
        if not exe.exists():
            # 若解压后没有主名，创建启动器/软链接逻辑（此处简单占位）
            if os.name == "nt":
                exe.write_text(f"@echo off\r\n\"%~dp0\\{name}.exe\" %*\r\n", encoding="utf-8")
            else:
                exe.write_text("#!/usr/bin/env bash\nexec \"$(dirname \"$0\")/%s\" \"$@\"\n" % run_target_rel, encoding="utf-8")
                import stat
                exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
        return str(exe)