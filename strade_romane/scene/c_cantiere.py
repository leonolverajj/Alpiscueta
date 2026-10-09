"""b06 cantiere · b07 tavole · b08 miliario · b10 posta"""
import json
import math
import os
import random

import cairo

from motore.film import scena
from motore.linea import (BG, H, W, Pen, arc, lerp2, length, at, catmull, clamp, ease_in, ease_io, ease_out, ellipse, lerp, morph,
                          resample, rot, smooth, trim, wave, win)
from motore.omino import DOWN, noodle, omino
from motore.personaggi import face, mitten, mulo

ROAD_Y = 790
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TXT = {b["visual"]: b["testo"] for b in
        json.load(open(os.path.join(_ROOT, "testo", "copione.json"), encoding="utf-8"))["battute"]}


# ======================================================================= shared helpers
def cue(T, vis, phrase, frac=0.0):
    """Local time (s) at which the narrator reaches `phrase` (speech ≈ uniform between 1.3 s and T-1.9 s)."""
    txt = _TXT[vis]
    i = txt.find(phrase)
    if i < 0:
        raise ValueError(phrase)
    n = max(1.0, T - 3.2)
    return 1.3 + n * (i + frac * len(phrase)) / len(txt)


_SURF = {}


def cached(pen, name, y0, y1, fn):
    """Draw a static, fully revealed drawing through a per-boil-phase bitmap cache (the boil has 3 phases).
    fn(p) draws with pen p in the current user space; only the band y0..y1 is kept."""
    key = (name, pen.boil_t % 3)
    surf = _SURF.get(key)
    if surf is None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, int(y1 - y0))
        c = cairo.Context(surf)
        c.translate(0, -y0)
        p = Pen(c, pen.t)
        p.boil_t = pen.boil_t
        fn(p)
        _SURF[key] = surf
    pen.ctx.set_source_surface(surf, 0, y0)
    pen.ctx.paint()


def pulse(t, a, b, fade=0.5):
    """0→1 at a, 1→0 at b (smooth)."""
    return smooth(win(t, a, a + fade)) * (1 - smooth(win(t, b - fade, b)))


def flat(y=ROAD_Y, x0=-60, x1=W + 60, n=40):
    return [(lerp(x0, x1, i / (n - 1)), y) for i in range(n)]


def ik(sh, P, l1, l2):
    """Two-bone IK; picks the elbow that hangs lower. Returns (a1, a2)."""
    dx, dy = P[0] - sh[0], P[1] - sh[1]
    d = clamp(math.hypot(dx, dy), 1e-3, l1 + l2 - 0.5)
    base = math.atan2(dy, dx)
    al = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    best = None
    for sg in (1, -1):
        a1 = base + sg * al
        p1 = (sh[0] + math.cos(a1) * l1, sh[1] + math.sin(a1) * l1)
        a2 = math.atan2(P[1] - p1[1], P[0] - p1[0])
        if best is None or p1[1] > best[2]:
            best = (a1, a2, p1[1])
    return best[0], best[1]


def _bob(t, seed):
    return wave(t, 0.23, seed) * 1.6


def worker(pen, x, y, s, t, costume, G, phi, grip2=-30.0, fx=1, lean=0.0, expr="calm", alpha=1.0, seed=0,
           look=0.0, head_tilt=0.0, back_target=None, front_target=None, tool=None):
    """An omino holding a tool with both hands. G: front-hand grip (local, facing right, feet at 0,0, unleaned),
    phi: tool direction. The back hand grips at G + dir(phi)*grip2 unless back_target is given."""
    L = lean * 0.25
    bob = _bob(t, seed)
    sh_f = (16, -186 + bob)
    sh_b = (-14, -186 + bob)
    Gr = rot(front_target or G, -L)
    af = ik(sh_f, Gr, 46, 47)
    bt = back_target or (G[0] + math.cos(phi) * grip2, G[1] + math.sin(phi) * grip2)
    ab = ik(sh_b, rot(bt, -L), 44, 45)
    omino(pen, x, y, s, t, costume, fx=fx, lean=lean, expr=expr, arm_f=af, arm_b=ab, alpha=alpha, seed=seed,
          look=look, head_tilt=head_tilt)
    with at(pen, x, y, s, fx=fx):
        if tool:
            tool(pen, G, phi, alpha, seed)


def pick_tool(pen, G, phi, alpha, seed):
    d = (math.cos(phi), math.sin(phi))
    p = (-d[1], d[0])
    b0 = (G[0] - d[0] * 40, G[1] - d[1] * 40)
    E = (G[0] + d[0] * 92, G[1] + d[1] * 92)
    pen.line([b0, E], 1.0, alpha, smooth_=False, seed=seed + 200)
    head = [(E[0] + p[0] * 62 - d[0] * 20, E[1] + p[1] * 62 - d[1] * 20), (E[0] + p[0] * 30 - d[0] * 2, E[1] + p[1] * 30 - d[1] * 2),
            (E[0] + d[0] * 6, E[1] + d[1] * 6),
            (E[0] - p[0] * 30 - d[0] * 2, E[1] - p[1] * 30 - d[1] * 2), (E[0] - p[0] * 50 - d[0] * 14, E[1] - p[1] * 50 - d[1] * 14)]
    pen.line(head, 1.1, alpha, seed=seed + 201)


def shovel_tool(pen, G, phi, alpha, seed):
    d = (math.cos(phi), math.sin(phi))
    p = (-d[1], d[0])
    b0 = (G[0] - d[0] * 96, G[1] - d[1] * 96)
    E = (G[0] + d[0] * 66, G[1] + d[1] * 66)
    pen.line([b0, E], 1.0, alpha, smooth_=False, seed=seed + 210)
    pen.line([(b0[0] - p[0] * 9, b0[1] - p[1] * 9), (b0[0] + p[0] * 9, b0[1] + p[1] * 9)], 0.9, alpha, seed=seed + 211)
    w = 19
    blade = [(E[0] + p[0] * w * 0.7, E[1] + p[1] * w * 0.7), (E[0] + p[0] * w + d[0] * 30, E[1] + p[1] * w + d[1] * 30),
             (E[0] + d[0] * 50, E[1] + d[1] * 50),
             (E[0] - p[0] * w + d[0] * 30, E[1] - p[1] * w + d[1] * 30), (E[0] - p[0] * w * 0.7, E[1] - p[1] * w * 0.7),
             (E[0] + p[0] * w * 0.7, E[1] + p[1] * w * 0.7)]
    pen.line(blade, 1.0, alpha, seed=seed + 212)


def shovel_tip(G, phi, k=100):
    return (G[0] + math.cos(phi) * k, G[1] + math.sin(phi) * k)


