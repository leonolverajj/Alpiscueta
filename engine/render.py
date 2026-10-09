"""Timeline + frame renderer.

Timeline is audio-driven: every scene lasts lead + narration + tail, and chapter scenes get
a title card in front. Each segment is rendered to its own mp4 (in parallel), then concatenated.
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

from . import kit
from .kit import FPS, H, W, col, ease_in, ease_out, fillp, mix, stroke, win

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
LEAD, TAIL, CARD = 0.6, 0.9, 3.4
WIPE = 0.45


def audio_len(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                   "csv=p=0", path])
    return float(out)


def timeline():
    g = json.load(open(os.path.join(ROOT, "guion", "guion.json"), encoding="utf-8"))
    segs, t = [], 0.0
    for i, s in enumerate(g["scenes"]):
        if s.get("kw"):
            segs.append(dict(name=f"{s['id']}_card", visual="chapter", start=t, dur=CARD, kw=s["kw"], scene=s))
            t += CARD
        mp3 = os.path.join(ROOT, "audio", "narration", s["id"] + ".mp3")
        n = audio_len(mp3) if os.path.exists(mp3) else len(s["text"]) / 12.3
        tail = TAIL + s.get("extra_tail", 0.0)
        if s["id"] in ("s03",):
            tail += 2.5
        if s["id"] in ("s52",):
            tail += 2.0
        if s["id"] == "s54":
            tail += 6.0
        nxt = g["scenes"][i + 1] if i + 1 < len(g["scenes"]) else None
        if nxt is not None and nxt.get("kw"):
            tail += 0.5
        dur = LEAD + n + tail
        segs.append(dict(name=s["id"], visual=s["visual"], start=t, dur=dur, narr=n, scene=s, voice_at=t + LEAD))
        t += dur
    return segs


def _wipe(ctx, t, T, seed):
    """Angular slab wipe: slabs leave at the start and arrive at the end of each segment."""
    import random
    k_in = 1 - ease_out(win(t, 0, WIPE), 2)          # 1 -> 0 at start
    k_out = ease_in(win(t, T - WIPE * 0.8, T), 2)    # 0 -> 1 at end
    for k, direction in ((k_in, 1), (k_out, -1)):
        if k <= 0.001:
            continue
        rng = random.Random(seed)
        cols = ["ink", mix("g5", "ink", 0.4), "g6"]
        for j in range(3):
            off = (1 - k) * (W * 1.6) * direction * (1 + j * 0.15)
            if direction == -1:
                off = (1 - k) * W * 1.6 * (1 + j * 0.15)
                off = -off if seed % 2 else off
            sk = 300 + j * 80
            pts = [(-sk + off, 0), (W + 60 + off, 0), (W + 60 + sk + off, H), (-200 + off, H)]
            pts = [(x + rng.uniform(-30, 30), y) for x, y in pts]
            fillp(ctx, pts, cols[j])
        if 0.15 < k < 0.95:
            stroke(ctx, [(W * 0.1, H * 0.5), (W * 0.9, H * 0.48)], 6, "teal", alpha=0.0)


def render_segment(seg, out_path, preview_at=None):
    from scenes import get_scene
    draw = get_scene(seg["visual"])
    T = seg["dur"]
    nframes = int(round(T * FPS))
    if preview_at is not None:
        frames = [int(min(nframes - 1, max(0, f * nframes))) for f in preview_at]
    else:
        frames = range(nframes)
        proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
                                 "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset",
                                 "medium", "-crf", "17", "-pix_fmt", "yuv420p", out_path], stdin=subprocess.PIPE)
    seed = sum(map(ord, seg["name"]))
    shots = []
    for fi in frames:
        t = fi / FPS
        surf, ctx = kit.new_frame()
        ctx.save()
        draw(ctx, t, T, seg)
        ctx.restore()
        kit.post(ctx, t)
        _wipe(ctx, t, T, seed)
        surf.flush()
        if preview_at is not None:
            shots.append(surf)
        else:
            proc.stdin.write(bytes(surf.get_data()))
    if preview_at is not None:
        return shots
    proc.stdin.close()
    proc.wait()
    return out_path


def _job(args):
    seg, out = args
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out
    tmp = out + ".tmp.mp4"
    render_segment(seg, tmp)
    os.replace(tmp, out)
    print("  rendered", seg["name"], f"{seg['dur']:.1f}s", flush=True)
    return out


def render_all(only=None, procs=4):
    segs = timeline()
    os.makedirs(os.path.join(BUILD, "segments"), exist_ok=True)
    jobs = []
    for s in segs:
        out = os.path.join(BUILD, "segments", s["name"] + ".mp4")
        if only and s["name"] not in only and s["visual"] not in only:
            continue
        if only and os.path.exists(out):
            os.remove(out)
        jobs.append((s, out))
    jobs.sort(key=lambda j: -j[0]["dur"])
    with Pool(procs) as p:
        list(p.imap_unordered(_job, jobs))
    with open(os.path.join(BUILD, "segments", "list.txt"), "w") as f:
        for s in segs:
            f.write(f"file '{s['name']}.mp4'\n")
    return segs


def contact_sheet(names=None, fracs=(0.15, 0.5, 0.85), out=None, scale=0.25):
    """Preview PNG: a few frames from each listed segment, tiled."""
    import cairo
    segs = [s for s in timeline() if not names or s["name"] in names or s["visual"] in names]
    cols = len(fracs)
    tw, th = int(W * scale), int(H * scale)
    sheet = cairo.ImageSurface(cairo.FORMAT_ARGB32, tw * cols, (th + 24) * len(segs))
    c = cairo.Context(sheet)
    c.set_source_rgb(1, 1, 1)
    c.paint()
    for r, s in enumerate(segs):
        shots = render_segment(s, None, preview_at=fracs)
        for k, surf in enumerate(shots):
            c.save()
            c.translate(k * tw, r * (th + 24) + 24)
            c.scale(scale, scale)
            c.set_source_surface(surf, 0, 0)
            c.paint()
            c.restore()
        c.set_source_rgb(0, 0, 0)
        c.select_font_face("Inter", 0, 1)
        c.set_font_size(16)
        c.move_to(6, r * (th + 24) + 18)
        c.show_text(f"{s['name']}  [{s['visual']}]  {s['dur']:.1f}s")
    out = out or os.path.join(BUILD, "preview", "sheet.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.write_to_png(out)
    return out


if __name__ == "__main__":
    sys.path.insert(0, ROOT)
    if len(sys.argv) > 1 and sys.argv[1] == "sheet":
        print(contact_sheet(sys.argv[2:] or None))
    else:
        render_all(sys.argv[1:] or None)
