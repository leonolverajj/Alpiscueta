"""Batch A (s01-s11): empires, the book, the lecturer, the explorer, Nietzsche, the scriptorium,
the Christmas tree, the broken statue, the marching columns and the raft.

Original designs only, built from engine.figures presets. Captions are Spanish CAPS.
"""
import math
import random

import cairo

from engine import figures as F
from engine.kit import (FONT_CAPS, FONT_TITLE, H, W, at, bg_studio, blade, camera, caption_tag, circle_pts, clip,
                        clamp, cel, col, ease_back, ease_in, ease_io, ease_out, fillp, glow, hatch, hud, lerp,
                        lerp2, lingrad, mix, particles, poly, setc, shape, ss, stroke, text, ui_glyphs, win)
from . import scene

PARCH = mix("gold_l", "white", 0.4)


# ================================================================ shared helpers
def _xf(pts, cx, cy, a=0.0, dx=0.0, dy=0.0):
    """Rotate pts about (cx, cy) by a, then translate by (dx, dy)."""
    ca, sa = math.cos(a), math.sin(a)
    out = []
    for x, y in pts:
        x0, y0 = x - cx, y - cy
        out.append((cx + dx + x0 * ca - y0 * sa, cy + dy + x0 * sa + y0 * ca))
    return out


def _night(ctx, t, seed, glow_xy=None, glow_c="teal_d", glow_a=0.2, top="ink", bot="night", stars=0):
    """Plain dark gradient backdrop with an optional light pool and a few stars."""
    ctx.set_source(lingrad(ctx, 0, 0, 0, H, [(0, top), (1, bot)]))
    ctx.paint()
    if glow_xy is not None:
        gx, gy = glow_xy
        c = col(glow_c)
        g = cairo.RadialGradient(gx, gy, 10, gx, gy, W * 0.65)
        g.add_color_stop_rgba(0, c[0], c[1], c[2], glow_a)
        g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
        ctx.set_source(g)
        ctx.paint()
    rng = random.Random(seed)
    for i in range(stars):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.6)
        r = rng.uniform(1.0, 2.2)
        setc(ctx, "g0", 0.25 + 0.25 * math.sin(t * 1.7 + i))
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.fill()


def _burst(ctx, x, y, age, seed, n=14, spread=200, color="g3", life=3.2):
    """Dust cloud that bursts out of (x, y) and thins away."""
    if age <= 0 or age > life:
        return
    rng = random.Random(seed)
    k = ease_out(age, 2)
    fade = 1 - ss(win(age, 1.6, life))
    for _ in range(n):
        a = rng.uniform(math.pi, 2 * math.pi)
        d = spread * rng.uniform(0.3, 1.0) * k
        r = rng.uniform(22, 56) * (0.5 + 0.6 * k)
        px = x + math.cos(a) * d
        py = y + math.sin(a) * d * 0.4 - 30 * age
        setc(ctx, color, 0.42 * fade)
        ctx.arc(px, py, r, 0, 2 * math.pi)
        ctx.fill()


def _drop(pts, tau, ground, spin, g=1100.0):
    """A rigid piece falling under gravity; it stops when its bottom reaches the ground line."""
    bottom = max(y for _, y in pts)
    drop = min(0.5 * g * tau * tau, max(0.0, ground - bottom))
    cx = sum(x for x, _ in pts) / len(pts)
    cy = sum(y for _, y in pts) / len(pts)
    return _xf(pts, cx, cy, spin * min(1.0, tau), 0.0, drop)


def _building(ctx, t, tc, pieces, bx, by, s, seed, fill="g5"):
    """Pieces stand still until the crumble time tc, then the top ones fall first and land as rubble."""
    rng = random.Random(seed)
    for i, loc in enumerate(pieces):
        wp = [(bx + x * s, by + y * s) for x, y in loc]
        ymid = sum(y for _, y in loc) / len(loc)
        delay = rng.uniform(0.0, 0.5) + 0.8 * (1.0 - min(1.0, -ymid / 380.0))
        spin = rng.uniform(-0.9, 0.9)
        tau = (t - tc) - delay
        pts = _drop(wp, tau, by, spin) if tau > 0 else wp
        shape(ctx, pts, fill, 4.0, seed=seed * 10 + i)


def _lens_pts(R, m, n=72):
    """Circle (m=0) morphing into an almond eye (m=1); same point count so it can animate."""
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        cxp, cyp = R * math.cos(a), R * math.sin(a)
        ax, ay = R * math.cos(a), 0.62 * R * math.sin(a) * abs(math.sin(a))
        out.append((lerp(cxp, ax, m), lerp(cyp, ay, m)))
    return out


# ================================================================ s01 empires_fall
def _castle():
    pcs = [
        [(-200, -170), (200, -170), (200, 0), (-200, 0)],
        [(-260, -262), (-180, -262), (-180, 0), (-260, 0)],
        [(180, -262), (260, -262), (260, 0), (180, 0)],
        [(-72, -300), (72, -300), (72, 0), (-72, 0)],
    ]
    for i in range(5):
        x = -200 + i * 80
        pcs.append([(x, -196), (x + 40, -196), (x + 40, -170), (x, -170)])
    return pcs


def _ziggurat():
    return [
        [(-260, -120), (260, -120), (260, 0), (-260, 0)],
        [(-200, -230), (200, -230), (200, -120), (-200, -120)],
        [(-140, -320), (140, -320), (140, -230), (-140, -230)],
        [(-80, -380), (80, -380), (80, -320), (-80, -320)],
        [(-34, -430), (34, -430), (34, -380), (-34, -380)],
    ]


def _temple():
    pcs = [
        [(-270, -40), (270, -40), (270, 0), (-270, 0)],
        [(-250, -62), (250, -62), (250, -40), (-250, -40)],
        [(-270, -214), (270, -214), (270, -200), (-270, -200)],
        [(-260, -200), (260, -200), (0, -290)],
    ]
    for k in range(6):
        x = -200 + k * 80
        pcs.append([(x - 16, -200), (x + 16, -200), (x + 16, -62), (x - 16, -62)])
    return pcs


def _book(ctx, cx, cy, s, t, flip=0.0, reveal=0.0, seed=1, pages=None, cover="red"):
    """Open book, origin at its centre (about 720 units wide at s=1). flip: 0..1 leaf turning.
    reveal: 0..1 progress of handwriting on the two pages."""
    if s <= 0.01:
        return
    pages = pages or "g0"
    with at(ctx, cx, cy, s):
        shape(ctx, [(-352, 22), (-4, 60), (352, 22), (366, 72), (0, 116), (-366, 72)], cover, 7, seed=seed)
        fillp(ctx, [(-340, 66), (0, 104), (340, 66), (0, 96)], mix(cover, "ink", 0.4), alpha=0.7)
        for side in (-1, 1):
            pg = [(side * 14, 60), (side * 318, 14), (side * 332, -150), (side * 36, -122), (side * 6, -70)]
            shape(ctx, pg, pages, 5, seed=seed + side)
            if reveal > 0:
                _page_lines(ctx, side, reveal, seed)
        if flip > 0:
            a = math.pi * ease_io(flip)
            x = math.cos(a) * 300
            lift = math.sin(a) * 130
            leaf = [(0, -70), (x, -150 - lift * 0.7), (x * 1.02, -30 - lift * 0.3), (0, 60)]
            shape(ctx, leaf, "g1" if x > 0 else "g2", 4, seed=seed + 9)
        stroke(ctx, [(0, 62), (0, -72)], 5)


def _page_lines(ctx, side, reveal, seed, n=14):
    """Dozens of wavy ink lines (handwriting) that fill in as reveal grows."""
    rng = random.Random(seed * 7 + (1 if side > 0 else 2))
    for k in range(n):
        y = -112 + k * 9.6
        L = rng.uniform(150, 215) * (1.0 - 0.28 * k / n)
        p = clamp((reveal * (n + 4) - k) / 4.0)
        if p <= 0:
            continue
        pts = []
        for j in range(15):
            u = j / 14 * p
            pts.append((side * (58 + u * L), y + math.sin(u * 11 + k) * 1.6))
        stroke(ctx, pts, 2.4, "ink2", alpha=0.85, taper=(0.02, 0.3), seed=k)


