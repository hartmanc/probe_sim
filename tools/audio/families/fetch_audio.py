"""Download one YouTube video's audio only (never video), check its licence on the page, convert to mono 48 kHz FLAC.

    python3 -I tools/audio/families/fetch_audio.py FAMILY VIDEO_ID [--max-s 900]

The download lands in its own fresh directory under cache/ (untrusted: only ffmpeg reads it), the FLAC goes to
cache/<family>__<id>.flac, the download is deleted, and a JSON record (url, title, channel, upload date, licence as
shown, duration) is written to cache/<family>__<id>.json. Refuses anything whose licence is not CC BY.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"


def main(fam, vid, max_s=900):
    url = f"https://www.youtube.com/watch?v={vid}"
    out = os.path.join(CACHE, f"{fam}__{vid}.flac")
    if os.path.exists(out):
        return
    d = tempfile.mkdtemp(prefix=f"dl_{vid}_", dir=CACHE)
    try:
        meta = json.loads(subprocess.run(["uvx", "yt-dlp", "--js-runtimes", "node", "--no-playlist", "-J", "--skip-download", url],
                                         check=True, capture_output=True, text=True).stdout)
        lic = meta.get("license") or ""
        if not lic.startswith("Creative Commons Attribution"):
            raise SystemExit(f"{vid}: licence is {lic!r}, not CC BY: refusing")
        subprocess.run(["uvx", "yt-dlp", "--js-runtimes", "node", "-q", "--no-playlist", "-f", "bestaudio", "-o",
                        os.path.join(d, "a.%(ext)s"), url], check=True, capture_output=True)
        got = [f for f in os.listdir(d) if f.startswith("a.")]
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", os.path.join(d, got[0]), "-vn", "-ac", "1", "-ar", "48000",
                        "-t", str(max_s), "-c:a", "flac", out], check=True)
        json.dump({"url": url, "title": meta.get("title"), "channel": meta.get("channel") or meta.get("uploader"),
                   "upload_date": meta.get("upload_date"), "licence": lic, "duration_s": meta.get("duration"),
                   "file": f"cache/{fam}__{vid}.flac", "max_s": max_s},
                  open(os.path.join(CACHE, f"{fam}__{vid}.json"), "w"), indent=1, ensure_ascii=False)
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    ms = 900
    if "--max-s" in sys.argv:
        ms = int(sys.argv[sys.argv.index("--max-s") + 1])
        a = [x for x in a if x != str(ms)]
    main(a[0], a[1], ms)