def sharpen(pts, step=16.0):
    """Split long segments into even short ones so the smoothing spline keeps corners crisp (no overshoot)."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(round(d / step)))
        for k in range(1, n + 1):
            out.append((lerp(a[0], b[0], k / n), lerp(a[1], b[1], k / n)))
    return out


def inside(p, poly):
    x, y = p
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1:
            c = not c
    return c


def tufts(pen, pts, y, reveal, start, alpha, seed=1):
    rng = random.Random(seed)
    strokes = []
    for x in pts:
        h = rng.uniform(10, 20)
        strokes += [[(x, y), (x - 4, y - h)], [(x + 5, y), (x + 7, y - h * 0.8)], [(x + 10, y), (x + 16, y - h * 0.6)]]
    pen.lines(strokes, reveal, start, alpha, 0.65, seed=seed)


def blob(cx, cy, rx, ry, rng, n=10, jag=0.12):
    pts = []
    ph = rng.uniform(0, 6.28)
    for i in range(n):
        a = ph + 2 * math.pi * i / n
        k = 1 + rng.uniform(-jag, jag)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return pts + [pts[0]]


# ======================================================================= b06 cantiere
# section geometry in "ground" coordinates: y = 0 is the ground surface, + is down (screen y = G + y)
TX0, TX1 = 400, 1360          # trench top
BX0, BX1 = 420, 1340          # trench bottom
DEPTH = 360
LV_STONE, LV_GRAVEL, LV_FINE = 255, 170, 86    # tops of the three lower layers
RX0, RX1 = 442, 1318          # basoli span (between the kerbs)
RCX, RHW = 880, 438
CROWN = 30
EDGE = -7
DITCH = ((326, 46), (1436, 46))   # (centre, half width)
GROUND_Y = 452


def surf_y(x):
    u = clamp((x - RCX) / RHW, -1, 1)
    return EDGE - CROWN * (1 - u * u)


def wall_x(y, side):
    k = clamp(y / DEPTH, 0, 1)
    return lerp(TX0, BX0, k) if side < 0 else lerp(TX1, BX1, k)


def _ditch_y(x, k):
    y = 0.0
    for cx, hw in DITCH:
        u = (x - cx) / hw
        if abs(u) < 1:
            y = max(y, 40 * k * (1 - u * u) ** 1.3)
    return y


def _final_top(x):
    if x < RX0 or x > RX1:
        return EDGE
    return surf_y(x)


def _section_geo():
    rng = random.Random(606)
    stones, gravel, fine, soil = [], [], [], []
    # big stones: packed rounded blobs (largest first)
    placed = []
    N = 9000
    for i in range(N):
        r = lerp(40, 17, i / N)
        y = rng.uniform(LV_STONE + r * 0.75, DEPTH - r * 0.75)
        xl, xr = wall_x(y, -1) + r * 1.2, wall_x(y, 1) - r * 1.2
        x = rng.uniform(xl, xr)
        if all(((x - px) / (1.2 * (r + pr) + 5)) ** 2 + ((y - py) / (0.8 * (r + pr) + 5)) ** 2 > 1 for px, py, pr in placed):
            placed.append((x, y, r))
    for x, y, r in placed:
        stones.append((y, blob(x, y, r * 1.2, r * 0.8, rng, 11, 0.09)))
    # gravel: small round pebbles
    placed = []
    N = 9000
    for i in range(N):
        r = lerp(10, 4.5, i / N)
        y = rng.uniform(LV_GRAVEL + r + 2, LV_STONE - r - 2)
        x = rng.uniform(wall_x(y, -1) + r + 4, wall_x(y, 1) - r - 4)
        if all(abs(x - px) > r + pr + 3.5 or math.hypot(x - px, y - py) > r + pr + 3.5 for px, py, pr in placed):
            placed.append((x, y, r))
    for x, y, r in placed:
        gravel.append((y, blob(x, y, r * 1.12, r * 0.84, rng, 8, 0.15)))
    # fine gravel: dots
    for _ in range(2400):
        y = rng.uniform(LV_FINE + 4, LV_GRAVEL - 4)
        x = rng.uniform(wall_x(y, -1) + 6, wall_x(y, 1) - 6)
        if all(abs(x - px) > 7 or abs(y - py) > 7 for px, py, _ in fine):
            fine.append((x, y, rng.uniform(1.2, 2.4)))
        if len(fine) >= 430:
            break
    # basoli in section: tapered polygonal blocks with flat tops on the crown
    xs = [RX0]
    while xs[-1] < RX1 - 150:
        xs.append(xs[-1] + rng.uniform(98, 128))
    xs[-1] = RX1 if RX1 - xs[-1] < 60 else xs[-1]
    if xs[-1] != RX1:
        xs.append(RX1)
    blocks = []
    for xa, xb in zip(xs, xs[1:]):
        xa2, xb2 = xa + 3, xb - 3
        yb = LV_FINE - rng.uniform(0, 5)
        mid = (xa2 + xb2) / 2 + rng.uniform(-18, 18)
        y1, y2 = rng.uniform(14, 40), rng.uniform(14, 40)
        if len(blocks) % 3 == 1:     # a flatter-bottomed block now and then
            bot = [(lerp(xa2, xb2, 0.22), yb - rng.uniform(2, 8)), (lerp(xa2, xb2, 0.5), yb + rng.uniform(-1, 2)),
                   (lerp(xa2, xb2, 0.8), yb - rng.uniform(2, 8))]
        else:
            bot = [(lerp(xa2, mid, 0.5) + rng.uniform(-4, 4), yb - rng.uniform(8, 16)), (mid, yb + rng.uniform(-2, 2)),
                   (lerp(mid, xb2, 0.5) + rng.uniform(-4, 4), yb - rng.uniform(8, 16))]
        sides = [(xa2, surf_y(xa2) + 1), (xa2 + rng.uniform(1, 7), y1)] + bot + [(xb2 - rng.uniform(1, 7), y2),
                                                                              (xb2, surf_y(xb2) + 1)]
        top = [(xa2, surf_y(xa2) + 1)] + [(lerp(xa2, xb2, k / 6), surf_y(lerp(xa2, xb2, k / 6)) + 1) for k in range(1, 6)] + [
            (xb2, surf_y(xb2) + 1)]
        blocks.append((sides, top, (xa + xb) / 2))
    # bedding: fine gravel packed in the gaps under and between the blocks
    bed = []
    polys = [sd for sd, _, _ in blocks]
    for _ in range(900):
        x, y = rng.uniform(RX0 + 4, RX1 - 4), rng.uniform(8, LV_FINE - 2)
        if not any(inside((x, y), [(px, py + (3 if py > 20 else 0)) for px, py in pl]) for pl in polys):
            if all(abs(x - px) > 6 or abs(y - py) > 6 for px, py, _ in bed):
                bed.append((x, y, rng.uniform(1.2, 2.3)))
    # kerbs (upright edge stones)
    kerbs = []
    for xa, xb in ((TX0 + 2, RX0 - 2), (RX1 + 2, TX1 - 2)):
        kerbs.append([(xa, EDGE), (xa, LV_FINE - 2), (xb, LV_FINE + 2), (xb, EDGE), (xa, EDGE)])
    # soil marks around the cut (avoid the trench and the label column)
    for _ in range(900):
        x, y = rng.uniform(20, W - 20), rng.uniform(26, 470)
        if TX0 - 30 < x < TX1 + 30 and y < DEPTH + 40:
            continue
        if x > 1470 and y < 360:
            continue
        if y > 370:
            continue
        if rng.random() > 0.55 - y / 1400:
            continue
        if any(math.hypot(x - a, y - b) < 34 for _, a, b, _ in soil):
            continue
        kind = rng.random()
        soil.append((kind, x, y, rng.uniform(4, 9)))
        if len(soil) > 70:
            break
    return dict(stones=sorted(stones, key=lambda s: -s[0]), gravel=sorted(gravel, key=lambda s: -s[0]),
                fine=fine, blocks=blocks, kerbs=kerbs, soil=soil, bed=bed)


_GEO = None


def _geo():
    global _GEO
    if _GEO is None:
        _GEO = _section_geo()
    return _GEO


_PAVE = None


def _paving(cx, cy, R):
    """Top view of polygonal paving: Voronoi cells, shrunk a little so the joints read."""
    global _PAVE
    if _PAVE is None:
        import numpy as np
        from scipy.spatial import Voronoi
        rng = random.Random(77)
        pts = []
        step = 46
        for j in range(-6, 7):
            for i in range(-6, 7):
                pts.append((i * step + (j % 2) * step / 2 + rng.uniform(-13, 13), j * step * 0.87 + rng.uniform(-13, 13)))
        vor = Voronoi(np.array(pts))
        cells = []
        for pi, ri in enumerate(vor.point_region):
            reg = vor.regions[ri]
            if not reg or -1 in reg:
                continue
            poly = [tuple(vor.vertices[v]) for v in reg]
            c = (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
            if math.hypot(*c) > R + 40:
                continue
            sh = [(c[0] + (p[0] - c[0]) * 0.86, c[1] + (p[1] - c[1]) * 0.86) for p in poly]
            cells.append((math.hypot(*c), sh + [sh[0]]))
        cells.sort()
        _PAVE = cells
    return [(d, [(cx + x, cy + y) for x, y in p]) for d, p in _PAVE]


def _road_profile(dig, level, top_k, ditch_k):
    """Road line in ground coords: ground → (ditch) → trench outline at `level` / road surface."""
    pts = []
    for x in range(-60, TX0 - 10, 18):
        pts.append((x, _ditch_y(x, ditch_k)))
    if top_k <= 0:
        d = DEPTH * dig if level is None else level
        if d < 1:
            pts += [(x, 0.0) for x in range(TX0, TX1 + 1, 40)]
        else:
            pts.append((TX0, 0.0))
            pts.append((wall_x(d, -1), d))
            pts.append((wall_x(d, 1), d))
            pts.append((TX1, 0.0))
    else:
        pts.append((TX0, 0.0))
        pts.append((TX0, lerp(LV_FINE, EDGE, top_k)))
        for x in [RX0] + list(range(RX0 + 30, RX1, 30)) + [RX1]:
            pts.append((x, lerp(LV_FINE, _final_top(x), top_k)))
        pts.append((TX1, lerp(LV_FINE, EDGE, top_k)))
        pts.append((TX1, 0.0))
    for x in range(TX1 + 18, W + 61, 18):
        pts.append((x, _ditch_y(x, ditch_k)))
    return sharpen(pts, 18)


@scena("cantiere")
def cantiere(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    C = lambda ph, f=0.0: cue(T, "cantiere", ph, f)
    geo = _geo()
    # ---------------------------------------------------------------- timeline (on the narration)
    t_dig = C("Una trincea") - 0.2
    t_st0, t_st1 = C("riempita"), C("poi ghiaia") - 0.1
    t_gr0, t_gr1 = C("poi ghiaia") - 0.1, C("e pietrisco")
    t_fi0, t_fi1 = C("e pietrisco"), C("ben compattati")
    t_cmp = C("ben compattati")
    t_bas0 = C("grandi blocchi")
    t_inset = C("incastrati")
    t_basl = C("i basoli")
    t_crown = C("leggermente bombata")
    t_rain = C("pioggia")
    t_note = C("Non c'era")
    t_leg = C("i legionari")
    t_op = C("operai")
    # ---------------------------------------------------------------- camera: from landscape down to the cut
    dive = ease_io(win(t, 0.3, 2.6))
    G = lerp(ROAD_Y, GROUND_Y, dive)
    dig = ease_io(win(t, t_dig, t_dig + 1.5))
    level = None
    if t >= t_st0:
        level = DEPTH
        for (a0, a1, l0, l1) in ((t_st0, t_st1, DEPTH, LV_STONE), (t_gr0, t_gr1, LV_STONE, LV_GRAVEL),
                                 (t_fi0, t_fi1, LV_GRAVEL, LV_FINE)):
            if t >= a0:
                level = lerp(l0, l1, ease_io(win(t, a0, a1)))
    nb = len(geo["blocks"])
    drop_dur = 0.8
    stag = (t_basl - 0.5 - t_bas0 - drop_dur) / max(1, nb - 1)
    t_top = t_bas0 + stag * (nb - 1) + drop_dur
    top_k = ease_io(win(t, t_top, t_top + 0.7))
    ditch_k = ease_io(win(t, t_crown + 0.3, t_crown + 1.5))
    lvl = level if level is not None else DEPTH * dig
    rain_k = pulse(t, t_rain - 0.4, t_rain + 5.0, 0.6)

    with at(pen, 0, G):
        # ---- far landscape that slides away up as we go down
        if dive < 0.999:
            hills = [(1150, -100), (1290, -180), (1420, -150), (1580, -230), (1760, -160), (1990, -200)]
            pen.lines([hills], appear, vanish, 0.45 * (1 - dive), 0.8, seed=11)
        tufts(pen, [130, 560, 1110, 1590, 1820], 0, appear, vanish, 0.5 * a, seed=3)
        # ---- the cut: soil marks fade in as the camera goes down
        sk = smooth(win(t, 1.0, 3.2))
        if sk > 0:
            strokes = []
            for kind, x, y, r in geo["soil"]:
                if kind < 0.6:
                    strokes.append([(x - r, y), (x + r, y + 0.5)])
                else:
                    strokes.append(ellipse(x, y, r * 0.5, r * 0.35, 8))
            pen.lines(strokes, sk * appear, vanish, 0.3, 0.6, seed=40)
            for j, yy in enumerate((150, 300)):
                for xa, xb in ((-40, TX0 - 40), (TX1 + 40, 1470)):
                    pen.line([(x, yy + 7 * math.sin(x / 70 + j * 2)) for x in range(int(xa), int(xb), 30)], 0.6,
                             0.18 * a, reveal=sk, start=vanish, seed=50 + j)
        # ---- trench outline below the current fill (the road line traces the rest)
        if (dig > 0 and level is not None) or top_k > 0:
            lv = LV_FINE if top_k > 0 else lvl
            outline = [(wall_x(lv, -1), lv), (BX0, DEPTH), (BX1, DEPTH), (wall_x(lv, 1), lv)]
            pen.line(sharpen(outline, 14), 1.05, a, start=vanish, seed=60)
            if top_k > 0:
                pen.line([(TX0, 0), (wall_x(LV_FINE, -1), LV_FINE)], 1.0, a, start=vanish, seed=61)
                pen.line([(TX1, 0), (wall_x(LV_FINE, 1), LV_FINE)], 1.0, a, start=vanish, seed=62)
        # ---- digging: spoil flying out of the trench
        if 0 < dig < 1:
            for i in range(12):
                u = (t * 1.4 + i / 12) % 1
                side = -1 if i % 2 else 1
                x0 = RCX + side * (90 + (i * 53) % 300)
                xa = x0 + side * 260 * u
                ya = DEPTH * dig * (1 - u) - 300 * u * (1 - u) * 1.6
                pen.dot(xa, ya, 2.4 + (i % 3) * 0.8, 0.7 * a * math.sin(math.pi * u))

        # ---- layers, filling from the bottom
        def rv(y, h=24.0):
            return clamp((y + h - lvl) / (2 * h)) if level is not None else 0.0

        if level is not None:
            for ly in (LV_STONE, LV_GRAVEL):
                if lvl < ly - 0.5:
                    pen.line([(wall_x(ly, -1), ly), (wall_x(ly, 1), ly)], 0.7, 0.75 * a, start=vanish, seed=70 + ly)
            if top_k > 0:
                pen.line([(wall_x(LV_FINE, -1), LV_FINE), (wall_x(LV_FINE, 1), LV_FINE)], 0.6, 0.45 * a * top_k,
                         start=vanish, seed=73)

            def stones(p, a=1.0, rvf=None, start=0.0):
                for i, (y, s_) in enumerate(geo["stones"]):
                    r = rvf(y, 30) if rvf else 1.0
                    if r > 0:
                        p.line(s_, 0.95, a, reveal=ease_out(r), start=start, seed=100 + i)

            def gravel(p, a=1.0, rvf=None, start=0.0):
                for i, (y, s_) in enumerate(geo["gravel"]):
                    r = rvf(y, 12) if rvf else 1.0
                    if r > 0:
                        p.line(s_, 0.65, 0.85 * a, reveal=ease_out(r), start=start, seed=300 + i, step=5.0)

            def fine(p, a=1.0, rvf=None, start=0.0):
                for x, y, r in geo["fine"]:
                    k = rvf(y, 8) if rvf else 1.0
                    if k > 0:
                        p.dot(x, y, r, 0.7 * a * k)

            # drain in order when the scene retracts: top layers first
            for fn, name, ytop, h in ((stones, "st", LV_STONE, 30), (gravel, "gr", LV_GRAVEL, 12), (fine, "fi", LV_FINE, 8)):
                done = lvl < ytop - 2 * h - 2
                if done and vanish <= 0:
                    cached(pen, name, ytop - 20, DEPTH + 20, fn)
                else:
                    fn(pen, a, rv if not done else None, vanish)
        # ---- compaction: a rammer's impact ticks
        ck = pulse(t, t_cmp - 0.2, t_cmp + 1.7, 0.3)
        if ck > 0:
            for j, x in enumerate((620, 880, 1140)):
                bump = abs(math.sin((t - t_cmp) * 6.0 + j * 1.3))
                y0 = lvl - 16 - 26 * bump
                pen.lines([[(x - 20, y0), (x, y0 + 12), (x + 20, y0)], [(x, y0 - 36), (x, y0 + 6)]], 1.0, 0.0,
                          0.75 * ck * a, 0.8, seed=80 + j)
        # ---- basoli drop into place one by one, then the kerbs; bedding fills the gaps
        all_down = t > t_top + 0.1

        def blocks(p, a=1.0, start=0.0):
            for i, (sides, top, xm) in enumerate(geo["blocks"]):
                p.line(sides, 1.0, a, start=start, smooth_=False, seed=500 + i)
            for x, y, r in geo["bed"]:
                p.dot(x, y, r, 0.65 * a)

        if all_down and top_k > 0.999 and vanish <= 0:
            cached(pen, "bas", -80, LV_FINE + 20, blocks)
        elif all_down:
            for x, y, r in geo["bed"]:
                pen.dot(x, y, r, 0.65 * a * top_k)
        for i, (sides, top, xm) in enumerate(geo["blocks"]):
            if all_down and (top_k > 0.999 and vanish <= 0):
                break
            b0 = t_bas0 + stag * i
            k = win(t, b0, b0 + drop_dur)
            if k <= 0:
                continue
            fall = ease_in(clamp(k / 0.75), 2.2)
            settle = math.sin(clamp((k - 0.75) / 0.25) * math.pi) * 5
            dy = -190 * (1 - fall) + settle
            al = smooth(clamp(k / 0.3)) * a
            pen.line([(x, y + dy) for x, y in sides], 1.0, al, start=vanish, smooth_=False, seed=500 + i)
            pen.line([(x, y + dy) for x, y in top], 1.0, al * (1 - top_k), start=vanish, seed=520 + i)
            if 0.75 < k < 1:     # little dust puffs on landing
                q = (k - 0.75) / 0.25
                for sd in (-1, 1):
                    xx = xm + sd * (40 + 26 * q)
                    pen.line(arc(xx, LV_FINE - 30, 8 + 8 * q, math.pi, 2 * math.pi, 8), 0.5, al * (1 - q) * 0.6,
                             seed=530 + i)
        if top_k > 0:
            pen.lines(geo["kerbs"], top_k, vanish, a, 1.0, seed=540, smooth_=False)
        # ---- labels on the right
        labs = [("pietre", (DEPTH + LV_STONE) / 2, t_st0 + 1.0), ("ghiaia", (LV_STONE + LV_GRAVEL) / 2, t_gr0 + 0.6),
                ("pietrisco", (LV_GRAVEL + LV_FINE) / 2, t_fi0 + 0.6), ("basoli", 30, t_basl)]
        for j, (s, y, tl) in enumerate(labs):
            k = win(t, tl, tl + 0.8)
            if k <= 0:
                continue
            x_in = 1250 if j < 3 else 1200
            yl = y + 4 if j < 3 else y + 30
            pen.line([(x_in, y), (1390, y + (0 if j < 3 else 14)), (1500, yl - 14)], 0.6, 0.55 * a,
                     reveal=ease_out(k), start=vanish, seed=90 + j)
            pen.dot(x_in, y, 3.4, 0.85 * a * smooth(k))
            pen.text(s, 1515, yl, 50, a, align="left", reveal=win(t, tl + 0.4, tl + 1.2))
        # ---- crown: a straight reference chord + a little bulge arrow
        crk = pulse(t, t_crown, t_rain + 0.4, 0.5)
        if crk > 0:
            dash = [[(lerp(RX0, RX1, k / 30), EDGE + 1), (lerp(RX0, RX1, (k + 0.55) / 30), EDGE + 1)] for k in range(30)]
            pen.lines(dash, crk, 0.0, 0.55 * a, 0.55, seed=95)
            yc = EDGE - CROWN
            pen.lines([[(RCX, EDGE - 2), (RCX, yc + 6)], [(RCX - 7, yc + 14), (RCX, yc + 6), (RCX + 7, yc + 14)]], crk, 0.0,
                      0.85 * a, 0.7, seed=96)
        # ---- rain: drops land on the crown and roll off into the side ditches
        if rain_k > 0:
            streaks = []
            for i in range(34):
                x0 = 260 + (i * 389) % 1240
                sp = 1000 + (i * 137) % 300
                y0 = ((t - t_rain) * sp + (i * 211) % 700) % 760 - 800
                streaks.append([(x0, y0), (x0 - 6, y0 + 34)])
            pen.lines(streaks, 1.0, 0.0, 0.32 * rain_k * a, 0.55, seed=97)
            for i in range(12):
                t0 = t_rain + i * 0.3
                u = t - t0
                if u < 0 or u > 2.6:
                    continue
                x0 = RCX + ((i * 71) % 300 - 150)
                x0 += 14 if x0 >= RCX else -14
                side = -1 if x0 < RCX else 1
                fade = 1 - smooth(win(u, 2.1, 2.6))
                if u < 0.4:
                    x, y = x0, surf_y(x0) - 9 - 520 * (1 - u / 0.4) ** 1.6
                else:
                    s_ = ease_in(clamp((u - 0.4) / 1.4), 2.0)
                    xe = DITCH[0][0] if side < 0 else DITCH[1][0]
                    x = lerp(x0, xe, s_)
                    if RX0 <= x <= RX1:
                        y = surf_y(x) - 9
                    elif TX0 <= x <= TX1:
                        y = EDGE - 9
                    else:
                        y = _ditch_y(x, ditch_k) - 9
                drop = [(x - 6, y + 3), (x - 1, y - 9), (x, y - 13), (x + 1, y - 9), (x + 6, y + 3), (x, y + 8), (x - 6, y + 3)]
                pen.line(drop, 0.8, a * fade, seed=600 + i)
            wk = smooth(win(t, t_rain + 1.6, t_rain + 4.2))
            if wk > 0:
                for cx, hw in DITCH:
                    yy = 40 * ditch_k - 14 * wk - 3
                    w_ = hw * (0.25 + 0.4 * wk)
                    pen.line([(cx - w_, yy), (cx - w_ * 0.3, yy + 1.5 * math.sin(t * 5)), (cx + w_ * 0.3, yy - 1.5 * math.sin(t * 5)),
                              (cx + w_, yy)], 0.7, 0.8 * a, start=vanish, seed=640)
            ak = pulse(t, t_rain + 0.6, t_rain + 4.8, 0.5)
            if ak > 0:
                for side in (-1, 1):
                    xs = [RCX + side * (70 + 300 * k / 8) for k in range(9)]
                    arr = [(x, surf_y(x) - 34) for x in xs]
                    e = arr[-1]
                    pen.lines([arr, [(e[0] - side * 13, e[1] - 10), e, (e[0] - side * 14, e[1] + 6)]], ak, 0.0,
                              0.7 * a, 0.75, seed=650 + side)
        # ---- "no single recipe" note
        nk = win(t, t_note, t_note + 1.4)
        if nk > 0:
            pen.text("* gli strati cambiavano da luogo a luogo", RCX, DEPTH + 96, 38, 0.7 * a, reveal=nk)
            _road_types(pen, t, C("ogni strada"), vanish, a)
        # ---- the top-view inset of the paving
        ik_ = pulse(t, t_inset - 0.3, t_crown - 0.2, 0.7)
        if ik_ > 0:
            icx, icy, R = 1060, -262, 122
            ctx = pen.ctx
            pen.line(ellipse(icx, icy, R, R, 48), 0.95, a, reveal=ik_, seed=700)
            ctx.save()
            ctx.new_path()
            ctx.arc(icx, icy, R - 5, 0, 2 * math.pi)
            ctx.clip()
            for j, (d, poly) in enumerate(_paving(icx, icy, R)):
                r = clamp(ik_ * 1.7 - d / R * 0.7) if t < t_inset + 2 else 1.0
                if r > 0:
                    pen.line(poly, 0.7, 0.85 * a * (ik_ if t > t_inset + 2 else 1.0), reveal=r, smooth_=False,
                             seed=710 + j, step=6.0)
            ctx.restore()
            dl = [(icx - 0.55 * R, icy + 0.84 * R), (lerp(icx - 0.55 * R, 960, 0.5), -90), (960, surf_y(960) - 10)]
            pen.line(dl, 0.5, 0.5 * a, reveal=ik_, seed=705)
            pen.text("vista dall'alto", icx + R + 18, icy + 12, 36, 0.65 * a * ik_, align="left")
        # ---- the workers
        wa = smooth(win(t, 0.6, 1.8)) * a
        _legionary(pen, 180, 0, t, t_leg, wa, rain_k)
        _labourer(pen, 1680, 0, t, t_op, wa, lvl, t_st0 + 0.2, t_fi1 + 0.2, rain_k)
        lk = win(t, t_leg + 0.4, t_leg + 1.4)
        if lk > 0:
            pen.text("legionari", 200, -372, 44, 0.8 * a, reveal=lk)
        ok = win(t, t_op + 0.3, t_op + 1.3)
        if ok > 0:
            pen.text("operai", 1680, -372, 44, 0.8 * a, reveal=ok)
    road = _road_profile(dig, level, top_k, ditch_k)
    return [(x, y + G) for x, y in road]


def _road_types(pen, t, t0, vanish, a):
    """Small side sections: the three Roman road classes (earth, gravel, paved)."""
    rng = random.Random(31)
    y0 = 440
    # via terrena: just beaten earth, slightly cambered
    k1 = win(t, t0, t0 + 1.2)
    if k1 > 0:
        cx = 200
        top = [(cx - 120 + i * 12, y0 - 10 * (1 - ((i - 10) / 10) ** 2)) for i in range(21)]
        pen.lines([top], k1, vanish, 0.85 * a, 0.9, seed=860)
        pen.lines([[(cx - 100 + j * 22, y0 + 12 + (j % 3) * 9), (cx - 90 + j * 22, y0 + 13 + (j % 3) * 9)] for j in range(10)],
                  k1, vanish, 0.4 * a, 0.6, seed=861)
        pen.text("via terrena", cx, y0 + 74, 34, 0.75 * a, reveal=k1)
        pen.text("terra battuta", cx, y0 + 106, 26, 0.5 * a, reveal=win(t, t0 + 0.5, t0 + 1.5))
    # via glarea strata: gravel on a stone bed
    k2 = win(t, t0 + 0.7, t0 + 1.9)
    if k2 > 0:
        cx = 1560
        top = [(cx - 120 + i * 12, y0 - 12 * (1 - ((i - 10) / 10) ** 2)) for i in range(21)]
        box = [(cx - 116, y0 - 2), (cx - 112, y0 + 46), (cx + 112, y0 + 46), (cx + 116, y0 - 2)]
        pen.lines([top, box], k2, vanish, 0.85 * a, 0.9, seed=870)
        pebbles = [ellipse(cx - 100 + (j * 37) % 200, y0 + 6 + (j * 13) % 18, 3.5, 2.6, 7) for j in range(16)]
        stones = [ellipse(cx - 86 + j * 43, y0 + 34, 15, 8, 10) for j in range(5)]
        pen.lines(pebbles + stones, k2, vanish, 0.6 * a, 0.6, seed=872)
        pen.text("via glarea strata", cx, y0 + 88, 34, 0.75 * a, reveal=k2)
        pen.text("ghiaia", cx, y0 + 120, 26, 0.5 * a, reveal=win(t, t0 + 1.2, t0 + 2.2))
    # the big one in the middle: paved
    k3 = win(t, t0 + 1.4, t0 + 2.4)
    if k3 > 0:
        pen.text("via silice strata", RCX, -170, 40, 0.8 * a, reveal=k3)
        pen.text("lastricata", RCX, -134, 28, 0.55 * a, reveal=win(t, t0 + 1.9, t0 + 2.9))


def _legionary(pen, x, y, t, t_rest, alpha, rain_k):
    """Pick-swinging legionary (windmill cycle: slow lift behind, fast strike over the top). He pauses to look
    at the rain, and at the end leans on the planted pick, sighs, then smiles."""
    per = 1.9
    u = (t / per) % 1.0
    if u < 0.55:
        th = lerp(1.05, 3.70, ease_io(u / 0.55))
    elif u < 0.68:
        th = 3.70 + 0.08 * math.sin((u - 0.55) / 0.13 * math.pi)
    elif u < 0.80:
        th = lerp(3.70, 1.05 + 2 * math.pi, ease_in((u - 0.68) / 0.12, 2.2))
    else:
        th = 1.05 + 2 * math.pi - 0.06 * math.sin((u - 0.8) / 0.2 * math.pi)
    R = 92
    Gs = (16 + math.cos(th) * R, -186 + math.sin(th) * R)
    phi_s = th + 0.22
    lean_s = 0.15 + 0.3 * (0.5 + 0.5 * math.cos(th - 1.05))
    # planted pose: pick upright, head on the ground, both hands resting on the butt of the handle
    Gp, phip = (74, -110), DOWN + 0.04
    stop = max(smooth(win(t, t_rest - 0.8, t_rest)), rain_k)
    rest = smooth(win(t, t_rest - 0.8, t_rest))
    phi_s = phip + ((phi_s - phip + math.pi) % (2 * math.pi) - math.pi)
    G = (lerp(Gs[0], Gp[0], stop), lerp(Gs[1], Gp[1], stop))
    phi = lerp(phi_s, phip, stop)
    sigh = pulse(t, t_rest + 0.2, t_rest + 1.9, 0.4)
    lean = lerp(lean_s, 0.06 + 0.08 * sigh, stop)
    butt = (G[0] - math.cos(phi) * 34, G[1] - math.sin(phi) * 34)
    front = (lerp(G[0], butt[0] + 2, stop), lerp(G[1], butt[1] - 4, stop))
    back = (lerp(G[0] - math.cos(phi) * 30, butt[0] - 6, stop), lerp(G[1] - math.sin(phi) * 30, butt[1] + 2, stop))
    strike = 0.78 < u and stop < 0.3
    if rest > 0.5:
        expr = "tired" if t < t_rest + 1.9 else "smile"
    elif rain_k > 0.5:
        expr = "surprise"
    else:
        expr = "determined"
    worker(pen, x, y, 1.0, t, "legionario", G, phi, fx=1, lean=lean, expr=expr, alpha=alpha, seed=3,
           front_target=front, back_target=back, tool=pick_tool,
           head_tilt=-0.28 * rain_k + 0.12 * sigh, look=-rain_k)
    if strike:
        k = (u - 0.78) / 0.22
        for j in range(5):
            ang = -0.6 - j * 0.5
            r = 12 + 50 * ease_out(k)
            pen.dot(x + 106 + math.cos(ang) * r, y - 6 + math.sin(ang) * r + 40 * k * k, 2.4, alpha * (1 - k))
    if rest > 0.5:
        # a sigh: two little puffs drifting from the mouth, and a drop of sweat
        for j in range(2):
            k = win(t, t_rest + 0.4 + j * 0.35, t_rest + 1.6 + j * 0.35)
            if 0 < k < 1:
                px, py = x + 66 + 70 * ease_out(k), y - 222 + 10 * k - j * 6
                pen.line(ellipse(px, py, 7 + 9 * k, 5 + 6 * k, 12), 0.6, alpha * (1 - k) * 0.8, seed=821 + j)
        k = win(t, t_rest + 0.7, t_rest + 1.5)
        if 0 < k < 1:
            px, py = x - 10 - 40 * k, y - 300 - 30 * k + 80 * k * k
            pen.line([(px - 4, py + 2), (px, py - 8), (px + 4, py + 2), (px, py + 5), (px - 4, py + 2)], 0.7,
                     alpha * (1 - k), seed=820)


def _labourer(pen, x, y, t, t_rest, alpha, lvl, t_w0, t_w1, rain_k):
    """Workman shovelling material into the trench (he faces left, toward it); idles leaning on the shovel."""
    per = 2.2
    u = (t / per + 0.3) % 1.0
    keys = [(0.0, (80, -96), 1.02, 0.35), (0.22, (94, -92), 0.98, 0.45), (0.5, (60, -166), 0.2, 0.1),
            (0.62, (82, -228), -0.6, -0.15), (0.72, (78, -220), -0.5, -0.1), (1.0, (80, -96), 1.02, 0.35)]
    for (u0, g0, p0, l0), (u1, g1, p1, l1) in zip(keys, keys[1:]):
        if u0 <= u <= u1:
            k = ease_io((u - u0) / (u1 - u0))
            Gw = (lerp(g0[0], g1[0], k), lerp(g0[1], g1[1], k))
            phw, lw = lerp(p0, p1, k), lerp(l0, l1, k)
            break
    work = smooth(win(t, t_w0 - 0.6, t_w0)) * (1 - smooth(win(t, t_w1, t_w1 + 0.7)))
    # idle: blade tip on the ground, both hands on top of the handle, gentle breathing
    br = 3 * wave(t, 0.28, 1.0)
    phi_i = 1.36 + 0.015 * br
    di = (math.cos(phi_i), math.sin(phi_i))
    Gi = (112 - di[0] * 116, -3 - di[1] * 116)
    top = (Gi[0] - di[0] * 96, Gi[1] - di[1] * 96)
    fi = (top[0] + di[0] * 20, top[1] + di[1] * 20)
    bi = (top[0] + di[0] * 3, top[1] + di[1] * 3)
    dw = (math.cos(phw), math.sin(phw))
    G = (lerp(Gi[0], Gw[0], work), lerp(Gi[1], Gw[1], work))
    phi = lerp(phi_i, phw, work)
    lean = lerp(0.04, lw, work)
    front = (lerp(fi[0], Gw[0], work), lerp(fi[1], Gw[1], work))
    back = (lerp(bi[0], Gw[0] - dw[0] * 82, work), lerp(bi[1], Gw[1] - dw[1] * 82, work))
    rest = smooth(win(t, t_rest - 0.4, t_rest + 0.4))
    nod = 0.1 * math.sin(max(0.0, t - t_rest) * 5.5) * pulse(t, t_rest, t_rest + 1.6, 0.3)
    expr = "determined" if work > 0.5 else ("smile" if rest > 0.5 else ("surprise" if rain_k > 0.5 else "calm"))
    worker(pen, x, y, 1.0, t, "operaio", G, phi, fx=-1, lean=lean, expr=expr, alpha=alpha, seed=7,
           tool=shovel_tool, head_tilt=-0.25 * rain_k + nod, front_target=front, back_target=back)
    # the heap in front of him
    pile = [(x - 236, 0), (x - 196, -24), (x - 146, -36), (x - 104, -20), (x - 80, 0)]
    pen.line(pile, 0.9, alpha, seed=830)
    pen.lines([[(x - 186, -12), (x - 172, -14)], [(x - 146, -22), (x - 134, -20)], [(x - 124, -8), (x - 110, -9)]], 1.0,
              0.0, alpha * 0.6, 0.6, seed=831)
    if work > 0.98:
        if 0.2 < u < 0.64:     # a load on the blade while lifting
            tip = shovel_tip(Gw, phw, 98)
            la = alpha * smooth(win(u, 0.2, 0.3))
            pen.line(arc(x - tip[0], y + tip[1] - 4, 16, math.pi * 1.1, math.pi * 1.9, 8), 0.8, la, seed=832)
    # material flying from the shovel into the trench, as a loose clump
    tr = (math.floor(t / per + 0.3) + 0.64 - 0.3) * per
    if t < tr:
        tr -= per
    if work > 0.98 or (t_w1 < tr + 0.01 and tr < t_w1 + 0.01):
        tip = shovel_tip((82, -228), -0.6, 98)
        sx, sy = x - tip[0], y + tip[1]
        for j in range(9):
            v = (t - tr) / (0.75 + 0.05 * (j % 3))
            if 0 <= v <= 1:
                ex = 700 + j * 62 + 25 * math.sin(j * 3.1)
                ey = lvl - 4
                px = lerp(sx, ex, v)
                py = lerp(sy, ey, v) - 230 * v * (1 - v) * (0.9 + 0.08 * (j % 4))
                pen.dot(px, py, 2.2 + (j % 3) * 1.1, alpha * (1 - smooth(win(v, 0.85, 1.0))))


# ======================================================================= b07 tavole
TAV_R, TAV_C = 330.0, (820.0, 390.0)        # curve radius and centre (plan view)
TAV_Y = 720.0
TAV_PHI = math.radians(80)


def _tav_path():
    """Centre line of the plan-view road: straight → arc turning up → straight out of the top."""
    pts = [(x, TAV_Y) for x in range(-80, 820, 20)]
    n = 40
    for i in range(n + 1):
        f = TAV_PHI * i / n
        pts.append((TAV_C[0] + TAV_R * math.sin(f), TAV_C[1] + TAV_R * math.cos(f)))
    e = pts[-1]
    d = (math.cos(TAV_PHI), -math.sin(TAV_PHI))
    for k in range(1, 30):
        pts.append((e[0] + d[0] * k * 20, e[1] + d[1] * k * 20))
    return pts


_TP = None


def _tp():
    """Arc-length table of the path: list of (s, x, y, heading)."""
    global _TP
    if _TP is None:
        P = _tav_path()
        out, s = [], 0.0
        for i, p in enumerate(P):
            if i:
                s += math.hypot(p[0] - P[i - 1][0], p[1] - P[i - 1][1])
            q = P[min(i + 1, len(P) - 1)]
            r = P[max(i - 1, 0)]
            out.append((s, p[0], p[1], math.atan2(q[1] - r[1], q[0] - r[0])))
        _TP = out
    return _TP


def tav_at(s):
    T_ = _tp()
    if s <= 0:
        s0, x, y, h = T_[0]
        return x + math.cos(h) * s, y + math.sin(h) * s, h
    for a, b in zip(T_, T_[1:]):
        if s <= b[0]:
            k = (s - a[0]) / ((b[0] - a[0]) or 1)
            dh = (b[3] - a[3] + math.pi) % (2 * math.pi) - math.pi
            return lerp(a[1], b[1], k), lerp(a[2], b[2], k), a[3] + dh * k
    s0, x, y, h = T_[-1]
    return x + math.cos(h) * (s - s0), y + math.sin(h) * (s - s0), h


S_CURVE0 = 900.0                  # arc length where the bend starts (x=820)
S_CURVE1 = S_CURVE0 + TAV_R * TAV_PHI


RI0 = TAV_R - 60                                    # inner fillet radius of an 8-foot bend
_CORNER_D = RI0 / math.cos(TAV_PHI / 2)
CORNER = (TAV_C[0] + _CORNER_D * math.sin(TAV_PHI / 2), TAV_C[1] + _CORNER_D * math.cos(TAV_PHI / 2))
K16 = (_CORNER_D - (TAV_R + 60 - 240)) / (_CORNER_D - RI0)   # fillet scale giving 16 feet mid-bend


def tav_edges(wide=1.0, ghost=False):
    """(outer, inner, middle). Outer edge: the 8-foot road. Inner edge: the same corner rounded with a bigger
    fillet (scaled about the corner of the inner lines), so the bend is wider on its inside."""
    k = 1.0 if ghost else lerp(1.0, K16, wide)
    outer, inner0 = [], []
    for s_, x, y, h in _tp():
        nx, ny = -math.sin(h), math.cos(h)
        outer.append((x + nx * 60, y + ny * 60))
    # inner edge: entry line, fillet, exit line
    t1 = (TAV_C[0], TAV_C[1] + RI0)
    t2 = (TAV_C[0] + RI0 * math.sin(TAV_PHI), TAV_C[1] + RI0 * math.cos(TAV_PHI))
    sc = lambda p: (CORNER[0] + (p[0] - CORNER[0]) * k, CORNER[1] + (p[1] - CORNER[1]) * k)
    T1, T2 = sc(t1), sc(t2)
    inner = [(x, T1[1]) for x in range(-80, int(T1[0]), 20)]
    for i in range(41):
        f = TAV_PHI * i / 40
        inner.append(sc((TAV_C[0] + RI0 * math.sin(f), TAV_C[1] + RI0 * math.cos(f))))
    d = (math.cos(TAV_PHI), -math.sin(TAV_PHI))
    L = (T2[1] + 80) / -d[1]
    for j in range(1, 31):
        inner.append((T2[0] + d[0] * L * j / 30, T2[1] + d[1] * L * j / 30))
    O, I = resample(outer, 160), resample(inner, 160)
    mid = [((p[0] + q[0]) / 2, (p[1] + q[1]) / 2) for p, q in zip(O, I)]
    return outer, inner, mid


def mid_bend(wide):
    k = lerp(1.0, K16, wide)
    f = TAV_PHI / 2
    di = _CORNER_D - (_CORNER_D - RI0) * k
    u = (math.sin(f), math.cos(f))
    return (TAV_C[0] + u[0] * di, TAV_C[1] + u[1] * di), (TAV_C[0] + u[0] * (TAV_R + 60), TAV_C[1] + u[1] * (TAV_R + 60))


def squiggle(x0, y0, length, rng, amp=6.0):
    """A handwritten-looking line of 'text': words of little loops."""
    words, x = [], x0
    while x < x0 + length - 20:
        wl = min(rng.uniform(30, 90), x0 + length - x)
        pts = []
        n = int(wl / 5)
        ph = rng.uniform(0, 6)
        for i in range(n + 1):
            u = i / max(1, n)
            pts.append((x + wl * u + 2.2 * math.sin(i * 1.9 + ph), y0 - amp * abs(math.sin(i * 0.9 + ph)) * (0.6 + 0.4 * math.sin(i * 0.37))))
        words.append(pts)
        x += wl + rng.uniform(12, 20)
    return words


_TAB = None


def _tablet_geo():
    global _TAB
    if _TAB is None:
        rng = random.Random(12)
        wdt, hgt = 520, 620
        x0, y0 = -wdt / 2, -hgt / 2
        outer = [(x0, y0 + 10), (x0 + 10, y0), (-x0 - 10, y0), (-x0, y0 + 10), (-x0, -y0 - 10), (-x0 - 10, -y0),
                 (x0 + 10, -y0), (x0, -y0 - 10), (x0, y0 + 10)]
        inner = [(x0 + 26, y0 + 26), (-x0 - 26, y0 + 26), (-x0 - 26, -y0 - 26), (x0 + 26, -y0 - 26), (x0 + 26, y0 + 26)]
        hatch = []
        for k in range(38):        # bevel hatching in the frame band
            u = k / 38
            per = 2 * (wdt + hgt)
            d = u * per
            if d < wdt:
                p = (x0 + d, y0)
                q = (p[0] + 14, p[1] + 20)
            elif d < wdt + hgt:
                p = (-x0, y0 + d - wdt)
                q = (p[0] - 20, p[1] + 14)
            elif d < 2 * wdt + hgt:
                p = (-x0 - (d - wdt - hgt), -y0)
                q = (p[0] - 14, p[1] - 20)
            else:
                p = (x0, -y0 - (d - 2 * wdt - hgt))
                q = (p[0] + 20, p[1] - 14)
            hatch.append([(lerp(p[0], q[0], 0.2), lerp(p[1], q[1], 0.2)), (lerp(p[0], q[0], 0.8), lerp(p[1], q[1], 0.8))])
        rivets = [ellipse(sx * (-x0 - 13), sy * (-y0 - 13), 5, 5, 10) for sx in (-1, 1) for sy in (-1, 1)]
        rows = []
        for r in range(10):
            y = y0 + 170 + r * 40
            rows.append(squiggle(x0 + 56, y, wdt - 112 - (rng.uniform(0, 120) if r % 4 == 3 else 0), rng))
        _TAB = dict(outer=outer, inner=inner, hatch=hatch, rivets=rivets, rows=rows, w=wdt, h=hgt)
    return _TAB


def mule_top(pen, x, y, h, t, alpha, ear=0.0, seed=0, walk=1.0, s=1.15):
    """The mule seen from above, heading h."""
    with at(pen, x, y, s, h):
        L = pen.line
        L(ellipse(0, 0, 40, 17, 22), 1.0, alpha, seed=seed)
        nod = wave(t, 1.4) * 2 * walk
        L(ellipse(52 + nod, 0, 21, 11, 16), 1.0, alpha, seed=seed + 1)
        L([(28, -9), (36, -6)], 0.7, alpha * 0.7, seed=seed + 2)
        L([(28, 9), (36, 6)], 0.7, alpha * 0.7, seed=seed + 3)
        for sgn in (-1, 1):       # long ears, flicking
            a = math.radians(160 - 25 * ear) + wave(t, 0.7, sgn) * 0.12
            bx, by = 44 + nod, sgn * 5
            tip = (bx + math.cos(a) * 40, by + sgn * math.sin(a) * 34)
            L([(bx, by), ((bx + tip[0]) / 2, (by + tip[1]) / 2 + sgn * 4), tip], 0.8, alpha, seed=seed + 4 + sgn)
        sw = wave(t, 0.9) * 8
        L([(-40, 0), (-52, sw * 0.5), (-62, sw)], 0.8, alpha, seed=seed + 7)
        for i, (hx, hy) in enumerate(((24, -18), (24, 18), (-24, -18), (-24, 18))):
            st = math.sin(t * 2 * math.pi * 1.4 + (0 if i in (0, 3) else math.pi)) * 6 * walk
            pen.dot(hx + st, hy * 1.05, 3.0, alpha * 0.8)


def cart_top(pen, x, y, h, alpha, seed=0, s=1.15):
    with at(pen, x, y, s, h):
        L = pen.line
        L([(-38, -28), (38, -28), (38, 28), (-38, 28), (-38, -28)], 1.0, alpha, smooth_=False, seed=seed)
        for k in (-12, 4, 18):
            L([(-34, k), (34, k)], 0.5, alpha * 0.6, seed=seed + 1 + k)
        L([(0, -42), (0, 42)], 0.7, alpha * 0.8, smooth_=False, seed=seed + 2)
        for sg in (-1, 1):
            L([(-22, sg * 36), (22, sg * 36), (22, sg * 43), (-22, sg * 43), (-22, sg * 36)], 0.9, alpha,
              smooth_=False, seed=seed + 3 + sg)


def mule_face(pen, cx, cy, s, t, mood, alpha, seed=0):
    """Close-up of the mule's head in profile. mood: 0 calm, -1 worried, +1 relieved."""
    worry, relief = max(0.0, -mood), max(0.0, mood)
    with at(pen, cx, cy, s):
        L = pen.line
        nod = wave(t, 0.4) * 2
        head = [(-50, -40), (0, -54), (52, -36), (94, -4), (110, 22), (100, 42), (76, 48), (48, 42), (18, 54),
                (-20, 62), (-52, 42), (-62, 4), (-50, -40)]
        L([(x, y + nod) for x, y in head], 1.1, alpha, seed=seed)
        L([(-52, 42), (-96, 150)], 1.0, alpha, seed=seed + 1)
        L([(-20, 62), (6, 150)], 1.0, alpha, seed=seed + 2)
        pen.dot(97, 18 + nod, 3.4, alpha)
        # ears: back and flat when worried, up and perky when relieved
        for k, bx in enumerate((-36, -16)):
            a = math.radians(-100 - 55 * worry + 10 * relief + k * 12) + wave(t, 0.5, k) * 0.05
            ln = 82
            tip = (bx + math.cos(a) * ln, -46 + nod + math.sin(a) * ln)
            m = ((bx + tip[0]) / 2, (-46 + nod + tip[1]) / 2)
            nx, ny = -math.sin(a) * 12, math.cos(a) * 12
            L([(bx - 8, -44 + nod), (m[0] - nx, m[1] - ny), tip, (m[0] + nx, m[1] + ny), (bx + 8, -48 + nod)], 0.95,
              alpha, seed=seed + 3 + k)
        ex, ey = 10, -16 + nod
        if relief > 0.5:
            L([(ex - 11, ey + 2), (ex, ey - 6), (ex + 11, ey + 2)], 1.0, alpha, seed=seed + 6)     # happy closed eye
        elif worry > 0.5:
            L(ellipse(ex, ey, 11, 13, 14), 0.9, alpha, seed=seed + 6)
            pen.dot(ex + 4, ey + 2, 4.0, alpha)
            L([(ex - 14, ey - 18), (ex, ey - 24), (ex + 12, ey - 26)], 0.9, alpha, seed=seed + 7)
        else:
            pen.dot(ex, ey, 5.0, alpha)
        if relief > 0.5:
            L([(56, 36 + nod), (72, 44 + nod), (88, 38 + nod)], 0.9, alpha, seed=seed + 8)
        elif worry > 0.5:
            L([(58, 40 + nod), (66, 37 + nod), (74, 41 + nod), (82, 38 + nod)], 0.8, alpha, seed=seed + 8)
        if worry > 0.5:     # a drop of sweat
            k = (t * 0.8) % 1
            L([(-58, -20 + 30 * k), (-54, -32 + 30 * k), (-50, -20 + 30 * k), (-54, -15 + 30 * k), (-58, -20 + 30 * k)],
              0.7, alpha * (1 - k), seed=seed + 9)