@scene("empires_fall")
def empires_fall(ctx, t, T, seg):
    bg_studio(ctx, t, seed=12, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.07), focus=(W * 0.5, H * 0.55))
    gy = 0.6 * H
    ridge = [(-60, H + 60), (-60, 0.66 * H), (0.1 * W, gy + 6), (0.22 * W, gy + 14), (0.36 * W, gy + 2),
             (0.5 * W, gy + 20), (0.64 * W, gy + 4), (0.8 * W, gy + 10), (0.92 * W, gy + 22),
             (W + 60, 0.66 * H), (W + 60, H + 60)]
    shape(ctx, ridge, mix("night", "g5", 0.5), 5, seed=3)

    tc = (0.10 * T, 0.25 * T, 0.40 * T)
    bxs = (0.19 * W, 0.5 * W, 0.81 * W)
    _building(ctx, t, tc[0], _castle(), bxs[0], gy + 6, 0.85, 1)
    _building(ctx, t, tc[1], _ziggurat(), bxs[1], gy + 14, 1.0, 2, fill="g6")
    _building(ctx, t, tc[2], _temple(), bxs[2], gy + 6, 0.92, 3)
    for i in range(3):
        _burst(ctx, bxs[i], gy - 20, t - tc[i], 31 + i * 7)

    # the book on its pedestal (0.6 T)
    tb = 0.6 * T
    px, py = W * 0.5, H * 0.79
    kp = ease_out(win(t, tb - 0.3, tb + 0.9), 3)
    if kp > 0:
        dy = (1 - kp) * 90
        slab = [(px - 160, py - 66 + dy), (px + 160, py - 66 + dy), (px + 160, py - 44 + dy), (px - 160, py - 44 + dy)]
        stem = [(px - 112, py - 44 + dy), (px + 112, py - 44 + dy), (px + 128, py + dy), (px - 128, py + dy)]
        shape(ctx, stem, "g3", 5, seed=8)
        cel(ctx, stem, [(px + 20, py - 60 + dy), (px + 200, py - 60 + dy), (px + 200, py + 10 + dy),
                        (px + 20, py + 10 + dy)], "g5")
        shape(ctx, slab, "g2", 5, seed=9)

    kb = ease_back(win(t, tb, tb + 1.2), 2.0)
    ka = ss(win(t, tb, tb + 1.6))
    if ka > 0:
        bcx, bcy = px, py - 96
        glow(ctx, bcx, bcy, 640, "gold_l", 0.55 * ka)
        for i in range(14):
            a = i * (2 * math.pi / 14) + t * 0.05
            L = 1600
            ray = [(bcx, bcy), (bcx + math.cos(a - 0.05) * L, bcy + math.sin(a - 0.05) * L),
                   (bcx + math.cos(a + 0.05) * L, bcy + math.sin(a + 0.05) * L)]
            fillp(ctx, ray, "gold_l", alpha=0.07 * ka)
        _book(ctx, bcx, bcy, 0.48 * max(kb, 0.02), t, seed=21, pages=mix("g0", "gold_l", 0.45), cover="red_d")

    particles(ctx, t, 36, seed=9, color="g3", region=(0, H * 0.45, W, H), speed=(10, -8), size=(2, 5), alpha=0.22)
    ui_glyphs(ctx, t, seed=2, n=5, alpha=0.6)


# ================================================================ s02 book_glow
SCRIBES = [
    # (edge, position along edge, hand colour, sleeve colour)
    ("L", 0.30, "skin", "coat"),
    ("R", 0.36, "skin2", "rust_d"),
    ("B", 0.32, "g4", "g6"),
    ("L", 0.62, "skin_s", "violet"),
    ("R", 0.66, "skin2", "cobalt_d"),
    ("B", 0.70, "gold_d", "g5"),
    ("R", 0.22, "skin", "steel_d"),
]


def _scribe(ctx, t, T, i, book_cx, book_cy, s):
    edge, pos, hcol, scol = SCRIBES[i]
    if edge == "L":
        start = (-140, H * pos)
    elif edge == "R":
        start = (W + 140, H * pos)
    else:
        start = (W * pos, H + 140)
    side = -1 if i % 2 else 1
    frac = (i * 0.37) % 1.0
    lx = side * (100 + 120 * frac)
    ly = -100 + 70 * ((i * 0.53) % 1.0)
    target = (book_cx + lx * s, book_cy + ly * s)
    ta = T * (0.04 + 0.085 * i)
    r = min(ss(win(t, ta, ta + 0.9)), 1 - ss(win(t, ta + 1.5, ta + 2.2)))
    if r <= 0.01:
        return
    wig = math.sin(t * 12 + i) * 6 * r
    hand = (lerp(start[0], target[0], r) + wig, lerp(start[1], target[1], r))
    sh = (start[0] + (W * 0.5 - start[0]) * 0.2, start[1] + (H * 0.5 - start[1]) * 0.2)
    el = ((sh[0] + hand[0]) / 2 + 40, (sh[1] + hand[1]) / 2 - 60)
    F.limb(ctx, sh, el, hand, 74, 56, scol, mix(scol, "ink", 0.3), 5, seed=i + 3)
    ang = math.atan2(target[1] - hand[1], target[0] - hand[0])
    F.hand(ctx, hand[0], hand[1], a=ang, s=1.25, color=hcol, kind="point")


@scene("book_glow")
def book_glow(ctx, t, T, seg):
    _night(ctx, t, 21, glow_xy=(W * 0.5, H * 0.5), glow_c="red_l", glow_a=0.22, top="ink", bot="night")
    camera(ctx, t, T, zoom=(1.0, 1.1), focus=(W * 0.5, H * 0.5))
    bx, by, bs = W * 0.5, H * 0.5 + 20, 1.32
    glow(ctx, bx, by, 760, "red_l", 0.22)
    flip = 0.5 + 0.5 * math.sin(t * 0.9)
    flip = ss(clamp((flip - 0.55) / 0.45))
    reveal = win(t, 0.0, T * 0.66)
    _book(ctx, bx, by, bs, t, flip=flip, reveal=reveal, seed=5, cover="red")
    for i in range(len(SCRIBES)):
        _scribe(ctx, t, T, i, bx, by, bs)

    kd = ss(win(t, T * 0.66, T * 0.74))
    if kd > 0:
        with hud(ctx):
            setc(ctx, "ink", 0.62 * kd)
            ctx.paint()
    kt = ease_out(win(t, T * 0.7, T * 0.78), 3)
    if kt > 0:
        with hud(ctx):
            dy = (1 - kt) * 40
            text(ctx, "¿POR QUÉ?", W / 2 + 10, H / 2 + 100 + dy, 210, FONT_TITLE, "red", tracking=0.04, alpha=kt)
            text(ctx, "¿POR QUÉ?", W / 2, H / 2 + 90 + dy, 210, FONT_TITLE, "g0", tracking=0.04, alpha=kt)
    ui_glyphs(ctx, t, seed=6, n=6, alpha=0.7)


# ================================================================ s04 lecturer
def _back_head(ctx, x, y, r, t, seed, c="ink"):
    """Back-of-head silhouette with shoulders, lit by a teal rim on the top-left."""
    y += math.sin(t * 1.1 + seed) * 3
    shape(ctx, [(x - 2.9 * r, y + 4.2 * r), (x - 1.9 * r, y + 1.2 * r), (x, y + 0.9 * r),
                (x + 1.9 * r, y + 1.2 * r), (x + 2.9 * r, y + 4.2 * r)], c, 5, seed=seed)
    fillp(ctx, [(x - 0.42 * r, y + 0.7 * r), (x + 0.42 * r, y + 0.7 * r), (x + 0.4 * r, y + 1.5 * r),
                (x - 0.4 * r, y + 1.5 * r)], c)
    shape(ctx, circle_pts(x, y, r, 26, ry=r * 1.12), c, 5, seed=seed + 1)
    arc = [(x + r * math.cos(a), y + r * 1.12 * math.sin(a))
           for a in [math.pi * (1.05 + 0.4 * k / 8) for k in range(9)]]
    stroke(ctx, arc, 4, "teal", alpha=0.6, taper=(0.3, 0.3), seed=seed)


