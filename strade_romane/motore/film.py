"""Timeline, continuous transitions and rendering for 'La linea che partì da Roma'.

No cuts and no title cards: each beat is a scene drawn in white line art. In the last moments of a
beat its drawing retracts (as if the pen ran backwards) while the next beat draws itself on, and the
*road line* — present in every beat — morphs from one shape to the next, carrying the eye along.
"""
import importlib
import json
import os
import pkgutil
import subprocess
from multiprocessing import Pool

from .linea import FPS, H, W, Pen, clamp, ease_io, finish, morph, new_frame, smooth, win

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
LEAD, TAIL = 0.5, 1.1     # silence before / after each narration line
XF = 1.6                  # cross-draw transition length (s), centred on the beat boundary

SCENES = {}


def scena(name):
    """Register a scene: fn(pen, t, T, appear, vanish) -> road polyline (screen coords) or None."""
    def deco(fn):
        SCENES[name] = fn
        return fn
    return deco


def _load():
    if SCENES.get("__loaded__"):
        return
    import scene as pkg
    for m in pkgutil.iter_modules(pkg.__path__):
        importlib.import_module(f"scene.{m.name}")
    SCENES["__loaded__"] = True


def _placeholder(pen, t, T, appear, vanish):
    return [(x, 790.0) for x in range(-60, W + 61, 60)]


def durata(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]))


CPS = 13.0                # design speaking rate the scenes were timed against


def _warp_points(b, has_p, n_act, n_est, lead, Tl_act, Tl_des):
    """Piecewise-linear map actual local time -> design local time, from word timings."""
    half = XF / 2 if has_p else 0.0
    s0 = half + lead
    pts = [(0.0, 0.0), (s0, s0)]
    al = os.path.join(ROOT, "audio", "narrazione", b["id"] + ".align.json")
    if os.path.exists(al):
        a = json.load(open(al, encoding="utf-8"))
        chars, st = a["characters"], a["character_start_times_seconds"]
        n = len(chars)
        L = len(b["testo"])
        for i in range(0, n, 6):
            if chars[i] == " ":
                continue
            ta = s0 + st[i]
            td = s0 + (i / max(1, n)) * L / CPS
            if ta > pts[-1][0] + 0.05 and td > pts[-1][1] + 0.01:
                pts.append((ta, td))
    end_a, end_d = s0 + n_act, s0 + n_est
    if end_a > pts[-1][0] and end_d > pts[-1][1]:
        pts.append((end_a, end_d))
    pts.append((max(Tl_act, pts[-1][0] + 0.1), max(Tl_des, pts[-1][1] + 0.1)))
    return pts


def warp(pts, t):
    if t <= pts[0][0]:
        return t
    for (a0, d0), (a1, d1) in zip(pts, pts[1:]):
        if t <= a1:
            return d0 + (d1 - d0) * (t - a0) / max(1e-6, a1 - a0)
    a1, d1 = pts[-1]
    return d1 + (t - a1)


def timeline():
    g = json.load(open(os.path.join(ROOT, "testo", "copione.json"), encoding="utf-8"))
    out, t = [], 0.0
    bs = g["battute"]
    for k, b in enumerate(bs):
        mp3 = os.path.join(ROOT, "audio", "narrazione", b["id"] + ".mp3")
        n_est = len(b["testo"]) / CPS
        n = durata(mp3) if os.path.exists(mp3) else n_est
        lead = LEAD + b.get("pausa_prima", 0.0)
        tail = TAIL + b.get("pausa_dopo", 0.0)
        if k == 0:
            lead += 2.5          # the line draws itself before the first words
        if k == len(bs) - 1:
            tail += 6.0          # let the ending breathe
        d = lead + n + tail
        has_p, has_n = k > 0, k + 1 < len(bs)
        ext = (XF / 2) * has_p + (XF / 2) * has_n
        Tl_act = d + ext
        Tl_des = lead + n_est + tail + ext
        wp = _warp_points(b, has_p, n, n_est, lead, Tl_act, Tl_des)
        out.append(dict(id=b["id"], visual=b["visual"], start=t, dur=d, voice_at=t + lead, narr=n, testo=b["testo"],
                        warp=wp, Tdes=Tl_des))
        t += d
    return out


