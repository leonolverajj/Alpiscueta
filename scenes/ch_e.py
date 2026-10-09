"""Batch E (s42-s47): the cosmos under the dome, the comedy arc, four sources, the Logos,
imago dei, and the law. All figures are original designs drawn with the flat-2D ink kit."""
import math
import random

from engine.kit import (FONT_TITLE, H, W, at, bg_studio, camera, caption_tag, catmull, cel, circle_pts, clip,
                        ease_back, ease_io, ease_out, fillp, glow, lerp, mix, ribbon, rot, shape, spikes, ss,
                        stroke, text, ui_glyphs, win)
from engine import figures as F
from . import scene


# ----------------------------------------------------------------- shared helpers
def _wave_edge(t, y0, amp, seed=0.0, step=64):
    """Animated horizontal wave line across the whole canvas (top edge of a water body)."""
    pts = []
    x = -40.0
    while x <= W + 41:
        pts.append((x, y0 + math.sin(t * 1.3 + x * 0.012 + seed) * amp))
        x += step
    return pts


def _crests(ctx, pts, color, every=3, alpha=0.6):
    for i in range(1, len(pts) - 1, every):
        x, y = pts[i]
        stroke(ctx, [(x - 22, y + 7), (x, y - 2), (x + 22, y + 7)], 3, color, alpha=alpha, taper=(0.3, 0.6))