@scene("lecturer")
def lecturer(ctx, t, T, seg):
    _night(ctx, t, 41, glow_xy=(W * 0.5, H * 0.3), glow_c="gold", glow_a=0.12, top="ink", bot="night")
    camera(ctx, t, T, zoom=(1.0, 1.07), focus=(W * 0.5, H * 0.7))
    # stage floor
    fillp(ctx, [(-60, H * 0.74), (W + 60, H * 0.74), (W + 200, H + 60), (-200, H + 60)], mix("ink", "g6", 0.35))
    stroke(ctx, [(-60, H * 0.74), (W + 60, H * 0.74)], 4, "g5", alpha=0.6)
    # big screen with an old map and a question mark
    sx0, sx1, sy0, sy1 = W * 0.5 - 520, W * 0.5 + 520, H * 0.1, H * 0.56
    frame = [(sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1)]
    glow(ctx, W * 0.5, (sy0 + sy1) / 2, 700, "gold", 0.10)
    shape(ctx, frame, "ink2", 9, seed=2)
    with clip(ctx, frame):
        fillp(ctx, frame, PARCH)
        rng = random.Random(4)
        for cx_, cy_, r_ in ((sx0 + 280, sy0 + 190, 110), (sx0 + 600, sy0 + 150, 140), (sx0 + 780, sy0 + 330, 90),
                             (sx0 + 150, sy0 + 380, 60)):
            pts = [(cx_ + r_ * (0.85 + 0.25 * rng.random()) * math.cos(a),
                    cy_ + r_ * 0.7 * (0.85 + 0.25 * rng.random()) * math.sin(a))
                   for a in [2 * math.pi * k / 12 for k in range(12)]]
            shape(ctx, pts, "rust", 3, smooth=True, seed=int(cx_), alpha=0.45)
        for gx in range(1, 6):
            stroke(ctx, [(sx0 + gx * 170, sy0), (sx0 + gx * 170 + 20, sy1)], 2, "g4", alpha=0.2, taper=(0, 0))
        route = []
        for k in range(22):
            u = k / 21
            route.append((sx0 + 120 + 700 * u, sy0 + 380 - 260 * u + 90 * math.sin(u * math.pi)))
        seen = int(win(t, T * 0.1, T * 0.6) * 22)
        for k, (x_, y_) in enumerate(route):
            if k <= seen:
                fillp(ctx, circle_pts(x_, y_, 5, 8), "red", alpha=0.85)
        qa = 0.85 + 0.15 * math.sin(t * 2.0)
        text(ctx, "?", sx0 + 700, sy1 - 40, 360, FONT_TITLE, "red_d", alpha=qa)
    # spotlight from above
    cone = [(W * 0.5 - 40, -40), (W * 0.5 + 40, -40), (W * 0.5 + 340, H * 0.8), (W * 0.5 - 340, H * 0.8)]
    ctx.set_source(lingrad(ctx, 0, 0, 0, H * 0.8, [(0, (1, 1, 0.95, 0.28)), (1, (1, 1, 0.95, 0.03))]))
    poly(ctx, cone)
    ctx.fill()
    # back-row heads (darker, further)
    for x, r in ((0.34 * W, 46), (0.66 * W, 50)):
        _back_head(ctx, x, H * 0.9, r, t, int(x), c="g6")
    # lecturer, seen small and back-lit
    lx, ly, lh = W * 0.5, H * 0.8, 330
    glow(ctx, lx, ly - 230, 230, "gold_l", 0.45)
    F.person(ctx, lx, ly, h=lh, color=F.LECTURER["coat"], shade=None, pose="stand", t=t, fx=1,
             head_c=F.LECTURER["skin"], ink=4.5, seed=2)
    s = lh / 300.0
    with at(ctx, lx, ly, s):
        shape(ctx, [(-34, -292), (-32, -320), (-8, -336), (20, -332), (36, -308), (34, -288), (16, -300),
                    (-8, -306), (-24, -296)], F.LECTURER["hair_c"], 3.5, seed=5)
        shape(ctx, [(-44, -150), (44, -150), (38, -40), (-38, -40)], "g6", 4.5, seed=6)
        fillp(ctx, [(-44, -150), (44, -150), (44, -144), (-44, -144)], "gold_l", alpha=0.7)
    # foreground back-of-head silhouettes
    _back_head(ctx, 0.11 * W, H * 0.98, 80, t, 11)
    _back_head(ctx, 0.25 * W, H * 1.02, 88, t, 12)
    _back_head(ctx, 0.76 * W, H * 1.0, 84, t, 13)
    _back_head(ctx, 0.9 * W, H * 0.95, 76, t, 14)
    caption_tag(ctx, "TORONTO · 2017", 100, 110, t, 40, appear=0.8)
    ui_glyphs(ctx, t, seed=8, n=6)


# ================================================================ s05 explorer_map
def _badge(ctx, x, y, on, color, glyph, label, seed):
    k = on
    if k > 0.01:
        glow(ctx, x, y, 150, color, 0.55 * k)
    shape(ctx, circle_pts(x, y, 58, 8, a0=math.pi / 8), mix("g3", color, k), 4.5, seed=seed)
    gcol = mix("ink", "white", k)
    with at(ctx, x, y, 1.0):
        if glyph == "tri":
            shape(ctx, [(0, -26), (26, 18), (-26, 18)], gcol, 3, seed=seed + 1)
        elif glyph == "leaf":
            shape(ctx, blade((-24, 20), (26, -22), 18, bend=0.15), gcol, 3, seed=seed + 1)
        else:
            sp = [(math.cos(a) * (3 + a * 2.2), math.sin(a) * (3 + a * 2.2))
                  for a in [3 * math.pi * k2 / 40 for k2 in range(41)]]
            stroke(ctx, sp, 4.5, gcol, taper=(0.05, 0.1), seed=seed)
    text(ctx, label, x, y + 98, 30, FONT_CAPS, "ink", tracking=0.12, alpha=0.45 + 0.55 * k)


