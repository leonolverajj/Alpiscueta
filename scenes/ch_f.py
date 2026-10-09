"""Batch F: crime and camps, the Trinity, the void, the light, and the final call."""
import math
import random

import cairo

from engine.kit import (FONT_CAPS, FONT_TITLE, H, W, at, bg_studio, blade, camera, caption_tag, cel, circle_pts,
                        clip, ease_back, ease_io, ease_out, fillp, glow, hatch, hud, lerp, lingrad, mix, particles,
                        setc, shape, speedlines, ss, stroke, text, ui_glyphs, win)
from engine import figures as F
from . import scene


# ----------------------------------------------------------------- shared helpers
def _faded(ctx, alpha, draw):
    """Draw into a group and paint it at alpha (fades a figure in or out)."""
    if alpha <= 0.002:
        return
    ctx.push_group()
    draw()
    grp = ctx.pop_group()
    ctx.set_source(grp)
    ctx.paint_with_alpha(min(1.0, alpha))


def _prefix(pts, k):
    """The first fraction k (0..1) of a polyline, measured by arc length."""
    lens = [0.0]
    for a, b in zip(pts, pts[1:]):
        lens.append(lens[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    target = lens[-1] * max(0.0, min(1.0, k))
    out = [pts[0]]
    for i in range(1, len(pts)):
        if lens[i] <= target:
            out.append(pts[i])
            continue
        a, b = pts[i - 1], pts[i]
        span = (lens[i] - lens[i - 1]) or 1.0
        f = (target - lens[i - 1]) / span
        out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
        break
    return out


def _churn(ctx, t, y0, amp, color, seed, crest, ink=4.5):
    """Rolling, chopped water: a smooth sum of swells, with foam on the crests."""
    ph = seed * 1.7
    top = []
    for i in range(41):
        x = -80 + i * (W + 160) / 40
        y = y0 + amp * (0.55 * math.sin(x * 0.0093 + t * 1.1 + ph)
                        + 0.30 * math.sin(x * 0.0231 - t * 1.9 + ph * 2.3)
                        + 0.15 * math.sin(x * 0.047 + t * 2.7 + ph * 0.7))
        top.append((x, y))
    shape(ctx, top + [(W + 80, H + 80), (-80, H + 80)], color, ink, smooth=True, seed=seed)
    rng = random.Random(seed)
    for i in range(1, len(top) - 1):
        x, y = top[i]
        if y < top[i - 1][1] and y < top[i + 1][1] and rng.random() < 0.7:
            stroke(ctx, [(x - 34, y + 12), (x, y - 2), (x + 30, y + 10)], 4, crest, alpha=0.75,
                   taper=(0.3, 0.6), seed=i)


def _sea(ctx, t, amp, warm=0.0):
    """Three churning layers of water. warm=0 is pitch dark, warm=1 is gold-lit."""
    c_back = mix(mix("sea", "ink", 0.35), "gold_d", warm * 0.5)
    c_mid = mix("sea", "gold_d", warm * 0.6)
    c_front = mix("ink", "gold_d", warm * 0.3)
    crest = mix("sea_l", "gold_l", warm)
    _churn(ctx, t * 0.9, H * 0.58, amp * 0.6, c_back, 11, crest, ink=3.5)
    _churn(ctx, t * 1.1, H * 0.71, amp * 0.85, c_mid, 12, crest, ink=4)
    _churn(ctx, t * 1.3, H * 0.87, amp * 1.0, c_front, 13, crest, ink=5.5)


# ----------------------------------------------------------------- s48 raskolnikov
def _axe_shadow(ctx, t, flick):
    """Shadow of an axe on the stairwell wall. Silhouette only."""
    p0 = (1260.0, 800.0)
    p1 = (1520.0 + math.sin(t * 0.7) * 14, 170.0 + math.sin(t * 1.1) * 10)
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    a = 0.88 * flick
    with at(ctx, p1[0], p1[1], 1.0, ang):
        stroke(ctx, [(-L, 0), (0, 0)], 18, "night", taper=(0.0, 0.0), wobble=0.0, alpha=a)
        head = [(-8, -78), (26, -90), (50, -62), (58, -20), (52, 0), (58, 26), (50, 64), (26, 92), (-8, 80)]
        shape(ctx, head, "night", 0, alpha=a)


@scene("raskolnikov")
def raskolnikov(ctx, t, T, seg):
    u = t / T
    k_line = ease_out(win(u, 0.60, 0.70), 2)     # the crimson split sweeps down
    k_grey = ss(win(u, 0.70, 0.84))              # the right side drains to grey
    k_crack = ss(win(u, 0.74, 0.92))             # cracks run out from the split
    flick = 0.9 + 0.1 * math.sin(t * 11.0) * math.sin(t * 2.7)

    bg_studio(ctx, t, seed=41, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.08), focus=(W * 0.5, H * 0.5))

    # stairwell wall, plaster cracks, door
    fillp(ctx, [(-40, -40), (W + 40, -40), (W + 40, H * 0.80), (-40, H * 0.80)], mix("g4", "night", 0.35))
    for i, (x, y) in enumerate([(300, 120), (640, 260), (1500, 90), (1720, 480)]):
        stroke(ctx, [(x, y), (x + 40, y + 120), (x + 10, y + 230)], 3, "g6", alpha=0.6, seed=i)
    shape(ctx, [(120, 240), (440, 240), (440, 830), (120, 830)], "night", 6, seed=2)
    stroke(ctx, [(160, 280), (400, 280), (400, 800), (160, 800)], 3, "g5", closed=True, alpha=0.7)

    # lamp and its warm pool on the wall
    glow(ctx, 1110, 200, 820, "gold", 0.42 * flick)
    shape(ctx, [(1080, 120), (1140, 120), (1150, 170), (1070, 170)], "g4", 4, seed=3)

    # stairs going down toward the viewer
    fillp(ctx, [(-40, H * 0.80), (W + 40, H * 0.80), (W + 40, H + 40), (-40, H + 40)], "night")
    for i in range(6):
        y = H * 0.80 + 26 + i * 44 + i * i * 2
        stroke(ctx, [(-40, y + i * 3), (W + 40, y - 6 + i * 3)], 5, "g6", taper=(0.02, 0.02), alpha=0.9, seed=i)

    _axe_shadow(ctx, t, flick)

    # Raskolnikov, gaunt, clutching his coat
    F.character(ctx, 1000, 430, 1.25, F.RASKOL, "fear", t)
    with at(ctx, 1000, 430, 1.25):
        F.hand(ctx, -78, 214, a=0.3, s=1.5, color=mix("skin", "skin_s", 0.3), kind="fist")

    # the split: crimson line, then the right half drains and cracks
    xt, xb = W * 0.56, W * 0.45
    with hud(ctx):
        if k_line > 0:
            stroke(ctx, [(xt, 0), (lerp(xt, xb, k_line), H * k_line)], 12, "red", taper=(0.0, 0.0),
                   wobble=0.05, seed=5)
        if k_grey > 0:
            ext = (xt - xb) * 60 / H
            right = [(xt, 0), (W + 60, 0), (W + 60, H + 60), (xb - ext, H + 60)]
            with clip(ctx, right):
                ctx.set_operator(cairo.OPERATOR_HSL_SATURATION)
                setc(ctx, "g4", k_grey)
                ctx.paint()
                ctx.set_operator(cairo.OPERATOR_OVER)
                setc(ctx, "night", 0.35 * k_grey)
                ctx.paint()
                rng = random.Random(7)
                for i in range(7):
                    y0 = rng.uniform(0.1, 0.9) * H
                    x0 = xt + (xb - xt) * (y0 / H)
                    pts = [(x0, y0)]
                    for _ in range(4):
                        x, y = pts[-1]
                        pts.append((x + rng.uniform(40, 120), y + rng.uniform(-80, 80)))
                    part = _prefix(pts, k_crack)
                    if len(part) > 1:
                        stroke(ctx, part, 5, "ink", taper=(0.05, 0.3), seed=i)
                        stroke(ctx, part, 1.6, "g0", alpha=0.7, taper=(0.05, 0.3), seed=i)
        text(ctx, "ANTES", 140, 150, 64, FONT_CAPS, "g0", align="left", tracking=0.12, alpha=k_line)
        text(ctx, "DESPUÉS", W - 140, 150, 64, FONT_CAPS, "g2", align="right", tracking=0.12, alpha=k_grey)

    caption_tag(ctx, "CRIMEN Y CASTIGO", 100, H - 170, t, size=40, appear=0.5)
    ui_glyphs(ctx, t, seed=6)


# ----------------------------------------------------------------- s49 gulag
def _book(ctx, cx, cy, t):
    """Open book with crimson boards and a title on the left page."""
    fillp(ctx, circle_pts(cx, cy + 160, 340, 40, ry=34), "ink", alpha=0.18)
    shape(ctx, [(cx - 340, cy - 40), (cx, cy - 90), (cx + 340, cy - 40), (cx + 352, cy + 120), (cx, cy + 170),
                (cx - 352, cy + 120)], "red_d", 6, seed=1)
    stroke(ctx, [(cx - 326, cy - 26), (cx, cy - 72), (cx + 326, cy - 26)], 2.5, "gold", alpha=0.8)
    for side in (-1, 1):
        pg = [(cx, cy - 70), (cx + side * 320, cy - 36), (cx + side * 330, cy + 100), (cx, cy + 140)]
        shape(ctx, pg, "g0", 5, seed=2 + side)
        rng = random.Random(30 + side)
        for k in range(9):
            y = cy - 6 + k * 16
            L = rng.uniform(170, 240)
            stroke(ctx, [(cx + side * 40, y), (cx + side * (40 + L), y - 4 + rng.uniform(-3, 3))], 2.6, "g5",
                   alpha=0.8, taper=(0.1, 0.3), seed=k)
    stroke(ctx, [(cx, cy - 70), (cx, cy + 140)], 6, "ink")
    text(ctx, "LOS DEMONIOS", cx - 165, cy - 24, 26, FONT_TITLE, "ink", tracking=0.04)


def _fence(ctx, x0, x1, ytop, ybot):
    xs = [x0 + i * (x1 - x0) / 6 for i in range(7)]
    for x in xs:
        stroke(ctx, [(x, ybot), (x + 2, ytop)], 7, "g5", taper=(0.0, 0.0), wobble=0.05, seed=int(x) % 97)
    for yy in (ytop + 30, ytop + 70):
        wire = [(x, yy + (6 if i % 2 else 0)) for i, x in enumerate(xs)]
        stroke(ctx, wire, 2.5, "ink", smooth=True, taper=(0.0, 0.0))
        for j in range(12):
            bx = x0 + (x1 - x0) * (j + 0.5) / 12
            by = yy + 2 * math.sin(j * 1.3)
            stroke(ctx, [(bx - 7, by - 7), (bx + 7, by + 7)], 3, "ink", taper=(0, 0))
            stroke(ctx, [(bx - 7, by + 7), (bx + 7, by - 7)], 3, "ink", taper=(0, 0))


def _tower(ctx, x, yb, t):
    for dx in (-60, 60):
        stroke(ctx, [(x + dx, yb - 250), (x + dx * 1.15, yb)], 9, "ink", taper=(0.0, 0.0))
    stroke(ctx, [(x - 60, yb - 120), (x + 60, yb - 60)], 5, "ink", taper=(0.0, 0.0))
    # searchlight sweeping over the camp
    o = (x, yb - 290)
    a = math.pi * 0.5 + 0.5 + math.sin(t * 0.55) * 0.4
    far = [(o[0] + math.cos(a + d) * 1000, o[1] + math.sin(a + d) * 1000) for d in (-0.12, 0.12)]
    fillp(ctx, [o, far[0], far[1]], "gold_l", alpha=0.20)
    shape(ctx, [(x - 80, yb - 330), (x + 80, yb - 330), (x + 80, yb - 240), (x - 80, yb - 240)], "ink", 5, seed=4)
    shape(ctx, [(x - 100, yb - 330), (x, yb - 400), (x + 100, yb - 330)], "ink", 5, seed=5)
    fillp(ctx, [(x - 40, yb - 300), (x + 40, yb - 300), (x + 40, yb - 272), (x - 40, yb - 272)], "gold_l")
    glow(ctx, o[0], o[1], 110, "gold_l", 0.5)


@scene("gulag")
def gulag(ctx, t, T, seg):
    u = t / T
    k_real = ss(win(u, 0.56, 0.70))
    divx = lambda y: lerp(W * 0.52, W * 0.48, y / H)  # the divider between the two worlds
    left = [(-60, -60), (divx(-60), -60), (divx(H + 60), H + 60), (-60, H + 60)]
    right = [(divx(-60), -60), (W + 80, -60), (W + 80, H + 60), (divx(H + 60), H + 60)]

    fillp(ctx, [(-60, -60), (W + 80, -60), (W + 80, H + 60), (-60, H + 60)], "paper")
    camera(ctx, t, T, zoom=(1.0, 1.05), focus=(W / 2, H / 2))

    # ---- left: the book of the prophecy
    with clip(ctx, left):
        hatch(ctx, [(0, 0), (W * 0.3, 0), (W * 0.3, H), (0, H)], angle=0.7, gap=18, w=1.2, color="g4",
              alpha=0.25, seed=3)
        cx, cy = 520, 640
        _book(ctx, cx, cy, t)
        for i in range(6):
            k = (t * 0.11 + i / 6) % 1.0
            x = cx + math.sin(i * 2.1) * (60 + 110 * k)
            y = cy - 40 - k * 420
            h = 170 + 70 * (1 - k)
            alpha = ss(k * 5) * (1 - ss((k - 0.6) / 0.4))
            _faded(ctx, alpha, lambda x=x, y=y, h=h, i=i: F.person(
                ctx, x, y, h, "ink", shade="g6", pose="stand", t=t, fx=1 if i % 2 else -1, seed=i, arm_up=0.6))

    # ---- right: the camp in snow
    with clip(ctx, right):
        fillp(ctx, [(divx(0), 0), (W + 80, 0), (W + 80, H + 60), (divx(H), H + 60)], "night")
        fillp(ctx, [(divx(H * 0.6), H * 0.6), (W + 80, H * 0.52), (W + 80, H + 60), (divx(H), H + 60)], "g2")
        fillp(ctx, [(divx(H * 0.6), H * 0.6), (W + 80, H * 0.52), (W + 80, H * 0.58), (divx(H * 0.6), H * 0.64)],
              "g0", alpha=0.9)
        _fence(ctx, W * 0.56, W * 0.82, H * 0.60, H * 0.78)
        _tower(ctx, W * 0.86, H * 0.70, t)
        for i in range(6):
            x = W * 0.55 + i * 175 - (t * 26) % 175
            y = H * 0.9 + math.sin(i * 1.7) * 14
            F.person(ctx, x, y, 230, "ink2", shade="ink", pose="walk", t=t + i * 0.3, fx=1, seed=i, ink=4)
        particles(ctx, t, 90, seed=8, color="g0", region=(W * 0.5, 0, W, H), speed=(-14, 55), size=(1.0, 2.6),
                  alpha=0.7)

    # ---- the thread that links prophecy and reality
    thread = [(800, 600), (960, 420), (1120, 470), (1240, 650), (1380, 860)]
    kt = ease_out(win(u, 0.22, 0.52), 2)
    if kt > 0.01:
        stroke(ctx, _prefix(thread, kt), 7, "red", smooth=True, taper=(0.02, 0.15), seed=2)
        stroke(ctx, _prefix(thread, kt), 2.2, "red_l", smooth=True, taper=(0.02, 0.15), seed=2)
    if kt >= 0.99:
        bx, by = _prefix(thread, (t * 0.12) % 1.0)[-1]
        glow(ctx, bx, by, 70, "red_l", 0.8)
        fillp(ctx, circle_pts(bx, by, 6, 12), "g0")

    caption_tag(ctx, "PROFECÍA", 100, 100, t, size=44, appear=0.2, accent="red")
    caption_tag(ctx, "REALIDAD", 1180, 100, t, size=44, appear=T * 0.58, accent="gold")
    ui_glyphs(ctx, t, seed=12, region=(W * 0.5, H * 0.6, W, H))


# ----------------------------------------------------------------- s50 trinity
def _c_padre(ctx, t, R):
    """An old king's hand offers a covenant scroll."""
    glow(ctx, 0, -40, R * 1.2, "gold", 0.45)
    sleeve = [(-R - 30, -60), (-120, -80), (-70, 30), (-60, 110), (-R - 30, 150)]
    shape(ctx, sleeve, "red_d", 5, seed=3)
    cel(ctx, sleeve, [(-R - 30, -10), (-90, -10), (-60, 150), (-R - 30, 150)], "red")
    shape(ctx, [(-124, -88), (-96, -96), (-48, 34), (-78, 46)], "gold", 4, seed=4)
    dy = math.sin(t * 1.1) * 4
    with at(ctx, 0, dy, 1.0):
        # open palm turned up, knuckled old hand, offering
        palm = [(-66, 34), (-34, 12), (8, 8), (44, 14), (58, 34), (20, 52), (-40, 54)]
        shape(ctx, palm, "skin2", 4.5, seed=6)
        for i in range(4):
            x0 = 14 + i * 13
            pts = [(x0, 14 + i * 2), (x0 + 12, -4 + i * 2), (x0 + 18 - (i % 2) * 4, -14 + i * 1)]
            stroke(ctx, pts, 17, "ink", taper=(0, 0))
            stroke(ctx, pts, 11, "skin2", taper=(0, 0.25))
        thumb = [(-30, 16), (-14, -6), (4, -12)]
        stroke(ctx, thumb, 17, "ink", taper=(0, 0))
        stroke(ctx, thumb, 11, "skin2", taper=(0, 0.25))
        for k in range(3):   # knuckle creases
            stroke(ctx, [(-10 + k * 16, 24), (-6 + k * 16, 36)], 2.2, "skin_s", alpha=0.8, taper=(0.2, 0.2))
        # the covenant scroll, held just above the palm
        with at(ctx, 4, -36 + math.sin(t * 1.3) * 3, 1.0, -0.08):
            shape(ctx, [(-62, -16), (62, -16), (62, 16), (-62, 16)], "paper", 4, seed=7)
            shape(ctx, circle_pts(-62, 0, 19, 16), "g2", 4, seed=8)
            shape(ctx, circle_pts(62, 0, 19, 16), "g2", 4, seed=9)
            for k in range(2):
                stroke(ctx, [(-40, -6 + k * 12), (40, -6 + k * 12)], 2.2, "g4", alpha=0.7, taper=(0.2, 0.2))
            fillp(ctx, circle_pts(0, 0, 10, 14), "red")
            stroke(ctx, circle_pts(0, 0, 12.5, 14), 2.5, "gold", closed=True, taper=(0, 0))


def _c_hijo(ctx, t, R):
    """Sunrise over a slain dragon; the son stands with a raised sword."""
    fillp(ctx, circle_pts(0, 0, R, 72), "cobalt_d")
    glow(ctx, 0, 40, R * 1.1, "gold_l", 0.5)
    upper = [(math.cos(a) * 118, 40 + math.sin(a) * 118) for a in [math.pi + i * math.pi / 24 for i in range(25)]]
    fillp(ctx, upper, "gold_l")
    for i in range(9):
        a = math.pi + (i + 0.5) * math.pi / 9
        stroke(ctx, [(math.cos(a) * 150, 40 + math.sin(a) * 150), (math.cos(a) * 200, 40 + math.sin(a) * 200)],
               6, "gold_l", alpha=0.5, taper=(0.2, 0.6), seed=i)
    fillp(ctx, [(-R - 10, 40), (-100, 30), (0, 46), (110, 28), (R + 10, 40), (R + 10, R + 10), (-R - 10, R + 10)],
          "ink")
    F.character(ctx, -18, -66, 0.62, F.HERO, "grim", t)
    F.limb(ctx, (46, 30), (106, -20), (94, -66), 26, 20, "coat", "coat_s", 4.5, 3)
    shape(ctx, blade((92, -74), (104, -186), 20, bend=0.05), "steel_l", 3.5, seed=8)
    stroke(ctx, [(74, -74), (110, -70)], 8, "gold", taper=(0, 0))
    F.hand(ctx, 92, -66, a=-0.2, s=0.7, color="coat", kind="fist")
    # the slain dragon lies across the foreground
    F.serpent(ctx, [(-210, 172), (-120, 160), (-30, 156), (60, 150), (120, 150)], t, thick=44, body="teal",
              belly="teal_l", spikes_c="ink2", head_size=0.9, seed=5, wave=0.0, open_jaw=0.0, ink=4)


def _flame(ctx, x0, base, L, sway, w, color, alpha=0.9):
    """One curved flame tongue rising from (x0, base) to a tip at height L."""
    tip = (x0 + sway, base - L)
    pts = [(x0 - w / 2, base), (x0 - w * 0.55 + sway * 0.3, base - L * 0.5), tip,
           (x0 + w * 0.5 + sway * 0.4, base - L * 0.45), (x0 + w / 2, base)]
    shape(ctx, pts, color, 0, smooth=True, alpha=alpha)


def _c_espiritu(ctx, t, R):
    """A flame that burns without consuming the bush: the leaves stay green and whole."""
    glow(ctx, 0, 90, R * 1.1, "teal", 0.30)
    rng = random.Random(21)
    for i in range(17):   # a rounded bush, rooted low, leaves intact
        bx = -150 + i * 19 + rng.uniform(-5, 5)
        tip = (bx + rng.uniform(-26, 26), 150 - rng.uniform(80, 120))
        shape(ctx, blade((bx, 170), tip, 40, bend=rng.uniform(-0.25, 0.25)),
              "teal_d" if i % 3 else "sea", 4, seed=i)
        stroke(ctx, [(bx, 150), (tip[0] * 0.8 + bx * 0.2, tip[1] + 18)], 2.2, "teal", alpha=0.55, taper=(0.2, 0.6))
    glow(ctx, 0, 84, 150, "teal_l", 0.45)
    # flame tongues rising from the bush's heart: curved outer, lighter inner, white core
    for i in range(5):
        x0 = lerp(-40, 40, i / 4)
        L = (120 + 60 * math.sin(t * 6 + i * 1.7) + (i % 2) * 20) * (1 - 0.25 * abs(i - 2) / 2)
        _flame(ctx, x0, 96, L, math.sin(t * 4 + i) * 10, 52, "teal", 0.9)
    for i in range(3):
        x0 = lerp(-22, 22, i / 2)
        L = (100 + 40 * math.sin(t * 7 + i * 2.3)) * (1 - 0.2 * abs(i - 1))
        _flame(ctx, x0, 96, L, math.sin(t * 5 + i * 1.1) * 8, 28, "teal_l", 0.95)
    _flame(ctx, 0, 100, 110 + 14 * math.sin(t * 9), math.sin(t * 7) * 5, 12, "white", 0.95)
    particles(ctx, t, 26, seed=4, color="teal_l", region=(-R, -R, R, R), speed=(-6, -34), size=(1.0, 2.6),
              alpha=0.7)


def _medallion(ctx, t, cx, cy, R, appear, base, content, label, words, seed):
    k = ease_back(win(t, appear, appear + 0.7), 1.5)
    if k <= 0.01:
        return
    with at(ctx, cx, cy, 0.8 + 0.2 * k):
        glow(ctx, 0, 0, R * 1.5, base, 0.35 * k)
        disc = circle_pts(0, 0, R, 72)
        fillp(ctx, disc, "night")
        with clip(ctx, disc):
            content(ctx, t, R)
        stroke(ctx, circle_pts(0, 0, R + 16, 72), 10, "gold", closed=True, taper=(0, 0), wobble=0.05, seed=seed)
        for j in range(24):
            a = 2 * math.pi * j / 24
            stroke(ctx, [(math.cos(a) * (R + 26), math.sin(a) * (R + 26)),
                         (math.cos(a) * (R + 38), math.sin(a) * (R + 38))], 4, "gold_d", taper=(0, 0))
    text(ctx, label, cx, cy + R + 84, 56, FONT_TITLE, "g0", tracking=0.14, alpha=k)
    offs = [(-150, -(R + 46)), (150, -(R + 46)), (-150, R + 30), (150, R + 30)]   # clear of the ring
    for j, w in enumerate(words):
        ka = ss(win(t, appear + 0.5 + j * 0.25, appear + 1.0 + j * 0.25))
        if ka <= 0.01:
            continue
        ox, oy = offs[j]
        x = cx + ox + math.sin(t * 0.5 + j) * 6
        y = cy + oy + math.sin(t * 0.8 + j) * 5
        pulse = 0.6 + 0.4 * math.sin(t * 1.5 + j * 2.1)
        text(ctx, w, x, y, 26, FONT_CAPS, "g2", tracking=0.1, alpha=0.9 * ka * pulse)


@scene("trinity")
def trinity(ctx, t, T, seg):
    bg_studio(ctx, t, seed=50, dark=True, tone=-0.2)
    camera(ctx, t, T, zoom=(1.0, 1.04), focus=(W / 2, H / 2))
    _medallion(ctx, t, 380, 440, 200, 0.05 * T, "red", _c_padre, "PADRE",
               ["PACTO", "SACRIFICIO", "JUZGA", "PERDONA"], 3)
    _medallion(ctx, t, 960, 440, 200, 0.40 * T, "cobalt", _c_hijo, "HIJO",
               ["CAOS EN ORDEN", "DRAGONES", "MUERTE", "RENACE"], 5)
    _medallion(ctx, t, 1540, 440, 200, 0.72 * T, "teal", _c_espiritu, "ESPÍRITU",
               ["CONCIENCIA", "ENGAÑO", "ARROGANCIA", "RESENTIMIENTO"], 7)
    ui_glyphs(ctx, t, seed=13, region=(0, H * 0.85, W, H), n=6)


# ----------------------------------------------------------------- s51 deep waters
def _spirit(ctx, x, y, t, k=1.0):
    """A luminous bird-like wind gliding over the water."""
    flap = math.sin(t * 2.4)
    with at(ctx, x, y, 1.0, 0.05 * math.sin(t * 0.9)):
        glow(ctx, 0, 0, 300, "teal_l", 0.30 * k)
        for side in (-1, 1):
            tip = (side * 210, -30 - flap * 50)
            fillp(ctx, blade((0, 0), tip, 54, bend=side * 0.2), "teal_l", alpha=0.75 * k)
            fillp(ctx, blade((0, 0), (tip[0] * 0.9, tip[1] * 0.9), 22, bend=side * 0.2), "white", alpha=0.6 * k)
        fillp(ctx, circle_pts(0, 0, 22, 14, ry=40), "white", alpha=0.9 * k)
        fillp(ctx, blade((0, 20), (0, 120), 26), "teal_l", alpha=0.6 * k)


@scene("deep_waters")
def deep_waters(ctx, t, T, seg):
    u = t / T
    ctx.set_source(lingrad(ctx, 0, 0, 0, H * 0.7, [(0, "ink"), (1, "night")]))
    ctx.paint()
    camera(ctx, t, T, zoom=(1.0, 1.06), focus=(W / 2, H / 2))
    rng = random.Random(3)
    for i in range(60):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.4)
        fillp(ctx, circle_pts(x, y, rng.uniform(1, 2.2), 6), "g3", alpha=0.25 + 0.2 * math.sin(t * 1.5 + i))

    _sea(ctx, t, 90)
    sx = lerp(W * 0.08, W * 0.92, u)
    sy = H * 0.36 + math.sin(t * 0.9) * 24
    fade_in = ss(win(u, 0.04, 0.2)) * (1 - ss(win(u, 0.9, 1.0)))
    for j in range(5):   # faint trail behind the spirit
        stroke(ctx, [(sx - 150 - j * 40, sy + 10 + j * 6), (sx - 60 - j * 30, sy + 4)], 3, "teal_l",
               alpha=0.18 * fade_in * (1 - j / 5), taper=(0.9, 0.0), seed=j)
    _spirit(ctx, sx, sy, t, fade_in)
    particles(ctx, t, 110, seed=4, color="teal_l", alpha=0.45, speed=(18, -35), size=(1.0, 2.8))
    ui_glyphs(ctx, t, seed=14, region=(0, H * 0.55, W, H), n=5)


