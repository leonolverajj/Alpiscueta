"""Batch B (chapter 3, 'El sueno'): island map, argument, fog mediators, subpersonalities,
rage god, dreamer, carver, myth quote. All characters are original designs."""
import math
import random

from engine import figures as F
from engine.kit import (FONT_CAPS, FONT_SERIF, H, W, at, bg_studio, blade, camera, caption_tag, catmull,
                        cel, circle_pts, clip, ease_back, ease_io, fillp, glow, hatch, hud, lerp, lingrad,
                        mix, particles, ribbon, rot, shape, spikes, ss, stroke, text, ui_glyphs, win)
from . import scene


# ----------------------------------------------------------------- shared helpers
def _angles(a0, a1, n):
    return [a0 + (a1 - a0) * i / n for i in range(n + 1)]


def _organic(cx, cy, rx, ry, angles, seed, amp=0.06):
    """Hand-drawn looking closed-ish curve: ellipse with a few sinusoidal wobbles."""
    rng = random.Random(seed)
    p0, p1, p2 = (rng.uniform(0, 6.28) for _ in range(3))
    out = []
    for a in angles:
        m = 1 + amp * (math.sin(3 * a + p0) + 0.6 * math.sin(5 * a + p1) + 0.3 * math.sin(9 * a + p2))
        out.append((cx + math.cos(a) * rx * m, cy + math.sin(a) * ry * m))
    return out


def _bez(p0, p1, p2, p3, u):
    v = 1 - u
    a, b, c, d = v ** 3, 3 * v * v * u, 3 * v * u * u, u ** 3
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def _curve(p0, p1, p2, p3, n=40):
    return [_bez(p0, p1, p2, p3, i / n) for i in range(n + 1)]


def _sea(ctx, x0, x1, y0, amp, t, seed, body="sea", crest="g1"):
    """Band of waves whose top edge bobs; fills everything below it."""
    rng = random.Random(seed)
    n = 12
    pts = [(x0, H + 40)]
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        y = y0 + (-amp if i % 2 == 0 else amp * 0.5) * rng.uniform(0.6, 1.2) + math.sin(t * 1.3 + i * 0.9) * amp * 0.4
        pts.append((x, y))
    pts.append((x1, H + 40))
    shape(ctx, pts, body, ink=4.5, seed=seed)
    for i in range(1, n, 2):
        x, y = pts[i + 1]
        stroke(ctx, [(x - 36, y + 14), (x, y + 2), (x + 30, y + 10)], 4, crest, alpha=0.7, taper=(0.3, 0.6),
               seed=i)


def _lp(px, py, s, fx, x, y):
    """Local figure point (x, y) -> screen, for a figure placed at (px, py) with scale s and flip fx."""
    return (px + fx * x * s, py + y * s)


# ================================================================= s12 island_map
ISL = (280, 190)
MIST_IN = (360, 255)
MIST_OUT = (600, 420)


@scene("island_map")
def island_map(ctx, t, T, seg):
    cx, cy = W / 2, H / 2
    z = lerp(1.35, 1.0, ease_io(t / max(T, 1e-6)))       # camera zoom, mirrored for label anchors
    camera(ctx, t, T, zoom=(1.35, 1.0), focus=(cx, cy))

    # open ocean, drawn in world space so it extends past the frame
    fillp(ctx, [(-W, -H), (2 * W, -H), (2 * W, 2 * H), (-W, 2 * H)], mix("night", "sea", 0.5))
    glow(ctx, cx, cy, 1100, "sea_l", 0.35)
    for r in range(-4, 24):
        y = r * 110 + 30
        for c in range(-6, 26):
            x = c * 150 + (r % 2) * 70 + math.sin(t * 0.4 + r * 0.7 + c) * 5
            stroke(ctx, [(x, y), (x + 40, y - 9), (x + 82, y)], 3, "sea_l", taper=(0.2, 0.2), alpha=0.35,
                   seed=r * 37 + c)
    # two sea-serpent hints, faded
    for path, a, sd in (([(cx + 980, cy + 640), (cx + 760, cy + 600), (cx + 700, cy + 430), (cx + 880, cy + 330)],
                         0.5, 4),
                        ([(cx - 1020, cy + 300), (cx - 820, cy + 330), (cx - 760, cy + 470)], 0.35, 9)):
        ctx.push_group()
        F.serpent(ctx, path, t, thick=54, body="sea_l", belly="teal", spikes_c="ink2", head_size=0.8, seed=sd,
                  wave=6, open_jaw=0.1)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(min(1.0, a * 1.6))

    a0 = -math.pi / 2
    # ring 2: misty band sweeps on
    sw = ease_io(win(t, 0.12 * T, 0.42 * T)) * 2 * math.pi
    if sw > 0.02:
        angs = _angles(a0, a0 + sw, 120)
        outer = _organic(cx, cy, *MIST_OUT, angs, 21)
        inner = _organic(cx, cy, *MIST_IN, angs, 22)
        fillp(ctx, outer + inner[::-1], "g1", alpha=0.28)
        rng = random.Random(5)
        for i in range(80):
            a = a0 + rng.uniform(0, 1) * sw
            k = rng.uniform(0, 1)
            px = cx + math.cos(a) * lerp(MIST_IN[0], MIST_OUT[0], k)
            py = cy + math.sin(a) * lerp(MIST_IN[1], MIST_OUT[1], k)
            glow(ctx, px, py, rng.uniform(50, 110), "g0", 0.2 + 0.07 * math.sin(t * 0.9 + i))
        stroke(ctx, outer, 4, "g2", alpha=0.7, taper=(0.1, 0.1), seed=2)
        stroke(ctx, inner, 4, "g2", alpha=0.7, taper=(0.1, 0.1), seed=3)

    # ring 3: outer edge of the ocean
    sw3 = ease_io(win(t, 0.45 * T, 0.7 * T)) * 2 * math.pi
    if sw3 > 0.02:
        edge = _organic(cx, cy, 860, 600, _angles(a0, a0 + sw3, 120), 31, amp=0.05)
        stroke(ctx, edge, 4, "teal", alpha=0.6, taper=(0.1, 0.1), seed=7)

    # the island, pops in first
    k_isl = ease_back(win(t, 0.0, 0.14 * T), 1.6)
    if k_isl > 0.01:
        base = _organic(0, 0, *ISL, _angles(0, 2 * math.pi, 48)[:-1], 7, amp=0.08)
        with at(ctx, cx, cy, k_isl):
            shape(ctx, base, "gold_l", ink=6, seed=3)
            cel(ctx, base, [(-400, 30), (400, 30), (400, 400), (-400, 400)], "gold")
            shape(ctx, [(-150, 40), (-60, -90), (20, 40)], "teal_d", ink=4, seed=4)
            shape(ctx, [(0, 50), (90, -40), (190, 50)], "rust", ink=4, seed=5)
            hatch(ctx, base, -0.9, 16, 1.4, "gold_d", 0.35, 6)

    # labels: screen-space tags with leader lines to world anchors
    def S(px, py):
        return (cx + z * (px - cx), cy + z * (py - cy))

    labels = [
        ("LO QUE SABEMOS", (cx + 150, cy + 30), (1330, 300), "gold", 0.2),
        ("LO QUE INTUIMOS", (cx + 480 * math.cos(-0.6), cy + 337 * math.sin(-0.6)), (1310, 150), "teal", 0.45),
        ("LO DESCONOCIDO · CAOS", (cx - 760, cy + 280), (90, 880), "red", 0.7),
    ]
    for label, anc, tag, accent, frac in labels:
        ap = frac * T
        k = ss(win(t, ap, ap + 0.6))
        sx, sy = S(*anc)
        if k > 0:
            with hud(ctx):
                stroke(ctx, [(sx, sy), (tag[0] - 14, tag[1] + 34)], 3, "g0", alpha=0.85 * k, taper=(0.1, 0.3),
                       seed=int(frac * 10))
                fillp(ctx, circle_pts(sx, sy, 8, 14), accent, alpha=k)
        caption_tag(ctx, label, tag[0], tag[1], t, 34, accent=accent, appear=ap)
    ui_glyphs(ctx, t, seed=12)