@scene("explorer_map")
def explorer_map(ctx, t, T, seg):
    bg_studio(ctx, t, seed=52, tone=0.15)
    camera(ctx, t, T, zoom=(1.0, 1.05), focus=(W * 0.6, H * 0.5))
    MX, MY = W * 0.6, H * 0.48
    glow(ctx, MX, MY, 780, "gold_l", 0.45)

    rel = [(-390, -200), (-240, -262), (10, -240), (260, -272), (400, -150), (384, 60), (410, 200), (200, 262),
           (-60, 240), (-300, 272), (-398, 120), (-372, -40)]
    mp = [(MX + x, MY + y) for x, y in rel]
    shape(ctx, mp, PARCH, 6, smooth=True, seed=4)
    with clip(ctx, mp, smooth=True):
        for gx in (-300, -150, 0, 150, 300):
            stroke(ctx, [(MX + gx, MY - 280), (MX + gx * 0.98, MY + 280)], 2, "g5", alpha=0.14, taper=(0, 0))
        rng = random.Random(9)
        for cx_, cy_, r_ in ((-220, -90, 92), (-40, -130, 70), (130, 20, 108), (-170, 120, 62)):
            pts = [(MX + cx_ + r_ * (0.85 + 0.3 * rng.random()) * math.cos(a),
                    MY + cy_ + r_ * 0.72 * (0.85 + 0.3 * rng.random()) * math.sin(a))
                   for a in [2 * math.pi * k / 12 for k in range(12)]]
            shape(ctx, pts, "rust", 3, smooth=True, seed=int(cx_ + 500), alpha=0.42)
        # the unlabelled misty region on the right edge: dark, drifting, no name
        mcx, mcy = MX + 262, MY + 10
        for i in range(16):
            ang = i * 2.4 + 0.3 * math.sin(t * 0.3 + i)
            d = 30 + 60 * ((i * 37) % 7) / 7.0
            r_ = 40 + 50 * ((i * 53) % 5) / 5.0
            fillp(ctx, circle_pts(mcx + math.cos(ang) * d, mcy + math.sin(ang) * d * 0.7 +
                                  math.sin(t * 0.5 + i) * 8, r_, 12), "g4", alpha=0.16)
        fillp(ctx, circle_pts(mcx, mcy, 95, 22, ry=120), "ink", alpha=0.42)
        fillp(ctx, circle_pts(mcx - 20, mcy + 10, 60, 18), "ink", alpha=0.3)

    # the route the explorer has traced so far
    seen = win(t, T * 0.08, T * 0.6)
    for k in range(20):
        u = k / 19
        x_ = MX - 300 + 600 * u
        y_ = MY + 140 - 200 * u + 60 * math.sin(u * math.pi)
        if u <= seen:
            fillp(ctx, circle_pts(x_, y_, 5, 8), "red", alpha=0.85)

    # icons light up in sequence
    icons = [
        ("RAZÓN", (MX - 290, 170), "teal", "tri", 0.22, (MX - 200, MY - 230)),
        ("BIOLOGÍA", (MX + 470, MY + 10), "gold", "leaf", 0.42, (MX + 390, MY + 10)),
        ("EVOLUCIÓN", (MX - 10, MY + 410), "red_l", "spiral", 0.62, (MX - 20, MY + 250)),
    ]
    for i, (label, (ix, iy), colr, glyph, f, edge) in enumerate(icons):
        on = ss(win(t, T * f, T * f + 0.35))
        for j in range(10):
            u0, u1 = j / 10, (j + 0.5) / 10
            p0 = lerp2((ix, iy), edge, u0)
            p1 = lerp2((ix, iy), edge, u1)
            stroke(ctx, [p0, p1], 3, colr if on > 0.5 else "g4", alpha=0.25 + 0.6 * on, taper=(0, 0), seed=j)
        _badge(ctx, ix, iy, on, colr, glyph, label, seed=30 + i)

    # the explorer: HERO bust, arm and magnifying lens
    F.character(ctx, 500, 430, 0.8, F.HERO, "neutral", t, look=0.8, tilt=0.03)
    sh = (614, 622)
    el = (770, 700)
    wr = (930, 585)
    F.limb(ctx, sh, el, wr, 58, 44, F.HERO["coat"], F.HERO["coat_s"], 5, seed=2)
    lens = (1040, 470)
    R = 92
    stroke(ctx, [(lens[0] - 64, lens[1] + 64), (wr[0] + 6, wr[1] - 6)], 26, "rust_d", taper=(0, 0))
    shape(ctx, circle_pts(lens[0], lens[1], R, 36), "steel_l", 6, seed=6)
    inner = circle_pts(lens[0], lens[1], R - 14, 36)
    with clip(ctx, inner):
        fillp(ctx, inner, mix(PARCH, "gold", 0.15))
        shape(ctx, [(lens[0] - 20 + 1.9 * 50 * math.cos(a) * 0.5, lens[1] - 10 + 1.9 * 50 * math.sin(a) * 0.4)
                    for a in [2 * math.pi * k / 10 for k in range(10)]],
              "rust", 2, smooth=True, seed=77, alpha=0.5)
        for k in range(6):
            fillp(ctx, circle_pts(lens[0] - 30 + 22 * k, lens[1] + 20 - 6 * (k % 3), 4, 8), "teal", alpha=0.9)
        glow(ctx, lens[0] - 20, lens[1] - 10, 90, "white", 0.45)
    stroke(ctx, circle_pts(lens[0], lens[1], R - 6, 40), 4, "ink2", closed=True, alpha=0.6)
    stroke(ctx, [(lens[0] - 60, lens[1] - 36), (lens[0] - 30, lens[1] - 62)], 6, "white", alpha=0.7,
           taper=(0.2, 0.2))
    F.hand(ctx, wr[0], wr[1], a=-0.6, s=1.3, color="ink2", kind="fist")
    ui_glyphs(ctx, t, seed=12, n=5, alpha=0.6)


# ================================================================ s06 nietzsche
def _red_bg(ctx, t, seed):
    ctx.set_source(lingrad(ctx, 0, 0, 0, H, [(0, mix("red_d", "ink", 0.2)), (0.6, mix("red_d", "ink", 0.6)),
                                             (1, "ink")]))
    ctx.paint()
    c = col("red_l")
    g = cairo.RadialGradient(W * 0.45, H * 0.34, 40, W * 0.45, H * 0.34, W * 0.7)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], 0.28)
    g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    ctx.set_source(g)
    ctx.paint()
    rng = random.Random(seed)
    for i in range(4):
        x0 = rng.uniform(-200, W * 0.6)
        y0 = rng.uniform(H * 0.1, H * 0.45)
        w = rng.uniform(700, 1200)
        h = rng.uniform(200, 380)
        pts = [(x0, y0 + h), (x0 + w * 0.2, y0 + rng.uniform(0, 50)), (x0 + w * 0.6, y0 - rng.uniform(10, 80)),
               (x0 + w, y0 + rng.uniform(20, 90)), (x0 + w * 1.05, y0 + h)]
        fillp(ctx, pts, mix("red", "ink", 0.5) if i % 2 else mix("red_d", "ink", 0.3), alpha=0.5)
    for i in range(10):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H * 0.6)
        stroke(ctx, [(x, y), (x + rng.uniform(40, 130), y + rng.uniform(-10, 10))], 1.6, "red_l", alpha=0.18,
               taper=(0.5, 0.5), seed=i)


def _mountains(ctx, t):
    pts = [(-60, H + 60), (-60, 0.8 * H), (0.08 * W, 0.66 * H), (0.18 * W, 0.74 * H), (0.3 * W, 0.58 * H),
           (0.4 * W, 0.7 * H), (0.52 * W, 0.6 * H), (0.64 * W, 0.76 * H), (0.78 * W, 0.64 * H),
           (0.9 * W, 0.74 * H), (W + 60, 0.7 * H), (W + 60, H + 60)]
    shape(ctx, pts, mix("red_d", "ink", 0.55), 5, seed=7)
    for px, py, hw in ((0.3 * W, 0.58 * H, 70), (0.52 * W, 0.6 * H, 60), (0.78 * W, 0.64 * H, 60)):
        shape(ctx, [(px - hw, py + 46), (px, py), (px + hw, py + 46), (px + hw * 0.4, py + 40), (px, py + 56),
                    (px - hw * 0.5, py + 40)], "g1", 3, seed=int(px), alpha=0.6)


def _telescope(ctx, x, y, a):
    with at(ctx, x, y, 1.0, a):
        shape(ctx, [(-120, -20), (120, -20), (120, 20), (-120, 20)], "steel_l", 5, seed=3)
        shape(ctx, [(-158, -12), (-120, -28), (-120, 28), (-158, 12)], "steel_d", 4, seed=4)
        for xx in (-50, 40):
            fillp(ctx, [(xx, -25), (xx + 12, -25), (xx + 12, 25), (xx, 25)], "steel_d")
        shape(ctx, [(120, -28), (136, -32), (136, 32), (120, 28)], "teal_l", 4, seed=5)


@scene("nietzsche")
def nietzsche(ctx, t, T, seg):
    _red_bg(ctx, t, seed=61)
    camera(ctx, t, T, zoom=(1.0, 1.08), focus=(W * 0.45, H * 0.4), shake=0.8)
    _mountains(ctx, t)
    F.character(ctx, W * 0.44, H * 0.36, 0.95, F.NIETZSCHE, "grim", t, look=-0.3, tilt=-0.02)

    # the cross of light and the telescope rising out of it (LA CIENCIA)
    kc = ss(win(t, T * 0.55, T * 0.68))
    if kc > 0:
        cx_, cy_ = W * 0.8, H * 0.6
        glow(ctx, cx_, cy_, 320, "gold", 0.5 * kc)
        bar_c = (1.0, 0.85, 0.5, 0.85 * kc)
        fillp(ctx, [(cx_ - 14, cy_ - 130), (cx_ + 14, cy_ - 130), (cx_ + 14, cy_ + 130), (cx_ - 14, cy_ + 130)],
              bar_c)
        fillp(ctx, [(cx_ - 130, cy_ - 14), (cx_ + 130, cy_ - 14), (cx_ + 130, cy_ + 14), (cx_ - 130, cy_ + 14)],
              bar_c)
        rise = ease_out(win(t, T * 0.62, T * 0.88), 2)
        _telescope(ctx, cx_ + 10, cy_ - 30 - rise * 170, -0.6)
    caption_tag(ctx, "FRIEDRICH NIETZSCHE · 1844–1900", 100, H * 0.84, t, 34, accent="gold", appear=0.4)
    caption_tag(ctx, "LA CIENCIA", W * 0.8 - 130, H * 0.8, t, 34, accent="teal", appear=T * 0.8)
    ui_glyphs(ctx, t, seed=14, n=6, alpha=0.7)