# ----------------------------------------------------------------- s52 light
@scene("light")
def light_scene(ctx, t, T, seg):
    u = t / T
    k_pt = ss(win(u, 0.22, 0.34))
    k_burst = ease_out(win(u, 0.34, 0.50), 3)
    flood = ss(win(u, 0.42, 0.53)) * (1 - ss(win(u, 0.62, 0.82)))
    calm = ss(win(u, 0.50, 0.90))
    amp = lerp(95, 6, calm)
    warm = ss(win(u, 0.50, 0.92)) * 0.9
    sx, sy = W / 2, H * 0.44

    ctx.set_source(lingrad(ctx, 0, 0, 0, H * 0.7, [(0, "ink"), (1, mix("night", "gold_d", 0.3 * k_burst))]))
    ctx.paint()
    camera(ctx, t, T, zoom=(1.0, 1.05), focus=(W / 2, H / 2))

    if k_burst > 0:
        glow(ctx, sx, sy, lerp(200, 1100, k_burst), "gold_l", 0.6 * k_burst)
    _sea(ctx, t, amp, warm)

    # rays burst from the point of light
    if k_burst > 0:
        ray_a = 0.45 * k_burst * (1 - 0.6 * calm)
        for i in range(36):
            ang = i * 2 * math.pi / 36 + 0.05 * math.sin(i * 3.1)
            L = lerp(0, 1500, k_burst) * (0.6 + 0.4 * math.sin(i * 7.1))
            fillp(ctx, [(sx, sy), (sx + math.cos(ang - 0.03) * L, sy + math.sin(ang - 0.03) * L),
                        (sx + math.cos(ang + 0.03) * L, sy + math.sin(ang + 0.03) * L)],
                  "gold_l", alpha=ray_a)
    # the point of light itself
    if k_pt > 0 and k_burst < 0.95:
        glow(ctx, sx, sy, 60 + 60 * k_pt, "white", 0.9 * k_pt)
        fillp(ctx, circle_pts(sx, sy, 4 + 8 * k_pt, 14), "white", alpha=k_pt)

    # the calm water mirrors the light
    if calm > 0:
        glow(ctx, sx, H * 0.78, 620, "gold_l", 0.45 * calm)
        for j in range(16):
            y = H * 0.6 + j * 30
            w = (1 - j / 16) * 300 * calm
            stroke(ctx, [(sx - w, y), (sx + w, y)], 4 + j * 0.25, "gold_l", alpha=0.7 * calm,
                   taper=(0.2, 0.2), seed=j)

    # white-gold flood, then it clears to reveal the calm sea
    if flood > 0:
        setc(ctx, mix("white", "gold_l", 0.45), flood)
        ctx.paint()
    ui_glyphs(ctx, t, seed=15, region=(0, H * 0.6, W, H), n=4, alpha=0.6 * (1 - flood))