def _path(ctrl, n=12):
    """Dense Catmull-Rom path with cumulative arc length: (poly, cum)."""
    poly = catmull(ctrl, n=n)
    cum = [0.0]
    for a, b in zip(poly, poly[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return poly, cum


def _along(path, u):
    """Point and unit tangent at arc-length fraction u (0..1) of a path."""
    poly, cum = path
    d = max(0.0, min(1.0, u)) * cum[-1]
    i = 1
    while i < len(cum) - 1 and cum[i] < d:
        i += 1
    a, b = poly[i - 1], poly[i]
    seg = (cum[i] - cum[i - 1]) or 1e-6
    k = (d - cum[i - 1]) / seg
    tx, ty = (b[0] - a[0]) / seg, (b[1] - a[1]) / seg
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k), (tx, ty)


def _upto(path, u):
    """Polyline of a path from its start up to arc-length fraction u."""
    poly, cum = path
    d = max(0.0, min(1.0, u)) * cum[-1]
    out = [poly[0]]
    for i in range(1, len(poly)):
        if cum[i] >= d:
            break
        out.append(poly[i])
    end, _ = _along(path, u)
    out.append(end)
    return out


def _y_at(poly, x):
    for a, b in zip(poly, poly[1:]):
        if min(a[0], b[0]) <= x <= max(a[0], b[0]):
            k = (x - a[0]) / ((b[0] - a[0]) or 1e-6)
            return a[1] + (b[1] - a[1]) * k
    return poly[-1][1]


def _zone(ctx, poly, x0, x1, color, alpha):
    """Fill the area between a curve and the bottom of the frame, for curve points with x in [x0, x1]."""
    pts = [p for p in poly if x0 <= p[0] <= x1]
    if len(pts) < 2:
        return
    fillp(ctx, pts + [(pts[-1][0], H + 10), (pts[0][0], H + 10)], color, alpha=alpha)


def _draw_faded(ctx, alpha, fn):
    """Run a drawing function with group opacity (for figures that take no alpha)."""
    if alpha <= 0.01:
        return
    if alpha >= 0.99:
        fn()
        return
    ctx.push_group()
    fn()
    g = ctx.pop_group()
    ctx.set_source(g)
    ctx.paint_with_alpha(alpha)


# ================================================================= s42  cosmos_dome
_DOME_CX, _DOME_CY = W / 2, H * 0.68
_DOME_RX, _DOME_RY = W * 0.36, H * 0.38
_LAND = [(W * 0.13, H * 0.68), (W * 0.30, H * 0.665), (W * 0.50, H * 0.678), (W * 0.70, H * 0.662),
         (W * 0.87, H * 0.68), (W * 0.83, H * 0.82), (W * 0.72, H * 0.95), (W * 0.50, H * 1.03),
         (W * 0.28, H * 0.95), (W * 0.17, H * 0.82)]
_WELL_X = W * 0.62


def _dome(n=44):
    pts = []
    for i in range(n + 1):
        a = math.pi - math.pi * i / n
        pts.append((_DOME_CX + math.cos(a) * _DOME_RX, _DOME_CY - math.sin(a) * _DOME_RY))
    return pts


def _rain(ctx, t, n=80, seed=3):
    """Rain falling from the upper waters, through the vault, onto the land."""
    rng = random.Random(seed)
    y0, y1 = H * 0.27, H * 0.66
    for i in range(n):
        x = rng.uniform(W * 0.16, W * 0.84)
        ph = rng.uniform(0, 1)
        y = y0 + ((ph + t * 0.55) % 1.0) * (y1 - y0)
        stroke(ctx, [(x, y), (x - 6, y + 34)], 3.4, "teal_l", alpha=0.9, taper=(0.1, 0.7), seed=i)


def _well(ctx, t):
    """Well cut in section: a dark shaft into the fresh water, with frame and bucket."""
    wx = _WELL_X
    top = H * 0.667
    shape(ctx, [(wx - 30, top), (wx + 30, top), (wx + 30, H * 0.80), (wx - 30, H * 0.80)], "ink", 4, seed=6)
    for sx in (-44, 44):
        shape(ctx, [(wx + sx - 7, H * 0.555), (wx + sx + 7, H * 0.555), (wx + sx + 7, top + 6),
                    (wx + sx - 7, top + 6)], "gold_d", 4, seed=7 + sx)
    shape(ctx, [(wx - 60, H * 0.54), (wx + 60, H * 0.54), (wx + 60, H * 0.565), (wx - 60, H * 0.565)],
          "gold", 4, seed=9)
    yb = lerp(H * 0.71, H * 0.77, 0.5 + 0.5 * math.sin(t * 1.1))
    stroke(ctx, [(wx, H * 0.555), (wx, yb)], 3, "gold_d", taper=(0, 0))
    shape(ctx, [(wx - 16, yb), (wx + 16, yb), (wx + 11, yb + 26), (wx - 11, yb + 26)], "steel", 4, seed=11)


@scene("cosmos_dome")
def cosmos_dome(ctx, t, T, seg):
    bg_studio(ctx, t, seed=42, tone=0.35)
    camera(ctx, t, T, zoom=(1.0, 1.05))
    # waters above the vault
    top = _wave_edge(t, H * 0.25, 10, seed=0.0)
    fillp(ctx, [(-40, -20), (W + 40, -20)] + list(reversed(top)), "cobalt_d")
    _crests(ctx, top, "teal_l", alpha=0.45)
    # the sun travels inside the vault, seen through its translucent skin
    k = win(t, 0.05, T * 0.95)
    th = math.pi * (0.96 - 0.92 * ss(k))
    sx = _DOME_CX + math.cos(th) * _DOME_RX * 0.78
    sy = _DOME_CY - math.sin(th) * _DOME_RY * 0.78
    glow(ctx, sx, sy, 200, "gold", 0.6)
    shape(ctx, circle_pts(sx, sy, 34, 24), "gold_l", 4, seed=2)
    # the vault
    dome = _dome()
    fillp(ctx, dome, "cobalt_l", alpha=0.25)
    shade_half = [p for p in dome if p[0] >= _DOME_CX] + [(_DOME_CX, _DOME_CY)]
    fillp(ctx, shade_half, "cobalt_d", alpha=0.22)
    stroke(ctx, dome, 7, "ink", taper=(0.04, 0.04), wobble=0.1, seed=4)
    _rain(ctx, t)
    # salt ocean around the edges
    sea = _wave_edge(t, H * 0.665, 8, seed=1.0)
    fillp(ctx, sea + [(W + 40, H + 20), (-40, H + 20)], "sea")
    _crests(ctx, sea, "sea_l", alpha=0.7)
    # the flat disc of earth
    shape(ctx, _LAND, "rust", 6, seed=5, wobble=0.1)
    cel(ctx, _LAND, [(W * 0.6, H * 0.7), (W * 0.95, H * 0.7), (W * 0.84, H * 1.1), (W * 0.6, H * 1.1)],
        "rust_d", alpha=0.8)
    # fresh water beneath the land
    with clip(ctx, _LAND):
        fw = _wave_edge(t, H * 0.80, 6, seed=2.0)
        fillp(ctx, fw + [(W + 40, H + 20), (-40, H + 20)], "cobalt")
        _crests(ctx, fw, "cobalt_l", alpha=0.5)
    _well(ctx, t)
    # labels appear one by one
    caption_tag(ctx, "AGUAS SOBRE LA CÚPULA · LLUVIA", 90, 120, t, 30, accent="teal", appear=0.10)
    caption_tag(ctx, "LA CÚPULA", 90, 470, t, 30, accent="gold", appear=0.30)
    caption_tag(ctx, "EL SOL RECORRE LA BÓVEDA", 1330, 330, t, 30, accent="gold", appear=0.42)
    caption_tag(ctx, "EL DISCO DE TIERRA", 300, 780, t, 30, accent="rust", appear=0.55)
    caption_tag(ctx, "AGUA DULCE · POZO", 1230, 930, t, 30, accent="cobalt_l", appear=0.68)
    caption_tag(ctx, "OCÉANO SALADO", 60, 1000, t, 30, accent="teal", appear=0.82)
    ui_glyphs(ctx, t, seed=42, n=6)


# ================================================================= s43  comedy_arc
_ARC = [(0.02, 0.44), (0.10, 0.36), (0.20, 0.32), (0.29, 0.42), (0.36, 0.62), (0.44, 0.82), (0.52, 0.88),
        (0.60, 0.80), (0.68, 0.60), (0.77, 0.42), (0.85, 0.33), (0.92, 0.30)]


def _tree(ctx, x, base, s=1.0):
    shape(ctx, [(x - 9 * s, base), (x + 9 * s, base), (x + 7 * s, base - 90 * s), (x - 7 * s, base - 90 * s)],
          "rust_d", 4, seed=int(x))
    crown = circle_pts(x, base - 140 * s, 52 * s, 20, ry=72 * s)
    shape(ctx, crown, "teal", 4.5, seed=int(x) + 1)
    cel(ctx, crown, [(x + 10 * s, base - 240 * s), (x + 80 * s, base - 240 * s), (x + 80 * s, base),
                     (x + 10 * s, base)], "teal_d", alpha=0.9)


def _bare_tree(ctx, x, base, hh):
    stroke(ctx, [(x, base), (x + 6, base - hh * 0.5), (x - 4, base - hh)], 7, "ink", taper=(0.1, 0.5))
    for k, (dx, dy) in enumerate(((-30, -0.5), (26, -0.6), (-14, -0.85))):
        y1 = base - hh * (0.45 + 0.2 * k)
        stroke(ctx, [(x + (dx * 0.4), y1), (x + dx, y1 + dy * 40)], 4, "ink", taper=(0.1, 0.6))


def _tower(ctx, x, base, w, h, seed):
    body = [(x, base), (x + w, base), (x + w, base - h), (x, base - h)]
    shape(ctx, body, "gold_l", 5, seed=seed)
    cel(ctx, body, [(x + w * 0.5, base), (x + w, base), (x + w, base - h), (x + w * 0.5, base - h)], "gold",
        alpha=0.9)
    if h > 170:
        shape(ctx, [(x - 6, base - h), (x + w * 0.5, base - h - 70), (x + w + 6, base - h)], "gold", 5, seed=seed + 1)
    for j in range(3):
        fillp(ctx, [(x + w * 0.3, base - h + 30 + j * 46), (x + w * 0.7, base - h + 30 + j * 46),
                    (x + w * 0.7, base - h + 52 + j * 46), (x + w * 0.3, base - h + 52 + j * 46)], "gold_d",
              alpha=0.8)


@scene("comedy_arc")
def comedy_arc(ctx, t, T, seg):
    bg_studio(ctx, t, seed=43, tone=0.25)
    camera(ctx, t, T, zoom=(1.0, 1.05))
    path = _path([(x * W, y * H) for x, y in _ARC], n=14)
    poly = path[0]
    # zones under the curve: a garden, a dark valley, a shining city
    _zone(ctx, poly, 0, W * 0.31, "teal_l", 0.35)
    glow(ctx, W * 0.14, H * 0.2, 260, "gold_l", 0.35)
    _zone(ctx, poly, W * 0.33, W * 0.68, "night", 0.92)
    _zone(ctx, poly, W * 0.78, W, "gold_l", 0.4)
    # garden trees and valley trees
    for xf in (0.06, 0.14, 0.22):
        _tree(ctx, xf * W, _y_at(poly, xf * W) + 4)
    for xf, hh in ((0.39, 150), (0.46, 110), (0.60, 170)):
        x = xf * W
        _bare_tree(ctx, x, _y_at(poly, x) + 6, hh)
    for xf in (0.43, 0.53, 0.62):
        x = xf * W
        yb = _y_at(poly, x) + 4
        shape(ctx, [(x - 22, yb), (x - 22, yb - 40), (x, yb - 54), (x + 22, yb - 40), (x + 22, yb)], "g3", 4,
              seed=int(x))
    for i in range(6):  # low fog drifting over the valley floor
        fx_ = W * (0.36 + 0.05 * i) + math.sin(t * 0.5 + i) * 26
        glow(ctx, fx_, H * (0.68 + 0.04 * (i % 3)), 120, "g3", 0.22)
    # city towers on the final plateau
    base = H * 0.315
    glow(ctx, W * 0.9, H * 0.2, 300, "gold", 0.45)
    for i, (xf, wf, hh) in enumerate(((0.80, 40, 120), (0.835, 56, 190), (0.875, 70, 240), (0.92, 52, 180),
                                      (0.96, 36, 110))):
        _tower(ctx, xf * W, base, wf, hh, seed=60 + i)
    # the curve, drawn as the walker advances
    stroke(ctx, poly, 4, "g5", alpha=0.35, taper=(0.02, 0.02))
    u = ease_io(win(t, 0.4, T * 0.9))
    pts = _upto(path, u)
    stroke(ctx, pts, 24, "ink", taper=(0.0, 0.0))
    stroke(ctx, pts, 13, "red", taper=(0.0, 0.0))
    # the tiny walker
    (px, py), (tx, _) = _along(path, u)
    glow(ctx, px, py - 50, 90, "teal", 0.55)
    F.person(ctx, px, py, h=120, color="cobalt", shade="cobalt_d", pose="walk", t=t,
             fx=1 if tx >= 0 else -1, head_c="skin", seed=3)
    # labels
    caption_tag(ctx, "PARAÍSO", 90, 110, t, 34, accent="gold", appear=0.10)
    caption_tag(ctx, "CAÍDA", W * 0.24, H * 0.58, t, 34, color="red", accent="ink", appear=0.35)
    caption_tag(ctx, "HISTORIA: MUERTE Y SUFRIMIENTO", W / 2 - 330, H * 0.94, t, 32, color="night",
                accent="red_l", appear=0.60)
    caption_tag(ctx, "REDENCIÓN", 1180, 200, t, 34, accent="gold", appear=1.00)
    ui_glyphs(ctx, t, seed=43, n=5)


# ================================================================= s44  four_sources
_FOUR = [
    ("J", "cobalt_d", [(-90, 0.24 * H), (0.18 * W, 0.30 * H), (0.34 * W, 0.40 * H), (W / 2 - 360, H / 2 - 70)],
     (0.10 * W, 0.40 * H)),
    ("E", "teal_d", [(0.66 * W, -90), (0.62 * W, 0.20 * H), (0.56 * W, 0.30 * H), (W / 2 - 120, H / 2 - 170)],
     (0.70 * W, 0.12 * H)),
    ("P", "red_d", [(W + 90, 0.74 * H), (0.80 * W, 0.68 * H), (0.68 * W, 0.60 * H), (W / 2 + 360, H / 2 + 70)],
     (0.86 * W, 0.84 * H)),
    ("D", "gold_d", [(0.30 * W, H + 90), (0.36 * W, 0.84 * H), (0.44 * W, 0.74 * H), (W / 2 + 120, H / 2 + 170)],
     (0.24 * W, 0.92 * H)),
]


def _river(ctx, t, ctrl, color, phase, grow):
    """A braided river of ink flowing from the edge of the frame into the scroll."""
    poly = catmull(ctrl, n=12)
    n = len(poly)
    m = max(2, int(n * ss(grow)))
    pts = poly[:m]
    if len(pts) < 2:
        return
    out = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        s = i / max(1, n - 1)
        off = math.sin(i * 0.22 + t * 2.4 + phase) * 22 * s
        out.append((x - dy / L * off, y + dx / L * off))
    ws = [8 + 70 * (i / max(1, n - 1)) for i in range(len(out))]
    fillp(ctx, ribbon(out, ws), color, alpha=0.95)
    stroke(ctx, out, 3, "g0", alpha=0.3, taper=(0.1, 0.1), seed=int(phase * 10))


def _scroll(ctx, t):
    cx, cy = W / 2, H / 2
    shape(ctx, [(cx - 340, cy - 150), (cx + 340, cy - 150), (cx + 340, cy + 150), (cx - 340, cy + 150)],
          "paper", 6, seed=1)
    fillp(ctx, [(cx - 340, cy + 105), (cx + 340, cy + 105), (cx + 340, cy + 150), (cx - 340, cy + 150)], "g2")
    rng = random.Random(9)
    for j in range(8):
        y = cy - 120 + j * 28
        x0 = cx - 300 + rng.uniform(0, 30)
        x1 = cx + 300 - rng.uniform(0, 160)
        stroke(ctx, [(x0, y), (x1, y + rng.uniform(-3, 3))], 3, "g5", alpha=0.5, taper=(0.1, 0.2), seed=j)
    for sgn in (-1, 1):
        rx = cx + sgn * 352
        shape(ctx, circle_pts(rx, cy, 34, 22, ry=158), "g1", 6, seed=20 + sgn)
        for k in range(4):
            yk = cy - 110 + k * 70
            stroke(ctx, [(rx - 20, yk), (rx + 20, yk + 8)], 3, "g4", alpha=0.6, taper=(0.2, 0.2))
    for dx in (-170, 0, 170):
        stroke(ctx, [(cx + dx, cy - 138), (cx + dx, cy + 138)], 2.5, "g4", alpha=0.5, taper=(0.1, 0.1))


def _stitchers(ctx, t):
    """Three editors' hands sew the page seams; the stitches accumulate over time."""
    cx, cy = W / 2, H / 2
    N = 9
    gap = 260 / N
    top = cy - 130
    for k, dx in enumerate((-170, 0, 170)):
        x = cx + dx
        m = (t * 0.42 + k * 0.31) * N
        for i in range(int(m)):
            y = top + (i % N + 0.5) * gap
            side = -1 if i % 2 else 1
            stroke(ctx, [(x - 9 * side, y - 4), (x + 9 * side, y + 4)], 3.5, "red", taper=(0.1, 0.1),
                   seed=i + k * 20)
        hy = top + ((int(m) % N) + 0.5) * gap
        F.hand(ctx, x + 30, hy, a=0.0, s=2.1, color="skin", kind="fist", fx=-1, shade="skin_s")


@scene("four_sources")
def four_sources(ctx, t, T, seg):
    bg_studio(ctx, t, seed=44, tone=0.2)
    camera(ctx, t, T, zoom=(1.0, 1.04))
    for i, (letter, color, ctrl, lab) in enumerate(_FOUR):
        _river(ctx, t, ctrl, color, phase=i * 1.7, grow=win(t, T * (0.04 + i * 0.05), T * (0.28 + i * 0.05)))
    _scroll(ctx, t)
    _stitchers(ctx, t)
    for i, (letter, color, ctrl, lab) in enumerate(_FOUR):
        a = win(t, T * (0.2 + i * 0.05), T * (0.3 + i * 0.05))
        text(ctx, letter, lab[0] + 6, lab[1] + 6, 130, FONT_TITLE, "red", alpha=a)
        text(ctx, letter, lab[0], lab[1], 130, FONT_TITLE, "ink", alpha=a)
    caption_tag(ctx, "CUATRO FUENTES", 90, 100, t, 40, accent="red", appear=0.6)
    ui_glyphs(ctx, t, seed=44, n=5)


# ================================================================= s45  logos
_SPK = (W * 0.17, H * 0.40)            # speaker's face centre
_ORIG = (_SPK[0] + 44, _SPK[1] + 58)   # his mouth: where the light is born
_LOGO_OBJS = []


def _logo_objects():
    if not _LOGO_OBJS:
        rng = random.Random(45)
        for i in range(24):
            ang = rng.uniform(-0.40, 0.40)
            d = rng.uniform(430, 1180)
            x = _ORIG[0] + math.cos(ang) * d
            y = _ORIG[1] + math.sin(ang) * d * 0.6 + 110
            kind = ("mount", "tree", "person")[i % 3]
            sc = 0.55 + d / 1180 * 0.55
            _LOGO_OBJS.append((ang, x, y, kind, sc, i))
    return _LOGO_OBJS


def _adiff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


def _logo_object(ctx, kind, x, y, sc, lit, t, seed):
    if kind == "mount":
        shape(ctx, [(x - 130 * sc, y), (x - 10 * sc, y - 230 * sc), (x + 110 * sc, y)],
              mix("cobalt_d", "gold_l", 0.35 * lit), 4, seed=seed)
        shape(ctx, [(x - 10 * sc, y), (x + 60 * sc, y - 120 * sc), (x + 170 * sc, y)],
              mix("cobalt", "gold_l", 0.25 * lit), 4, seed=seed + 1)
        shape(ctx, [(x - 40 * sc, y - 150 * sc), (x - 10 * sc, y - 230 * sc), (x + 20 * sc, y - 170 * sc)],
              "g0", 3, seed=seed + 2)
    elif kind == "tree":
        shape(ctx, [(x - 8 * sc, y), (x + 8 * sc, y), (x + 6 * sc, y - 80 * sc), (x - 6 * sc, y - 80 * sc)],
              "rust_d", 3.5, seed=seed)
        shape(ctx, circle_pts(x, y - 130 * sc, 56 * sc, 16, ry=80 * sc), mix("teal", "gold_l", 0.3 * lit), 4,
              seed=seed + 1)
    else:
        F.person(ctx, x, y, h=190 * sc, color=mix("g3", "gold_l", 0.3 * lit), shade="g5", pose="stand", t=t,
                 seed=seed, head_c="skin")


def _static(ctx, t, th):
    """Formless grey static everywhere outside the beam."""
    rng = random.Random(int(t * 14))
    for _ in range(650):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H)
        ang = math.atan2(y - _ORIG[1], x - _ORIG[0])
        if abs(_adiff(ang, th)) < 0.2 and x > _ORIG[0]:
            continue
        g = rng.uniform(0.25, 0.6)
        s = rng.choice([2, 3, 4, 6])
        ctx.set_source_rgba(g, g, g + 0.02, rng.uniform(0.25, 0.7))
        ctx.rectangle(x, y, s, s)
        ctx.fill()