# ================================================================ s07 scribes
def _arch(ctx, x0, y0, w, h, t, k):
    pts = [(x0, y0 + h), (x0, y0 + w / 2)]
    for j in range(13):
        a = math.pi + math.pi * j / 12
        pts.append((x0 + w / 2 + w / 2 * math.cos(a), y0 + w / 2 + w / 2 * math.sin(a)))
    pts.append((x0 + w, y0 + h))
    shape(ctx, pts, "g4", 4, seed=k, alpha=0.35)
    flick = 0.8 + 0.2 * math.sin(t * 1.3 + k)
    fillp(ctx, [(x0, y0 + h), (x0 + w, y0 + h), (x0 + w * 2.4, H * 0.92), (x0 - w * 1.0, H * 0.92)],
          "gold_l", alpha=0.07 * flick)


def _monk(ctx, x, feet, h, t, fx, seed, robe):
    s = h / 300.0
    F.person(ctx, x, feet, h=h, color=robe, shade=mix(robe, "ink", 0.45), pose="kneel", t=t, fx=fx,
             head_c="skin2", ink=3.5, seed=seed)
    with at(ctx, x, feet, s, fx=fx):
        shape(ctx, [(-44, -226), (-40, -270), (-18, -312), (6, -322), (30, -300), (44, -258), (40, -226),
                    (0, -212)], mix(robe, "ink", 0.35), 3.5, seed=seed + 2)
        fillp(ctx, circle_pts(4, -256, 16, 12, ry=20), "ink", alpha=0.8)


def _writer(ctx, t, x, feet, h, seed, robe, fx=1):
    s = h / 300.0
    _monk(ctx, x, feet, h, t, fx, seed, robe)
    dy = feet - 0.44 * h
    w = 220 * s
    top = [(x - w / 2, dy), (x + w / 2, dy), (x + w / 2 + 14 * s, dy + 26 * s), (x - w / 2 - 14 * s, dy + 26 * s)]
    shape(ctx, top, mix("rust_d", "ink", 0.2), 4, seed=seed + 5)
    fillp(ctx, [(x - w / 2 - 14 * s, dy + 26 * s), (x + w / 2 + 14 * s, dy + 26 * s),
                (x + w / 2 + 14 * s, feet + 6), (x - w / 2 - 14 * s, feet + 6)], mix("rust_d", "ink", 0.5))
    px0, px1 = x - w * 0.38, x + w * 0.3
    py0, py1 = dy - 56 * s, dy - 6 * s
    shape(ctx, [(px0, py0), (px1, py0 - 4 * s), (px1 + 4 * s, py1), (px0 - 2 * s, py1 + 2 * s)], PARCH, 3,
          seed=seed + 3)
    phase = (t * 0.22 + seed * 0.37) % 1.0
    rowh = (py1 - py0) / 6.0
    for k in range(5):
        ly = py0 + (k + 1) * rowh
        L = (px1 - px0 - 16 * s) * clamp(phase * 6 - k)
        if L > 2:
            stroke(ctx, [(px0 + 8 * s, ly), (px0 + 8 * s + L * 0.5, ly + 2 * s), (px0 + 8 * s + L, ly)],
                   2.2 * s + 0.6, "ink2", alpha=0.85, taper=(0.05, 0.3), seed=k)
    kc = min(4, int(phase * 6))
    frac = phase * 6 - kc
    hx = px0 + 8 * s + frac * (px1 - px0 - 16 * s)
    hy = py0 + (kc + 1) * rowh - 8 * s
    stroke(ctx, [(hx, hy), (hx + 26 * s, hy - 58 * s)], 3 * s, "ink2", taper=(0, 0.4))
    F.hand(ctx, hx, hy, a=-0.35, s=1.0 * s + 0.1, color="skin2", kind="point")


def _lens_morph_diagram(ctx, t, T, cx, cy, R=210):
    m = ss(win(t, T * 0.6, T * 0.82))
    turn = math.pi * ss(win(t, T * 0.8, T * 0.96))
    sx = math.cos(turn)
    look = ss(win(t, T * 0.9, T * 0.99))
    if abs(sx) < 0.03:
        sx = 0.03 if sx >= 0 else -0.03
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(sx, 1.0)
    for k in range(24):
        if m >= 0.98:
            break
        a = k * 2 * math.pi / 24 + t * 0.12
        stroke(ctx, [(math.cos(a) * R * 0.86, math.sin(a) * R * 0.86),
                     (math.cos(a) * R * 0.97, math.sin(a) * R * 0.97)], 4, "gold_l", taper=(0, 0),
               alpha=0.8 * (1 - m))
    shape(ctx, _lens_pts(R, m), "ink2", 9, ink_color="gold", seed=5)
    for i, rr in enumerate((0.8, 0.6, 0.4)):
        r = lerp(R * rr, R * 0.42, m)
        stroke(ctx, circle_pts(0, 0, r, 48), 5 - i, "teal" if i % 2 == 0 else "gold_l", closed=True,
               alpha=0.9 - 0.3 * m)
    py = lerp(0.0, R * 0.22, look)
    fillp(ctx, circle_pts(0, py, R * 0.42, 28), "teal", alpha=m)
    fillp(ctx, circle_pts(0, py, R * 0.16, 16), "ink", alpha=m)
    fillp(ctx, circle_pts(-R * 0.1 + 0, py - R * 0.14, R * 0.05, 8), "white", alpha=m * 0.8)
    hk = ss(win(t, T * 0.84, T * 0.95))
    if hk > 0:
        stroke(ctx, [(R * 0.66, R * 0.66), (R * 0.66 + R * 0.9 * hk, R * 0.66 + R * 0.9 * hk)], 26, "steel_d",
               taper=(0.05, 0.05))
    ctx.restore()


def _monk_row(ctx, t, feet, h, xs, seed0, robe):
    for i, x in enumerate(xs):
        _writer(ctx, t, x * W, feet, h, seed0 + i, robe, fx=1 if i % 2 == 0 else -1)


@scene("scribes")
def scribes(ctx, t, T, seg):
    _night(ctx, t, 71, glow_xy=(W * 0.5, H * 0.2), glow_c="gold", glow_a=0.16, top="ink2", bot="night")
    camera(ctx, t, T, zoom=(1.0, 1.06), pan=((0, 0), (-30, -10)), focus=(W * 0.5, H * 0.5))
    for i, x in enumerate((0.16, 0.5, 0.84)):
        _arch(ctx, x * W - 90, 0.04 * H, 180, 0.4 * H, t, i)
    _lens_morph_diagram(ctx, t, T, W * 0.5, H * 0.25)
    _monk_row(ctx, t, 0.6 * H, 270, (0.12, 0.34, 0.56, 0.78, 0.96), 40, "g5")
    _monk_row(ctx, t, H * 1.02, 390, (0.2, 0.5, 0.82), 60, "g6")
    caption_tag(ctx, "MIL AÑOS", 100, 110, t, 44, accent="red", appear=0.6)
    ui_glyphs(ctx, t, seed=16, n=5, alpha=0.6)


# ================================================================ s08 xmas_tree
TREE_CX, TREE_BASE = 1420, 1000
TIERS = [(-700, -430, 150), (-560, -270, 235), (-400, -120, 305), (-250, 0, 370)]


