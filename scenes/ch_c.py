"""Batch C: museum, concert, hamlet_numbers, ancestors_chain, campfire, moses_judge,
moses_tablets, chimp_abstraction, emperor. All characters are original designs."""
import functools
import math
import random

import cairo

from engine import figures as F
from engine.kit import (FONT_CAPS, FONT_TITLE, H, W, at, bg_studio, blade, camera, caption_tag, cel, circle_pts,
                        clamp, clip, col, ease_back, ease_io, ease_out, fillp, glow, lerp, lerp2, lingrad, mix,
                        particles, poly, rot, setc, shape, ss, stroke, text, text_width, ui_glyphs, win)
from . import scene


# ----------------------------------------------------------------- shared helpers
def _rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def _grad_poly(ctx, pts, grad):
    ctx.set_source(grad)
    poly(ctx, pts)
    ctx.fill()


def _dusk(ctx, top, mid, bot):
    ctx.set_source(lingrad(ctx, 0, 0, 0, H, [(0, top), (0.6, mid), (1, bot)]))
    ctx.paint()


def _fade(ctx, a, fn):
    """Run fn() with global opacity a (uses a group only while partly transparent)."""
    if a >= 0.999:
        fn()
        return
    if a <= 0.01:
        return
    ctx.push_group()
    fn()
    g = ctx.pop_group()
    ctx.set_source(g)
    ctx.paint_with_alpha(a)


def _resample_loop(pts, n):
    """Resample a closed polyline to n points spaced evenly by arc length (for shape morphing)."""
    P = list(pts) + [pts[0]]
    segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(P, P[1:])]
    total = sum(segs)
    out = []
    for j in range(n):
        d = total * j / n
        i = 0
        while i < len(segs) - 1 and d > segs[i]:
            d -= segs[i]
            i += 1
        k = d / segs[i] if segs[i] else 0.0
        out.append(lerp2(P[i], P[i + 1], k))
    return out


def _tally(ctx, x, y, s, color, alpha):
    """One tally group: four uprights and a slash (plain cairo, cheap enough for ~300 per frame)."""
    setc(ctx, color, alpha)
    ctx.set_line_width(2.6 * s)
    for i in range(4):
        xx = x + (i - 1.5) * 7 * s
        ctx.move_to(xx, y - 9 * s)
        ctx.line_to(xx, y + 9 * s)
    ctx.move_to(x - 13 * s, y + 6 * s)
    ctx.line_to(x + 13 * s, y - 6 * s)
    ctx.stroke()


_TALLY_RNG = random.Random(77)
_TALLY_POS = []
for _r in range(14):
    for _c in range(24):
        _TALLY_POS.append((W * (0.04 + 0.92 * (_c + 0.5 + _TALLY_RNG.uniform(-0.3, 0.3)) / 24),
                           H * (0.04 + 0.36 * (_r + 0.5 + _TALLY_RNG.uniform(-0.3, 0.3)) / 14)))
_TALLY_RNG.shuffle(_TALLY_POS)


def _cheer(ctx, x, y, h, color, seed, lift=1.0, fx=1):
    """Full silhouette with both arms raised (lift 0 = arms down, 1 = arms up). (x, y) = feet."""
    s = h / 300
    shade = mix(color, "ink", 0.4)
    with at(ctx, x, y, s, fx=fx):
        for a, b, c in (((-12, -130), (-18, -64), (-22, 0)), ((12, -130), (16, -64), (22, 0))):
            F.limb(ctx, a, b, c, 30, 22, shade, None, 4.0, seed)
        body = [(-38, -250), (38, -250), (44, -140), (30, -110), (-30, -110), (-44, -140)]
        shape(ctx, body, color, 4.0, seed=seed)
        for side in (-1, 1):
            a1 = lerp(2.3, -2.0, lift)
            a2 = lerp(2.6, -2.5, lift)
            if side > 0:
                a1, a2 = math.pi - a1, math.pi - a2
            S = (side * 34, -236)
            E = (S[0] + 62 * math.cos(a1), S[1] + 62 * math.sin(a1))
            Wr = (E[0] + 60 * math.cos(a2), E[1] + 60 * math.sin(a2))
            F.limb(ctx, S, E, Wr, 22, 18, color, shade, 4.0, seed + side + 5)
        shape(ctx, circle_pts(0, -284, 32, 18, ry=36), color, 4.0, seed=seed + 7)


# ----------------------------------------------------------------- s20 museum
def _radiant(ctx, x, y, s):
    """Abstract golden figure with raised arms, lit from within (painting content)."""
    with at(ctx, x, y, s):
        stroke(ctx, circle_pts(0, -96, 60, 40), 6, "gold_l", closed=True, alpha=0.6, wobble=0.05)
        fillp(ctx, circle_pts(0, -94, 22, 16), "gold_l")
        fillp(ctx, [(-12, -62), (12, -62), (30, 40), (-30, 40)], "gold_l")
        fillp(ctx, blade((-6, -40), (-96, -128), 26), "gold_l")
        fillp(ctx, blade((6, -40), (96, -128), 26), "gold_l")
        fillp(ctx, blade((-22, 36), (-54, 150), 30), "gold")
        fillp(ctx, blade((22, 36), (54, 150), 30), "gold")