def _cat1(keys, t):
    """Smooth 1-D interpolation through (t, v) keys (Catmull-Rom in value, clamped at the ends)."""
    if t <= keys[0][0]:
        return keys[0][1]
    if t >= keys[-1][0]:
        return keys[-1][1]
    for i in range(len(keys) - 1):
        if keys[i][0] <= t <= keys[i + 1][0]:
            p0 = keys[max(0, i - 1)]
            p1, p2 = keys[i], keys[i + 1]
            p3 = keys[min(len(keys) - 1, i + 2)]
            u = (t - p1[0]) / (p2[0] - p1[0])
            m1 = (p2[1] - p0[1]) / ((p2[0] - p0[0]) or 1) * (p2[0] - p1[0])
            m2 = (p3[1] - p1[1]) / ((p3[0] - p1[0]) or 1) * (p2[0] - p1[0])
            if i == 0:
                m1 = 0.0
            u2, u3 = u * u, u * u * u
            return (2 * u3 - 3 * u2 + 1) * p1[1] + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * p2[1] + (u3 - u2) * m2


def double_arrow(p, q, head=12):
    dx, dy = q[0] - p[0], q[1] - p[1]
    d = math.hypot(dx, dy) or 1
    ux, uy = dx / d, dy / d
    nx, ny = -uy, ux
    return [[p, q],
            [(p[0] + ux * head + nx * head * 0.6, p[1] + uy * head + ny * head * 0.6), p,
             (p[0] + ux * head - nx * head * 0.6, p[1] + uy * head - ny * head * 0.6)],
            [(q[0] - ux * head + nx * head * 0.6, q[1] - uy * head + ny * head * 0.6), q,
             (q[0] - ux * head - nx * head * 0.6, q[1] - uy * head - ny * head * 0.6)]]


