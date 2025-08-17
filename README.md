# 📥 Media Fetcher (YouTube Downloader)

This is a small Python script to download **YouTube videos or audio** directly from the terminal.
It supports choosing a safe video format (MP4 / H.264) or converting audio to MP3.

---

## ⚙️ Requirements

### 1. Python

* Python **3.8 or higher** installed
* Check with:

  ```bash
  python --version
  ```

### 2. Dependencies (Python packages)

The script will try to **auto-install** missing dependencies at runtime, but you can install them manually:

```bash
pip install yt-dlp imageio-ffmpeg
```

* **yt-dlp** → the actual YouTube/Spotify/etc. downloader backend
* **imageio-ffmpeg** → provides a portable FFmpeg binary if you don’t have FFmpeg installed system-wide

### 3. FFmpeg

The script needs **FFmpeg** to:

* merge video and audio tracks
* convert audio to MP3
* embed thumbnails and metadata

Two options:

* **System install** (recommended):

  * Windows: [Download FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/), extract, and add the `bin/` folder to your PATH
  * Linux (Debian/Ubuntu):

    ```bash
    sudo apt install ffmpeg
    ```
  * macOS (Homebrew):

    ```bash
    brew install ffmpeg
    ```

* **Python fallback**: if FFmpeg is not found, the script uses `imageio-ffmpeg` to download a portable FFmpeg binary automatically.

---

## ▶️ Usage

Run the script:

```bash
python media-fetcher.py
```

It will ask:

1. **Paste the YouTube link**
2. **Choose file type**

   * `1` → Video (choose resolution among safe MP4/H.264)
   * `2` → Audio (MP3, choose bitrate)

### Example session

```
=== Downloader (YouTube) — terminal ===
Paste YouTube link: https://youtu.be/example

Wanted file type:
  1 - Video (choose a safe MP4/H.264)
  2 - Audio (MP3)
Your choice (1/2): 1

=== Safe MP4/H.264 formats ===
[1] 1080p  avc1  ~80.4 MB  id=137
[2] 720p   avc1  ~29.6 MB  id=136
[3] 480p   avc1  ~16.4 MB  id=135
[4] 360p   avc1  ~9.8 MB   id=134

[0] Best automatically (MP4+M4A preferred)
Choose a number: 2

→ Downloading (format selector: 136+bestaudio[ext=m4a]/bestaudio) …
✅ Done. Files saved to ./downloads
```

---

## 📂 Output

* All files are saved in the `./downloads/` folder (created automatically).
* Video files are saved in `.mp4` format.
* Audio files are saved in `.mp3` format.

---

## ⚠️ Notes

* Only **YouTube** is supported in this script (Spotify can only provide metadata, not direct media files).
* The script filters out exotic formats (AV1, WebM, mhtml, opus, etc.) to ensure maximum compatibility.
* For MP3 downloads, audio is extracted from the best available M4A or AAC stream.