# ================================================================= s13 argument
def _burst(cx, cy, rx, ry, seed, n=24):
    """Jagged speech-bubble outline (alternating long and short spikes)."""
    rng = random.Random(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        m = 1.0 if i % 2 == 0 else rng.uniform(0.82, 0.9)
        pts.append((cx + math.cos(a) * rx * m, cy + math.sin(a) * ry * m))
    return pts


def _scribble(ctx, x0, x1, y, amp, n, grow, seed):
    rng = random.Random(seed)
    pts = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts.append((x, y + (amp if i % 2 else -amp) * rng.uniform(0.6, 1.2)))
    m = max(2, int(len(pts) * grow))
    if grow > 0:
        stroke(ctx, pts[:m], 4, "ink", taper=(0.1, 0.1), seed=seed)


def _bubble(ctx, cx, cy, rx, ry, k, tail, seed, grow):
    if k <= 0.01:
        return
    rxk, ryk = rx * k, ry * k
    side = 1 if tail[0] > cx else -1
    base1 = (cx + side * 0.25 * rxk, cy + 0.55 * ryk)
    base2 = (cx + side * 0.55 * rxk, cy + 0.1 * ryk)
    shape(ctx, [base1, tail, base2], "g0", ink=4, seed=seed + 1)
    shape(ctx, _burst(cx, cy, rxk, ryk, seed), "g0", ink=5, seed=seed)
    for j in range(3):
        y = cy - ryk * 0.35 + j * ryk * 0.35
        _scribble(ctx, cx - rxk * 0.62, cx + rxk * 0.62, y, ryk * 0.13, 16, grow, seed + j)


@scene("argument")
def argument(ctx, t, T, seg):
    bg_studio(ctx, t, seed=13, tone=-0.1)
    camera(ctx, t, T, zoom=(1.0, 1.06), focus=(W / 2, H / 2))
    ten = ss(win(t, 0.0, 0.45 * T))          # tension builds over the first half
    cry = ss(win(t, 0.5 * T, 0.58 * T))      # she breaks down at the midpoint
    hx, wx, fy, s = 560, 1360, 480, 0.9
    jit = math.sin(t * 31) * 7 * ten
    wom = dict(F.WOMAN, coat="cobalt", coat_s="cobalt_d", lining="gold")

    # crimson tension zigzags between the two
    for i in range(6):
        y = 330 + i * 62
        pts = []
        for j in range(12):
            x = 730 + j * (460 / 11)
            amp = 16 * ten * (1 if j % 2 else -1) * (0.6 + 0.4 * math.sin(t * 9 + i))
            pts.append((x, y + amp))
        stroke(ctx, pts, 5, "red", taper=(0.3, 0.3), alpha=0.85 * ten, seed=i)

    F.character(ctx, hx + jit, fy, s, F.HERO, "shout" if cry < 0.4 else "grim", t, fx=1, tilt=0.06 * ten)
    F.character(ctx, wx - jit, fy, s, wom, "shout" if cry < 0.4 else "closed", t, fx=-1, tilt=-0.05 * ten)

    # speech bubbles: his first, hers stops when she breaks down
    k1 = ease_back(win(t, 0.04 * T, 0.16 * T), 1.6)
    _bubble(ctx, 520, 215, 330, 120, k1, (hx + 60, 340), 40, ss(win(t, 0.06 * T, 0.2 * T)))
    k2 = ease_back(win(t, 0.22 * T, 0.34 * T), 1.6) * (1 - ss(win(t, 0.47 * T, 0.54 * T)))
    _bubble(ctx, 1400, 215, 330, 120, k2, (wx - 60, 340), 60, ss(win(t, 0.25 * T, 0.4 * T)))

    # tears
    if cry > 0.3:
        for ex, ey in ((wx - 34 * s, fy - 2 * s + 10), (wx + 18 * s, fy - 2 * s + 10)):
            for j in range(3):
                p = ((t - 0.5 * T) * 0.9 + j / 3) % 1.0
                x, y = ex + math.sin(j * 2) * 3, ey + p * 170
                fillp(ctx, [(x, y - 12), (x + 7, y + 2), (x + 4, y + 8), (x - 4, y + 8), (x - 7, y + 2)],
                      "cobalt_l", alpha=cry * ss(1 - p))

    # the realisation: a soft light rises from her chest to her head
    rk = ease_io(win(t, 0.6 * T, 0.92 * T))
    if rk > 0.001:
        chest = (wx, fy + 230 * s)
        head = (wx - 10, fy - 40 * s)
        px, py = lerp(chest[0], head[0], rk), lerp(chest[1], head[1], rk)
        stroke(ctx, [chest, (px, py)], 8, "gold_l", taper=(0.05, 0.9), alpha=rk * 0.8)
        glow(ctx, px, py, 170, "gold_l", 0.75)
        fillp(ctx, circle_pts(px, py, 16, 16), "g0")
        for k in range(4):
            a = k * math.pi / 2 + 0.3 + t * 0.5
            shape(ctx, blade((px, py), (px + math.cos(a) * 46, py + math.sin(a) * 46), 12), "gold_l", ink=3,
                  seed=k)
    ui_glyphs(ctx, t, seed=13)


# ================================================================= s14 fog_mediators
def _fog(ctx, t, a, seed=44):
    rng = random.Random(seed)
    for i in range(18):
        x = rng.uniform(560, 1400) + math.sin(t * 0.15 + i) * 50
        y = rng.uniform(260, 900)
        glow(ctx, x, y, rng.uniform(180, 320), "g0", a)


@scene("fog_mediators")
def fog_mediators(ctx, t, T, seg):
    # bright on the left, black on the right
    ctx.set_source(lingrad(ctx, 0, 0, W, 0, [(0, "gold_l"), (0.28, mix("g1", "gold_l", 0.4)), (0.5, "g3"),
                                              (0.7, "sea"), (1, "night")]))
    ctx.paint()
    glow(ctx, 340, 360, 900, "gold_l", 0.35)
    _fog(ctx, t, 0.16)

    # stormy ocean on the right
    flash = (t % 6.1) < 0.14
    _sea(ctx, 1180, 1960, 700, 46, t, 3, body="sea", crest="sea_l")
    _sea(ctx, 1100, 1960, 820, 64, t, 6, body="ink2", crest="steel_l")
    if flash:
        fillp(ctx, [(1000, 0), (W, 0), (W, H), (1000, H)], "white", alpha=0.22)
        stroke(ctx, [(1560, 0), (1520, 120), (1585, 210), (1500, 330), (1540, 430), (1480, 520)], 7, "white",
               taper=(0.1, 0.4))

    # little island city on the left
    isl = [(-40, 1000), (-40, 860), (60, 800), (240, 790), (420, 820), (560, 800), (700, 850), (760, 1000)]
    shape(ctx, isl, "g3", ink=6, seed=8)
    cel(ctx, isl, [(-60, 900), (800, 880), (800, 1100), (-60, 1100)], "g4")
    base_y = 800
    blds = [(60, 70, 160), (140, 60, 240), (210, 90, 120), (400, 60, 150), (470, 70, 220), (550, 60, 110),
            (620, 50, 180)]
    for x, w, h in blds + [(300, 40, 330)]:
        top = base_y - h
        pts = [(x, base_y + 10), (x, top), (x + w, top), (x + w, base_y + 10)]
        shape(ctx, pts, "g6", ink=4, seed=int(x))
        cel(ctx, pts, [(x + w * 0.5, top), (x + w, top), (x + w, base_y + 10), (x + w * 0.5, base_y + 10)], "ink2")
        for wy in range(int(top + 18), int(base_y - 20), 34):
            for wx in range(int(x + 12), int(x + w - 12), 22):
                on = math.sin(t * 1.7 + wx * 0.13 + wy * 0.07)
                if on > -0.2:
                    fillp(ctx, [(wx, wy), (wx + 8, wy), (wx + 8, wy + 12), (wx, wy + 12)], "gold_l",
                          alpha=0.9 if on > 0.4 else 0.5)
    shape(ctx, [(296, 470), (320, 430), (344, 470)], "g6", ink=4, seed=77)
    glow(ctx, 330, 600, 420, "gold_l", 0.4)

    # the mediators, standing in the fog
    my_x, my_y, my_h = 820, 930, 470
    ms = my_h / 300
    F.person(ctx, my_x, my_y, h=my_h, color=mix("violet", "ink", 0.25), shade="ink2", pose="stand", t=t,
             fx=1, head_c="ink", seed=3, arm_up=0.6)
    with at(ctx, my_x, my_y, ms):
        cowl = [(0, -372), (46, -334), (56, -290), (44, -234), (0, -224), (-44, -234), (-56, -290), (-46, -334)]
        shape(ctx, cowl, "ink2", ink=4, seed=9)
        for ex in (-12, 12):
            fillp(ctx, circle_pts(ex, -290, 4.5, 10), "teal_l", alpha=0.6 + 0.4 * math.sin(t * 2))
    mystic_hand = _lp(my_x, my_y, ms, 1, -49.6, -238)
    mystic_head = _lp(my_x, my_y, ms, 1, 0, -300)

    ar_x, ar_y, ar_h = 1120, 930, 440
    ars = ar_h / 300
    F.person(ctx, ar_x, ar_y, h=ar_h, color="cobalt", shade="cobalt_d", pose="stand", t=t, fx=-1,
             head_c="skin2", seed=5)
    wrist = _lp(ar_x, ar_y, ars, -1, 52, -126)
    tip = _lp(ar_x, ar_y, ars, -1, 128, -300)
    artist_head = _lp(ar_x, ar_y, ars, -1, 0, -300)
    stroke(ctx, [wrist, tip], 9, "gold_d", taper=(0.0, 0.2))
    fillp(ctx, circle_pts(tip[0], tip[1], 9, 12), "teal_l")
    # the artist paints a glowing mark in the fog, repeating
    cyc = t % 9.0
    trail = _curve(tip, (tip[0] - 150, tip[1] - 120), (tip[0] - 260, tip[1] + 60), (tip[0] - 330, tip[1] - 60), 60)
    m = max(2, int(len(trail) * ss(win(cyc, 0.3, 4.5))))
    fade = 1 - ss(win(cyc, 5.5, 7.5))
    stroke(ctx, trail[:m], 16, "teal", alpha=0.25 * fade, taper=(0.1, 0.5))
    stroke(ctx, trail[:m], 5, "teal_l", alpha=0.9 * fade, taper=(0.1, 0.5))

    # glowing threads from both figures to the island and to the ocean
    threads = [
        (mystic_hand, (320, 425), (600, 470), (430, 360), "gold_l"),
        (mystic_head, (1600, 560), (1000, 300), (1350, 260), "teal_l"),
        (tip, (330, 600), (700, 520), (520, 640), "gold_l"),
        (artist_head, (1700, 760), (1250, 700), (1480, 640), "teal_l"),
    ]
    for i, (p0, p3, c1, c2, colr) in enumerate(threads):
        pts = _curve(p0, c1, c2, p3, 50)
        stroke(ctx, pts, 16, colr, alpha=0.18, taper=(0.1, 0.1), seed=i)
        stroke(ctx, pts, 4, colr, alpha=0.95, taper=(0.15, 0.15), seed=i)
        px, py = _bez(p0, c1, c2, p3, (t * 0.22 + i * 0.25) % 1.0)
        glow(ctx, px, py, 40, "g0", 0.8)

    # low fog in front of the feet
    for x in (300, 700, 1100, 1500):
        glow(ctx, x, 1000, 420, "g0", 0.2)
    _fog(ctx, t + 3, 0.1, seed=45)
    ui_glyphs(ctx, t, seed=14, region=(0, H * 0.7, W, H), color="teal")


# ================================================================= s15 subpersonalities
MASKS = [("shout", "red", -1.0), ("fear", "cobalt_l", -0.5), ("smile", "gold", 0.0),
         ("grim", "teal", 0.5), ("awe", "violet", 1.0)]


@scene("subpersonalities")
def subpersonalities(ctx, t, T, seg):
    bg_studio(ctx, t, seed=15, tone=0.1)
    camera(ctx, t, T, zoom=(1.0, 1.06), focus=(W / 2, H / 2))
    hx, hy, hs = W / 2, H * 0.5, 0.9
    pvx, pvy = hx, hy + 240 * hs            # pivot: the chest, cards fan out from behind it

    for i, (expr, tint, ang) in enumerate(MASKS):
        st = T * (0.1 + 0.07 * i)
        k = ease_back(win(t, st, st + 0.3 * T), 1.4)
        if k <= 0.01:
            continue
        R = 430 * k
        a = ang * min(1.0, k)
        px, py = pvx + R * math.sin(a), pvy - R * math.cos(a)
        c = dict(F.HERO, skin=mix("skin", tint, 0.45), skin_s=mix("skin_s", tint, 0.6),
                 hair_c=mix("hair_dk", tint, 0.5), hair_s=mix("ink2", tint, 0.4), eye=tint)
        with at(ctx, px, py, 0.62, a):
            card = [(-165, -185), (165, -185), (165, 205), (-165, 205)]
            fillp(ctx, card, mix(tint, "g0", 0.2), alpha=0.82)
            stroke(ctx, card, 6, "ink", closed=True, alpha=0.9, taper=(0, 0))
            ctx.push_group()
            F.head(ctx, c, expr, t)
            g = ctx.pop_group()
            ctx.set_source(g)
            ctx.paint_with_alpha(0.8)

    F.character(ctx, hx, hy, hs, F.HERO, "neutral", t, fx=1, tilt=0.02 * math.sin(t * 0.8))
    caption_tag(ctx, "SUBPERSONALIDADES", 110, 110, t, 46, accent="teal", appear=T * 0.45)
    ui_glyphs(ctx, t, seed=15, n=6)


# ================================================================= s16 rage_god
def _war_god(ctx, x, y, s, t):
    """Original war-god spirit: horned steel helm with a red crest, flame halo, pauldrons."""
    with at(ctx, x, y, s):
        rng = random.Random(16)
        for i in range(14):
            a = 2 * math.pi * i / 14 + 0.1
            L = rng.uniform(120, 200) * (1 + 0.15 * math.sin(t * 6 + i))
            p0 = (math.cos(a) * 170, math.sin(a) * 170 - 20)
            p1 = (math.cos(a) * (170 + L), math.sin(a) * (170 + L) - 20)
            shape(ctx, blade(p0, p1, 46, bend=0.18), "red_l" if i % 2 else "rust", ink=3.5, seed=i)
        body = [(-300, 520), (-270, 230), (-200, 150), (-110, 120), (0, 110), (110, 120), (200, 150), (270, 230),
                (300, 520)]
        shape(ctx, body, "red_d", ink=6, seed=21)
        cel(ctx, body, [(40, 130), (300, 160), (300, 520), (40, 520)], "ink", alpha=0.45)
        shape(ctx, [(-80, 260), (0, 230), (80, 260), (60, 380), (0, 420), (-60, 380)], "steel", ink=5, seed=22)
        for side in (-1, 1):
            for bl in ((side * 240, 170, side * 330, 90), (side * 260, 200, side * 380, 190)):
                shape(ctx, blade((bl[0], bl[1]), (bl[2], bl[3]), 70, bend=-0.1 * side), "steel", ink=5,
                      seed=30 + side)
        shape(ctx, [(-130, 30), (-140, -60), (-86, -150), (0, -190), (86, -150), (140, -60), (130, 30), (72, 70),
                    (-72, 70)], "steel", ink=6, seed=40)
        cel(ctx, [(-130, 30), (-140, -60), (-86, -150), (0, -190), (86, -150), (140, -60), (130, 30), (72, 70),
                  (-72, 70)], [(20, -200), (200, -200), (200, 100), (20, 100)], "steel_d")
        for p0, p1, w in (((-40, -180), (-60, -270), 36), ((0, -192), (0, -296), 40), ((40, -180), (70, -260), 36)):
            shape(ctx, blade(p0, p1, w), "red_l", ink=4, seed=int(p0[0]) + 50)
        for side in (-1, 1):
            shape(ctx, blade((side * 120, -80), (side * 250, -290), 70, bend=-0.22 * side), "g1", ink=5,
                  seed=60 + side)
        shape(ctx, [(-112, -20), (112, -20), (92, 14), (-92, 14)], "ink", ink=3, seed=70)
        pulse = 0.6 + 0.4 * math.sin(t * 2.4)
        for ex in (-48, 48):
            fillp(ctx, [(ex - 26, -2), (ex, -14), (ex + 26, -2), (ex, 8)], "gold_l")
            glow(ctx, ex, -2, 80, "red_l", 0.6 * pulse)


@scene("rage_god")
def rage_god(ctx, t, T, seg):
    bg_studio(ctx, t, seed=16, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.1), focus=(W / 2, H * 0.45))
    grow = ease_io(win(t, 0, 0.7 * T))
    glow(ctx, 960, 420, 760, "red", 0.5 * (0.6 + 0.4 * grow))
    _war_god(ctx, 960, 400, lerp(0.8, 1.05, grow), t)
    particles(ctx, t, 50, seed=16, color="gold_l", alpha=0.5, speed=(-6, -40))

    hx, hy, hs = 620, 880, 0.42
    possessed = dict(F.HERO, skin=mix("skin", "red", 0.4), skin_s=mix("skin_s", "red_d", 0.5), hair_c="ink",
                     coat="red_d", coat_s="ink", lining="red", eye="red_l", armor="steel_d", strap="red")
    F.character(ctx, hx, hy, hs, F.HERO, "fear" if t < 0.4 * T else "grim", t, fx=1)
    level = lerp(H + 10, 800, ease_io(win(t, 0.25 * T, 0.8 * T)))
    with clip(ctx, [(0, level), (W, level), (W, H), (0, H)]):
        F.character(ctx, hx, hy, hs, possessed, "shout", t, fx=1)
    if level < H:
        glow(ctx, hx, level, 220, "red_l", 0.5)
        stroke(ctx, [(hx - 150, level), (hx + 150, level)], 6, "red_l", alpha=0.6, taper=(0.2, 0.2))
    caption_tag(ctx, "MARTE", 110, 120, t, 52, accent="red", appear=T * 0.75)
    ui_glyphs(ctx, t, seed=16)