def _tier(cx, base, ap, bt, hw, n=3):
    right = []
    for j in range(1, n + 1):
        f = j / (n + 1)
        right.append((cx + hw * f * (0.8 if j % 2 else 1.0), base + lerp(ap, bt, f)))
    right.append((cx + hw, base + bt))
    left = [(2 * cx - x, y) for x, y in reversed(right)]
    return [(cx, base + ap)] + right + left


def _tree(ctx, t):
    cx, base = TREE_CX, TREE_BASE
    shape(ctx, [(cx - 28, base - 6), (cx + 28, base - 6), (cx + 30, base + 70), (cx - 30, base + 70)], "rust_d", 4,
          seed=5)
    for k, (ap, bt, hw) in enumerate(TIERS):
        pts = _tier(cx, base, ap, bt, hw)
        shape(ctx, pts, "teal_d", 5, seed=20 + k)
        cel(ctx, pts, [(cx + 10, base - 800), (cx + 600, base - 800), (cx + 600, base + 200), (cx + 10, base + 200)],
            mix("teal_d", "ink", 0.35))
        hatch(ctx, pts, angle=0.9, gap=18, w=1.3, color="ink", alpha=0.25, seed=k)


def _ornaments():
    rng = random.Random(5)
    out = []
    for i in range(14):
        ap, bt, hw = TIERS[i % len(TIERS)]
        f = 0.3 + 0.55 * rng.random()
        u = rng.uniform(-0.8, 0.8)
        y = TREE_BASE + lerp(ap, bt, f)
        x = TREE_CX + u * hw * f * 0.75
        out.append((x, y, "red_l" if i % 2 == 0 else "gold_l", 16 + rng.random() * 6))
    return out


def _elbow(sh, wr, L1=190.0, L2=190.0):
    """Two-bone arm: clamps the wrist to reach and bends the elbow downward."""
    dx, dy = wr[0] - sh[0], wr[1] - sh[1]
    d0 = max(1e-6, math.hypot(dx, dy))
    ux, uy = dx / d0, dy / d0
    d = max(1.0, min(d0, (L1 + L2) * 0.98))
    wr2 = (sh[0] + ux * d, sh[1] + uy * d)
    along = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
    hgt = math.sqrt(max(0.0, L1 * L1 - along * along))
    px, py = -uy, ux
    if py < 0:
        px, py = -px, -py
    el = (sh[0] + ux * along + px * hgt, sh[1] + uy * along + py * hgt)
    return wr2, el


@scene("xmas_tree")
def xmas_tree(ctx, t, T, seg):
    bg_studio(ctx, t, seed=81, tone=0.3)
    camera(ctx, t, T, zoom=(1.0, 1.06), focus=(W * 0.5, H * 0.5))
    # window with the night snow outside
    x0, y0, ww, wh = 80, 90, 360, 330
    rect = [(x0, y0), (x0 + ww, y0), (x0 + ww, y0 + wh), (x0, y0 + wh)]
    with clip(ctx, rect):
        ctx.set_source(lingrad(ctx, 0, y0, 0, y0 + wh, [(0, mix("cobalt_d", "ink", 0.2)), (1, "ink")]))
        ctx.paint()
        shape(ctx, [(x0 - 10, y0 + wh), (x0 + ww * 0.3, y0 + wh * 0.7), (x0 + ww * 0.7, y0 + wh * 0.8),
                    (x0 + ww + 10, y0 + wh * 0.66), (x0 + ww + 10, y0 + wh + 10), (x0 - 10, y0 + wh + 10)],
              "g0", 3, seed=3)
        particles(ctx, t, 70, seed=4, color="white", region=(x0, y0, x0 + ww, y0 + wh), speed=(-10, 60),
                  size=(1.6, 3.2), alpha=0.9)
    shape(ctx, rect, None, 9)
    stroke(ctx, [(x0 + ww / 2, y0), (x0 + ww / 2, y0 + wh)], 8, "ink")
    stroke(ctx, [(x0, y0 + wh / 2), (x0 + ww, y0 + wh / 2)], 8, "ink")

    # floor and warm light
    fillp(ctx, [(-60, 0.86 * H), (W + 60, 0.86 * H), (W + 60, H + 60), (-60, H + 60)], mix("rust", "g3", 0.55),
          alpha=0.9)
    glow(ctx, 760, 520, 480, "gold_l", 0.35)
    shape(ctx, circle_pts(760, 0.95 * H, 300, 30, ry=48), "red", 4, seed=9, alpha=0.85)

    _tree(ctx, t)

    # ornaments hung one by one; the hand moves to each in turn
    orn = _ornaments()
    places = []
    for i, (ox, oy, colr, r) in enumerate(orn):
        ti = T * (0.14 + i * 0.05)
        places.append((ti, (ox, oy)))
    for i, (ox, oy, colr, r) in enumerate(orn):
        ti = T * (0.14 + i * 0.05)
        k = ease_back(win(t, ti, ti + 0.45), 2.0)
        if k > 0:
            shape(ctx, circle_pts(ox, oy, r * k, 16), colr, 3.5, seed=50 + i)
            fillp(ctx, circle_pts(ox - r * 0.35 * k, oy - r * 0.35 * k, r * 0.26 * k, 8), "g0", alpha=0.8)

    sh_s = 0.8
    hero = (760, 540)
    sh = (hero[0] + 150 * sh_s * 0.95, hero[1] + 240 * sh_s)
    rest = (1000, 800)
    prev = rest
    hand = rest
    for ti, tg in places:
        if t < ti - 0.9:
            hand = prev
            break
        if t < ti:
            hand = lerp2(prev, tg, ss(win(t, ti - 0.9, ti)))
            break
        prev = tg
        hand = tg
    wr, el = _elbow(sh, hand)
    F.limb(ctx, sh, el, wr, 50, 38, F.HERO["coat"], F.HERO["coat_s"], 5, seed=8)

    smile_k = ss(win(t, T * 0.42, T * 0.55))
    expr = "smile" if smile_k < 0.5 else "neutral"
    F.character(ctx, hero[0], hero[1], sh_s, F.HERO, expr, t, tilt=-0.1 * smile_k, look=-0.8 * smile_k)
    F.hand(ctx, wr[0], wr[1], a=0.0, s=0.95, color="ink2", kind="fist")

    # the big question mark floating above
    kq = ss(win(t, T * 0.42, T * 0.55))
    if kq > 0:
        text(ctx, "?", 700, 330 + math.sin(t * 2.0) * 14, 300, FONT_TITLE, "teal_d", alpha=kq)
    ui_glyphs(ctx, t, seed=18, n=5, alpha=0.6)


# ================================================================ s09 broken_statue
def _stone_head(ctx, t, cx, cy, s):
    c = dict(F.SAGE, skin="g3", skin_s="g5", hair_c="g4", hair_s="g5", eye="g6", coat="g5", coat_s="g6")
    with at(ctx, cx, cy, s):
        F.head(ctx, c, "closed", t)


def _banner(ctx, t, x, y, w, h, seed):
    sway = math.sin(t * 2.4 + seed) * 16
    bob = math.sin(t * 6.0 + seed * 0.8) * 8
    y += bob
    pole = [(x, y - 80), (x, y + h + 10)]
    stroke(ctx, pole, 8, "ink", taper=(0, 0))
    pts = [(x - w / 2, y), (x + w / 2 + sway * 0.4, y + 4), (x + w / 2 + sway, y + h),
           (x, y + h - 60), (x - w / 2 + sway * 0.3, y + h)]
    shape(ctx, pts, "red", 5, seed=seed)
    fillp(ctx, [(x - w / 2 + 16, y + 20), (x - w / 2 + 40, y + 20), (x - w / 2 + 40, y + h - 80),
                (x - w / 2 + 16, y + h - 80)], "gold", alpha=0.85)
    shape(ctx, circle_pts(x + sway * 0.3, y + h * 0.4, w * 0.2, 16), None, 4, seed=seed + 2)