def total_length(tl=None):
    tl = tl or timeline()
    return tl[-1]["start"] + tl[-1]["dur"]


def draw_frame(tl, T):
    """Render the frame at global time T (seconds). Returns the cairo surface.

    A beat is visible from (start - XF/2) to (start + dur + XF/2). Scenes receive a local clock t that
    starts when they begin to appear, their full visible length Tl, and appear/vanish fractions
    (0..1) to feed into pen.lines(reveal=appear, start=vanish)."""
    _load()
    surf, ctx = new_frame()
    pen = Pen(ctx, T)
    half = XF / 2
    actives = []
    for i, b in enumerate(tl):
        has_p, has_n = i > 0, i + 1 < len(tl)
        a0 = b["start"] - (half if has_p else 0.0)
        a1 = b["start"] + b["dur"] + (half if has_n else 0.0)
        if a0 <= T < a1:
            actives.append((i, b, has_p, has_n, a0, a1))
    roads = []
    for i, b, has_p, has_n, a0, a1 in actives:
        t, Tl = T - a0, a1 - a0
        appear = smooth(t / XF) if has_p else smooth(t / 2.4)
        vanish = smooth((t - (Tl - XF)) / XF) if has_n else 0.0
        slide = 150 * (1 - ease_io(clamp(t / XF))) * has_p - 150 * ease_io(clamp((t - (Tl - XF)) / XF)) * has_n
        ctx.save()
        ctx.translate(slide, 0)
        td = warp(b["warp"], t)
        road = SCENES.get(b["visual"], _placeholder)(pen, td, b["Tdes"], appear, vanish)
        ctx.restore()
        if road:
            roads.append([(x + slide, y) for x, y in road])
    if len(roads) == 2:
        # morph from the outgoing road to the incoming one across the overlap
        i, b = actives[1][0], actives[1][1]
        k = ease_io(clamp((T - (b["start"] - half)) / XF))
        pen.line(morph(roads[0], roads[1], k, 180), 1.15, 1.0, seed=3)
    elif roads:
        first = actives[0][0] == 0
        rv = smooth((T - 0.2) / 2.2) if first else 1.0
        pen.line(roads[0], 1.15, 1.0, reveal=rv, seed=3)
    finish(ctx, T)
    return surf


# ----------------------------------------------------------------- rendering
def _render_chunk(args):
    a, b, out = args
    tl = timeline()
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s",
                             f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                             "-tune", "animation", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(a, b):
        s = draw_frame(tl, f / FPS)
        proc.stdin.write(bytes(s.get_data()))
    proc.stdin.close()
    proc.wait()
    return out


def render(t0=0.0, t1=None, procs=4, name="video"):
    """Render [t0, t1) seconds into build/<name>.mp4 using parallel chunks."""
    tl = timeline()
    t1 = t1 if t1 is not None else total_length(tl)
    f0, f1 = int(t0 * FPS), int(t1 * FPS)
    os.makedirs(os.path.join(BUILD, "chunks"), exist_ok=True)
    n = max(procs * 3, 1)
    step = max(1, (f1 - f0 + n - 1) // n)
    jobs = []
    for k, a in enumerate(range(f0, f1, step)):
        jobs.append((a, min(f1, a + step), os.path.join(BUILD, "chunks", f"{name}_{k:03d}.mp4")))
    with Pool(procs) as p:
        outs = list(p.imap(_render_chunk, jobs))
    lst = os.path.join(BUILD, "chunks", f"{name}.txt")
    with open(lst, "w") as fh:
        for o in outs:
            fh.write(f"file '{o}'\n")
    out = os.path.join(BUILD, f"{name}.mp4")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    return out


def still(T, path):
    draw_frame(timeline(), T).write_to_png(path)
    return path