@scene("logos")
def logos(ctx, t, T, seg):
    bg_studio(ctx, t, seed=45, dark=True, slabs=False)
    camera(ctx, t, T, zoom=(1.0, 1.04), focus=(_ORIG[0], _ORIG[1]))
    th = lerp(-0.6, 0.6, ease_io(win(t, T * 0.15, T * 0.85)))
    _static(ctx, t, th)
    # the beam from the mouth
    far = 2600
    p1 = (_ORIG[0] + math.cos(th - 0.2) * far, _ORIG[1] + math.sin(th - 0.2) * far)
    p2 = (_ORIG[0] + math.cos(th + 0.2) * far, _ORIG[1] + math.sin(th + 0.2) * far)
    fillp(ctx, [_ORIG, p1, p2], "gold_l", alpha=0.16)
    p3 = (_ORIG[0] + math.cos(th - 0.08) * far, _ORIG[1] + math.sin(th - 0.08) * far)
    p4 = (_ORIG[0] + math.cos(th + 0.08) * far, _ORIG[1] + math.sin(th + 0.08) * far)
    fillp(ctx, [_ORIG, p3, p4], "white", alpha=0.10)
    glow(ctx, _ORIG[0], _ORIG[1], 260, "gold_l", 0.35)
    # the world, revealed where the light has passed
    for ang, x, y, kind, sc, seed in _logo_objects():
        rev = ss((th - ang + 0.22) / 0.3)
        lit = 1 - ss(abs(th - ang) / 0.25)
        _draw_faded(ctx, rev, lambda k=kind, xx=x, yy=y, s_=sc, l_=lit, sd=seed:
                    _logo_object(ctx, k, xx, yy, s_, l_, t, sd))
    # the speaker
    glow(ctx, _SPK[0], _SPK[1], 200, "gold", 0.25)
    F.character(ctx, _SPK[0], _SPK[1], 0.95,
                dict(F.SAGE, coat="g5", coat_s="g6", skin="skin2", skin_s="skin2_s", hair_c="hair_white"),
                expr="awe", t=t)
    glow(ctx, _ORIG[0], _ORIG[1], 120, "gold_l", 0.5 + 0.2 * math.sin(t * 8))
    # the words
    text(ctx, "EN EL PRINCIPIO ERA EL VERBO", W / 2, H * 0.14, 60, FONT_TITLE, "g0", tracking=0.08,
         alpha=win(t, 0.05, 0.9))
    ui_glyphs(ctx, t, seed=45, n=5, color="teal_l")