# ----------------------------------------------------------------- s53 hero final
def _eye_halo(ctx, cx, cy, R, k, t):
    """A faint ring of watching eyes behind the hero (own design, Marduk-like idea)."""
    n = 14
    for i in range(n):
        a = -math.pi / 2 + (i - n / 2 + 0.5) * (2 * math.pi / n)
        ex, ey = cx + math.cos(a) * R, cy + math.sin(a) * R * 0.82
        kk = ss(k * 1.6 - i / n * 0.6)
        if kk <= 0.01:
            continue
        blink = 0.85 + 0.15 * math.sin(t * 2 + i)
        with at(ctx, ex, ey, 1.25, a + math.pi / 2):
            glow(ctx, 0, 0, 60, "teal", 0.3 * kk)
            shape(ctx, [(-30, 0), (0, -18 * blink), (30, 0), (0, 18 * blink)], "g0", 3, alpha=0.6 * kk)
            fillp(ctx, circle_pts(0, 0, 10, 14), "teal", alpha=0.85 * kk)
            fillp(ctx, circle_pts(0, 0, 4.5, 10), "ink", alpha=0.9 * kk)


def _lids(ctx, open_k):
    """Eyelids in head coordinates: closed at 0, open at 1. Each lid covers only its own eye."""
    closed = 1 - open_k
    if closed <= 0.01:
        return
    skin = F.HERO["skin"]
    for ex, ew, ey in ((34, 40, -4), (-18, 29, -2)):
        top = ey - 16
        lid = lerp(top, ey + 7, closed)
        fillp(ctx, [(ex - ew / 2 - 3, top), (ex + ew / 2 + 3, top), (ex + ew / 2 + 3, lid), (ex - ew / 2 - 3, lid)],
              skin)
        stroke(ctx, [(ex - ew / 2, lid), (ex + ew * 0.1, lid + 1.5), (ex + ew / 2 - 2, lid - 1)], 4, "ink",
               taper=(0.15, 0.15), smooth=True)


