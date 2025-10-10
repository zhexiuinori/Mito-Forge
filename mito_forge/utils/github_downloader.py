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
    说明：本版本不解析 GitHub Release 列表，仅支持 sources.json 提供的 assets[plat].url。
    """
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
        # http/https
        req = Request(url, headers={"User-Agent": "Mito-Forge/1.0"})
        with urlopen(req) as resp, open(dest_file, "wb") as out:
            shutil.copyfileobj(resp, out)

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