@scene("broken_statue")
def broken_statue(ctx, t, T, seg):
    _night(ctx, t, 91, glow_xy=(W * 0.5, H * 0.3), glow_c="g3", glow_a=0.14, top="ink", bot="night")
    camera(ctx, t, T, zoom=(1.0, 1.06), focus=(W * 0.5, H * 0.5))
    cx, cy, s = W * 0.5, H * 0.32, 1.5
    pit = [(0.3 * W, 0.66 * H), (0.7 * W, 0.66 * H), (0.78 * W, H + 60), (0.22 * W, H + 60)]
    ground = [(0, 0.7 * H), (0.3 * W, 0.66 * H), (0.7 * W, 0.66 * H), (W, 0.7 * H), (W, H), (0, H)]
    fillp(ctx, ground, mix("g6", "ink", 0.3))
    stroke(ctx, [(0, 0.7 * H), (0.3 * W, 0.66 * H), (0.7 * W, 0.66 * H), (W, 0.7 * H)], 5, "ink")
    fillp(ctx, pit, "ink")

    # black void on the left
    void = [(-60, -60), (0.3 * W, -60), (0.27 * W, 0.2 * H), (0.33 * W, 0.42 * H), (0.26 * W, 0.62 * H),
            (0.31 * W, 0.8 * H), (0.28 * W, H + 60), (-60, H + 60)]
    fillp(ctx, void, "ink")
    fillp(ctx, [(0, 0), (0.12 * W, 0), (0.1 * W, H), (0, H)], "night", alpha=0.6)
    kn = ss(win(t, T * 0.05, T * 0.2))
    text(ctx, "NIHILISMO", 0.15 * W, 0.44 * H, 64, FONT_CAPS, "g3", tracking=0.18, alpha=kn)

    # statue head: intact, then cracked and split into four shards that fall into the pit
    kc = win(t, T * 0.2, T * 0.25)
    t_cracks = [
        [(cx - 40, cy - 260), (cx - 10, cy - 60), (cx - 50, cy + 40), (cx + 5, cy + 150), (cx - 30, cy + 300)],
        [(cx + 70, cy - 260), (cx + 40, cy - 20), (cx + 95, cy + 120), (cx + 55, cy + 230), (cx + 80, cy + 300)],
    ]
    h_crack = [(cx - 220, cy - 95), (cx - 60, cy - 80), (cx + 20, cy - 120), (cx + 100, cy - 70), (cx + 220, cy - 100)]
    X0, X1, Y0, Y1 = cx - 260, cx + 260, cy - 300, cy + 330
    if t < T * 0.24:
        _stone_head(ctx, t, cx, cy, s)
        if kc > 0:
            for crack in t_cracks + [h_crack]:
                n = max(2, int(len(crack) * kc))
                stroke(ctx, crack[:n], 7, "red_l", taper=(0.2, 0.4), alpha=0.9)
    else:
        left = [(X0 - 40, Y0 - 40)] + t_cracks[0] + [(X0 - 40, Y1 + 40)]
        mid = t_cracks[0] + list(reversed(t_cracks[1]))
        right = t_cracks[1] + [(X1 + 40, Y1 + 40), (X1 + 40, Y0 - 40)]
        crown = [(X0 - 40, Y0 - 40), (X1 + 40, Y0 - 40)] + list(reversed(h_crack))
        lower_clip = h_crack + [(X1 + 40, Y1 + 40), (X0 - 40, Y1 + 40)]
        shards = [(crown, None, 0.24, -0.5, 0.0), (left, lower_clip, 0.245, 0.35, -60.0),
                  (mid, lower_clip, 0.25, -0.2, 20.0), (right, lower_clip, 0.255, 0.5, 70.0)]
        for region, extra, t_rel, spin, dxp in shards:
            tau = t - T * t_rel
            dy = 0.5 * 700 * tau * tau if tau > 0 else 0.0
            ang = spin * max(0.0, tau)
            dx = dxp * max(0.0, tau)
            ctx.save()
            ctx.translate(cx + dx, cy + dy)
            ctx.rotate(ang)
            ctx.translate(-cx, -cy)
            poly(ctx, region)
            ctx.clip()
            if extra is not None:
                poly(ctx, extra)
                ctx.clip()
            _stone_head(ctx, t, cx, cy, s)
            ctx.restore()

    # the chasm swallows the falling pieces
    gpat = lingrad(ctx, 0, 0.66 * H, 0, H, [(0, (0.07, 0.07, 0.1, 0.0)), (1, (0.07, 0.07, 0.1, 1.0))])
    ctx.set_source(gpat)
    poly(ctx, pit)
    ctx.fill()

    # the narrow ridge between the void and the banners, with a small HERO on it
    ridge = [(0.27 * W, 0.7 * H), (0.36 * W, 0.66 * H), (0.5 * W, 0.635 * H), (0.64 * W, 0.66 * H),
             (0.73 * W, 0.7 * H), (0.66 * W, 0.74 * H), (0.5 * W, 0.67 * H), (0.34 * W, 0.74 * H)]
    shape(ctx, ridge, "g5", 5, seed=12)
    F.person(ctx, 0.5 * W, 0.635 * H + 4, h=150, color=F.HERO["coat"], shade=F.HERO["coat_s"], pose="stand",
             t=t, fx=1, head_c=F.HERO["skin"], ink=3.5, seed=4)
    hs = 150 / 300.0
    with at(ctx, 0.5 * W, 0.635 * H + 4, hs):
        for k, a in enumerate((-2.6, -2.0, -1.4)):
            shape(ctx, blade((-14 + k * 14, -282), (-14 + k * 14 + math.cos(a) * 60, -282 + math.sin(a) * 60),
                             18, bend=0.1), "ink2", 3, seed=60 + k)

    # right side: marching red banners
    for i in range(5):
        bx = 0.76 * W + i * 0.055 * W
        _banner(ctx, t, bx, 0.2 * H + (i % 2) * 14, 110, 230, i)
    caption_tag(ctx, "IDEOLOGÍAS", 0.72 * W, 0.1 * H, t, 40, accent="red", appear=T * 0.35)
    ui_glyphs(ctx, t, seed=22, n=6, alpha=0.6)


# ================================================================ s10 marching
def _banner_tall(ctx, t, x, top, w, h, seed):
    sway = math.sin(t * 0.9 + seed) * 12
    pts = [(x - w / 2, top), (x + w / 2, top), (x + w / 2 + sway, top + h), (x, top + h - 46),
           (x - w / 2 + sway * 0.6, top + h)]
    stroke(ctx, [(x - w / 2 - 40, top), (x + w / 2 + 40, top)], 12, "ink", taper=(0, 0))
    shape(ctx, pts, "red_d", 6, seed=seed)
    fillp(ctx, [(x - w / 2 + 22, top + 40), (x - w / 2 + 40, top + 40), (x - w / 2 + 40, top + h - 60),
                (x - w / 2 + 22, top + h - 60)], "red", alpha=0.9)
    shape(ctx, circle_pts(x + sway * 0.3, top + h * 0.4, w * 0.24, 20), None, 8, seed=seed + 3,
          ink_color="gold")
    stroke(ctx, [(x - w * 0.18, top + h * 0.4), (x + w * 0.18, top + h * 0.4)], 8, "gold")


def _row(ctx, t, feet, h, spacing, speed, seed):
    margin = 220
    span = W + 2 * margin
    n = int(span / spacing) + 2
    for i in range(n):
        x = (i * spacing + speed * t) % span - margin
        F.person(ctx, x, feet, h=h, color="g4", pose="walk", t=t, fx=1, seed=seed, ink=4.0)