def _hero(ctx, x, y, s, t, open_k, wind, light):
    c = F.HERO
    with at(ctx, x, y, s):
        F.bust(ctx, c, t, wind, width=1.0)
        with at(ctx, 0, math.sin(t * 1.6) * 1.5):
            F.head(ctx, c, "grim", t, wind)
            if light > 0.01:
                fillp(ctx, [(8, -96), (72, -44), (70, 6), (44, 60), (16, 88), (-4, -40)], "gold_l",
                      alpha=0.32 * light)
                glow(ctx, 40, -30, 200, "gold_l", 0.3 * light)
                stroke(ctx, [(-40, -118), (10, -150), (62, -118)], 6, "gold_l", alpha=0.6 * light, taper=(0.3, 0.3))
            _lids(ctx, open_k)


@scene("hero_final")
def hero_final(ctx, t, T, seg):
    u = t / T
    open_k = ease_io(win(u, 0.12, 0.34))     # eyes open
    light = ss(win(u, 0.28, 0.50))           # light finds his face
    ring = ss(win(u, 0.48, 0.70))            # the watching ring appears
    step = ease_io(win(u, 0.62, 0.95))       # he steps forward
    wind = 0.3 + 0.9 * step
    hx, hy = lerp(640, 690, step), lerp(470, 500, step)
    hs = lerp(1.45, 1.7, step)

    bg_studio(ctx, t, seed=53, dark=True, tone=-0.4)
    camera(ctx, t, T, zoom=(1.0, 1.12), focus=(W * 0.42, H * 0.5))
    glow(ctx, W * 0.7, H * 0.45, 900, "teal_d", 0.35)

    # the huge dark-teal dragon, facing him from the right
    path = [(W + 400, H + 120), (W * 0.98, H * 0.86), (W * 0.84, H * 0.66), (W * 0.74, H * 0.5),
            (W * 0.64, H * 0.42), (W * 0.58, H * 0.40)]
    F.serpent(ctx, path, t, thick=120, body=mix("teal_d", "ink", 0.35), belly="sea_l", spikes_c="ink2",
              head_size=1.25, seed=21, wave=18, open_jaw=0.55)

    if light > 0:
        beam = [(W * 0.62, -40), (W * 0.80, -40), (hx + 150, hy - 60), (hx - 40, hy + 40)]
        fillp(ctx, beam, "gold_l", alpha=0.22 * light)

    _eye_halo(ctx, hx, hy - 30, 330 * hs / 1.45, ring, t)
    glow(ctx, hx, H * 1.02, 640, "gold_l", 0.22 * light)   # floor light under his feet
    speedlines(ctx, hx, hy, t, 30, 420, 1500, "gold_l", alpha=0.12 * step)
    _hero(ctx, hx, hy, hs, t, open_k, wind, light)
    particles(ctx, t, 70, seed=17, color="gold_l", alpha=0.55, speed=(-8, -46), size=(1.0, 3.0))
    ui_glyphs(ctx, t, seed=16, n=8)