# ================================================================= s17 dreamer
ICONS = [(1150, 290, "dragon"), (1330, 290, "tower"), (1150, 400, "hero"), (1330, 400, "tree")]


def _dream_icon(ctx, kind, x, y, s, a, color, alpha):
    with at(ctx, x, y, s, a):
        if kind == "dragon":
            stroke(ctx, catmull([(-90, 30), (-40, -10), (0, 20), (50, -10), (95, -40)], n=8), 6, color,
                   taper=(0.1, 0.3), alpha=alpha)
            stroke(ctx, [(-20, -4), (-10, -66), (30, -30), (-20, -4)], 4, color, alpha=alpha, taper=(0, 0))
            stroke(ctx, [(95, -40), (130, -52), (110, -26)], 5, color, alpha=alpha, taper=(0, 0))
            stroke(ctx, [(-90, 30), (-130, 10)], 5, color, alpha=alpha, taper=(0.1, 0.8))
        elif kind == "tower":
            stroke(ctx, [(-40, 40), (-40, -60), (40, -60), (40, 40)], 5, color, alpha=alpha)
            stroke(ctx, [(-40, -60), (-40, -86), (-28, -86), (-28, -70), (-12, -70), (-12, -86), (12, -86),
                         (12, -70), (28, -70), (28, -86), (40, -86), (40, -60)], 5, color, alpha=alpha)
            stroke(ctx, [(-12, 40), (-12, 0), (12, 0), (12, 40)], 4, color, alpha=alpha)
        elif kind == "hero":
            stroke(ctx, circle_pts(0, -60, 22, 14), 5, color, closed=True, alpha=alpha)
            stroke(ctx, [(0, -38), (0, 20)], 5, color, alpha=alpha)
            stroke(ctx, [(0, -20), (-22, 0)], 5, color, alpha=alpha)
            stroke(ctx, [(0, -20), (20, -6)], 5, color, alpha=alpha)
            stroke(ctx, [(0, 20), (-18, 60)], 5, color, alpha=alpha)
            stroke(ctx, [(0, 20), (18, 60)], 5, color, alpha=alpha)
            stroke(ctx, [(24, -8), (40, -70)], 5, color, alpha=alpha)
            stroke(ctx, [(34, -12), (48, -6)], 4, color, alpha=alpha)
        elif kind == "tree":
            stroke(ctx, [(0, 60), (0, 0)], 6, color, alpha=alpha)
            for bx, by in ((-40, -30), (40, -30), (0, -40), (-22, -10), (22, -12)):
                stroke(ctx, [(0, 0 if by > -35 else -10), (bx, by)], 4, color, alpha=alpha)
            stroke(ctx, circle_pts(0, -60, 40, 14), 4, color, closed=True, alpha=alpha)


