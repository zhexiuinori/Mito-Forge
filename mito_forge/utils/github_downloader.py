from __future__ import annotations
import hashlib
import shutil
import tarfile
import zipfile
from urllib.parse import urlparse, unquote
from urllib.request import urlopen, Request, url2pathname
from pathlib import Path

class GitHubDownloader:
    """
    简化的下载器实现：
    - 支持 http/https 与 file:// 直链下载
    - 可选 sha256 校验
    - 自动解压 zip 与 tar.gz
    - 支持镜像站自动切换
    说明：本版本不解析 GitHub Release 列表，仅支持 sources.json 提供的 assets[plat].url。
    """
    
    # GitHub 镜像站列表（按优先级排序）
    GITHUB_MIRRORS = [
        "",  # 首先尝试直连
        "https://ghproxy.com/",
        "https://ghproxy.net/",
        "https://mirror.ghproxy.com/",
    ]
    @staticmethod
    def _sha256(p: Path) -> str:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _download_to(url: str, dest_file: Path) -> None:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            local_path = url2pathname(parsed.path)
            src = Path(local_path)
            if not src.exists():
                raise FileNotFoundError(f"file url not found: {src}")
            shutil.copyfile(src, dest_file)
            return
        
        # http/https - 尝试多个镜像
        last_error = None
        for mirror in GitHubDownloader.GITHUB_MIRRORS:
            try:
                # 构造下载 URL
                if mirror and url.startswith("https://github.com/"):
                    download_url = mirror + url
                else:
                    download_url = url
                
                req = Request(download_url, headers={"User-Agent": "Mito-Forge/1.0"})
                with urlopen(req, timeout=600) as resp, open(dest_file, "wb") as out:
                    # 获取文件大小
                    total_size = int(resp.headers.get('Content-Length', 0))
                    downloaded = 0
                    chunk_size = 8192
                    
                    # 分块下载并显示进度
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        out.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示进度
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            print(f"\rDownloading: {mb_downloaded:.1f}MB / {mb_total:.1f}MB ({percent:.1f}%)", end='', flush=True)
                        else:
                            mb_downloaded = downloaded / (1024 * 1024)
                            print(f"\rDownloading: {mb_downloaded:.1f}MB", end='', flush=True)
                    
                    print()  # 换行
                
                # 下载成功
                if mirror:
                    print(f"Successfully downloaded via mirror: {mirror}")
                return
                
            except Exception as e:
                last_error = e
                if mirror:
                    print(f"Mirror {mirror} failed: {e}")
                else:
                    print(f"Direct download failed: {e}, trying mirrors...")
                continue
        
        # 所有镜像都失败
        raise last_error or Exception("All download attempts failed")

    @staticmethod
    def _extract(archive: Path, dest_dir: Path) -> None:
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = archive.name.lower()
        if name.endswith(".zip"):
            with zipfile.ZipFile(archive, "r") as zf:
                zf.extractall(dest_dir)
        elif name.endswith(".tar.gz") or name.endswith(".tgz"):
            with tarfile.open(archive, "r:gz") as tf:
                tf.extractall(dest_dir)
        else:
            # 不识别的格式，直接保留
            pass

    @staticmethod
    def download(repo: str, version: str, asset_url_or_pattern: str, dest_dir: Path, sha256: str | None = None) -> Path:
        """
        当前 asset_url_or_pattern 必须是可下载的直链 URL（http/https/file），pattern 暂不支持。
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        url_lower = asset_url_or_pattern.lower()
        if url_lower.endswith(".zip") or "/zip/" in url_lower:
            tmp = dest_dir / "download.zip"
        elif url_lower.endswith(".tar.gz") or url_lower.endswith(".tgz") or "/tar.gz/" in url_lower:
            tmp = dest_dir / "download.tar.gz"
        else:
            tmp = dest_dir / "download.tmp"
        GitHubDownloader._download_to(asset_url_or_pattern, tmp)

        if sha256:
            got = GitHubDownloader._sha256(tmp)
            if got.lower() != sha256.lower():
                tmp.unlink(missing_ok=True)
                raise ValueError(f"sha256 mismatch: got {got}, expect {sha256}")

        # 解压（如果是压缩包）
        GitHubDownloader._extract(tmp, dest_dir)
        return dest_dir