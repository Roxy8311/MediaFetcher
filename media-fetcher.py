#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import shutil
import subprocess
from pathlib import Path

# ---------- anti-spam install: helpers ----------

_DEPS_READY = False           # garde-fou pour ne pas relancer ensure_requirements()
_FFMPEG_ADDED = False         # évite d'ajouter plusieurs fois au PATH

def run_pip_install(pkg: str) -> bool:
    """Install a package via pip (silencieux) et retourne True si OK."""
    try:
        cmd = [
            sys.executable, "-m", "pip", "install",
            "--disable-pip-version-check", "--quiet", "--upgrade", pkg
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except Exception:
        return False

def ensure_import(import_name: str, pip_name: str = None) -> bool:
    """Tente d'importer; sinon installe pip_name (ou import_name) UNE fois, puis réessaie."""
    try:
        __import__(import_name)
        return True
    except ImportError:
        if pip_name is None:
            pip_name = import_name
        ok = run_pip_install(pip_name)
        if not ok:
            return False
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False

def ensure_requirements_once():
    """Assure yt-dlp + ffmpeg (via imageio-ffmpeg si besoin). Ne s'exécute qu'une seule fois."""
    global _DEPS_READY, _FFMPEG_ADDED
    if _DEPS_READY:
        return

    # 1) yt-dlp
    if not ensure_import("yt_dlp", "yt-dlp"):
        print("✗ Could not install/import 'yt-dlp'.")
        sys.exit(1)

    # 2) ffmpeg
    if shutil.which("ffmpeg") is None:
        # Essayer imageio-ffmpeg
        if not ensure_import("imageio_ffmpeg", "imageio-ffmpeg"):
            print("✗ FFmpeg not found and 'imageio-ffmpeg' install failed.")
            sys.exit(1)
        import imageio_ffmpeg
        ff = Path(imageio_ffmpeg.get_ffmpeg_exe())
        ff_dir = str(ff.parent)
        # Ajouter au PATH seulement si pas déjà présent
        if ff_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + ff_dir
            _FFMPEG_ADDED = True

    _DEPS_READY = True

# ---------- formats filtrés & téléchargement ----------

YRX = re.compile(r"(youtu\.be/|youtube\.com/)", re.IGNORECASE)

def list_safe_formats(url: str):
    """Retourne uniquement les formats vidéo MP4/H.264 (avc1), triés par hauteur décroissante."""
    from yt_dlp import YoutubeDL
    with YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])
    safe = []
    for f in formats:
        if f.get("ext") == "mp4" and str(f.get("vcodec", "")).startswith("avc1") and (f.get("height") or 0) > 0:
            safe.append(f)
    safe.sort(key=lambda f: f.get("height") or 0, reverse=True)
    return safe

def human_mb(size):
    if not size:
        return "unknown"
    try:
        return f"{(size/1024/1024):.1f} MB"
    except Exception:
        return "unknown"

def download_with_format(url: str, fmt: str):
    from yt_dlp import YoutubeDL
    out_dir = Path("downloads"); out_dir.mkdir(exist_ok=True)
    opts = {
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "format": fmt,
        "postprocessors": [
            {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"},
            {"key": "FFmpegMetadata"},
        ],
        "noplaylist": True,
        "socket_timeout": 15,
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])

def download_audio_mp3(url: str, bitrate: str):
    from yt_dlp import YoutubeDL
    out_dir = Path("downloads"); out_dir.mkdir(exist_ok=True)
    opts = {
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "format": "bestaudio[ext=m4a]/bestaudio",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": bitrate},
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata"},
        ],
        "noplaylist": True,
        "socket_timeout": 15,
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])

# ---------- CLI ----------

def main():
    print("=== Downloader (YouTube) — terminal ===")
    ensure_requirements_once()  # ne s’exécute qu’une fois

    url = input("Paste YouTube link: ").strip()
    if not YRX.search(url):
        print("⚠️ Only YouTube links are supported.")
        sys.exit(0)

    print("\nWanted file type:")
    print("  1 - Video (choose a safe MP4/H.264)")
    print("  2 - Audio (MP3)")
    t = input("Your choice (1/2): ").strip()

    if t == "1":
        # Affiche seulement les formats sûrs
        try:
            fmts = list_safe_formats(url)
        except Exception as e:
            print(f"✗ Could not fetch formats: {e}")
            sys.exit(1)

        if not fmts:
            print("No safe MP4/H.264 formats found. You can try audio-only.")
            sys.exit(1)

        print("\n=== Safe MP4/H.264 formats ===")
        for idx, f in enumerate(fmts, 1):
            h = f.get("height") or "?"
            fps = f.get("fps") or ""
            note = f.get("format_note") or ""
            size = human_mb(f.get("filesize") or f.get("filesize_approx"))
            print(f"[{idx}] {h}p{' '+str(int(fps)) if fps else ''}  {note}  {f.get('vcodec')}  ~{size}  id={f.get('format_id')}")

        print("\n[0] Best automatically (MP4+M4A preferred)")
        sel = input("Choose a number: ").strip()

        if sel == "0":
            # MP4 video + M4A audio si possible; sinon best fallback
            fmt = "bv*[ext=mp4][vcodec^=avc1]+ba[ext=m4a]/best[ext=mp4]/best"
        else:
            try:
                i = int(sel)
                if i < 1 or i > len(fmts):
                    raise ValueError
            except ValueError:
                print("Invalid choice.")
                sys.exit(1)
            fid = fmts[i-1]["format_id"]
            # Combinaison avec audio M4A/AAC prioritaire; fallback bestaudio
            fmt = f"{fid}+bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio"

        print(f"\n→ Downloading (format selector: {fmt}) …")
        try:
            download_with_format(url, fmt)
        except Exception as e:
            print(f"✗ Download error: {e}")
            sys.exit(1)

    elif t == "2":
        br = input("MP3 bitrate (128/192/320, default=192): ").strip() or "192"
        print(f"\n→ Downloading audio MP3 ({br} kbps) …")
        try:
            download_audio_mp3(url, br)
        except Exception as e:
            print(f"✗ Download error: {e}")
            sys.exit(1)
    else:
        print("Invalid choice.")
        sys.exit(1)

    print("\n✅ Done. Files saved to ./downloads")

if __name__ == "__main__":
    main()