def _bulb(ctx, x, y, s, k, t):
    with at(ctx, x, y, s):
        glow(ctx, 0, 0, 340, "gold", 0.6 * k)
        shape(ctx, spikes(0, 0, 120, 220, 10, 0, 2 * math.pi, random.Random(3), 0.2), "gold_l", ink=0,
              alpha=0.35 * k)
        bulb = circle_pts(0, 0, 80, 30, ry=92)
        shape(ctx, bulb, "gold_l", ink=6, seed=3, alpha=k)
        cel(ctx, bulb, [(20, -100), (120, -100), (120, 100), (20, 100)], "gold", alpha=k)
        shape(ctx, [(-40, 80), (40, 80), (40, 130), (-40, 130)], "steel", ink=5, seed=4, alpha=k)
        for ly in (96, 112):
            stroke(ctx, [(-40, ly), (40, ly)], 3, "steel_d", alpha=k)
        stroke(ctx, [(-22, 20), (-10, -10), (0, 20), (10, -10), (22, 20)], 4, "red", alpha=k, taper=(0.2, 0.2))


@scene("dreamer")
def dreamer(ctx, t, T, seg):
    bg_studio(ctx, t, seed=17, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.04), focus=(W / 2, H / 2))
    particles(ctx, t, 40, seed=17, color="g0", alpha=0.35, speed=(-2, -1), size=(1, 2.5))

    # bed, side view, lower left
    shape(ctx, [(120, 700), (1000, 700), (1000, 800), (120, 800)], "rust_d", ink=6, seed=2)
    shape(ctx, [(110, 540), (170, 540), (170, 820), (110, 820)], "rust", ink=6, seed=3)
    shape(ctx, [(400, 548), (560, 540), (600, 600), (560, 650), (410, 660)], "g0", ink=5, seed=4)
    # sleeper, lying on his back with the face turned up toward the dream
    F.character(ctx, 560, 600, 0.72, F.HERO, "closed", t, fx=1, tilt=-1.42)
    shape(ctx, [(610, 520), (1000, 500), (1000, 720), (610, 740)], "cobalt", ink=5, seed=6)
    cel(ctx, [(610, 520), (1000, 500), (1000, 720), (610, 740)], [(600, 640), (1000, 620), (1000, 760), (600, 760)],
        "cobalt_d")

    # dream bubble leading up to the cloud
    gather = ease_io(win(t, 0.3 * T, 0.7 * T))
    for (cx_, cy_, r) in ((600, 470, 12), (680, 420, 20), (790, 380, 28)):
        shape(ctx, circle_pts(cx_, cy_, r, 14), "teal_l", ink=3, seed=int(cx_), alpha=0.7 * (1 - gather))

    # the dream cloud
    cloud_c = (1240, 330)
    cloud = _organic(cloud_c[0], cloud_c[1], 300, 190, _angles(0, 2 * math.pi, 60)[:-1], 17, amp=0.10)
    shape(ctx, cloud, "sea", ink=5, smooth=True, ink_color="teal", seed=2, alpha=0.85 - 0.4 * gather)

    # mythic shapes float, then gather into one lit idea
    for i, (x0, y0, kind) in enumerate(ICONS):
        fx_ = x0 + math.sin(t * 0.6 + i * 1.3) * 16
        fy_ = y0 + math.cos(t * 0.5 + i) * 12
        px = lerp(fx_, cloud_c[0], gather)
        py = lerp(fy_, cloud_c[1], gather)
        sc = lerp(0.95, 0.4, gather)
        alpha = (1 - ss(win(t, 0.6 * T, 0.78 * T))) * ss(win(t, 0.02 * T, 0.12 * T))
        if alpha > 0.01:
            _dream_icon(ctx, kind, px, py, sc, math.sin(t * 0.4 + i) * 0.15 * gather, "teal_l", alpha)

    kb = ease_back(win(t, 0.5 * T, 0.85 * T), 1.2)
    if kb > 0.01:
        _bulb(ctx, cloud_c[0], cloud_c[1], lerp(0.3, 1.1, kb), ss(win(t, 0.5 * T, 0.7 * T)), t)

    caption_tag(ctx, "CARL JUNG", 110, 110, t, 46, accent="teal", appear=T * 0.1)
    ui_glyphs(ctx, t, seed=17, n=6)


