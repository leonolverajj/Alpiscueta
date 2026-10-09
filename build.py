"""One-command build of 'La Idea de Dios'.

  python build.py              # render every segment (skips finished ones), mix audio, mux final mp4
  python build.py s31 battle   # re-render only these segments / visuals, then re-mux
  python build.py --audio      # only rebuild the soundtrack + re-mux

Narration must exist in audio/narration (python audio/narrate.py).
Output: build/La_Idea_de_Dios.mp4 (1080p24, H.264 + AAC) and build/La_Idea_de_Dios.srt.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine.render import BUILD, render_all, timeline  # noqa: E402


def srt():
    """Spanish subtitles from ElevenLabs character alignment (sentence-sized cues)."""
    def fmt(x):
        h, m = int(x // 3600), int(x % 3600 // 60)
        s = x % 60
        return f"{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    cues = []
    for seg in timeline():
        if seg["visual"] == "chapter":
            continue
        sid = seg["scene"]["id"]
        al = json.load(open(os.path.join(ROOT, "audio", "narration", sid + ".align.json"), encoding="utf-8"))
        chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
        buf, b0 = "", None
        for i, ch in enumerate(chars):
            if b0 is None and ch.strip():
                b0 = st[i]
            buf += ch
            end_here = ch in ".?!:;" or (ch in "," and len(buf) > 55) or (ch == " " and len(buf) > 80)
            if end_here or i == len(chars) - 1:
                if buf.strip():
                    cues.append((seg["voice_at"] + b0, seg["voice_at"] + en[i], buf.strip()))
                buf, b0 = "", None
    path = os.path.join(BUILD, "La_Idea_de_Dios.srt")
    with open(path, "w", encoding="utf-8") as f:
        for k, (a, b, txt) in enumerate(cues, 1):
            f.write(f"{k}\n{fmt(a)} --> {fmt(b)}\n{txt}\n\n")
    return path


def mux():
    segdir = os.path.join(BUILD, "segments")
    video = os.path.join(BUILD, "video_only.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i",
                           os.path.join(segdir, "list.txt"), "-c", "copy", video])
    out = os.path.join(BUILD, "La_Idea_de_Dios.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", os.path.join(BUILD, "audio", "mix.wav"),
                           "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                           "-shortest", "-movflags", "+faststart", out])
    print("wrote", out)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--audio" in args:
        from audio.score import build as build_audio
        build_audio()
    else:
        render_all(args or None)
        if not os.path.exists(os.path.join(BUILD, "audio", "mix.wav")):
            from audio.score import build as build_audio
            build_audio()
    print("wrote", srt())
    mux()