# ================================================================= s46  imago_dei
def _spark(ctx, x, y, r, a):
    if a <= 0.01:
        return
    glow(ctx, x, y, r * 4.5, "gold", 0.55 * a)
    star = spikes(x, y, r * 0.35, r, 4, -math.pi / 2, -math.pi / 2 + 2 * math.pi, var=0.0)
    fillp(ctx, star, "gold_l", alpha=a)
    fillp(ctx, circle_pts(x, y, r * 0.35, 12), "white", alpha=a)


@scene("imago_dei")
def imago_dei(ctx, t, T, seg):
    bg_studio(ctx, t, seed=46, tone=-0.2, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.05))
    man = dict(F.HERO, coat="cobalt", coat_s="cobalt_d", lining="gold")
    mx, my = W * 0.31, H * 0.44
    wx, wy = W * 0.69, H * 0.44
    F.character(ctx, mx, my, 1.0, man, "awe" if t > T * 0.55 else "neutral", t)
    F.character(ctx, wx, wy, 1.0, F.WOMAN, "awe" if t > T * 0.55 else "smile", t, fx=-1)
    # the two sparks in the chests
    sm = (mx, my + 230)
    sw = (wx, wy + 230)
    star_at = (W / 2, H * 0.2)
    u = ease_io(win(t, T * 0.12, T * 0.45))
    flare = 0.8 + 0.2 * math.sin(t * 5)
    for (x0, y0), tag in ((sm, 0), (sw, 1)):
        cxq = (x0 + star_at[0]) / 2
        cyq = H * 0.3
        def bez(v):
            return ((1 - v) ** 2 * x0 + 2 * (1 - v) * v * cxq + v * v * star_at[0],
                    (1 - v) ** 2 * y0 + 2 * (1 - v) * v * cyq + v * v * star_at[1])
        # trail
        for j in range(1, 9):
            px_, py_ = bez(max(0.0, u - j * 0.03))
            glow(ctx, px_, py_, 22, "gold_l", 0.35 * (1 - j / 9) * (1 if u > 0 else 0))
        px_, py_ = bez(u)
        if u < 1:
            _spark(ctx, px_, py_, 14 * flare, 1.0)
        # ember left behind in the chest
        glow(ctx, x0, y0, 60, "gold", 0.35 * flare)
    # the star they form above them
    ks = ease_back(win(t, T * 0.45, T * 0.6), 1.6)
    if ks > 0:
        glow(ctx, star_at[0], star_at[1], 320 * ks, "gold", 0.5 * ks)
        star = spikes(star_at[0], star_at[1], 26 * ks, 92 * ks, 8, -math.pi / 2, 1.5 * math.pi, var=0.0)
        fillp(ctx, star, "gold_l", alpha=min(1.0, ks))
        fillp(ctx, circle_pts(star_at[0], star_at[1], 18 * ks, 14), "white", alpha=min(1.0, ks))
    caption_tag(ctx, "A IMAGEN DE LO DIVINO", 90, 100, t, 36, accent="gold", appear=T * 0.7)
    ui_glyphs(ctx, t, seed=46, n=6, color="teal_l")


