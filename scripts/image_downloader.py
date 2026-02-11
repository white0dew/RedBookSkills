"""
Media downloader for Xiaohongshu publishing.

Downloads images and videos from URLs to a local temp directory for upload,
and cleans up after publishing is complete.
"""

import os
import sys
import tempfile
import shutil
import uuid
from urllib.parse import urlparse, unquote

import requests

DEFAULT_TIMEOUT = 30  # seconds per download
TEMP_DIR_PREFIX = "xhs_images_"


class ImageDownloader:
    """Download images from URLs and manage a temporary directory for them."""

    def __init__(self, temp_dir: str | None = None):
        if temp_dir:
            self.temp_dir = temp_dir
            os.makedirs(self.temp_dir, exist_ok=True)
            self._owns_dir = False
        else:
            self.temp_dir = tempfile.mkdtemp(prefix=TEMP_DIR_PREFIX)
            self._owns_dir = True
        self.downloaded_files: list[str] = []

    def _guess_extension(self, url: str, content_type: str | None) -> str:
        """Guess file extension from URL path or Content-Type header."""
        # Try URL path first
        path = urlparse(url).path
        _, ext = os.path.splitext(unquote(path))
        if ext and ext.lower() in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
            return ext.lower()

        # Fall back to Content-Type
        ct_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
        }
        if content_type:
            for mime, ext in ct_map.items():
                if mime in content_type:
                    return ext

        return ".jpg"  # safe default

    def _guess_video_extension(self, url: str, content_type: str | None) -> str:
        """Guess video file extension from URL path or Content-Type header."""
        path = urlparse(url).path
        _, ext = os.path.splitext(unquote(path))
        if ext and ext.lower() in (".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"):
            return ext.lower()

        ct_map = {
            "video/mp4": ".mp4",
            "video/quicktime": ".mov",
            "video/x-msvideo": ".avi",
            "video/x-matroska": ".mkv",
            "video/x-flv": ".flv",
            "video/x-ms-wmv": ".wmv",
            "video/webm": ".webm",
        }
        if content_type:
            for mime, ext in ct_map.items():
                if mime in content_type:
                    return ext

        return ".mp4"  # safe default for video

    def download(self, url: str, referer: str | None = None) -> str:
        """
        Download a single image and return the local file path.

        Args:
            url: Image URL to download
            referer: Optional Referer header. If None, auto-generates from URL domain.

        Raises requests.RequestException on network errors.
        """
        # Build headers with Referer to bypass hotlink protection
        parsed = urlparse(url)
        if referer is None:
            referer = f"{parsed.scheme}://{parsed.netloc}/"

        headers = {
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        resp = requests.get(url, timeout=DEFAULT_TIMEOUT, stream=True, headers=headers)
        resp.raise_for_status()

        ext = self._guess_extension(url, resp.headers.get("Content-Type"))
        filename = f"{uuid.uuid4().hex[:12]}{ext}"
        filepath = os.path.join(self.temp_dir, filename)

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        self.downloaded_files.append(filepath)
        print(f"[image_downloader] Downloaded: {url}")
        print(f"  -> {filepath} ({os.path.getsize(filepath)} bytes)")
        return filepath

    def download_video(self, url: str, referer: str | None = None) -> str:
        """
        Download a single video and return the local file path.

        Args:
            url: Video URL to download
            referer: Optional Referer header. If None, auto-generates from URL domain.

        Raises requests.RequestException on network errors.
        """
        parsed = urlparse(url)
        if referer is None:
            referer = f"{parsed.scheme}://{parsed.netloc}/"

        headers = {
            "Referer": referer,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        resp = requests.get(url, timeout=DEFAULT_TIMEOUT * 4, stream=True, headers=headers)
        resp.raise_for_status()

        ext = self._guess_video_extension(url, resp.headers.get("Content-Type"))
        filename = f"{uuid.uuid4().hex[:12]}{ext}"
        filepath = os.path.join(self.temp_dir, filename)

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)

        self.downloaded_files.append(filepath)
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"[image_downloader] Downloaded video: {url}")
        print(f"  -> {filepath} ({size_mb:.1f} MB)")
        return filepath

    def download_all(self, urls: list[str]) -> list[str]:
        """
        Download multiple images. Returns list of local file paths.

        Skips URLs that fail to download (logs the error, continues).
        """
        paths = []
        for url in urls:
            try:
                path = self.download(url)
                paths.append(path)
            except Exception as e:
                print(f"[image_downloader] Failed to download {url}: {e}", file=sys.stderr)
        return paths

    def cleanup(self):
        """Remove all downloaded files and the temp directory."""
        if self._owns_dir and os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print(f"[image_downloader] Cleaned up temp dir: {self.temp_dir}")
        else:
            for f in self.downloaded_files:
                try:
                    os.remove(f)
                except OSError:
                    pass
            print(f"[image_downloader] Cleaned up {len(self.downloaded_files)} files.")
        self.downloaded_files.clear()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cleanup()


if __name__ == "__main__":
    # Quick test: download URLs passed as command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python image_downloader.py <url1> [url2] ...")
        sys.exit(1)

    dl = ImageDownloader()
    paths = dl.download_all(sys.argv[1:])
    print(f"\nDownloaded {len(paths)} image(s):")
    for p in paths:
        print(f"  {p}")
    print(f"Temp dir: {dl.temp_dir}")
    print("Files will remain until manually cleaned up.")