@scene("museum")
def museum(ctx, t, T, seg):
    bg_studio(ctx, t, seed=41, tone=-0.7, dark=True, drift=0.4)
    camera(ctx, t, T, zoom=(1.0, 1.07), focus=(W * 0.5, H * 0.42))
    px, py, pw, ph = W * 0.5 - 440, H * 0.07, 880, 520
    # floor and pilasters
    fillp(ctx, [(0, H * 0.8), (W, H * 0.8), (W, H), (0, H)], mix("night", "g6", 0.3))
    for x in (W * 0.05, W * 0.95):
        shape(ctx, [(x - 50, 0), (x + 50, 0), (x + 60, H * 0.8), (x - 60, H * 0.8)], mix("night", "g6", 0.7), 4,
              seed=int(x))
    # light spilling from the painting onto the floor
    ctx.set_source(lingrad(ctx, 0, py + ph, 0, H, [(0, col("gold_l", 0.5)), (1, col("gold_l", 0.0))]))
    poly(ctx, [(px + 80, py + ph), (px + pw - 80, py + ph), (px + pw + 300, H), (px - 300, H)])
    ctx.fill()
    # the painting: gilt frame, sky gradient, clouds, rising golden figure
    shape(ctx, _rect(px - 34, py - 34, pw + 68, ph + 68), "gold", 6, seed=5)
    shape(ctx, _rect(px - 12, py - 12, pw + 24, ph + 24), "gold_d", 3, seed=6)
    with clip(ctx, _rect(px, py, pw, ph)):
        _grad_poly(ctx, _rect(px, py, pw, ph),
                   lingrad(ctx, 0, py, 0, py + ph, [(0, "rust_d"), (0.6, mix("rust", "gold", 0.5)), (1, "gold_d")]))
        for i in range(6):
            cx_ = px + pw * (0.1 + 0.16 * i) + math.sin(t * 0.25 + i * 1.7) * 40
            cy_ = py + ph * (0.62 + 0.12 * (i % 3))
            fillp(ctx, circle_pts(cx_, cy_, 120 + 30 * (i % 2), 26, ry=36 + 6 * (i % 2)), "g0", alpha=0.55)
        k = ease_io(win(t, 0.0, T))
        fx_, fy_ = px + pw * 0.5, lerp(py + ph * 0.95, py + ph * 0.2, k)
        glow(ctx, fx_, fy_, 300, "gold_l", 0.6)
        _radiant(ctx, fx_, fy_, 1.0)
        particles(ctx, t, 18, seed=3, color="g0", region=(px, py, px + pw, py + ph), speed=(4, -10), alpha=0.5)
    # visitors in silhouette, faces lit from the painting
    for i, x in enumerate((W * 0.2, W * 0.36, W * 0.64, W * 0.8)):
        F.person(ctx, x, H * 0.8, 240, color="g6", pose="stand", t=t, fx=1 if i % 2 else -1, head_c="g6",
                 seed=20 + i)
        glow(ctx, x, H * 0.8 - 228, 70, "gold_l", 0.22)
    for i, (x, h) in enumerate(((W * 0.07, 470), (W * 0.3, 430), (W * 0.7, 440), (W * 0.93, 480))):
        y = H * 1.03
        F.person(ctx, x, y, h, color="ink", pose="stand", t=t, fx=1, head_c="ink", seed=30 + i)
        glow(ctx, x + (W * 0.5 - x) * 0.04, y - h * 0.95, h * 0.28, "gold_l", 0.3)
    particles(ctx, t, 50, seed=12, color="gold_l", region=(W * 0.3, 0, W * 0.7, H * 0.8), speed=(3, -12),
              alpha=0.5, size=(1, 2.5))
    ui_glyphs(ctx, t, seed=5, n=5)


# ----------------------------------------------------------------- s21 concert
@scene("concert")
def concert(ctx, t, T, seg):
    beat = 0.5                       # 120 bpm
    bt = t / beat
    pulse = math.exp(-(bt % 1.0) * 5)
    bg_studio(ctx, t, seed=51, dark=True, tone=-0.3, drift=0.6)
    camera(ctx, t, T, zoom=(1.0, 1.05), focus=(W * 0.5, H * 0.45))
    cx, cy = W * 0.5, H * 0.44
    # stage light beams, teal and gold
    for i, (x0, c) in enumerate(((W * 0.16, "teal"), (W * 0.36, "gold"), (W * 0.64, "gold"), (W * 0.84, "teal"))):
        tx = cx + (x0 - cx) * 0.6 + math.sin(t * 0.9 + i * 1.3) * 160
        fillp(ctx, [(x0 - 14, -60), (x0 + 14, -60), (tx + 260, H * 0.94), (tx - 260, H * 0.94)], c,
              alpha=0.13 + 0.1 * pulse)
    # stage with a silhouetted singer
    glow(ctx, cx, cy, 460, "gold", 0.35 + 0.25 * pulse)
    fillp(ctx, [(W * 0.33, cy + 40), (W * 0.67, cy + 40), (W * 0.73, cy + 92), (W * 0.27, cy + 92)], "g6")
    _cheer(ctx, cx, cy + 40, 230, "ink2", seed=2, lift=0.55 + 0.45 * pulse)
    # concentric angular waves, one new ring per beat
    k0 = math.floor(bt)
    for k in range(k0 - 7, k0 + 1):
        age = t - k * beat
        if age < 0:
            continue
        u = min(age / 2.4, 1.0)
        if u >= 1:
            continue
        r = 150 + 640 * ease_out(u, 2)
        a = (1 - u) ** 1.3 * 0.85
        c = "teal_l" if k % 2 == 0 else "gold_l"
        pts = []
        for j in range(72):
            an = 2 * math.pi * j / 72
            m = 1 + 0.04 * (j % 2)
            pts.append((cx + math.cos(an) * r * m, cy + 40 + math.sin(an) * r * 0.42 * m))
        stroke(ctx, pts, 4 + 8 * (1 - u), c, closed=True, wobble=0.05, seed=k, alpha=a)
    # crowd with raised arms, doing a wave (phase shifts per person)
    rng = random.Random(9)
    for i in range(18):
        x = W * (i + 0.5) / 18 + rng.uniform(-30, 30)
        h = rng.uniform(230, 270)
        y = H * 0.84 + rng.uniform(-14, 14)
        lift = 0.8 + 0.2 * math.sin(2 * math.pi * t / (beat * 2) + i * 0.7)
        _cheer(ctx, x, y, h, ("ink2", "g6", "night")[i % 3], seed=100 + i, lift=lift, fx=1)
    for i in range(9):
        x = W * (i + 0.5) / 9 + rng.uniform(-40, 40)
        h = rng.uniform(420, 470)
        y = H * 1.04
        lift = 0.75 + 0.25 * math.sin(2 * math.pi * t / (beat * 2) + i * 0.9)
        _cheer(ctx, x, y, h, ("ink", "g6")[i % 2], seed=200 + i, lift=lift, fx=1 if i % 2 else -1)
        glow(ctx, x, y - h * 0.95, h * 0.2, "teal_l" if i % 2 else "gold_l", 0.2 + 0.25 * pulse)
    particles(ctx, t, 30, seed=2, color="gold_l", alpha=0.4, speed=(0, -20))
    ui_glyphs(ctx, t, seed=6, n=6)