# ================================================================= s47  law
def _facade(ctx, t):
    pedi = [(W * 0.10, H * 0.26), (W / 2, H * 0.10), (W * 0.90, H * 0.26)]
    shape(ctx, pedi, "g3", 6, seed=3)
    cel(ctx, pedi, [(W / 2, 0), (W, 0), (W, H), (W / 2, H)], "g4", alpha=0.7)
    shape(ctx, [(W * 0.10, H * 0.26), (W * 0.90, H * 0.26), (W * 0.90, H * 0.32), (W * 0.10, H * 0.32)],
          "g2", 6, seed=4)
    # the hall behind the colonnade
    hall = [(W * 0.14, H * 0.32), (W * 0.86, H * 0.32), (W * 0.86, H * 0.88), (W * 0.14, H * 0.88)]
    shape(ctx, hall, mix("night", "g6", 0.4), 5, seed=5)
    for k in range(8):
        x = W * (0.18 + k * 0.09)
        stroke(ctx, [(x, H * 0.34), (x, H * 0.86)], 2, "g5", alpha=0.35, taper=(0.1, 0.1))
    # columns
    for xf in (0.15, 0.245, 0.755, 0.85):
        x = W * xf
        col_pts = [(x - 34, H * 0.32), (x + 34, H * 0.32), (x + 34, H * 0.86), (x - 34, H * 0.86)]
        shape(ctx, col_pts, "g1", 5, seed=int(x))
        cel(ctx, col_pts, [(x + 6, 0), (x + 80, 0), (x + 80, H), (x + 6, H)], "g3", alpha=0.9)
        for k in (-1, 0, 1):
            stroke(ctx, [(x + k * 14, H * 0.34), (x + k * 14, H * 0.84)], 2.5, "g4", alpha=0.6)
        shape(ctx, [(x - 44, H * 0.30), (x + 44, H * 0.30), (x + 44, H * 0.33), (x - 44, H * 0.33)], "g2", 5,
              seed=int(x) + 1)
        shape(ctx, [(x - 44, H * 0.85), (x + 44, H * 0.85), (x + 44, H * 0.88), (x - 44, H * 0.88)], "g2", 5,
              seed=int(x) + 2)
    # steps
    shape(ctx, [(W * 0.07, H * 0.88), (W * 0.93, H * 0.88), (W * 0.93, H * 0.92), (W * 0.07, H * 0.92)],
          "g2", 5, seed=8)
    shape(ctx, [(W * 0.04, H * 0.92), (W * 0.96, H * 0.92), (W * 0.96, H * 0.97), (W * 0.04, H * 0.97)],
          "g3", 5, seed=9)