@scena("tavole")
def tavole(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    C = lambda ph, f=0.0: cue(T, "tavole", ph, f)
    t_xii = C("Dodici Tavole")
    t_date = C("a metà del quinto")
    t_rule = C("fissavano")
    t_8 = C("otto piedi")
    t_16 = C("sedici in curva")
    t_why = C("Perché in curva")
    t_carri = C("i carri")
    geo = _tablet_geo()
    # ---------------------------------------------------------------- the bronze tablet
    mv = ease_io(win(t, t_rule - 0.6, t_rule + 0.9))
    tx, ty, ts = lerp(900, 230, mv), lerp(500 + 3 * wave(t, 0.2), 230, mv), lerp(1.0, 0.36, mv)
    # a magistrate presents the tablet, then steps out of the picture
    ga = a * smooth(win(t, 0.8, 1.8)) * (1 - smooth(win(t, t_rule - 0.8, t_rule + 0.2)))
    if ga > 0:
        pt = pulse(t, 1.6, t_rule - 0.6, 0.5)
        talk = (C("C'erano") < t < C("Dodici") - 0.2) or (t_date < t < t_rule - 0.8)
        expr = "proud" if win(t, t_xii, t_xii + 1.6) * (t < t_xii + 1.6) else ("talk" if talk else "smile")
        omino(pen, 1430, 812, 1.2, t, "toga", fx=-1, expr=expr, alpha=ga, seed=4, head_tilt=-0.05 * pt,
              arm_f=(lerp(DOWN - 0.3, -0.35, pt), lerp(0.4, -0.25 + 0.05 * wave(t, 0.6), pt)))
    shine = win(t, t_xii + 0.2, t_xii + 1.4)
    with at(pen, tx, ty, ts):
        if 0 < shine < 1:
            u = lerp(-420, 420, ease_io(shine))
            for j, off in enumerate((0, 34)):
                p0, p1 = (u + off - 140, -300), (u + off + 140, 300)
                pen.line([(clamp(p0[0], -234, 234), lerp(-300, 300, clamp((clamp(p0[0], -234, 234) - p0[0]) / 280))),
                          (clamp(p1[0], -234, 234), lerp(300, -300, clamp((p1[0] - clamp(p1[0], -234, 234)) / 280)))],
                         0.5, 0.35 * a * math.sin(math.pi * shine), seed=980 + j)
        pen.lines([geo["outer"], geo["inner"]], appear, vanish, a, 1.15, seed=900, smooth_=False)
        pen.lines(geo["hatch"], appear * win(t, 0.8, 2.6), vanish, 0.55 * a, 0.6, seed=905)
        pen.lines(geo["rivets"], win(t, 1.6, 2.4), vanish, a, 0.8, seed=950)
        k = win(t, t_xii - 0.2, t_xii + 0.7)
        if k > 0:
            pen.text("XII", 0, -geo["h"] / 2 + 118, 104, a, reveal=k)
            pen.line([(-70, -geo["h"] / 2 + 140), (70, -geo["h"] / 2 + 140)], 0.8, 0.7 * a, reveal=k, start=vanish,
                     seed=960)
        for r, row in enumerate(geo["rows"]):
            rk = win(t, t_xii + 0.3 + r * 0.32, t_xii + 0.9 + r * 0.32)
            if rk > 0:
                pen.lines(row, rk, vanish, 0.8 * a, 0.65, seed=970 + r * 9)
        # the rule about road width: one line circled
        hk = win(t, t_rule - 0.2, t_rule + 0.8)
        if hk > 0:
            yb = -geo["h"] / 2 + 170 + 6 * 40 - 6
            pen.line(ellipse(0, yb, 230, 28, 40, a0=-2.6), 1.0, a, reveal=hk, start=vanish, seed=990)
    dk = win(t, t_date, t_date + 1.0) * (1 - win(t, t_rule - 0.6, t_rule))
    if dk > 0:
        pen.text("Roma · metà del V secolo a.C.", 900, 900, 46, a * dk, reveal=dk)
    # ---------------------------------------------------------------- the plan-view road
    path = _tav_path()
    shelf = [(x, 812.0) for x in range(-60, W + 61, 40)]
    wide = ease_io(win(t, t_16 - 0.4, t_16 + 1.2))
    left, right, middle = tav_edges(wide)
    rk = ease_io(win(t, t_rule - 0.2, t_rule + 1.6))
    road = morph(shelf, middle, rk, 140) if rk < 1 else middle
    ek = ease_io(win(t, t_rule + 0.6, t_rule + 2.6))
    if ek > 0:
        pen.lines([left], ek, vanish, a, 1.0, seed=1000)
        pen.lines([right], ek, vanish, a, 1.0, seed=1001)
        # grass tufts outside the edges
        tuf = []
        for px, py in ((180, 830), (640, 836), (1190, 800), (1330, 430), (300, 590), (600, 470), (900, 250),
                       (1500, 150)):
            tuf += [[(px - 8, py + 4), (px - 4, py - 6)], [(px, py + 4), (px, py - 9)], [(px + 8, py + 4), (px + 4, py - 6)]]
        pen.lines(tuf, ek, vanish, 0.45 * a, 0.6, seed=1010)
    # ghost of an 8-foot bend (too narrow), shown dashed
    gk = pulse(t, t_why - 0.2, T, 0.6)
    if gk > 0:
        gl, gr, _ = tav_edges(ghost=True)
        for side, E in enumerate((gr,)):
            seg = [p for p in E if p[0] > 380 and p[1] > 120]
            dashes = [seg[i:i + 3] for i in range(0, len(seg) - 2, 4)]
            pen.lines(dashes, gk, vanish, 0.5 * a, 0.6, seed=1020 + side)
    # measuring arrows
    k8 = win(t, t_8 - 0.3, t_8 + 0.7)
    if k8 > 0:
        xm = 300
        pen.lines(double_arrow((xm, TAV_Y - 56), (xm, TAV_Y + 56)), ease_out(k8), vanish, 0.9 * a, 0.8, seed=1030)
        pen.text("8 piedi", xm, TAV_Y + 122, 52, a, reveal=win(t, t_8, t_8 + 0.8))
        pen.text("≈ 2,4 m", xm, TAV_Y + 166, 34, 0.6 * a, reveal=win(t, t_8 + 0.5, t_8 + 1.3))
    k16 = win(t, t_16 - 0.1, t_16 + 0.9)
    if k16 > 0:
        f = math.radians(40)
        c = TAV_C
        p_in, p_out = mid_bend(wide)
        p_in, p_out = lerp2(p_in, p_out, 0.02), lerp2(p_in, p_out, 0.98)
        pen.lines(double_arrow(p_in, p_out), ease_out(k16), vanish, 0.9 * a, 0.8, seed=1040)
        lx, ly = c[0] + (TAV_R + 150) * math.sin(f), c[1] + (TAV_R + 150) * math.cos(f)
        pen.text("16 piedi", lx + 30, ly, 52, a, reveal=win(t, t_16 + 0.1, t_16 + 0.9))
        pen.text("≈ 4,7 m", lx + 30, ly + 44, 34, 0.6 * a, reveal=win(t, t_16 + 0.6, t_16 + 1.4))
    # ---------------------------------------------------------------- the cart takes the bend
    keys = [(t_8 - 1.0, -260.0), (t_why - 0.4, S_CURVE0 - 120), (t_carri + 0.6, S_CURVE1 + 40), (T + 1.5, S_CURVE1 + 900)]
    if t > keys[0][0]:
        sm = _cat1(keys, t)
        mx, my, mh = tav_at(sm)
        hx, hy = mx - math.cos(mh) * 40, my - math.sin(mh) * 40
        ch = tav_at(sm - 300)[2]
        cx, cy = hx - math.cos(ch) * 92, hy - math.sin(ch) * 92
        ca = a * smooth(win(t, keys[0][0], keys[0][0] + 0.6))
        # tracks of the wheels (swept path), faint dotted
        for sg in (-1, 1):
            dots = []
            for j in range(1, 40):
                tt = t - j * 0.09
                if tt < keys[0][0]:
                    break
                s2 = _cat1(keys, tt)
                x2, y2, h2 = tav_at(s2)
                hx2, hy2 = x2 - math.cos(h2) * 40, y2 - math.sin(h2) * 40
                if s2 < S_CURVE0 - 80:
                    break
                c2 = tav_at(s2 - 300)[2]
                ccx, ccy = hx2 - math.cos(c2) * 92, hy2 - math.sin(c2) * 92
                pen.dot(ccx - math.sin(c2) * 46 * sg, ccy + math.cos(c2) * 46 * sg, 2.0,
                        ca * (0.35 if sg > 0 else 0.8) * (1 - j / 40))
        cart_top(pen, cx, cy, ch, ca, seed=1100)
        for sg in (-1, 1):   # shafts
            f0 = (cx + math.cos(ch) * 44 - math.sin(ch) * 23 * sg, cy + math.sin(ch) * 44 + math.cos(ch) * 23 * sg)
            f1 = (mx - math.sin(mh) * 21 * sg, my + math.cos(mh) * 21 * sg)
            pen.line([f0, f1], 0.75, ca, seed=1110 + sg)
        in_bend = smooth(win(sm, S_CURVE0 - 60, S_CURVE0 + 40)) * (1 - smooth(win(sm, S_CURVE1 - 40, S_CURVE1 + 60)))
        mule_top(pen, mx, my, mh, t, ca, ear=-in_bend, seed=1120)
        # the close-up: worried in the bend, relieved after it
        ik_ = pulse(t, t_why + 0.2, T + 2, 0.6)
        if ik_ > 0:
            mood = -1.0 if sm < S_CURVE1 - 20 else 1.0
            icx, icy, R = 1580, 600, 170
            pen.line(ellipse(icx, icy, R, R, 56), 0.95, a, reveal=ik_, start=vanish, seed=1130)
            ctx = pen.ctx
            ctx.save()
            ctx.new_path()
            ctx.arc(icx, icy, R - 5, 0, 2 * math.pi)
            ctx.clip()
            mule_face(pen, icx - 10, icy + 10, 1.25, t, mood, a * smooth(win(t, t_why + 0.4, t_why + 1.0)), seed=1140)
            ctx.restore()
            if mood > 0:
                uk = win(t, t_carri + 0.7, t_carri + 1.5)
                if uk > 0:
                    pen.text("uff!", icx + R - 10, icy - R + 30, 54, a, reveal=uk)
                    for j in range(3):
                        q = (t * 0.9 + j / 3) % 1
                        pen.line(ellipse(icx + 140 + 40 * q, icy + 30 + 10 * q, 4 + 8 * q, 3 + 5 * q, 10), 0.6,
                                 a * (1 - q) * 0.7 * uk, seed=1150 + j)
    return road


# ======================================================================= b08 miliario
MIL_X = 1080                 # where the milestone stops
MIL_H, MIL_R = 450, 64
ROMA = (950.0, 550.0)        # convergence point in the last shot (= where Rome sits on the next map)


def _walk_clock(t, t0, t1, boost=3.2):
    """Integrated walking clock: normal pace, a fast-forward between t0 and t1, then a stop."""
    n = 120
    acc, prev = 0.0, 0.0
    for i in range(1, n + 1):
        u = t * i / n
        sp = 1 + boost * smooth(win(u, t0, t0 + 1.0)) * (1 - smooth(win(u, t1 - 0.8, t1)))
        acc += sp * (u - prev)
        prev = u
    return acc


def milestone_geo(cx, foot, h=MIL_H, r=MIL_R):
    top = foot - 60 - h
    base = [(cx - 100, foot), (cx - 100, foot - 52), (cx + 100, foot - 52), (cx + 100, foot)]
    plinth = [(cx - 112, foot - 52), (cx - 112, foot - 62), (cx + 112, foot - 62), (cx + 112, foot - 52)]
    left = [(cx - r, foot - 62), (cx - r, top)]
    right = [(cx + r, foot - 62), (cx + r, top)]
    cap = ellipse(cx, top, r, r * 0.28, 32)
    bottom = arc(cx, foot - 62, r, 0, math.pi, 18, ry=r * 0.28)
    return [base, plinth, left, right, cap, bottom], top


def ring_text(cx, y, r, rng, width=0.8):
    """A squiggle row bent around the cylinder (slight smile curve)."""
    words = squiggle(cx - r * width, y, 2 * r * width, rng, amp=5)
    out = []
    for w_ in words:
        out.append([(x, yy + 10 * (1 - ((x - cx) / r) ** 2)) for x, yy in w_])
    return out


_MILTXT = None


def _mil_text():
    global _MILTXT
    if _MILTXT is None:
        rng = random.Random(8)
        _MILTXT = [ring_text(0, -MIL_H + 40 + k * 34, MIL_R, rng, 0.78 - 0.04 * (k == 3)) for k in range(5)]
    return _MILTXT


def chain(x0, x1, y):
    links = []
    n = int((x1 - x0) / 22)
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        if i % 2 == 0:
            links.append(ellipse(x, y, 12, 5.5, 12))
        else:
            links.append([(x - 9, y), (x + 9, y)])
    return links


def golden_column(pen, cx, foot, s, t, reveal, start, alpha, glow=1.0):
    with at(pen, cx, foot, s):
        r, h = 46, 400
        base = [[(-110, 0), (-110, -56), (110, -56), (110, 0)], [(-124, -56), (-124, -70), (124, -70), (124, -56)],
                [(-96, -70), (-96, -84), (96, -84), (96, -70)]]
        shaft = [[(-r, -84), (-r * 0.92, -84 - h)], [(r, -84), (r * 0.92, -84 - h)]]
        capital = [[(-r * 0.92, -84 - h), (-r - 26, -84 - h - 24), (r + 26, -84 - h - 24), (r * 0.92, -84 - h)],
                   [(-r - 34, -84 - h - 24), (-r - 34, -84 - h - 36), (r + 34, -84 - h - 36), (r + 34, -84 - h - 24)]]
        bands = [arc(0, -84 - k * h / 4, r * (1 - 0.02 * k), 0, math.pi, 16, ry=r * 0.25) for k in (1, 2, 3)]
        pen.lines(base + shaft + capital, reveal, start, alpha, 1.15, seed=1300, smooth_=False)
        pen.lines(bands, reveal, start, 0.7 * alpha, 0.7, seed=1310)
        # inscribed distances: short lines on the shaft
        rng = random.Random(3)
        rows = [ring_text(0, -150 - k * 40, r, rng, 0.7) for k in range(6)]
        for k, row in enumerate(rows):
            pen.lines(row, reveal, start, 0.55 * alpha, 0.5, seed=1320 + k * 7)
        if glow > 0:
            # glow: a soft second outline and slowly turning rays
            g = glow * (0.75 + 0.25 * wave(t, 0.5))
            pen.lines([[(-r - 8, -84), (-r * 0.92 - 8, -84 - h)], [(r + 8, -84), (r * 0.92 + 8, -84 - h)]], reveal,
                      start, 0.3 * alpha * g, 0.6, seed=1340)
            rays = []
            for k in range(22):
                ang = 2 * math.pi * k / 22 + t * 0.06
                cy = -84 - h / 2
                r0 = 150 + 18 * math.sin(k * 2.3 + t * 1.3)
                L_ = 40 + 30 * (k % 3 == 0)
                rays.append([(math.cos(ang) * r0 * 1.0, cy + math.sin(ang) * r0 * 1.55),
                             (math.cos(ang) * (r0 + L_), cy + math.sin(ang) * (r0 + L_) * 1.55)])
            pen.lines(rays, reveal, start, 0.45 * alpha * g, 0.6, seed=1350)
            for k in range(5):        # twinkles
                ph = (t * 0.7 + k * 0.37) % 1
                tw = math.sin(math.pi * ph)
                px, py = [(-150, -420), (140, -330), (-120, -200), (170, -520), (90, -110)][k]
                sz = 6 + 10 * tw
                pen.lines([[(px - sz, py), (px + sz, py)], [(px, py - sz), (px, py + sz)]], reveal, start,
                          0.8 * alpha * tw * glow, 0.6, seed=1360 + k)


def forum(pen, reveal, start, alpha):
    G_ = ROAD_Y
    temple = [[(150, G_), (150, G_ - 24), (590, G_ - 24), (590, G_)], [(170, G_ - 24), (170, G_ - 44), (570, G_ - 44), (570, G_ - 24)],
              [(160, G_ - 300), (370, G_ - 400), (580, G_ - 300), (160, G_ - 300)],
              [(160, G_ - 300), (160, G_ - 318), (580, G_ - 318)]]
    for k in range(5):
        x = 200 + k * 85
        temple.append([(x, G_ - 44), (x, G_ - 300)])
        temple.append([(x + 22, G_ - 44), (x + 22, G_ - 300)])
    cols = []
    for k in range(3):
        x = 1430 + k * 120
        cols += [[(x, G_), (x, G_ - 330)], [(x + 26, G_), (x + 26, G_ - 330)], [(x - 10, G_ - 330), (x + 36, G_ - 330)]]
    cols.append([(1410, G_ - 346), (1696, G_ - 346), (1696, G_ - 330), (1410, G_ - 330), (1410, G_ - 346)])
    pen.lines(temple, reveal, start, alpha, 0.8, seed=1400, smooth_=False)
    pen.lines(cols, reveal, start, alpha, 0.8, seed=1430, smooth_=False)


# the great roads leaving Rome (screen angle, 0 = east, y down) — north is up
VIAE = [("Flaminia", -82), ("Salaria", -48), ("Tiburtina", -12), ("Latina", 58), ("Appia", 21),
        ("Ostiense", 142), ("Aurelia", 186), ("Cassia", -118)]


def via_ray(ang_deg, length=None, bend=1.0):
    a_ = math.radians(ang_deg)
    d = (math.cos(a_), math.sin(a_))
    # distance to leave the screen
    ts = []
    for k, (lo, hi) in enumerate(((-80, W + 80), (-80, H + 80))):
        c = ROMA[k]
        if abs(d[k]) > 1e-6:
            ts.append(((hi if d[k] > 0 else lo) - c) / d[k])
    Ln = length or min(ts)
    n = (-d[1], d[0])
    pts = []
    for i in range(25):
        u = i / 24
        off = 26 * math.sin(u * math.pi * 1.3 + ang_deg) * bend * u
        pts.append((ROMA[0] + d[0] * Ln * u + n[0] * off, ROMA[1] + d[1] * Ln * u + n[1] * off))
    return pts


@scena("miliario")
def miliario(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    C = lambda ph, f=0.0: cue(T, "miliario", ph, f)
    t_mille = C("Ogni mille passi")
    t_km = C("circa un chilometro")
    t_col = C("ecco una colonna")
    t_mil = C("il miliario.")
    t_manc = C("quante miglia")
    t_cost = C("chi l'aveva")
    t_20 = C("Nel venti")
    t_aug = C("Augusto")
    t_oro = C("Miliario d'oro")
    t_punto = C("il punto simbolico")
    t_strade = C("tutte le grandi strade")
    # ---------------------------------------------------------------- phase A/B: the roadside
    out1 = smooth(win(t, t_20 - 0.9, t_20 + 0.5))          # roadside retracts
    aA = a * (1 - out1)
    t_ff0, t_stop = t_mille + 1.4, t_col - 0.3
    clock = _walk_clock(t, t_ff0, t_stop)
    walking = 1 - smooth(win(t, t_stop - 0.5, t_stop + 0.2))
    # world scroll: px per walking-clock second; frozen after the stop
    v = 210.0
    tt = min(t, t_stop + 0.2)
    scroll = _walk_clock(tt, t_ff0, t_stop) * v
    stop_scroll = _walk_clock(t_stop + 0.2, t_ff0, t_stop) * v
    mx = MIL_X + (stop_scroll - scroll)
    rv0 = 1 - out1
    if aA > 0.003:
        # passing scenery: tufts and pebbles on the road side, a far ridge
        tf = []
        for k in range(14):
            x = (k * 263 - scroll) % 2400 - 240
            tf += [[(x, ROAD_Y + 2), (x - 4, ROAD_Y - 12)], [(x + 6, ROAD_Y + 2), (x + 8, ROAD_Y - 10)]]
        pen.lines(tf, appear * rv0, vanish, 0.45 * aA, 0.6, seed=1200)
        # far cypresses and a farmhouse, sliding by with parallax
        far = []
        for k in range(7):
            x = (k * 397 + 120 - scroll * 0.35) % 2780 - 300
            if k == 3:
                far += [[(x - 60, 700), (x - 60, 650), (x, 615), (x + 60, 650), (x + 60, 700)],
                        [(x - 70, 655), (x, 607), (x + 70, 655)], [(x - 14, 700), (x - 14, 672), (x + 8, 672), (x + 8, 700)]]
            else:
                h_ = 110 + (k * 37) % 50
                far.append([(x - 3, 702), (x - 16, 702 - h_ * 0.35), (x - 10, 702 - h_ * 0.75), (x, 702 - h_),
                            (x + 10, 702 - h_ * 0.75), (x + 16, 702 - h_ * 0.35), (x + 3, 702)])
        pen.lines(far, appear * rv0, vanish, 0.38 * aA, 0.75, seed=1201)
        pen.lines([[(-60, 702), (W + 60, 702)]], appear * rv0, vanish, 0.18 * aA, 0.6, seed=1202)
        # the milestone slides in as he arrives, drawing itself
        mk = win(t, t_col - 2.2, t_col + 0.6)
        if mk > 0:
            strokes, top = milestone_geo(mx, ROAD_Y)
            pen.lines(strokes, mk * rv0, vanish, aA, 1.15, seed=1210, smooth_=False)
            with at(pen, mx, ROAD_Y - 60):
                for k, row in enumerate(_mil_text()):
                    pen.lines(row, win(t, t_col + 0.2 + k * 0.25, t_col + 0.8 + k * 0.25) * rv0, vanish, 0.75 * aA,
                              0.6, seed=1220 + k * 9)
            k2 = win(t, t_mil - 0.4, t_mil + 0.4)
            if k2 > 0:
                pen.text("M · P", mx, ROAD_Y - 238, 40, aA * 0.85, reveal=k2)
                pen.text("XII", mx, ROAD_Y - 156, 92, aA, reveal=win(t, t_mil, t_mil + 0.8))
            # highlights: the distance, then the builder's name
            hk = win(t, t_manc - 0.2, t_manc + 0.8)
            if hk > 0:
                pen.line(ellipse(mx, ROAD_Y - 186, 78, 46, 36, a0=-2.4), 0.9, aA, reveal=hk, start=vanish, seed=1240)
                pen.line([(mx + 84, ROAD_Y - 196), (mx + 160, ROAD_Y - 226), (mx + 196, ROAD_Y - 232)], 0.6, 0.6 * aA,
                         reveal=hk, start=vanish, seed=1241)
                pen.text("XII miglia a Roma", mx + 210, ROAD_Y - 222, 46, aA, align="left",
                         reveal=win(t, t_manc + 0.3, t_manc + 1.3))
            ck = win(t, t_cost - 0.2, t_cost + 0.8)
            if ck > 0:
                y0, y1 = ROAD_Y - 60 - MIL_H + 22, ROAD_Y - 60 - MIL_H + 22 + 4 * 34 + 20
                br = [(mx + 84, y0), (mx + 96, y0 + 8), (mx + 96, (y0 + y1) / 2 - 10), (mx + 108, (y0 + y1) / 2),
                      (mx + 96, (y0 + y1) / 2 + 10), (mx + 96, y1 - 8), (mx + 84, y1)]
                pen.line(br, 0.8, aA, reveal=ck, start=vanish, seed=1242)
                pen.text("chi l'ha costruita", mx + 128, (y0 + y1) / 2 - 4, 46, aA, align="left",
                         reveal=win(t, t_cost + 0.3, t_cost + 1.3))
                pen.text("o restaurata", mx + 128, (y0 + y1) / 2 + 40, 38, 0.7 * aA, align="left",
                         reveal=win(t, t_cost + 0.9, t_cost + 1.8))
        # pace counter
        ck_ = win(t, t_mille - 0.2, t_mille + 0.5)
        if ck_ > 0:
            cycles = clock * 0.85 * 1.0
            n = int(max(cycles, 1000 * ease_in(win(t, t_ff0 + 0.6, t_stop - 0.4), 2.6)))
            n = min(1000, n)
            fade = 1 - smooth(win(t, t_col + 1.5, t_col + 2.5))
            pen.text(f"{n}", 330, 250, 96, aA * fade * smooth(ck_), align="right")
            pen.text("passo" if n == 1 else "passi", 350, 250, 56, 0.8 * aA * fade * smooth(ck_), align="left")
            pen.text("1 passo = 2 falcate ≈ 1,48 m", 330, 300, 32, 0.55 * aA * fade * smooth(win(t, t_mille + 0.6, t_mille + 1.4)),
                     align="center")
            # tally: one bundle every hundred paces
            tal = []
            for g in range(n // 100):
                gx = 120 + g * 46
                for j in range(4):
                    tal.append([(gx + j * 8, 330), (gx + j * 8 + 1, 362)])
                tal.append([(gx - 4, 356), (gx + 30, 334)])
            if tal:
                pen.lines(tal, 1.0, 0.0, 0.7 * aA * fade, 0.7, seed=1250)
        # the measuring chain under the road
        kk = win(t, t_km - 0.4, t_km + 1.2)
        if kk > 0:
            x0c, x1c = 120, MIL_X - 120
            yC = ROAD_Y + 90
            pen.lines(chain(x0c, x1c, yC), ease_io(kk) * rv0, vanish, 0.75 * aA, 0.6, seed=1260)
            pen.lines([[(x0c, yC - 18), (x0c, yC + 18)], [(x1c, yC - 18), (x1c, yC + 18)]], kk * rv0, vanish, 0.75 * aA,
                      0.7, seed=1261)
            pen.text("1 miglio romano = 1000 passi ≈ 1,5 km", (x0c + x1c) / 2, yC + 70, 46, aA,
                     reveal=win(t, t_km, t_km + 1.2))
        # the traveller
        exitk = ease_io(win(t, t_20 - 1.6, t_20 + 0.6))
        ta = aA * smooth(win(t, 0.6, 1.6))
        px = 620 + 70 * smooth(win(t, t_stop + 0.1, t_stop + 1.4)) + exitk * 900
        w_ = max(walking, pulse(t, t_stop + 0.1, t_stop + 1.4, 0.3), smooth(win(t, t_20 - 1.6, t_20 - 1.2)))
        clk = clock if t < t_stop + 0.2 else _walk_clock(t_stop + 0.2, t_ff0, t_stop) + (t - t_stop - 0.2)
        read = smooth(win(t, t_col + 0.5, t_col + 1.2)) * (1 - smooth(win(t, t_20 - 1.8, t_20 - 1.4)))
        point = pulse(t, t_manc + 0.1, t_cost - 0.1, 0.4)
        ff = smooth(win(t, t_ff0 + 0.5, t_ff0 + 1.2)) * (1 - smooth(win(t, t_stop - 1.2, t_stop - 0.4)))
        expr = "determined" if ff > 0.5 else ("surprise" if t_col - 0.3 < t < t_col + 0.9 else
                                               ("smile" if point > 0.3 else ("squint" if read > 0.5 else "calm")))
        omino(pen, px, ROAD_Y, 1.2, clk, "viandante", walk=w_, expr=expr, alpha=ta, seed=1,
              head_tilt=-0.18 * read, look=0.5 * read,
              arm_f=((lerp(DOWN - 0.35, -0.55, point), lerp(0.4, -0.5, point)) if point > 0.01 else None),
              hold=None if point > 0.01 else "staff")
        if ff > 0.05:     # speed lines behind him while fast-forwarding
            sl = [[(px - 90 - k * 30, ROAD_Y - 240 + k * 50), (px - 200 - k * 30, ROAD_Y - 240 + k * 50)] for k in range(4)]
            pen.lines(sl, 1.0, 0.0, 0.45 * ff * aA, 0.6, seed=1270)
    # ---------------------------------------------------------------- phase C: the golden milestone in the Forum
    road = flat()
    inC = smooth(win(t, t_20 - 0.3, t_20 + 1.6))
    if inC > 0:
        zk = ease_io(win(t, t_punto - 0.4, t_punto + 1.8))
        cxg = lerp(960, ROMA[0], zk)
        fg = lerp(ROAD_Y, ROMA[1] + 20, zk)
        sg = lerp(0.88, 0.42, zk)
        golden_column(pen, cxg, fg, sg, t, win(t, t_20 - 0.2, t_20 + 2.4), vanish, a, glow=smooth(win(t, t_aug, t_oro)))
        fk = win(t, t_20 + 0.6, t_20 + 2.6)
        if fk > 0:
            forum(pen, fk, max(vanish, smooth(win(t, t_punto - 0.4, t_punto + 0.8))), 0.35 * a)
        ok = win(t, t_oro - 0.1, t_oro + 1.0)
        if ok > 0:
            fo = 1 - smooth(win(t, t_punto - 0.4, t_punto + 0.4))
            pen.text("Miliario d'oro", 960, 112, 78, a * fo, reveal=ok)
            pen.text("Miliarium Aureum · Foro Romano · 20 a.C.", 960, 166, 38, 0.65 * a * fo,
                     reveal=win(t, t_oro + 0.5, t_oro + 1.6))
        # roads converging on it from every direction
        rk = win(t, t_punto, t_punto + 3.0)
        if rk > 0:
            for i, (name, ang) in enumerate(VIAE):
                ray = via_ray(ang)
                inward = list(reversed(ray))
                k = clamp(rk * 1.6 - i * 0.08)
                pen.line(trim(inward, 0.0, 0.93), 0.8, 0.75 * a, reveal=ease_out(k), start=vanish, seed=1450 + i)
            for i, (name, ang) in enumerate(VIAE):
                ray = via_ray(ang)
                k = win(t, t_punto + 0.8 + i * 0.25, t_punto + 1.8 + i * 0.25)
                if k > 0:
                    p = resample(ray, 25)[15]
                    d = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
                    pen.text(name.lower(), p[0] - d[1] * 34, p[1] + d[0] * 34 + 12, 38, 0.7 * a, reveal=k)
                # travellers flowing in
                for j in range(2):
                    u = 1 - ((t * 0.18 + j * 0.5 + i * 0.13) % 1)
                    if u > 0.12:
                        R_ = resample(ray, 25)
                        q = u * 24
                        qi = int(q)
                        qp = lerp2(R_[qi], R_[min(24, qi + 1)], q - qi)
                        pen.dot(qp[0], qp[1], 3.2, a * smooth(rk) * smooth(win(u, 0.12, 0.3)) * 0.85)
            pen.text("Roma", ROMA[0] - 80, ROMA[1] + 64, 46, a, reveal=win(t, t_punto + 1.0, t_punto + 2.0))
        full = via_ray(21)
        appia = trim(full, 0.0, 480.0 / length(full))
        rk2 = ease_io(win(t, t_punto, t_punto + 2.4))
        if rk2 > 0:
            road = morph(flat(), appia, rk2, 120)
    return road


# ======================================================================= b10 posta
from motore.personaggi import tube  # noqa: E402


def leg_ik(hip, foot, l1, l2, joint_forward):
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = clamp(math.hypot(dx, dy), 1e-3, l1 + l2 - 0.5)
    base = math.atan2(dy, dx)
    al = math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1))
    js = [(hip[0] + math.cos(base + sg * al) * l1, hip[1] + math.sin(base + sg * al) * l1) for sg in (1, -1)]
    js.sort(key=lambda p: p[0])
    j = js[1] if joint_forward else js[0]
    # put the foot exactly at reach
    ff = (hip[0] + dx / max(1e-3, math.hypot(dx, dy)) * d, hip[1] + dy / max(1e-3, math.hypot(dx, dy)) * d)
    return j, ff


# body outline (local, facing right, hooves at y = 0); pivot of the body = (0, -160)
_H_BACK = [(-104, -176), (-70, -186), (-20, -180), (30, -186), (64, -194)]
_H_BELLY = [(98, -150), (92, -122), (54, -104), (0, -99), (-52, -106), (-84, -124)]
_H_RUMP = [(-104, -176), (-116, -154), (-108, -132), (-84, -124)]
_H_NECK_TOP = [(0, 0), (34, -40), (62, -76), (78, -88)]           # relative to the withers (64, -194)
_H_NECK_FRONT = [(70, -44), (52, -10), (40, 20), (34, 44)]
_H_HEAD = [(78, -88), (94, -90), (112, -72), (136, -42), (146, -26), (140, -14), (120, -14), (98, -26), (80, -40), (70, -44)]


def horse(pen, x, y, s, ph, g, t, alpha, fx=1, head_down=0.0, seed=0, saddle=True, tired=0.0):
    """A line-art horse with a rotary gallop. ph: gait phase (cycles), g: 0 standing .. 1 full gallop.
    Returns the rider's seat in screen coords and the body pitch."""
    L = pen.line
    two = 2 * math.pi
    bob = -13 * g * (0.5 + 0.5 * math.sin(two * ph)) + 1.6 * math.sin(t * 1.7 + seed) * (1 - g)
    pitch = 0.07 * g * math.cos(two * ph)
    seat_local = None
    with at(pen, x, y, s, fx=fx):
        piv = (0, -160 + bob)

        def bf(p):        # body frame → base frame
            q = rot((p[0], p[1] + 160), pitch)
            return (q[0] + piv[0], q[1] + piv[1])

        legs = [("hind", -70, 0.0, 0.7), ("fore", 76, 0.42, 0.7), ("hind", -62, 0.10, 1.0), ("fore", 84, 0.52, 1.0)]
        for kind, hx, off, la in legs:
            hip = bf((hx, -124))
            q = ph + off
            c, sn = math.cos(two * q), math.sin(two * q)
            reach = 62 * g
            if kind == "fore":
                fxp = hx + 10 + reach * c
                l1, l2 = 66, 66
            else:
                fxp = hx - 8 + reach * c
                l1, l2 = 62, 70
            lift = g * (56 if kind == "fore" else 44) * max(0.0, -sn)
            foot = (fxp, -8 - lift)
            j, ff = leg_ik(hip, foot, l1, l2, joint_forward=(kind == "fore"))
            tube(pen, [hip, j, ff], 28, 11, alpha * la, seed=seed + int(hx), lw=0.95)
            # hoof
            a_ = math.atan2(ff[1] - j[1], ff[0] - j[0]) - math.pi / 2
            hf = [rot(p, a_) for p in [(-8, 0), (-9, 9), (10, 9), (8, 0)]]
            L([(ff[0] + p[0], ff[1] + p[1]) for p in hf], 0.9, alpha * la, smooth_=False, seed=seed + 7 + int(hx))
        with at(pen, piv[0], piv[1], 1.0, pitch):
            sh = lambda pts: [(px, py + 160) for px, py in pts]
            back = list(_H_BACK)
            if saddle:
                back_a, back_b = back[:3], back[2:]
                L(sh(back_a), 1.1, alpha, seed=seed + 1)
                L(sh(back_b), 1.1, alpha, seed=seed + 2)
                L(sh([(-34, -176), (-30, -150), (30, -152), (34, -182)]), 0.8, alpha * 0.8, seed=seed + 3)   # saddle cloth
            else:
                L(sh(back), 1.1, alpha, seed=seed + 1)
            L(sh(_H_BELLY), 1.1, alpha, seed=seed + 4)
            L(sh(_H_RUMP), 1.1, alpha, seed=seed + 5)
            # tail: streams back at the gallop, swishes when standing
            sw = math.sin(t * 2.1 + seed) * (1 - g) * 10
            tl = []
            for k in range(3):
                fl = math.sin(two * ph + k) * 10 * g
                tl.append(sh([(-106, -172 + k * 4), (-128 - 30 * g, -158 + 6 * k - 20 * g + fl * 0.4),
                              (-140 - 60 * g + sw, -120 + 8 * k - 50 * g + fl), (-138 - 80 * g + sw * 1.4, -86 + 6 * k - 70 * g + fl)]))
            for k, st in enumerate(tl):
                L(st, 0.8, alpha * (1.0 - 0.2 * k), seed=seed + 10 + k)
            # neck and head, nodding with the stride
            nod = 0.09 * g * math.sin(two * ph + 1.2) + head_down * 0.75 + 0.03 * math.sin(t * 0.9 + seed) * (1 - g)
            with at(pen, 64, -194 + 160, 1.0, nod):
                L(_H_NECK_TOP, 1.1, alpha, seed=seed + 20)
                L(_H_NECK_FRONT, 1.1, alpha, seed=seed + 21)
                L(_H_HEAD, 1.1, alpha, seed=seed + 22)
                pen.dot(136, -30, 2.6, alpha)                       # nostril
                if tired > 0.5:
                    L([(100, -66), (108, -63), (116, -66)], 0.9, alpha, seed=seed + 23)
                    L([(98, -74), (116, -76)], 0.7, alpha, seed=seed + 24)
                else:
                    pen.dot(106, -66, 3.6, alpha)
                L([(118, -22), (128, -20)], 0.6, alpha * 0.7, seed=seed + 25)   # mouth
                fl = wave(t, 0.6, seed) * 0.1
                for k, bx in enumerate((80, 88)):
                    a_ = -1.9 + k * 0.25 + fl - 0.5 * tired - 0.3 * g
                    tip = (bx + math.cos(a_) * 26, -90 + math.sin(a_) * 26)
                    L([(bx - 4, -88), ((bx + tip[0]) / 2 - 4, (-88 + tip[1]) / 2), tip, ((bx + tip[0]) / 2 + 5, (-88 + tip[1]) / 2),
                       (bx + 6, -90)], 0.8, alpha, seed=seed + 26 + k)
                for k in range(5):       # mane
                    bx, by = 8 + k * 15, -10 - k * 16
                    fl = math.sin(two * ph * 1.0 + k * 0.8) * 5 * g + math.sin(t * 1.3 + k) * 2
                    L([(bx, by), (bx - 14 - 10 * g, by + 4 + fl * 0.5), (bx - 26 - 18 * g, by + 14 + fl)], 0.7,
                      alpha * 0.85, seed=seed + 30 + k)
                if saddle:      # reins
                    L([(112, -30), (60, -10), (-20, 30)], 0.5, alpha * 0.7, seed=seed + 36)
        seat_local = bf((2, -192))
    sx = x + seat_local[0] * s * fx
    sy = y + seat_local[1] * s
    return sx, sy, pitch


def rider(pen, x, y, s, t, alpha, lean=0.0, expr="determined", hold=None, legs="ride", gallop=0.0, fx=1, seed=0,
          cloak=1.0, look=0.0, hat=True, crown=False, hand_up=0.0):
    """A courier seated at (x, y) (the seat), facing right."""
    L = pen.line
    with at(pen, x, y, s, fx=fx):
        # near leg
        if legs == "ride":
            knee, ft = (34, 40), (24, 96)
        else:   # seated in a cart: legs forward
            knee, ft = (50, 6), (58, 58)
        noodle(pen, (6, 4), knee, 6, 1.1, alpha, seed=seed)
        noodle(pen, knee, ft, -6, 1.1, alpha, seed=seed + 1)
        L([(ft[0] - 8, ft[1] - 6), (ft[0] - 8, ft[1] + 2), (ft[0] + 18, ft[1] + 3), (ft[0] + 16, ft[1] - 4)], 0.9, alpha,
          seed=seed + 2)
        with at(pen, 0, 0, 1.0, lean):
            bob = math.sin(t * 2 * math.pi * 2.2) * 3 * gallop
            body = [(-30, 6), (-36, -30), (-28, -66), (-14, -84 + bob), (16, -84 + bob), (30, -64), (34, -30), (28, 6)]
            L(body, 1.1, alpha, seed=seed + 3)
            L([(-32, -22), (0, -18), (32, -24)], 0.7, alpha * 0.85, seed=seed + 4)
            # cloak streaming behind
            fl = math.sin(t * 9) * 8 * cloak * (0.4 + gallop)
            L([(-14, -80 + bob), (-60 - 30 * gallop, -74 + fl), (-100 - 40 * gallop, -50 - fl), (-70 - 10 * gallop, -36)], 0.9,
              alpha * 0.9 * cloak, seed=seed + 5)
            # back arm: reins or a raised message
            sh_b = (-10, -76 + bob)
            if hand_up > 0:
                el = (lerp(0, -18, hand_up), lerp(-40, -118, hand_up))
                hd = (lerp(40, 4, hand_up), lerp(-30, -150, hand_up))
            else:
                el, hd = (10, -40), (50, -36)
            noodle(pen, sh_b, hd, 8, 1.05, alpha * 0.85, seed=seed + 6)
            mitten(pen, hd[0], hd[1], 0, 8, alpha * 0.85, seed=seed + 7)
            if hold == "scroll" and hand_up > 0.05:
                k = hand_up
                L([(hd[0] - 18, hd[1] - 26), (hd[0] + 18, hd[1] - 26), (hd[0] + 18, hd[1] - 4), (hd[0] - 18, hd[1] - 4),
                   (hd[0] - 18, hd[1] - 26)], 0.9, alpha * k, smooth_=False, seed=seed + 8)
                pen.dot(hd[0], hd[1] - 15, 4.5, alpha * k)
                L([(hd[0], hd[1] - 10), (hd[0] - 4, hd[1] + 2)], 0.6, alpha * k, seed=seed + 9)
            # head
            hx, hy = 10, -136 + bob
            face(pen, hx, hy, 40, expr, look, t, True, 1.0, True, seed + 10, alpha)
            if hat:
                L([(hx - 44, hy - 18), (hx - 26, hy - 40), (hx + 12, hy - 44), (hx + 38, hy - 26), (hx - 44, hy - 18)], 0.9,
                  alpha, seed=seed + 11)
            else:
                L([(hx - 36, hy - 22), (hx - 24, hy - 40), (hx + 4, hy - 46), (hx + 30, hy - 36)], 0.9, alpha, seed=seed + 11)
                if crown:   # a simple laurel sprig for a young noble
                    for k in range(4):
                        a_ = math.radians(200 + k * 22)
                        px, py = hx + math.cos(a_) * 42, hy + math.sin(a_) * 40
                        L(ellipse(px, py, 6, 3, 8, a0=a_), 0.6, alpha * 0.8, seed=seed + 12 + k)
            # front arm with the reins
            sh_f = (14, -76 + bob)
            hd = (66, -40 + bob * 0.5)
            noodle(pen, sh_f, hd, 10, 1.1, alpha, seed=seed + 20)
            mitten(pen, hd[0], hd[1], -0.4, 8, alpha, seed=seed + 21)


def _gait_clock(t, fn, steps=None):
    """∫0^t fn(u) du with a fixed step (fn smooth)."""
    n = steps or max(8, int(t * 12))
    h = t / n
    acc = 0.0
    for i in range(n):
        acc += fn((i + 0.5) * h) * h
    return acc


def building_mutatio(cx, g):
    w, h = 300, 170
    x0, x1 = cx - w / 2, cx + w / 2
    walls = [[(x0, g), (x0, g - h), (x1, g - h), (x1, g)]]
    roof = [[(x0 - 26, g - h + 4), (cx, g - h - 92), (x1 + 26, g - h + 4)]]
    door = [[(cx - 30, g), (cx - 30, g - 92), (cx + 30, g - 92), (cx + 30, g)]]
    win_ = [[(x0 + 34, g - 120), (x0 + 74, g - 120), (x0 + 74, g - 90), (x0 + 34, g - 90), (x0 + 34, g - 120)]]
    tiles = [[(lerp(x0 - 26, cx, k / 5), lerp(g - h + 4, g - h - 92, k / 5)), (lerp(x1 + 26, cx, k / 5), lerp(g - h + 4, g - h - 92, k / 5))]
             for k in (2, 4)]
    trough = [[(x1 + 20, g), (x1 + 26, g - 34), (x1 + 120, g - 34), (x1 + 126, g)], [(x1 + 30, g - 26), (x1 + 116, g - 26)]]
    post = [[(x0 - 60, g), (x0 - 60, g - 210)], [(x0 - 60, g - 196), (x0 + 50, g - 196)],
            [(x0 - 40, g - 196), (x0 - 40, g - 176)], [(x0 + 30, g - 196), (x0 + 30, g - 176)],
            [(x0 - 70, g - 176), (x0 + 60, g - 176), (x0 + 60, g - 122), (x0 - 70, g - 122), (x0 - 70, g - 176)]]
    return walls + roof + door + win_ + tiles + trough, post, (x0 - 5, g - 140)


def building_mansio(cx, g):
    w, h = 330, 270
    x0, x1 = cx - w / 2, cx + w / 2
    walls = [[(x0, g), (x0, g - h), (x1, g - h), (x1, g)], [(x0, g - 140), (x1, g - 140)]]
    roof = [[(x0 - 24, g - h + 6), (x0 + 30, g - h - 70), (x1 - 30, g - h - 70), (x1 + 24, g - h + 6)]]
    door = [[(x0 + 40, g), (x0 + 40, g - 100), (x0 + 100, g - 100), (x0 + 100, g)]]
    wins = [[(x1 - 120, g - 112), (x1 - 50, g - 112), (x1 - 50, g - 60), (x1 - 120, g - 60), (x1 - 120, g - 112)],
            [(x0 + 50, g - 236), (x0 + 150, g - 236), (x0 + 150, g - 168), (x0 + 50, g - 168), (x0 + 50, g - 236)]]
    sign = [[(x1, g - 190), (x1 + 70, g - 190)], [(x1 + 14, g - 190), (x1 + 14, g - 176)], [(x1 + 62, g - 190), (x1 + 62, g - 176)],
            [(x1 - 10, g - 176), (x1 + 102, g - 176), (x1 + 102, g - 128), (x1 - 10, g - 128), (x1 - 10, g - 176)]]
    return walls + roof + door + wins, sign, (x0 + 100, g - 170)


def cypress(x, g, h):
    return [(x - 3, g), (x - 15, g - h * 0.35), (x - 10, g - h * 0.75), (x, g - h), (x + 10, g - h * 0.75), (x + 15, g - h * 0.35),
            (x + 3, g)]


@scena("posta")
def posta(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    C = lambda ph, f=0.0: cue(T, "posta", ph, f)
    t_cp = C("cursus publicus")
    t_serv = C("il servizio")
    t_staz = C("stazioni")
    t_camb = C("cambiare i cavalli")
    t_loc = C("e locande")
    t_cor = C("Un corriere")
    t_50 = C("una cinquantina")
    t_pli = C("E Plinio")
    t_tib = C("il futuro imperatore")
    t_ger = C("malato in Germania")
    t_200 = C("coprì duecento")
    t_notte = C("e una notte")
    V = 640.0
    t_stop = t_camb - 0.2
    t_dec = t_stop - 2.6
    t_hop = t_camb + 0.2
    t_go = t_hop + 0.9
    s_h = 0.95
    s_r = 0.76
    # camera speed and integrated scroll
    def vcam(u):
        return V * (1 - smooth(win(u, t_dec, t_stop))) + V * smooth(win(u, t_go + 0.4, t_go + 2.6))
    scroll = _gait_clock(t, vcam)
    scroll_stop = _gait_clock(t_stop, vcam)
    rel = scroll - scroll_stop                  # world offset since the stop (≤ 0 before)
    # ---------------------------------------------------------------- road (rises over the Alps at the end)
    climb = ease_io(win(t, t_tib - 0.5, T - 0.4))

    def ground(x):
        u = clamp((x - 260) / 1600)
        return ROAD_Y - climb * (330 * smooth(u) + 40 * math.sin(u * 7.0) * u)

    road = [(x, ground(x)) for x in range(-60, W + 61, 40)]
    # ---------------------------------------------------------------- background: cypresses / Alps / sky
    far = []
    for k in range(8):
        x = (k * 331 + 90 - scroll * 0.3) % 2650 - 300
        h_ = 100 + (k * 41) % 60
        far.append(cypress(x, 700, h_))
    alps_k = smooth(win(t, t_pli, t_tib + 0.6))
    farA = (1 - alps_k) * (1 - pulse(t, t_staz - 2.6, t_cor + 1.2, 1.0))
    pen.lines(far, appear, vanish, 0.35 * a * farA, 0.7, seed=1500)
    pen.lines([[(-60, 700), (W + 60, 700)]], appear, vanish, 0.16 * a * farA, 0.6, seed=1501)
    if alps_k > 0:
        px_ = -(scroll * 0.05) % 600
        peaks = []
        for j in range(5):
            bx = 300 + j * 420 - px_
            hh = 300 + (j * 97) % 160
            peaks.append([(bx - 260, 720), (bx - 120, 720 - hh * 0.55), (bx - 70, 720 - hh * 0.5), (bx, 720 - hh),
                          (bx + 90, 720 - hh * 0.6), (bx + 140, 720 - hh * 0.65), (bx + 280, 720)])
            peaks.append([(bx - 46, 720 - hh * 0.8), (bx - 20, 720 - hh * 0.74), (bx, 720 - hh * 0.84), (bx + 26, 720 - hh * 0.76),
                          (bx + 52, 720 - hh * 0.82)])
        ctx = pen.ctx
        ctx.save()
        ctx.new_path()
        ctx.move_to(-200, -200)
        ctx.line_to(W + 200, -200)
        for x in range(W + 200, -201, -40):
            ctx.line_to(x, ground(x) - 4)
        ctx.close_path()
        ctx.clip()
        pen.lines(peaks, alps_k, vanish, 0.42 * a, 0.75, seed=1510, smooth_=False)
        ctx.restore()
    # sun → moon over the record ride
    dayk = win(t, t_tib - 1.0, t_200)
    nightk = win(t, t_200 - 0.2, T)
    if 0 < dayk and t < t_200 + 0.4:
        ang = math.radians(lerp(200, 345, ease_io(dayk)))
        sx, sy = 960 + math.cos(ang) * 840, 820 + math.sin(ang) * 540
        sa = a * smooth(win(t, t_tib - 1.0, t_tib)) * (1 - smooth(win(t, t_200 - 0.2, t_200 + 0.4)))
        pen.line(ellipse(sx, sy, 34, 34, 24), 1.0, sa, seed=1520)
        rays = [[(sx + math.cos(k * 0.785 + t * 0.4) * 46, sy + math.sin(k * 0.785 + t * 0.4) * 46),
                 (sx + math.cos(k * 0.785 + t * 0.4) * 62, sy + math.sin(k * 0.785 + t * 0.4) * 62)] for k in range(8)]
        pen.lines(rays, 1.0, 0.0, sa * 0.8, 0.7, seed=1521)
    if nightk > 0:
        ang = math.radians(lerp(222, 300, ease_io(nightk)))
        mx_, my_ = 960 + math.cos(ang) * 840, 760 + math.sin(ang) * 430
        ma = a * smooth(win(t, t_200 - 0.2, t_200 + 0.8))
        pen.line(arc(mx_, my_, 32, math.radians(-60), math.radians(200), 20), 1.0, ma, seed=1530)
        pen.line(arc(mx_ + 14, my_ - 6, 26, math.radians(-40), math.radians(170), 18), 0.9, ma, seed=1531)
        for k in range(16):
            sx, sy = (k * 487) % 1840 + 40, 70 + (k * 211) % 330
            tw = 0.6 + 0.4 * math.sin(t * 2.0 + k)
            pen.dot(sx, sy, 2.2, ma * tw * smooth(win(t, t_200 + 0.2 + k * 0.05, t_200 + 1.0 + k * 0.05)))
    # ---------------------------------------------------------------- the relay station and the inn
    stat_x = 520 - rel
    inn_x = 1600 - rel
    if -700 < stat_x < 2600:
        bk = win(t, t_staz - 2.8, t_staz + 0.2)
        st, post, sign_at = building_mutatio(stat_x, ROAD_Y)
        pen.lines(st, bk, vanish, 0.62 * a, 0.9, seed=1540, smooth_=False)
        pen.lines(post, bk, vanish, 0.8 * a, 0.8, seed=1560, smooth_=False)
        pen.text("mutatio", sign_at[0], sign_at[1] + 2, 40, a * 0.9 * bk, reveal=win(t, t_staz, t_staz + 0.8))
    if -700 < inn_x < 2700:
        bk = win(t, t_staz - 1.8, t_staz + 1.2)
        mn, sign, win_at = building_mansio(inn_x, ROAD_Y)
        pen.lines(mn, bk, vanish, 0.62 * a, 0.9, seed=1570, smooth_=False)
        pen.lines(sign, bk, vanish, 0.8 * a, 0.8, seed=1590, smooth_=False)
        x1 = inn_x + 165
        pen.text("mansio", x1 + 46, ROAD_Y - 142, 38, a * 0.9 * bk, reveal=win(t, t_loc, t_loc + 0.8))
        # a sleepy guest at the upper window
        gk = smooth(win(t, t_loc - 0.2, t_loc + 0.8)) * a
        if gk > 0:
            gx, gy = win_at[0] - 50, win_at[1] - 4
            gy += 6 + 3 * math.sin(t * 1.2)
            face(pen, gx, gy, 28, "squint", 0, t, False, 0.8, True, 1600, gk)
            pen.line([(gx - 30, gy - 8), (gx - 16, gy - 40), (gx + 16, gy - 36), (gx + 46, gy - 10), (gx + 56, gy + 2)], 0.8, gk,
                     seed=1601)           # nightcap
            pen.dot(gx + 58, gy + 4, 4.5, gk)
            pen.line([(gx - 50, gy + 34), (gx + 50, gy + 34)], 0.6, gk * 0.7, seed=1602)
            for j in range(3):
                q = (t * 0.35 + j / 3) % 1
                pen.text("z", gx + 50 + 50 * q, gy - 30 - 80 * q, 26 + 14 * q, gk * math.sin(math.pi * q) * 0.9)
        mk = win(t, t_loc, t_loc + 1.0) * (1 - smooth(win(t, t_cor + 0.5, t_cor + 1.5)))
        if mk > 0:
            pen.line(arc(inn_x - 20, ROAD_Y - 470, 30, math.radians(-60), math.radians(200), 20), 0.9, a * mk, seed=1610)
            pen.line(arc(inn_x - 6, ROAD_Y - 476, 24, math.radians(-40), math.radians(170), 18), 0.8, a * mk, seed=1611)
    # ---------------------------------------------------------------- the courier, the horses
    two = 2 * math.pi
    # courier screen position: rides in at 620, drifts to the station, hops onto the fresh horse, rides on
    px_arr = lerp(-380, 620, ease_out(win(t, 0.5, 3.4), 2.2)) + 320 * smooth(win(t, t_dec, t_stop))
    fresh_x0 = 940 + 330
    out_ride = smooth(win(t, t_go, t_go + 1.0)) * 140 - smooth(win(t, t_go + 1.2, t_go + 5.0)) * (fresh_x0 + 140 - 700)
    px_fresh = fresh_x0 + out_ride - 0  # fresh horse on screen (stationary in the world until t_go)
    if t < t_go:
        px_fresh = fresh_x0 - rel
    # gait amplitudes
    g1 = 1 - smooth(win(t, t_dec + 0.8, t_stop + 0.1))
    g2 = smooth(win(t, t_go - 0.1, t_go + 0.9))
    f_g = lambda gg: 0.6 + 1.6 * gg
    ph1 = _gait_clock(t, lambda u: f_g(1 - smooth(win(u, t_dec + 0.8, t_stop + 0.1))))
    ph2 = _gait_clock(t, lambda u: f_g(smooth(win(u, t_go - 0.1, t_go + 0.9))) if u > t_go - 0.5 else 0.6)
    # phase C/D: the courier gallops off and the record carriage arrives
    exit_c = ease_in(win(t, t_pli - 0.3, t_pli + 1.6), 2)
    px_fresh += exit_c * 1500
    ca = a * smooth(win(t, 0.5, 1.3))
    # tired horse (stays at the station)
    tired_x = 940 - max(0.0, rel) if t > t_stop else px_arr
    hop = smooth(win(t, t_hop, t_hop + 0.7))
    if tired_x > -400:
        sx, sy, pt = horse(pen, tired_x, ROAD_Y, s_h, ph1, g1, t, ca, seed=1700,
                           head_down=0.6 * smooth(win(t, t_hop + 0.4, t_hop + 1.4)),
                           tired=smooth(win(t, t_stop, t_stop + 0.5)), saddle=True)
        seat1 = (sx, sy, pt)
    # the fresh horse waits, tied to the inn's post
    if px_fresh < W + 400:
        head_up = smooth(win(t, t_stop - 0.4, t_stop + 0.4))
        sx2, sy2, pt2 = horse(pen, px_fresh, ROAD_Y, s_h, ph2, g2, t, ca * smooth(win(t, t_staz - 1.5, t_staz)) if t < t_go else ca,
                              seed=1800, saddle=True)
        seat2 = (sx2, sy2, pt2)
    else:
        seat2 = None
    # the rider: on horse 1, a hop, then on horse 2
    if t < t_pli + 1.8:
        if hop <= 0:
            rx, ry, rp = seat1
            gal = g1
        elif hop >= 1 and seat2:
            rx, ry, rp = seat2
            gal = g2
        else:
            ax_, ay_, _ = seat1
            bx_, by_, _ = seat2 if seat2 else seat1
            rx, ry = lerp(ax_, bx_, hop), lerp(ay_, by_, hop) - 150 * math.sin(math.pi * hop)
            rp = -0.2 * math.sin(math.pi * hop)
            gal = 0.0
        hand = pulse(t, t_serv - 0.4, t_staz - 1.0, 0.5)
        expr = "talk" if t_cp - 0.3 < t < t_cp + 1.2 else ("surprise" if 0 < hop < 1 else ("grin" if t_go < t < t_go + 1.6 else "determined"))
        rider(pen, rx, ry, s_r, t, ca, lean=0.25 * gal + rp, expr=expr, hold="scroll", gallop=gal, hand_up=hand, seed=1900)
    # ---------------------------------------------------------------- labels
    k = win(t, t_cp - 0.2, t_cp + 1.0)
    fo = 1 - smooth(win(t, t_staz - 1.2, t_staz - 0.4))
    if k > 0 and fo > 0:
        pen.text("cursus publicus", 960, 170, 84, a * fo, reveal=k)
        pen.text("messaggi · funzionari", 960, 236, 42, 0.7 * a * fo, reveal=win(t, t_serv + 0.6, t_serv + 1.6))
    if t > t_cor - 0.5:
        k = win(t, t_cor, t_cor + 1.0) * (1 - smooth(win(t, t_pli - 0.4, t_pli + 0.4)))
        if k > 0:
            n = int(lerp(10, 50, ease_io(win(t, t_cor + 0.3, t_50 + 1.8))))
            pen.text(f"≈ {n}", 860, 200, 110, a * k, align="right")
            pen.text("miglia al giorno", 890, 200, 54, a * k, align="left")
            pen.text("≈ 75 km", 960, 262, 38, 0.6 * a * k)
            # passing milestones: one per mile
            ms = []
            for j in range(6):
                x = (j * 420 - scroll * 1.0) % 2520 - 300
                g = ROAD_Y
                ms += [[(x - 16, g), (x - 16, g - 70), (x + 16, g - 70), (x + 16, g)], ellipse(x, g - 70, 16, 5, 12)]
            pen.lines(ms, k, 0.0, 0.6 * a * k, 0.8, seed=1950)
    # ---------------------------------------------------------------- the record: Tiberius's dash
    k = win(t, t_pli - 0.2, t_pli + 0.9) * (1 - smooth(win(t, t_200 - 1.0, t_200 - 0.2)))
    if k > 0:
        pen.text("un record, raccontato da Plinio il Vecchio", 960, 118, 46, 0.75 * a * k, reveal=k)
    cin = ease_out(win(t, t_pli + 0.4, t_tib + 0.6), 2.5)
    if cin > 0:
        cx_ = lerp(-500, 760, cin)
        gy = ground(cx_)
        slope = math.atan2(ground(cx_ + 30) - ground(cx_ - 30), 60)
        ph3 = t * 2.4
        car = a * smooth(win(t, t_pli + 0.4, t_pli + 1.0))
        with at(pen, cx_, gy, 1.0, slope):
            # light two-wheeled carriage (cisium) behind the horse
            wx, wy, wr = -230, -56, 56
            spin = -scroll / wr
            pen.line(ellipse(wx, wy, wr, wr, 36), 1.05, car, seed=2000)
            pen.line(ellipse(wx, wy, wr * 0.8, wr * 0.8, 30), 0.6, car * 0.6, seed=2001)
            pen.lines([[(wx + math.cos(spin + k_ * math.pi / 4) * 8, wy + math.sin(spin + k_ * math.pi / 4) * 8),
                        (wx + math.cos(spin + k_ * math.pi / 4) * wr * 0.8, wy + math.sin(spin + k_ * math.pi / 4) * wr * 0.8)]
                       for k_ in range(8)], 1.0, 0.0, car * 0.8, 0.7, seed=2002)
            body = [(-296, -112), (-290, -80), (-176, -78), (-160, -96), (-152, -132), (-164, -150)]
            pen.line(body, 1.05, car, seed=2003)
            pen.line([(-296, -112), (-176, -112)], 0.7, car * 0.8, seed=2004)
            pen.line([(-170, -92), (-60, -112), (40, -128)], 0.9, car, seed=2005)        # shaft
            # dust and speed lines
            for j in range(4):
                q = (t * 1.6 + j / 4) % 1
                pen.line(ellipse(wx - 60 - 120 * q, -6 - 14 * q, 8 + 14 * q, 5 + 8 * q, 12), 0.6, car * (1 - q) * 0.6,
                         seed=2010 + j)
            sl = [[(-340 - j * 40, -200 + j * 46), (-520 - j * 40, -200 + j * 46)] for j in range(4)]
            pen.lines(sl, 1.0, 0.0, 0.45 * car, 0.6, seed=2020)
        hx3 = cx_ + 40
        sx3, sy3, pt3 = horse(pen, hx3, ground(hx3), 0.88, ph3, 1.0, t, car, seed=2100, saddle=False)
        # Tiberius on the seat
        dx, dy = rot((-212, -128), slope)
        rider(pen, cx_ + dx, gy + dy, 0.82, t, car, lean=0.3 + slope, expr="determined", legs="cart", gallop=1.0,
              hat=False, crown=True, seed=2200)
        lk = win(t, t_tib - 0.2, t_tib + 0.8)
        if lk > 0:
            pen.text("Tiberio", cx_ + dx, gy + dy - 230, 46, a * lk, reveal=lk)
            pen.text("9 a.C.", cx_ + dx, gy + dy - 192, 32, 0.6 * a * lk, reveal=win(t, t_tib + 0.4, t_tib + 1.2))
        # where he is going
        gk = win(t, t_ger - 0.3, t_ger + 0.7)
        if gk > 0:
            gx = 1620
            gyy = ground(gx)
            pen.lines([[(gx, gyy), (gx, gyy - 150)], [(gx - 10, gyy - 140), (gx + 150, gyy - 140), (gx + 176, gyy - 118),
                                                         (gx + 150, gyy - 96), (gx - 10, gyy - 96), (gx - 10, gyy - 140)]],
                      gk, vanish, a, 0.9, seed=2300, smooth_=False)
            pen.text("Germania", gx + 78, gyy - 108, 32, a * gk)
            pen.text("dal fratello Druso", gx + 78, gyy - 168, 30, 0.6 * a * gk, reveal=win(t, t_ger + 0.2, t_ger + 1.0))
        rk = win(t, t_200 - 0.1, t_200 + 1.0)
        if rk > 0:
            pen.text("200 miglia · un giorno e una notte", 960, 120, 64, a, reveal=rk)
            pen.text("≈ 300 km", 960, 172, 38, 0.6 * a, reveal=win(t, t_notte, t_notte + 0.8))
    return road