# ----------------------------------------------------------------- s22 hamlet_numbers
HAMLET = dict(F.HERO, hair="messy", hair_c="hair_dk", hair_s="ink2", coat="g6", coat_s="ink2",
              lining="g4", collar="high", armor=None, strap=None, eye="g5")


def _skull(ctx, x, y, r, a=0.0):
    with at(ctx, x, y, r / 50.0, a):
        cran = circle_pts(0, -6, 46, 24, ry=44)
        shape(ctx, cran, "g0", 4.5, seed=71)
        cel(ctx, cran, [(12, -60), (60, -60), (60, 30), (12, 30)], "g2")
        shape(ctx, [(-30, 26), (30, 26), (26, 52), (-26, 52)], "g0", 4.0, seed=72)
        for k in range(-2, 3):
            stroke(ctx, [(k * 9, 30), (k * 9, 48)], 2.5, "ink", alpha=0.7)
        fillp(ctx, circle_pts(-18, -4, 13, 14, ry=15), "ink")
        fillp(ctx, circle_pts(18, -4, 13, 14, ry=15), "ink")
        fillp(ctx, [(-3, 10), (3, 10), (0, 20)], "ink")


def _hamlet_actor(ctx, t):
    with at(ctx, W * 0.25, H * 0.42, 0.95):
        F.character(ctx, 0, 0, 1.0, HAMLET, "grim", t, look=0.8)
        F.limb(ctx, (118, 214), (226, 226), (206, 128), 26, 21, "g5", "ink2", 4.5, 77)
        _skull(ctx, 190, 30, 46, 0.12 * math.sin(t * 0.6))
        F.hand(ctx, 200, 118, 0.0, 1.0, "skin2", "fist")


def _glyph(ctx, kind, x, y, size, color, alpha):
    if kind == "pi":
        s = size / 120.0
        for pts in (((x - 34 * s, y - 40 * s), (x + 34 * s, y - 40 * s)),
                    ((x - 22 * s, y - 40 * s), (x - 26 * s, y + 40 * s)),
                    ((x + 22 * s, y - 40 * s), (x + 26 * s, y + 40 * s))):
            stroke(ctx, list(pts), 9 * s + 2, color, taper=(0.05, 0.05), alpha=alpha)
    elif kind == "tri":
        shape(ctx, [(x - 46, y + 30), (x + 46, y + 30), (x, y - 40)], None, ink=7, ink_color=color, alpha=alpha)
    else:
        text(ctx, kind, x, y + size * 0.35, size, FONT_TITLE, color, alpha=alpha)