def _spot(ctx, t):
    beam = [(W * 0.46, H * 0.32), (W * 0.52, H * 0.32), (W * 0.66, H * 0.88), (W * 0.30, H * 0.88)]
    fillp(ctx, beam, "gold_l", alpha=0.10 + 0.03 * math.sin(t * 1.7))
    glow(ctx, W * 0.49, H * 0.34, 220, "gold_l", 0.35)


def _scales(ctx, t, T):
    x, y0 = W * 0.66, H * 0.40
    k = ease_out(win(t, 0.3, T * 0.72), 3)
    tilt = lerp(-0.34, 0.0, k) + 0.025 * math.sin(t * 2.4) * (1 - k)
    shape(ctx, [(x - 76, H * 0.80), (x + 76, H * 0.80), (x + 96, H * 0.88), (x - 96, H * 0.88)], "g2", 5, seed=21)
    shape(ctx, [(x - 12, y0 + 10), (x + 12, y0 + 10), (x + 12, H * 0.80), (x - 12, H * 0.80)], "gold", 5, seed=22)
    L = rot((x - 270, y0), tilt, (x, y0))
    R = rot((x + 270, y0), tilt, (x, y0))
    stroke(ctx, [L, R], 14, "gold", taper=(0, 0))
    shape(ctx, circle_pts(x, y0, 16, 14), "gold_l", 4, seed=23)
    for end, pan_c, seed_ in ((L, "steel", 24), (R, "gold_l", 25)):
        px_, py_ = end[0], end[1] + 170
        stroke(ctx, [end, (px_ - 80, py_)], 3, "g5", taper=(0, 0))
        stroke(ctx, [end, (px_ + 80, py_)], 3, "g5", taper=(0, 0))
        shape(ctx, [(px_ - 90, py_), (px_ + 90, py_), (px_ + 62, py_ + 40), (px_ - 62, py_ + 40)], pan_c, 5,
              seed=seed_)
    # the heavy weight of guilt in the left pan
    lx, ly = L[0], L[1] + 170
    for j, (hw, hh) in enumerate(((60, 30), (44, 28), (30, 24))):
        yb = ly + 22 - j * 28
        shape(ctx, [(lx - hw, yb), (lx + hw, yb), (lx + hw - 4, yb - hh), (lx - hw + 4, yb - hh)], "ink2", 4,
              seed=30 + j)
    # the golden worth in the right pan
    rx, ry = R[0], R[1] + 170
    glow(ctx, rx, ry - 30, 110, "gold", 0.55)
    shape(ctx, circle_pts(rx, ry - 30, 24, 16), "gold_l", 4, seed=33)


