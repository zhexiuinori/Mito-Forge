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
        # 尝试从sources.json获取配置
        try:
            cfg = self.get_tool_config(name)
            ver = version or cfg.get("version", "latest")
            d = self._target_dir(name, ver)
            if not d.exists():
                # 配置存在但目录不存在，尝试fallback扫描
                pass
            else:
                # 首选标准启动器位置
                exe = d / (f"{name}.cmd" if os.name == "nt" else name)
                if exe.exists():
                    return exe
        except KeyError:
            # sources.json中没有配置，使用fallback扫描
            pass
        
        # Fallback: 直接扫描tools/bin目录查找工具
        # 支持多种目录结构: name/version/name, name/*/name, name/*/*/name.py 等
        d = None
        if self.bin_root.exists():
            candidates = []
            # 查找启动器: tools/bin/{name}/{version}/{name}
            candidates.extend(self.bin_root.glob(f"{name}/*/{name}"))
            # 查找Python脚本: tools/bin/{name}/{version}/{name}.py
            candidates.extend(self.bin_root.glob(f"{name}/*/{name}.py"))
            # 查找嵌套结构: tools/bin/{name}/{version}/*/bin/{name}
            candidates.extend(self.bin_root.glob(f"{name}/*/*/{name}"))
            candidates.extend(self.bin_root.glob(f"{name}/*/*/*/{name}.py"))
            
            for candidate in candidates:
                if candidate.exists() and (os.access(candidate, os.X_OK) or candidate.suffix == '.py'):
                    return candidate
            
            # 如果找到了目录但没有启动器，使用第一个版本目录
            version_dirs = list(self.bin_root.glob(f"{name}/*"))
            if version_dirs:
                d = sorted(version_dirs)[-1]  # 使用最新版本
        
        if not d or not d.exists():
            return None
        
        # 使用原有逻辑继续处理
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
            try:
                GitHubDownloader.download(cfg["repo"], ver, asset_url, target, sha256=sha256)
                print(f"✅ {name} 下载完成")
            except Exception as e:
                raise RuntimeError(f"下载失败: {e}\n可能原因:\n1. 网络问题\n2. URL无效\n3. 权限问题\n建议: 检查网络连接或使用conda安装")
        else:
            raise RuntimeError("asset url is required in sources.json for current platform; pattern-only not supported yet")
        
        # 验证下载是否成功
        if not list(target.iterdir()):
            raise RuntimeError(f"下载目录为空,下载可能失败了: {target}\n建议使用conda安装或手动下载")
        
        # 确定构建根目录
        build_root = None
        try:
            dirs = [p for p in target.iterdir() if p.is_dir() and p.name != "__MACOSX"]
            build_root = dirs[0] if dirs else target
        except Exception:
            build_root = target
        
        # 获取工具类型和可执行文件路径
        tool_type = cfg.get("type", "auto")
        explicit_exe = cfg.get("executable")
        run_target_rel = name
        
        # 根据工具类型处理
        if os.name != "nt":
            if tool_type == "source_with_makefile":
                # 源码需要编译
                mk = build_root / "Makefile"
                if mk.exists():
                    try:
                        print(f"Building {name} with make...")
                        jobs = os.cpu_count() or 1
                        subprocess.run(["make", f"-j{jobs}"], cwd=str(build_root), check=True)
                        print(f"Build complete: {name}")
                    except Exception as e:
                        print(f"Build failed: {e}")
                        pass
            elif tool_type == "python_package":
                # Python包需要编译/安装 (如unicycler有C++扩展)
                setup_py = build_root / "setup.py"
                makefile = build_root / "Makefile"
                
                if setup_py.exists():
                    try:
                        print(f"Building Python package {name}...")
                        # 尝试编译扩展 (如果有)
                        result = subprocess.run(
                            ["python", "setup.py", "build_ext", "--inplace"],
                            cwd=str(build_root),
                            capture_output=True,
                            text=True
                        )
                        if result.returncode == 0:
                            print(f"  ✅ Python扩展编译成功")
                        else:
                            # 编译失败不是致命问题,可能不需要编译
                            print(f"  ℹ️  Python扩展编译跳过 (可能不需要)")
                    except Exception as e:
                        print(f"  ⚠️  编译过程出错: {e}")
                
                # 如果有Makefile,也尝试make
                if makefile.exists():
                    try:
                        print(f"  Running make for {name}...")
                        jobs = os.cpu_count() or 1
                        subprocess.run(["make", f"-j{jobs}"], cwd=str(build_root), check=True)
                        print(f"  ✅ Make编译成功")
                    except Exception as e:
                        print(f"  ⚠️  Make编译失败: {e}")
                        
            elif tool_type == "java_jar":
                # Java JAR 文件，创建启动脚本
                jar_file = None
                for f in target.iterdir():
                    if f.suffix == '.jar':
                        jar_file = f
                        break
                if jar_file:
                    try:
                        run_target_rel = jar_file.name
                    except Exception:
                        pass
            
            # 查找可执行文件
            if explicit_exe:
                # 使用配置中指定的路径
                exe_path = target / explicit_exe
                if not exe_path.exists():
                    # 尝试在 build_root 下查找
                    exe_path = build_root / explicit_exe
                if exe_path.exists():
                    # 确保可执行权限
                    try:
                        import stat
                        current_mode = exe_path.stat().st_mode
                        exe_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    except Exception:
                        pass
                    try:
                        run_target_rel = os.path.relpath(str(exe_path), str(target))
                    except Exception:
                        run_target_rel = exe_path.name
            else:
                # 自动查找（兼容旧逻辑）
                candidates = [name, name.upper(), name.lower()]
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
                    # 确保可执行权限
                    try:
                        import stat
                        current_mode = found.stat().st_mode
                        found.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                    except Exception:
                        pass
                    try:
                        run_target_rel = os.path.relpath(str(found), str(target))
                    except Exception:
                        run_target_rel = found.name

        # 规范化主可执行（Windows: .cmd 启动器；POSIX: chmod +x）
        exe = target / (f"{name}.cmd" if os.name == "nt" else name)
        if not exe.exists():
            # 若解压后没有主名，创建启动器/软链接逻辑
            if os.name == "nt":
                exe.write_text(f"@echo off\r\n\"%~dp0\\{name}.exe\" %*\r\n", encoding="utf-8")
            else:
                # 对于 Java JAR，创建 java -jar 启动器
                if tool_type == "java_jar":
                    exe.write_text("#!/usr/bin/env bash\nexec java -jar \"$(dirname \"$0\")/%s\" \"$@\"\n" % run_target_rel, encoding="utf-8")
                else:
                    exe.write_text("#!/usr/bin/env bash\nexec \"$(dirname \"$0\")/%s\" \"$@\"\n" % run_target_rel, encoding="utf-8")
                import stat
                exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        
        # 验证工具是否真的可用
        if exe.exists():
            try:
                # 尝试运行 --version 或 --help 验证
                test_result = subprocess.run(
                    [str(exe), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if test_result.returncode == 0:
                    print(f"✅ {name} 安装成功并可执行")
                else:
                    # --version失败,尝试--help
                    test_result = subprocess.run(
                        [str(exe), "--help"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if test_result.returncode == 0 or "usage" in test_result.stdout.lower():
                        print(f"✅ {name} 安装成功")
                    else:
                        print(f"⚠️  {name} 可能需要额外配置或依赖")
            except subprocess.TimeoutExpired:
                print(f"⚠️  {name} 验证超时,但可能正常工作")
            except Exception as e:
                print(f"⚠️  {name} 验证失败: {e}")
        
        return str(exe)