@scene("hamlet_numbers")
def hamlet_numbers(ctx, t, T, seg):
    camera(ctx, t, T, zoom=(1.0, 1.04))
    bg_studio(ctx, t, seed=61, tone=0.4, drift=0.5)
    # right half: light studio with teal geometry, a lever and a planet
    stroke(ctx, circle_pts(W * 0.86, H * 0.24, 150, 48), 4, "teal", closed=True, alpha=0.45)
    shape(ctx, [(W * 0.58, H * 0.3), (W * 0.66, H * 0.14), (W * 0.74, H * 0.3)], None, ink=4, ink_color="teal")
    fx0, fy0 = W * 0.74, H * 0.8
    th = -0.22 * ease_io(win(t, T * 0.2, T * 0.6)) - 0.015 * math.sin(t * 2.0)
    L = rot((fx0 - 260, fy0), th, (fx0, fy0))
    R = rot((fx0 + 380, fy0), th, (fx0, fy0))
    shape(ctx, [(fx0 - 60, H * 0.95), (fx0 + 60, H * 0.95), (fx0, fy0 + 4)], "steel_d", 5, seed=40)
    stroke(ctx, [L, R], 26, "ink", taper=(0.02, 0.02), wobble=0.04)
    stroke(ctx, [L, R], 8, "steel_l", taper=(0.02, 0.02), wobble=0.0, alpha=0.8)
    # planet riding the lifted end
    P = (R[0], R[1] - 72)
    ring_back = [(P[0] + math.cos(a) * 110, P[1] + math.sin(a) * 30) for a in
                 [math.pi + i * math.pi / 30 for i in range(31)]]
    ring_front = [(P[0] + math.cos(a) * 110, P[1] + math.sin(a) * 30) for a in
                  [i * math.pi / 30 for i in range(31)]]
    stroke(ctx, ring_back, 9, "gold_l", taper=(0.1, 0.1), wobble=0.0)
    globe = circle_pts(P[0], P[1], 62, 36)
    shape(ctx, globe, "cobalt", 5, seed=41)
    cel(ctx, globe, circle_pts(P[0] + 26, P[1] + 12, 62, 36), "cobalt_d")
    stroke(ctx, ring_front, 9, "gold_l", taper=(0.1, 0.1), wobble=0.0)
    # numbers and figures pushing down on the short end of the lever
    kinds = [("1", "gold"), ("pi", "teal"), ("2", "teal_l"), ("3", "gold_l"), ("tri", "red_l"), ("pi", "gold"),
             ("2", "teal")]
    for i, (kind, c) in enumerate(kinds):
        ph = (t / (T * 0.45) + i / len(kinds)) % 1.0
        sx = W * (0.56 + 0.36 * ((i * 0.37) % 1.0))
        sy = H * (0.1 + 0.22 * ((i * 0.61) % 1.0))
        tgt = (L[0] + (i % 3 - 1) * 34, L[1] - 60 - (i // 3) * 40)
        x, y = lerp2((sx, sy), tgt, ease_io(ph))
        a = ss(min(ph * 6, 1.0)) * (1 - ss((ph - 0.7) / 0.3))
        if a > 0.02:
            _glyph(ctx, kind, x, y, 92, c, a)
    # left half: dark stage with a spotlight on the actor
    left = [(0, 0), (W * 0.5 + 80, 0), (W * 0.5 - 80, H), (0, H)]
    with clip(ctx, left):
        fillp(ctx, _rect(0, 0, W, H), "night")
        spot = [(W * 0.25 - 30, -20), (W * 0.25 + 30, -20), (W * 0.25 + 420, H), (W * 0.25 - 420, H)]
        fillp(ctx, spot, "white", alpha=0.09 + 0.02 * math.sin(t))
        fillp(ctx, circle_pts(W * 0.25, H * 0.9, 360, 40, ry=80), "white", alpha=0.10)
        _hamlet_actor(ctx, t)
    stroke(ctx, [(W * 0.5 + 80, 0), (W * 0.5 - 80, H)], 10, "red", taper=(0.05, 0.05))
    cap = "FICCIÓN ≠ FALSEDAD"
    w = text_width(ctx, cap, 40, tracking=0.08) + 40
    caption_tag(ctx, cap, W * 0.5 - w / 2, H * 0.86, t, 40, accent="gold", appear=T * 0.5)
    ui_glyphs(ctx, t, seed=8, n=6)


# ----------------------------------------------------------------- s23 ancestors_chain
_CHAIN_FORMS = [
    circle_pts(0, 0, 84, 40),                                                       # cell
    [(105, 0), (74, -44), (22, -64), (-30, -52), (-72, -30), (-112, -68), (-98, 0), (-112, 68), (-72, 30),
     (-30, 52), (22, 64), (74, 44)],                                               # fish
    [(100, -12), (82, -34), (50, -48), (0, -44), (-40, -40), (-78, -44), (-120, -64), (-126, -52), (-88, -24),
     (-64, -6), (-66, 30), (-48, 34), (-44, 8), (-8, 14), (18, 14), (24, 36), (40, 38), (42, 12), (70, 10),
     (96, 6)],                                                                     # small mammal
    [(-6, -96), (24, -112), (56, -106), (74, -84), (66, -60), (54, -48), (62, -18), (56, 28), (60, 54), (44, 58),
     (38, 30), (20, 6), (12, 40), (-4, 58), (-24, 54), (-14, 26), (-30, -4), (-40, -40), (-34, -72),
     (-20, -86)],                                                                  # primate
    [(-8, -62), (-30, -52), (-40, -6), (-36, 50), (-24, 52), (-22, -4), (-16, -30), (-18, 20), (-22, 100),
     (-8, 100), (0, 40), (8, 100), (22, 100), (18, 20), (16, -30), (24, -4), (24, 52), (36, 50), (40, -6),
     (30, -52), (8, -62), (14, -76), (10, -96), (0, -106), (-10, -96), (-14, -76)],  # human
]
_CHAIN_N = [_resample_loop(f, 72) for f in _CHAIN_FORMS]
_CHAIN_LABELS = ["CÉLULA", "PEZ", "MAMÍFERO", "PRIMATE", "HUMANO"]


@scene("ancestors_chain")
def ancestors_chain(ctx, t, T, seg):
    bg_studio(ctx, t, seed=81, tone=0.2, drift=0.4)
    camera(ctx, t, T, zoom=(1.0, 1.04))
    cy = H * 0.56
    xs = [W * (0.16 + 0.68 * j / 4) for j in range(5)]
    # timeline axis
    stroke(ctx, [(W * 0.07, cy + 130), (W * 0.93, cy + 130)], 4, "g4", taper=(0.02, 0.02), alpha=0.8)
    for j, x in enumerate(xs):
        stroke(ctx, [(x, cy + 120), (x, cy + 140)], 3, "g4", taper=(0.1, 0.1))
        text(ctx, _CHAIN_LABELS[j], x, cy + 182, 26, FONT_CAPS, "g5", tracking=0.12)
    # unbroken chain links between neighbours
    for j in range(4):
        mx = (xs[j] + xs[j + 1]) / 2
        stroke(ctx, circle_pts(mx, cy, 22, 24, ry=34), 6, "teal_d", closed=True, wobble=0.04)
    # silhouettes morphing: node j blends its own form into the next, with a lag per node
    p = 0.5 - 0.5 * math.cos(2 * math.pi * t / 6.0)
    for j, x in enumerate(xs):
        pj = clamp((p - j * 0.12) * 1.3)
        a, b = _CHAIN_N[j], _CHAIN_N[min(j + 1, 4)]
        k = ss(pj)
        pts = [(x + (p0[0] + (q0[0] - p0[0]) * k) * 1.2, cy + (p0[1] + (q0[1] - p0[1]) * k) * 1.2)
               for p0, q0 in zip(a, b)]
        glow(ctx, x, cy, 160, "teal", 0.22)
        shape(ctx, pts, mix("g5", "ink", 0.15), 5, seed=j)
    # people watching people: eyes above the chain, looking down at it
    for i in range(11):
        ex = W * (0.08 + 0.84 * i / 10)
        ey = H * 0.24 + math.sin(t * 0.7 + i) * 4
        sy = 0.12 if 2.0 < (t * 0.4 + i * 0.3) % 4.0 < 2.12 else 1.0
        tgt = min(xs, key=lambda xx: abs(xx - ex))
        dx = clamp((tgt - ex) / 400.0) * 9
        shape(ctx, [(ex - 26, ey), (ex, ey - 20 * sy), (ex + 26, ey), (ex, ey + 18 * sy)], "g0", 3.5, seed=200 + i)
        if sy > 0.5:
            fillp(ctx, circle_pts(ex + dx, ey + 4, 9, 14), "teal")
            fillp(ctx, circle_pts(ex + dx, ey + 4, 4, 10), "ink")
    caption_tag(ctx, "3.500 MILLONES DE AÑOS", 110, 110, t, 44, appear=0.8)
    ui_glyphs(ctx, t, seed=6, n=6)


# ----------------------------------------------------------------- s24 campfire
@scene("campfire")
def campfire(ctx, t, T, seg):
    bg_studio(ctx, t, seed=91, dark=True, drift=0.3)
    camera(ctx, t, T, zoom=(1.0, 1.06), focus=(W * 0.5, H * 0.6))
    FX, FY = W * 0.5, H * 0.74
    flick = 0.5 * math.sin(t * 7.0) + 0.5 * math.sin(t * 13.0)
    glow(ctx, FX, FY - 120, 760, "rust", 0.32 + 0.04 * flick)
    glow(ctx, FX, FY - 80, 330, "gold", 0.48 + 0.06 * flick)
    # the elder storyteller, behind the fire, gesturing up at the smoke
    F.person(ctx, FX + 10, H * 0.66, 340, color="rust_d", shade="ink2", pose="stand", t=t, fx=1,
             head_c="skin2", arm_up=0.85 + 0.15 * math.sin(t * 1.7), seed=5)
    # smoke strands rising from the fire
    for i in range(5):
        x0 = FX + (i - 2) * 26
        pts = []
        for j in range(9):
            u = j / 8
            pts.append((x0 + math.sin(t * 0.8 + i * 1.7 + u * 5) * (20 + 60 * u), FY - 210 - u * 620))
        stroke(ctx, pts, 16 + 8 * (i % 2), "g3", smooth=True, alpha=0.14, taper=(0.1, 0.6))
    # the fire
    shape(ctx, [(FX - 150, FY + 26), (FX + 110, FY - 6), (FX + 140, FY + 18), (FX - 120, FY + 56)], "rust_d", 5,
          seed=3)
    for i in range(7):
        k = i - 3
        x = FX + k * 34 + math.sin(t * 6 + i) * 6
        hh = (200 - abs(k) * 34) * (0.85 + 0.15 * math.sin(t * 9 + i * 1.3))
        fillp(ctx, blade((x, FY + 10), (x + math.sin(t * 5 + i) * 14, FY - hh), 62 - abs(k) * 8, bend=0.1), "rust")
        fillp(ctx, blade((x, FY + 10), (x + math.sin(t * 4 + i) * 10, FY - hh * 0.6), 34 - abs(k) * 4, bend=0.1),
              "gold")
        fillp(ctx, blade((x, FY + 10), (x, FY - hh * 0.3), 16, bend=0.05), "gold_l")
    shape(ctx, [(FX - 110, FY + 10), (FX + 150, FY + 40), (FX + 120, FY + 62), (FX - 140, FY + 34)], "ink2", 5,
          seed=4)
    # stories drifting in the smoke, one after another
    def _story(a, b, fn):
        k = ss(win(t, a, a + 0.12 * T)) * (1 - ss(win(t, b - 0.12 * T, b)))
        if k > 0.01:
            fn(k)

    def _dragon(k):
        pts = [(W * 0.16, H * 0.36), (W * 0.22, H * 0.30), (W * 0.28, H * 0.36), (W * 0.34, H * 0.30),
               (W * 0.40, H * 0.26), (W * 0.44, H * 0.22)]
        stroke(ctx, pts, 13, "teal_l", smooth=True, alpha=1.0 * k, taper=(0.1, 0.4))
        shape(ctx, blade((W * 0.44, H * 0.22), (W * 0.47, H * 0.18), 26, 0.1), "teal_l", 4, alpha=k)
        stroke(ctx, [(W * 0.26, H * 0.34), (W * 0.24, H * 0.2), (W * 0.31, H * 0.28)], 6, "teal_l", alpha=0.6 * k)

    def _hero(k):
        stroke(ctx, circle_pts(W * 0.7, H * 0.3, 24, 20), 9, "g0", closed=True, alpha=k)
        stroke(ctx, [(W * 0.68, H * 0.34), (W * 0.72, H * 0.34), (W * 0.73, H * 0.46), (W * 0.67, H * 0.46)], 6,
               "g0", closed=True, alpha=k)
        stroke(ctx, [(W * 0.72, H * 0.38), (W * 0.78, H * 0.2)], 10, "gold_l", alpha=k)

    def _mother(k):
        stroke(ctx, circle_pts(W * 0.47, H * 0.17, 22, 20), 6, "g0", closed=True, alpha=k)
        stroke(ctx, [(W * 0.42, H * 0.27), (W * 0.45, H * 0.22), (W * 0.5, H * 0.22), (W * 0.52, H * 0.27)], 6,
               "g0", alpha=k)
        stroke(ctx, circle_pts(W * 0.53, H * 0.24, 13, 14), 5, "gold_l", closed=True, alpha=k)

    _story(0.08 * T, 0.42 * T, _dragon)
    _story(0.36 * T, 0.7 * T, _hero)
    _story(0.64 * T, 0.96 * T, _mother)
    # foreground people around the fire, kneeling, lit from the fire
    for side in (-1, 1):
        for i in range(4):
            x = FX + side * (330 + i * 112)
            y = H * (0.93 - 0.05 * i)
            F.person(ctx, x, y, 260 + 10 * (i % 2), color="ink", pose="kneel", t=t, fx=side, head_c="ink",
                     seed=40 + i * 2 + (side > 0))
    particles(ctx, t, 40, seed=21, color="gold_l", region=(FX - 200, FY - 500, FX + 200, FY), speed=(10, -60),
              size=(1, 2.4), alpha=0.7)
    caption_tag(ctx, "10.000 AÑOS", 110, 110, t, 44, appear=0.8)
    ui_glyphs(ctx, t, seed=8, n=5)


# ----------------------------------------------------------------- s25 / s26 Moses
SAGE_ELDER = F.SAGE


@scene("moses_judge")
def moses_judge(ctx, t, T, seg):
    _dusk(ctx, "night", mix("red_d", "night", 0.2), "rust")
    camera(ctx, t, T, zoom=(1.0, 1.05), focus=(W * 0.5, H * 0.5))
    glow(ctx, W * 0.5, H * 0.62, 620, "gold", 0.45)
    # tally marks gathering in the sky: dozens, then hundreds
    n = int(lerp(24, 300, ease_io(win(t, T * 0.15, T * 0.85))))
    for i in range(n):
        x, y = _TALLY_POS[i]
        _tally(ctx, x, y, 1.0, "g0", 0.85)
    # dunes and tents
    fillp(ctx, [(-40, H * 0.72), (W * 0.25, H * 0.62), (W * 0.55, H * 0.7), (W * 0.8, H * 0.6), (W + 40, H * 0.68),
                (W + 40, H + 40), (-40, H + 40)], "rust_d")
    for x, w in ((W * 0.1, 260), (W * 0.9, 280)):
        shape(ctx, [(x - w / 2, H * 0.78), (x, H * 0.62), (x + w / 2, H * 0.78)], "g5", 5, seed=int(x))
        fillp(ctx, [(x, H * 0.62), (x + w / 2, H * 0.78), (x, H * 0.78)], "g6")
    fillp(ctx, [(-40, H * 0.82), (W * 0.3, H * 0.76), (W * 0.7, H * 0.84), (W + 40, H * 0.78), (W + 40, H + 40),
                (-40, H + 40)], "ink2")
    # people queued behind the judge
    F.crowd(ctx, W * 0.06, W * 0.94, H * 0.76, 9, 200, t, seed=12, colors=("g5", "g6", "ink2"), pose="walk")
    # the judge, seated on a rock, with his staff
    F.character(ctx, W * 0.5, H * 0.44, 0.95, SAGE_ELDER, "neutral", t)
    stroke(ctx, [(W * 0.5 + 250, H * 0.36), (W * 0.5 + 256, H * 0.96)], 14, "gold_d", taper=(0.02, 0.02))
    fillp(ctx, circle_pts(W * 0.5 + 250, H * 0.36, 16, 16), "gold")
    shape(ctx, [(W * 0.5 - 240, H * 0.86), (W * 0.5 - 170, H * 0.8), (W * 0.5 + 170, H * 0.8),
                (W * 0.5 + 240, H * 0.86), (W * 0.5 + 300, H * 1.02), (W * 0.5 - 300, H * 1.02)], "g6", 5, seed=9)
    # the two men quarrelling
    F.person(ctx, W * 0.34, H * 0.93, 430, color="cobalt_d", pose="stand", t=t, fx=1, head_c="skin2",
             arm_up=0.6 + 0.4 * math.sin(t * 3.1), seed=41)
    F.person(ctx, W * 0.66, H * 0.93, 430, color="rust_d", pose="stand", t=t, fx=-1, head_c="skin2",
             arm_up=0.6 + 0.4 * math.sin(t * 2.7 + 1.0), seed=42)
    ui_glyphs(ctx, t, seed=9, n=5)


@scene("moses_tablets")
def moses_tablets(ctx, t, T, seg):
    _dusk(ctx, "night", mix("cobalt_d", "gold", 0.25), "gold")
    camera(ctx, t, T, zoom=(1.0, 1.06), focus=(W * 0.5, H * 0.42))
    cx, cy = W * 0.5, H * 0.27 + 268 * 0.92         # centre of the tablets in screen space
    pulse = 0.5 + 0.5 * math.sin(t * 2.2)
    # light rays from the tablets
    for i in range(18):
        a = i * 2 * math.pi / 18 + t * 0.04
        fillp(ctx, [(cx, cy), (cx + math.cos(a - 0.05) * 1400, cy + math.sin(a - 0.05) * 1400),
                    (cx + math.cos(a + 0.05) * 1400, cy + math.sin(a + 0.05) * 1400)], "gold_l",
              alpha=0.10 + 0.08 * pulse)
    glow(ctx, cx, cy, 480, "gold", 0.42 + 0.25 * pulse)
    # the mountain: back ridge, the elder, then the summit in front
    shape(ctx, [(-40, H + 40), (-40, H * 0.8), (W * 0.28, H * 0.7), (W * 0.5, H * 0.6), (W * 0.72, H * 0.7),
                (W + 40, H * 0.8), (W + 40, H + 40)], "g6", 5, seed=3)
    F.character(ctx, W * 0.5, H * 0.27, 0.92, SAGE_ELDER, "grim", t)
    # the two tablets, held in front of the chest, blazing
    with at(ctx, W * 0.5, H * 0.27, 0.92):
        for side, ang in ((-1, -0.08), (1, 0.08)):
            tcx, tcy = side * 66, 268
            pts = [rot((tcx + dx, tcy + dy), ang, (tcx, tcy)) for dx, dy in
                   ((-44, -64), (44, -64), (44, 64), (-44, 64))]
            shape(ctx, pts, "g0", 5, seed=60 + side)
            for k in range(4):
                p0 = rot((tcx - 28, tcy - 34 + k * 22), ang, (tcx, tcy))
                p1 = rot((tcx + 28, tcy - 34 + k * 22), ang, (tcx, tcy))
                stroke(ctx, [p0, p1], 3, "gold_d", alpha=0.8, taper=(0.1, 0.1))
            F.hand(ctx, tcx, 336, 0.0, 1.0, "skin2", "fist")
    shape(ctx, [(W * 0.5 - 300, H + 40), (W * 0.5 - 180, H * 0.72), (W * 0.5 - 90, H * 0.64), (W * 0.5, H * 0.62),
                (W * 0.5 + 90, H * 0.64), (W * 0.5 + 180, H * 0.72), (W * 0.5 + 300, H + 40)], "ink2", 6, seed=4)
    # tally marks condense into the tablets
    for i in range(300):
        x0, y0 = _TALLY_POS[i]
        d = (i / 300.0) * 0.35
        kk = ease_io(clamp((win(t, T * 0.12, T * 0.72) - d) / 0.6))
        x = lerp(x0, cx, kk) + math.sin(i) * 6 * (1 - kk)
        y = lerp(y0, cy, kk)
        alpha = 0.85 * (1 - ss(clamp((kk - 0.7) / 0.3)))
        if alpha > 0.02:
            _tally(ctx, x, y, 1 - 0.7 * kk, "g0", alpha)
    caption_tag(ctx, "LA LEY", 110, 110, t, 44, appear=T * 0.5)
    ui_glyphs(ctx, t, seed=10, n=5)


# ----------------------------------------------------------------- s27 chimp_abstraction
def _chimp(ctx, x, y, s, color, t, fx=1, arms=0.0, seed=0):
    """Original stylised ape: hunched, knuckles on the ground; arms=1 raises them. (x, y) = feet."""
    shade = mix(color, "ink", 0.35)
    with at(ctx, x, y, s, fx=fx):
        F.limb(ctx, (20, -108), lerp2((28, -56), (70, -160), arms), lerp2((20, 4), (42, -214), arms), 22, 16,
               shade, None, 4.0, seed + 9)
        F.limb(ctx, (-40, -96), (-72, -48), (-62, 0), 30, 22, shade, None, 4.0, seed)
        body = [(-72, -104), (-40, -126), (12, -124), (46, -110), (44, -70), (4, -58), (-52, -68)]
        shape(ctx, body, color, 4.0, seed=seed + 1)
        F.limb(ctx, (36, -110), lerp2((58, -62), (98, -168), arms), lerp2((64, 0), (86, -220), arms), 24, 18,
               color, shade, 4.0, seed + 2)
        shape(ctx, circle_pts(58, -142, 34, 22), color, 4.0, seed=seed + 3)
        shape(ctx, [(80, -132), (110, -120), (108, -100), (84, -102)], color, 3.5, seed=seed + 4)


def _leader(ctx, x, y, s, color, crown, t, seed):
    """Human leader with a crown (kings) or a feather headdress (chiefs). (x, y) = feet."""
    F.person(ctx, x, y, 300 * s, color=color, pose="stand", t=t, fx=1, head_c="skin", seed=seed)
    with at(ctx, x, y - 320 * s, s):
        if crown:
            shape(ctx, [(-26, 0), (-26, -30), (-12, -14), (0, -40), (12, -14), (26, -30), (26, 0)], "gold", 4,
                  seed=seed)
        else:
            for j in range(5):
                fillp(ctx, blade((-14 + j * 7, 0), (-30 + j * 15, -56 - (j % 2) * 12), 10, 0.1), "teal_l")


@scene("chimp_abstraction")
def chimp_abstraction(ctx, t, T, seg):
    bg_studio(ctx, t, seed=101, dark=True, drift=0.4)
    camera(ctx, t, T, zoom=(1.0, 1.05))
    merge_k = ease_io(win(t, T * 0.52, T * 0.82))
    # zone labels
    k_lab = ss(win(t, 0.05, 0.4))
    text(ctx, "CHIMPANCÉS", W * 0.2, H * 0.17, 30, FONT_CAPS, "g3", tracking=0.12, alpha=k_lab * (1 - merge_k))
    text(ctx, "LÍDERES HUMANOS", W * 0.5, H * 0.17, 30, FONT_CAPS, "g3", tracking=0.12,
         alpha=k_lab * (1 - merge_k))
    text(ctx, "EL IDEAL", W * 0.83, H * 0.17, 30, FONT_CAPS, "gold_l", tracking=0.12, alpha=ss(win(t, T * 0.5, T * 0.8)))
    # arrows showing the abstraction steps
    for (x0, x1, a, b) in ((0.25, 0.44, 0.28, 0.45), (0.58, 0.74, 0.4, 0.55)):
        k = win(t, T * a, T * b)
        if k <= 0:
            continue
        xe = lerp(W * x0, W * x1, ease_out(k, 2))
        stroke(ctx, [(W * x0, H * 0.3), (xe - (18 if k > 0.9 else 0), H * 0.3)], 8, "teal_l", taper=(0.05, 0.1))
        if k > 0.9:
            fillp(ctx, [(W * x1 + 6, H * 0.3), (W * x1 - 24, H * 0.3 - 18), (W * x1 - 24, H * 0.3 + 18)], "teal_l",
                  alpha=ss(win(k, 0.9, 1.0)))
    # the chimpanzee tribe around a big dominant one
    chimps = [(0.2, 0.86, 1.55, 1, "red_l", 0.5 + 0.5 * math.sin(t * 1.6), 1),
              (0.06, 0.92, 0.85, 1, "g4", 0.0, 2), (0.12, 0.66, 0.66, 1, "g5", 0.0, 3),
              (0.32, 0.92, 0.85, -1, "g4", 0.0, 4), (0.27, 0.64, 0.66, -1, "g5", 0.0, 5)]
    leaders = [(0.43, 0.88, 1.3, "cobalt", True), (0.51, 0.88, 1.33, "red", False),
               (0.59, 0.88, 1.27, "gold_d", True), (0.67, 0.88, 1.3, "cobalt_d", False)]
    tx, ty = W * 0.83, H * 0.64
    idx = 0
    for (xf, yf, s, fx, c, arms, sd) in chimps:
        k = ease_io(clamp(win(t, T * 0.5 + idx * 0.012, T * 0.8)))
        x = lerp(W * xf, tx + (xf - 0.2) * 60, k)
        y = lerp(H * yf, ty, k)
        sc = lerp(s, 0.25, k)
        _fade(ctx, 1 - k, functools.partial(_chimp, ctx, x, y, sc, c, t, fx, arms, sd * 7))
        idx += 1
    for (xf, yf, s, c, crown) in leaders:
        k = ease_io(clamp(win(t, T * 0.5 + idx * 0.012, T * 0.8)))
        x = lerp(W * xf, tx + (xf - 0.5) * 60, k)
        y = lerp(H * yf, ty, k)
        sc = lerp(s, 0.25, k)
        _fade(ctx, 1 - k, functools.partial(_leader, ctx, x, y, sc, c, crown, t, 300 + idx))
        idx += 1
    # the merged abstract ideal: gold outline, glowing
    sm = 1.9 * ease_back(win(t, T * 0.6, T * 0.92), 1.4)
    if sm > 0.02:
        glow(ctx, tx, ty - 40, 340 * sm, "gold", 0.35)
        with at(ctx, tx, ty, sm):
            stroke(ctx, _CHAIN_N[4], 26, "gold", closed=True, alpha=0.25, wobble=0.0)
            shape(ctx, _CHAIN_N[4], "night", 9, ink_color="gold_l", seed=7)
            stroke(ctx, circle_pts(0, -96, 120, 60, ry=44), 6, "gold_l", closed=True, alpha=0.7)
    ui_glyphs(ctx, t, seed=11, n=5)


# ----------------------------------------------------------------- s28 emperor
EMPEROR = dict(F.HERO, hair="short", hair_c="ink2", hair_s="ink", eye="g6", coat="red", coat_s="red_d",
               lining="gold", collar="fur", armor=None, strap="gold_d")


def _throne(ctx):
    shape(ctx, [(-196, -250), (-150, -340), (150, -340), (196, -250), (196, 300), (-196, 300)], "steel_d", 6,
          seed=90)
    stroke(ctx, [(-150, -300), (0, -318), (150, -300)], 6, "gold", alpha=0.9)
    for side in (-1, 1):
        shape(ctx, [(side * 196, 170), (side * 250, 150), (side * 256, 250), (side * 226, 300), (side * 196, 300)],
              "gold", 5, seed=92 + side)
    shape(ctx, [(-236, 300), (236, 300), (262, 372), (-262, 372)], "gold_d", 5, seed=91)


def _laurel(ctx):
    for i in range(13):
        a = lerp(-math.pi * 0.92, -math.pi * 0.08, i / 12)
        p0 = (math.cos(a) * 92, math.sin(a) * 92 - 14)
        p1 = (math.cos(a) * 126, math.sin(a) * 126 - 14)
        shape(ctx, blade(p0, p1, 26, bend=0.25 if i % 2 else -0.25), "gold_l" if i % 2 else "gold", 3.5,
              seed=110 + i)


def _worship(ctx, x, y, h, fx, t, seed):
    """A kneeling worshipper, leaning toward the emperor. (x, y) = feet."""
    with at(ctx, x, y, 1.0, a=0.2 * fx):
        F.person(ctx, 0, 0, h, color="rust_d", pose="kneel", t=t, fx=fx, head_c="ink2", seed=seed)


@scene("emperor")
def emperor(ctx, t, T, seg):
    bg_studio(ctx, t, seed=46, dark=True, drift=0.4)
    camera(ctx, t, T, zoom=(1.0, 1.05), focus=(W * 0.5, H * 0.5))
    # the dais
    fillp(ctx, [(W * 0.22, H * 0.78), (W * 0.66, H * 0.78), (W * 0.7, H * 0.9), (W * 0.18, H * 0.9)], "g6")
    # the tall column of light, EL PRINCIPIO
    cxc = W * 0.8
    bright = ss(win(t, T * 0.5, T * 0.7))
    glow(ctx, cxc, H * 0.45, 440, "teal", 0.3 + 0.3 * bright)
    colpts = [(cxc - 78, H * 0.08), (cxc + 78, H * 0.08), (cxc + 78, H * 0.9), (cxc - 78, H * 0.9)]
    _grad_poly(ctx, colpts, lingrad(ctx, cxc - 78, 0, cxc + 78, 0, [(0, "teal_d"), (0.5, mix("teal_l", "white", 0.3)),
                                                                     (1, "teal_d")]))
    stroke(ctx, colpts + [colpts[0]], 6, "ink", taper=(0.01, 0.01))
    for k in range(-2, 3):
        stroke(ctx, [(cxc + k * 28, H * 0.15), (cxc + k * 28, H * 0.82)], 3, "ink", alpha=0.35, taper=(0.02, 0.02))
    shape(ctx, _rect(cxc - 104, H * 0.08, 208, H * 0.05), "gold", 5, seed=120)
    shape(ctx, _rect(cxc - 104, H * 0.86, 208, H * 0.04), "gold_d", 5, seed=121)
    cap = "EL PRINCIPIO"
    w = text_width(ctx, cap, 40, tracking=0.08) + 40
    caption_tag(ctx, cap, cxc - w / 2, H * 0.5, t, 40, accent="gold", appear=T * 0.25)
    # the emperor on his throne; he bows toward the column at 0.55-0.8 T
    ex, ey = W * 0.42, H * 0.446
    bow = ease_io(win(t, T * 0.55, T * 0.8)) * 0.28
    with at(ctx, ex, ey, 1.0):
        _throne(ctx)
        ctx.save()
        ctx.translate(0, 420)
        ctx.rotate(bow)
        ctx.translate(0, -420)
        F.character(ctx, 0, 0, 1.0, EMPEROR, "grim" if bow < 0.05 else "awe", t)
        _laurel(ctx)
        ctx.restore()
    # worshippers bowing on both sides
    for i, (x, h) in enumerate(((W * 0.1, 260), (W * 0.2, 240), (W * 0.3, 270))):
        _worship(ctx, x, H * 0.97, h, 1, t, 300 + i)
    for i, (x, h) in enumerate(((W * 0.6, 250), (W * 0.7, 270))):
        _worship(ctx, x, H * 0.97, h, -1, t, 310 + i)
    particles(ctx, t, 30, seed=7, color="teal_l", region=(W * 0.7, 0, W * 0.9, H), speed=(0, -20), alpha=0.5)
    ui_glyphs(ctx, t, seed=12, n=6)