# ================================================================= s18 carver
CARVER = dict(F.SAGE, hair="long", hair_c="ink2", hair_s="g5", beard=None, coat="cobalt_d", coat_s="ink2",
              lining="gold", collar="hood", eye="gold", skin="skin2", skin_s="skin2_s", strap="gold_d")
ELDER = dict(F.SAGE, beard="long")


def _dream_animal(ctx, kind, x, y, s, a, t, alpha):
    color = "teal_l"
    glow(ctx, x, y, 170 * s, "teal", 0.22 * alpha)
    with at(ctx, x, y, s, a):
        if kind == "whale":
            stroke(ctx, catmull([(-130, 0), (-70, -40), (20, -46), (100, -22), (128, 0), (100, 24), (20, 30),
                                 (-70, 30)], closed=True, n=6), 5, color, closed=True, alpha=alpha)
            stroke(ctx, [(118, -4), (170, -40), (160, 0), (172, 36), (118, 8)], 5, color, closed=True, alpha=alpha)
            stroke(ctx, [(-20, -44), (0, -84), (30, -44)], 5, color, closed=True, alpha=alpha)
        elif kind == "raven":
            stroke(ctx, [(-60, -10), (0, -50), (70, -30), (120, -6), (40, 10), (-10, 30), (-60, -10)], 5, color,
                   closed=True, alpha=alpha)
            stroke(ctx, circle_pts(-70, -20, 18, 12), 5, color, closed=True, alpha=alpha)
            stroke(ctx, [(-86, -26), (-112, -16), (-86, -10)], 4, color, closed=True, alpha=alpha)
        elif kind == "bear":
            stroke(ctx, [(-50, 40), (-70, 0), (-40, -40), (0, -50), (40, -40), (70, 0), (50, 40)], 5, color,
                   closed=True, alpha=alpha)
            stroke(ctx, circle_pts(0, -70, 36, 16), 5, color, closed=True, alpha=alpha)
            stroke(ctx, circle_pts(-30, -102, 12, 10), 4, color, closed=True, alpha=alpha)
            stroke(ctx, circle_pts(30, -102, 12, 10), 4, color, closed=True, alpha=alpha)