def _statue(ctx, t, x, feet, s):
    stone, shade = "g3", "g5"
    step = math.sin(t * 3.2)
    tilt = -0.1 + 0.03 * step
    bob = -abs(step) * 12
    c = dict(F.SAGE, skin=stone, skin_s=shade, hair_c="g4", hair_s=shade, eye="g6", coat=stone, coat_s=shade,
             beard="long")
    with at(ctx, x, feet + bob, s, tilt):
        F.limb(ctx, (-58, -380), (-64 + 14 * step, -200), (-54 + 22 * step, -18), 120, 84, stone, shade, 6, seed=5)
        shape(ctx, [(-100, -6), (-14, -6), (-18, 8), (-104, 8)], shade, 4, seed=6)
        shape(ctx, [(40, -390), (126, -390), (116, -322), (102, -318), (92, -296), (70, -304), (58, -270),
                    (46, -300)], stone, 6, seed=7)
        torso = [(-150, -600), (150, -600), (132, -380), (-132, -380)]
        shape(ctx, torso, stone, 6, seed=8)
        cel(ctx, torso, [(20, -610), (170, -610), (170, -370), (20, -370)], shade)
        shape(ctx, [(-44, -650), (44, -650), (42, -596), (-42, -596)], stone, 5, seed=9)
        F.limb(ctx, (-150, -585), (-236, -470), (-196, -356), 92, 72, stone, shade, 6, seed=10)
        shape(ctx, [(138, -628), (206, -606), (190, -580), (214, -556), (150, -546)], stone, 5, seed=11)
        stroke(ctx, [(-30, -560), (8, -510), (-18, -462), (14, -420)], 4, "ink", alpha=0.8)
        stroke(ctx, [(60, -520), (92, -488)], 3, "ink", alpha=0.7)
        with at(ctx, 0, -722, 1.0):
            F.head(ctx, c, "closed", t)


@scene("marching")
def marching(ctx, t, T, seg):
    bg_studio(ctx, t, seed=101, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.05), pan=((0, 0), (-20, 0)), focus=(W * 0.5, H * 0.5))
    for x, sd in ((0.2 * W, 1), (0.5 * W, 2), (0.8 * W, 3)):
        _banner_tall(ctx, t, x, -30, 300, 660, sd)
    _row(ctx, t, 0.55 * H, 120, 92, 70, 0)
    _row(ctx, t, 0.72 * H, 200, 140, 110, 0)
    _statue(ctx, t, 0.8 * W, 0.99 * H, 0.78)
    _row(ctx, t, 0.93 * H, 320, 250, 160, 0)
    caption_tag(ctx, "SIGLO XX", 100, 110, t, 44, accent="red", appear=0.5)
    ui_glyphs(ctx, t, seed=24, n=5, alpha=0.5)


# ================================================================ s11 raft
RAFT_LOGS = (-2.5, -1.5, -0.5, 0.5, 1.5, 2.5)   # log offsets (x = centre + k * 170)


def _capsule(xc, yc, L, R, n=8):
    pts = []
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n
        pts.append((xc + L / 2 + R * math.cos(a), yc + R * math.sin(a)))
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n
        pts.append((xc - L / 2 + R * math.cos(a), yc + R * math.sin(a)))
    return pts


def _lift(s):
    k = clamp(s / 1.6)
    return 980 * ease_in(k, 2), 70 * k


def _raft_hand(t, pulls, yr):
    hover = (W * 0.86, H * 0.16)
    prev = hover
    for tp, xc in pulls:
        g = (xc, yr - 72)
        if t < tp - 1.1:
            return prev
        if t < tp:
            return lerp2(prev, g, ss(win(t, tp - 1.1, tp)))
        s = t - tp
        if s < 1.6:
            ly, dx = _lift(s)
            return (g[0] + dx, g[1] - ly)
        prev = hover
    return prev


def _spray(ctx, x, y, s, seed):
    if s <= 0 or s > 1.2:
        return
    rng = random.Random(seed)
    for _ in range(12):
        a = rng.uniform(-math.pi * 0.9, -math.pi * 0.1)
        d = rng.uniform(40, 150) * s
        setc(ctx, "teal_l", 0.5 * (1 - s / 1.2))
        ctx.arc(x + math.cos(a) * d, y + math.sin(a) * d * 0.6, rng.uniform(3, 7), 0, 2 * math.pi)
        ctx.fill()


@scene("raft")
def raft(ctx, t, T, seg):
    _night(ctx, t, 111, glow_xy=(W * 0.5, H * 0.5), glow_c="teal_d", glow_a=0.26, top="ink", bot="sea", stars=60)
    camera(ctx, t, T, zoom=(1.0, 1.05), focus=(W * 0.5, H * 0.62))
    _sea_band(ctx, t, 0.5 * H, mix("sea", "ink", 0.25), 12, 3)

    # faint glowing serpents beneath the surface
    ctx.push_group()
    F.serpent(ctx, [(-220, 0.93 * H), (0.22 * W, 0.86 * H), (0.4 * W, 0.9 * H)], t, thick=84, body="teal_d",
              belly="teal", spikes_c="ink2", seed=4, wave=10, open_jaw=0.1, ink=4)
    F.serpent(ctx, [(W + 220, 0.97 * H), (0.8 * W, 0.9 * H), (0.62 * W, 0.96 * H)], t + 1.3, thick=70,
              body="teal_d", belly="teal", spikes_c="ink2", seed=9, wave=9, open_jaw=0.1, ink=4)
    grp = ctx.pop_group()
    ctx.set_source(grp)
    ctx.paint_with_alpha(0.32)

    # HERO kneeling on the raft
    F.character(ctx, W * 0.42, 0.36 * H, 0.9, F.HERO, "grim", t, look=0.6, tilt=-0.02)

    # the raft: logs, three of them are pulled out one by one
    yr = 0.66 * H
    pulls = [(T * 0.2, W * 0.5 + 2.5 * 190, "VERDAD"), (T * 0.4, W * 0.5 + 1.5 * 190, "VALORES"),
             (T * 0.6, W * 0.5 + 0.5 * 190, "SENTIDO")]
    for kx in RAFT_LOGS:
        xc = W * 0.5 + kx * 190
        lift_y, dx = 0.0, 0.0
        alpha = 1.0
        lab = None
        for tp, pxc, plab in pulls:
            if abs(pxc - xc) < 1:
                lab = plab
                s_ = t - tp
                if s_ >= 0:
                    lift_y, dx = _lift(s_)
                    alpha = 1 - ss(clamp((s_ - 1.0) / 0.6))
                    _spray(ctx, xc, yr, s_, int(tp))
        if alpha <= 0.01:
            continue
        cx_, cy_ = xc + dx, yr - lift_y
        log = _capsule(cx_, cy_, 290, 66)
        shape(ctx, log, "rust_d", 5, seed=int(kx * 10 + 40), alpha=alpha)
        fillp(ctx, _capsule(cx_, cy_ - 28, 270, 26), "rust", alpha=0.7 * alpha)
        stroke(ctx, circle_pts(cx_ - 145, cy_, 36, 14), 3, "gold_d", closed=True, alpha=0.7 * alpha)
        if lab:
            text(ctx, lab, cx_, cy_ + 14, 40, FONT_CAPS, "g0", tracking=0.12, alpha=alpha)

    # the huge shadowy hand, approaching, grabbing, lifting
    hx, hy = _raft_hand(t, [(tp, pxc) for tp, pxc, _ in pulls], yr)
    shoulder = (W + 200, -200)
    el = ((shoulder[0] + hx) / 2 + 60, (shoulder[1] + hy) / 2 - 40)
    F.limb(ctx, shoulder, el, (hx, hy - 30), 170, 118, "g6", "ink", 6, seed=12)
    F.hand(ctx, hx - 8, hy - 8, a=0.0, s=4.4, color="teal_d", kind="fist")
    F.hand(ctx, hx, hy, a=0.0, s=4.4, color="g6", kind="fist")

    # the near water covers the bottoms of the logs
    _sea_band(ctx, t, 0.74 * H, "sea", 22, 7)
    ui_glyphs(ctx, t, seed=26, n=4, alpha=0.5)


def _sea_band(ctx, t, y0, color, amp, seed, n=16):
    rng = random.Random(seed)
    offs = [rng.uniform(-amp, amp) for _ in range(n + 1)]
    pts = [(-60, H + 60)]
    for i in range(n + 1):
        x = -60 + i * (W + 120) / n
        y = y0 + offs[i] + math.sin(t * 1.3 + i * 0.9 + seed) * amp * 0.35
        pts.append((x, y))
    pts.append((W + 60, H + 60))
    shape(ctx, pts, color, 4.0, seed=seed, wobble=0.1)
    for i in range(0, n + 1, 2):
        x, y = pts[1 + i]
        stroke(ctx, [(x - 46, y + 16), (x, y + 2), (x + 40, y + 12)], 4, "teal_l", alpha=0.35, taper=(0.3, 0.6),
               seed=i)