def _defendant(ctx, t):
    fx_, fy = W * 0.40, H * 0.88
    s = 560 / 300
    F.person(ctx, fx_, fy, h=560, color=mix("rust_d", "g5", 0.3), shade="ink2", pose="stand", t=t, seed=5,
             head_c="skin2", ink=4.5)
    with at(ctx, fx_, fy, s):
        # shackles: a sagging chain between the wrists, with steel cuffs
        for k in range(11):
            u = k / 10
            xk = lerp(-52, 54, u)
            yk = -118 + math.sin(math.pi * u) * 14
            stroke(ctx, circle_pts(xk, yk, 5, 10, ry=3.5), 2.2, "steel_l", closed=True, taper=(0, 0))
        for cx_ in (-52, 54):
            shape(ctx, [(cx_ - 12, -134), (cx_ + 12, -134), (cx_ + 12, -112), (cx_ - 12, -112)], "steel", 4,
                  seed=int(cx_) + 60)
        # the golden spark the law cannot take away
        pulse = 0.8 + 0.2 * math.sin(t * 2.2)
        glow(ctx, 0, -190, 90, "gold", 0.8 * pulse)
        fillp(ctx, spikes(0, -190, 4, 11, 4, -math.pi / 2, 1.5 * math.pi, var=0.0), "gold_l", alpha=1.0)


@scene("law")
def law(ctx, t, T, seg):
    bg_studio(ctx, t, seed=47, tone=0.1)
    camera(ctx, t, T, zoom=(1.0, 1.06), focus=(W / 2, H * 0.5))
    _facade(ctx, t)
    _spot(ctx, t)
    _scales(ctx, t, T)
    _defendant(ctx, t)
    caption_tag(ctx, "VALOR INTRÍNSECO", 90, 90, t, 40, accent="gold", appear=0.4)
    ui_glyphs(ctx, t, seed=47, n=6)