def _carver_dream(ctx, t):
    drift = [("whale", 1330, 230, 0.9), ("raven", 1580, 330, 0.75), ("bear", 1060, 160, 0.7)]
    for i, (kind, x, y, s) in enumerate(drift):
        dx = math.sin(t * 0.2 + i * 2.1) * 40
        dy = math.cos(t * 0.15 + i) * 25
        pulse = 0.55 + 0.35 * math.sin(t * 1.4 + i * 1.7)
        _dream_animal(ctx, kind, x + dx, y + dy, s, math.sin(t * 0.25 + i) * 0.08, t, pulse)


def _elder(ctx, x, y, s, fx, look, t, alpha):
    glow(ctx, x, y - 90, 240, "gold_l", 0.22 * alpha)
    ctx.push_group()
    F.character(ctx, x, y, s, ELDER, "smile", t, fx=fx, look=look)
    g = ctx.pop_group()
    ctx.set_source(g)
    ctx.paint_with_alpha(alpha)


@scene("carver")
def carver(ctx, t, T, seg):
    bg_studio(ctx, t, seed=18, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.05), focus=(W / 2, H / 2))
    particles(ctx, t, 45, seed=18, color="g0", alpha=0.4, speed=(-2, -1), size=(1, 2.5))
    glow(ctx, 1600, 170, 260, "g0", 0.25)
    fillp(ctx, circle_pts(1600, 170, 60, 36), "g1", alpha=0.9)
    fillp(ctx, circle_pts(1624, 156, 56, 36), "g6", alpha=0.85)

    _carver_dream(ctx, t)
    _elder(ctx, 250, 330, 0.85, 1, 0.6, t, 0.38)
    _elder(ctx, 1640, 560, 0.8, -1, 0.6, t, 0.32)

    # ground and fire
    fillp(ctx, [(0, 920), (W, 880), (W, H), (0, H)], "ink")
    fx0, fy0 = 520, 960
    glow(ctx, fx0, fy0 - 80, 520, "rust", 0.5 + 0.1 * math.sin(t * 7))
    stroke(ctx, [(fx0 - 110, fy0 + 20), (fx0 + 110, fy0 - 10)], 26, "rust_d", taper=(0.1, 0.1))
    stroke(ctx, [(fx0 - 100, fy0 - 10), (fx0 + 100, fy0 + 30)], 26, "rust_d", taper=(0.1, 0.1))
    for i in range(7):
        ph = t * 6 + i * 1.7
        hgt = 150 + 40 * math.sin(ph) + 20 * math.sin(ph * 2.3)
        dx = (i - 3) * 26
        p0 = (fx0 + dx, fy0 - 10)
        p1 = (fx0 + dx * 0.5 + math.sin(ph) * 18, fy0 - hgt)
        shape(ctx, blade(p0, p1, 60, bend=0.1 * (1 if i % 2 else -1)), "red_l", ink=4, seed=i)
        shape(ctx, blade(p0, (p1[0], p1[1] + 30), 30), "gold_l", ink=3, seed=20 + i)

    # carver, lit by the fire
    cvx, cvy, cvs = 900, 400, 0.95
    F.character(ctx, cvx, cvy, cvs, CARVER, "neutral", t, fx=1, tilt=0.03 * math.sin(t * 0.9))
    glow(ctx, 760, 700, 420, "rust", 0.10)

    # the carving: a generic angular bear block, revealed from the bottom up
    kc = ease_io(win(t, 0.05 * T, 0.8 * T))
    with at(ctx, 930, 720, 1.0):
        bear = [(-60, -130), (60, -130), (72, -70), (40, -40), (-40, -40), (-72, -70)]
        body = [(-90, -30), (90, -30), (110, 40), (70, 100), (-70, 100), (-110, 40)]
        ears = [(-60, -130), (-80, -170), (-40, -140)], [(60, -130), (80, -170), (40, -140)]
        ytop = lerp(120, -180, kc)
        with clip(ctx, [(-300, ytop), (300, ytop), (300, 300), (-300, 300)]):
            for e in ears:
                shape(ctx, e, "gold_l", ink=5, seed=3)
            shape(ctx, bear, "gold_l", ink=5, seed=2)
            shape(ctx, body, "gold_l", ink=5, seed=4)
            cel(ctx, body, [(20, -60), (150, -60), (150, 120), (20, 120)], "gold")
            cel(ctx, bear, [(10, -150), (150, -150), (150, -20), (10, -20)], "gold")
            fillp(ctx, circle_pts(-24, -92, 6, 8), "ink")
            fillp(ctx, circle_pts(24, -92, 6, 8), "ink")
        # knife and chips while carving
        osc = math.sin(t * 9) * 10
        stroke(ctx, [(60 + osc, -90), (120 + osc * 0.5, -30)], 7, "steel_l", taper=(0.1, 0.4))
        for j in range(8):
            p = ((t * 0.8) + j / 8.0) % 1.0
            fillp(ctx, circle_pts(20 + j * 9 + p * 20, -40 + p * 130, 4, 6), "gold_l", alpha=1 - p)
    F.hand(ctx, 830, 770, a=-0.2, s=1.1, color="skin2", shade="skin2_s", kind="fist")
    F.hand(ctx, 1040, 760, a=0.2, s=1.1, color="skin2", shade="skin2_s", kind="fist", fx=-1)
    ui_glyphs(ctx, t, seed=18, n=6)


# ================================================================= s19 myth_quote
def _tragic_mask(ctx, x, y, s, alpha):
    with at(ctx, x, y, s):
        face = [(-80, -100), (80, -100), (90, -20), (50, 50), (0, 70), (-50, 50), (-90, -20)]
        shape(ctx, face, "g1", ink=6, smooth=True, seed=5, alpha=alpha)
        for sgn in (-1, 1):
            ex = sgn * 36
            fillp(ctx, [(ex - 22, -34), (ex + 22, -34), (ex + 14, -14), (ex - 14, -14)], "ink", alpha=alpha)
            stroke(ctx, [(ex - 28, -58 + sgn * 0), (ex + 22, -46)] if sgn > 0 else [(ex - 22, -46), (ex + 28, -58)],
                   5, "ink", alpha=alpha, taper=(0.2, 0.2))
        stroke(ctx, [(-40, 36), (0, 12), (40, 36)], 7, "ink", alpha=alpha, taper=(0.2, 0.2), smooth=True)


@scene("myth_quote")
def myth_quote(ctx, t, T, seg):
    fillp(ctx, [(0, 0), (W, 0), (W, H), (0, H)], "night")
    # spotlight cone and floor
    fillp(ctx, [(W * 0.5 - 70, 0), (W * 0.5 + 70, 0), (W * 0.5 + 560, H), (W * 0.5 - 560, H)], "gold_l",
          alpha=0.10 + 0.02 * math.sin(t * 0.7))
    glow(ctx, W * 0.5, 0, 900, "gold", 0.16)
    fillp(ctx, [(0, H * 0.62), (W, H * 0.62), (W, H), (0, H)], mix("night", "g6", 0.5))
    glow(ctx, W * 0.5, H * 0.9, 620, "gold", 0.14)

    # the path: stem, then splits into a gold branch and a branch to the mask
    f0 = (W * 0.5, H * 0.6)
    stem = [(W * 0.5, H * 1.02), f0]
    right = _curve(f0, (W * 0.56, H * 0.56), (W * 0.66, H * 0.5), (W * 0.73, H * 0.44), 40)
    left = _curve(f0, (W * 0.44, H * 0.56), (W * 0.34, H * 0.5), (W * 0.27, H * 0.44), 40)
    stem_pts = [(W * 0.5, H * 1.02), (W * 0.5, H * 0.8), f0]
    stem_w = [lerp(240, 60, i / (len(stem_pts) - 1)) for i in range(len(stem_pts))]
    fillp(ctx, ribbon(stem_pts, stem_w), "g5", alpha=0.55)
    fillp(ctx, ribbon(left, [lerp(70, 6, i / len(left)) for i in range(len(left))]), "g4", alpha=0.4)
    fillp(ctx, ribbon(right, [lerp(70, 6, i / len(right)) for i in range(len(right))]), "g4", alpha=0.45)
    stroke(ctx, left, 4, "g4", alpha=0.6, taper=(0.1, 0.1))
    # gold branch glows
    stroke(ctx, right, 24, "gold", alpha=0.18, taper=(0.1, 0.1))
    stroke(ctx, right, 6, "gold_l", alpha=0.9, taper=(0.1, 0.1))
    glow(ctx, W * 0.73, H * 0.44, 300, "gold", 0.6)
    _tragic_mask(ctx, W * 0.27, H * 0.44 - 20, 0.85, 0.55)

    # the lone walker: up the stem, then onto the gold branch
    u = ss(win(t, 0.12 * T, 0.8 * T))
    if u < 0.5:
        v = u / 0.5
        wx, wy = lerp(W * 0.5, f0[0], v), lerp(H * 1.0, f0[1], v)
        fx = 1
    else:
        v = (u - 0.5) / 0.5
        idx = int(v * (len(right) - 1))
        wx, wy = right[idx]
        fx = 1
    depth = u
    F.person(ctx, wx, wy, h=lerp(230, 110, depth), color="g1", shade="g3", pose="walk", t=t, fx=fx,
             head_c="g1", ink=4, seed=4)

    # the quote, in serif italic
    ka = ss(win(t, 0.08 * T, 0.3 * T))
    text(ctx, "Todos vivimos un mito,", W / 2, H * 0.2, 66, font=FONT_SERIF, color="g0", bold=False,
         italic=True, alpha=ka)
    text(ctx, "pero muy pocos sabemos cuál.", W / 2, H * 0.2 + 84, 66, font=FONT_SERIF, color="g0",
         bold=False, italic=True, alpha=ka)
    text(ctx, "— C. G. JUNG", W / 2, H * 0.2 + 150, 30, font=FONT_CAPS, color="gold_l", tracking=0.25,
         alpha=ka)
    particles(ctx, t, 30, seed=19, color="gold_l", alpha=0.35, speed=(-4, -12))
    ui_glyphs(ctx, t, seed=19, n=6)
