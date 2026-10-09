"""Batch D: gods merge (s29), the world breaks (s34), freeze (s35), confront (s36),
hyperlinks (s37), drowning (s38), constraints (s39), field (s40), summit (s41).

All characters are original designs. Helpers are local; engine/ is not modified.
"""
import math
import random

from engine.kit import (FONT_CAPS, FONT_TITLE, H, W, at, bg_studio, blade, camera, caption_tag, circle_pts, cel,
                        clip, col, ease_in, ease_io, ease_out, fillp, glow, hatch, hud, lingrad, lerp, lerp2, mix,
                        particles, poly, rot, setc, shape, ss, stroke, text, text_width, win)
from engine import figures as F
from . import scene


# ================================================================== shared helpers
def _with_alpha(ctx, a, fn):
    """Run fn() as a group faded to alpha a. fn keeps its own transforms balanced."""
    if a <= 0.001:
        return
    if a >= 0.999:
        ctx.save()
        fn()
        ctx.restore()
        return
    ctx.save()
    ctx.push_group()
    ctx.save()
    fn()
    ctx.restore()
    grp = ctx.pop_group()
    ctx.restore()
    ctx.set_source(grp)
    ctx.paint_with_alpha(a)


def _center_tag(ctx, s, y, t, size=40, appear=0.0, accent="red", color="ink"):
    w = text_width(ctx, s, size, tracking=0.08) + 40
    caption_tag(ctx, s, W / 2 - w / 2, y, t, size, color=color, accent=accent, appear=appear)


def _partial(pts, k):
    """First fraction k (0..1) of a polyline, measured by segment count."""
    if k >= 1:
        return list(pts)
    n = len(pts) - 1
    f = max(0.0, k) * n
    i = int(f)
    out = list(pts[:i + 1])
    if i < n:
        out.append(lerp2(pts[i], pts[i + 1], f - i))
    return out


def _bez_cut(P, k):
    """Left part of a cubic bezier up to parameter k (de Casteljau)."""
    if k >= 1:
        return P
    p0, p1, p2, p3 = P
    a = lerp2(p0, p1, k)
    b = lerp2(p1, p2, k)
    c = lerp2(p2, p3, k)
    d = lerp2(a, b, k)
    e = lerp2(b, c, k)
    return (p0, a, d, lerp2(d, e, k))


def _perim(w, h, n):
    """n points spread evenly along a w x h rectangle centred on the origin."""
    corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    total = 2 * (w + h)
    out = []
    for k in range(n):
        d = total * k / n
        for i in range(4):
            a, b = corners[i], corners[(i + 1) % 4]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if d <= L:
                out.append(lerp2(a, b, d / L))
                break
            d -= L
    return out


def _eye(ctx, x, y, s, k):
    """Almond eye with a slit pupil; k = openness 0..1."""
    glow(ctx, x, y, 95 * s, "gold", 0.35 * k)
    fillp(ctx, [(x - 26 * s, y), (x, y - 15 * s * k), (x + 26 * s, y), (x, y + 15 * s * k)], "gold_l")
    if k > 0.05:
        fillp(ctx, [(x - 3 * s, y - 13 * s * k), (x + 3 * s, y - 13 * s * k), (x + 2 * s, y + 13 * s * k),
                    (x - 2 * s, y + 13 * s * k)], "ink")


def _hero_fig(ctx, x, y, h, t, pose="stand", seed=2, lantern=False):
    """Full-body HERO (original): dark coat, spiky hair, red scarf, optional lantern in the right hand."""
    s = h / 300
    F.person(ctx, x, y, h, F.HERO["coat"], F.HERO["coat_s"], pose=pose, t=t, seed=seed, head_c="skin")
    with at(ctx, x, y, s):
        for k in range(5):
            shape(ctx, blade((-24 + k * 12, -300), (-34 + k * 16, -352 - (k % 2) * 12), 16, bend=0.1),
                  "hair_dk", 3, seed=seed + k)
        shape(ctx, [(-40, -250), (40, -250), (36, -230), (-36, -230)], "red", 3.5, seed=seed + 9)
        if lantern:
            stroke(ctx, [(52, -126), (62, -112), (70, -104)], 3, "ink", taper=(0, 0))
            glow(ctx, 70, -80, 140, "gold_l", 0.55)
            shape(ctx, [(56, -102), (84, -102), (84, -72), (56, -72)], "gold_l", 3.5, seed=seed + 10)


# ================================================================== 1. gods_merge (s29)
TAG_NAMES = [f"NOMBRE {i:02d}" for i in range(1, 51)]


def _idol(ctx, x, y, s, c_left, c_right, accent="red", seed=0):
    """Original totem idol: horned angular head, slit eyes, chevron belly. (x, y) = base centre."""
    body = [(-70, 0), (70, 0), (58, -150), (-58, -150)]
    head = [(-92, -150), (-70, -290), (0, -330), (70, -290), (92, -150), (50, -170), (-50, -170)]
    with at(ctx, x, y, s):
        shape(ctx, body, c_left, 5, seed=seed)
        shape(ctx, head, c_left, 5, seed=seed + 1)
        fillp(ctx, [(0, 0), (70, 0), (58, -150), (0, -150)], c_right)
        fillp(ctx, [(0, -330), (70, -290), (92, -150), (50, -170), (0, -170)], c_right)
        shape(ctx, body, None, 5, seed=seed)
        shape(ctx, head, None, 5, seed=seed + 1)
        for k in range(3):
            yy = -40 - k * 42
            stroke(ctx, [(-46, yy + 16), (0, yy - 6), (46, yy + 16)], 7, accent, taper=(0.1, 0.1))
        for side in (-1, 1):
            shape(ctx, blade((side * 70, -270), (side * 150, -380), 36, bend=-0.15 * side), accent, 4.5,
                  seed=seed + 3 + side)
            sx = side * 38
            fillp(ctx, [(sx - 26, -240), (sx, -252), (sx + 26, -240), (sx, -226)], "ink")
            fillp(ctx, [(sx - 14, -240), (sx, -246), (sx + 14, -240), (sx, -232)], "gold_l")
        stroke(ctx, [(-50, -184), (-26, -172), (0, -184), (26, -172), (50, -184)], 6, "ink", taper=(0.1, 0.1))


@scene("gods_merge")
def gods_merge(ctx, t, T, seg):
    bg_studio(ctx, t, seed=41, tone=0.1)
    camera(ctx, t, T, zoom=(1.0, 1.05))
    lift = ease_out(win(t, T * 0.10, T * 0.36), 3)
    meet = ease_io(win(t, T * 0.40, T * 0.58))
    fade = ss(win(t, T * 0.58, T * 0.68))
    fuse_in = ss(win(t, T * 0.60, T * 0.64))
    base_y = lerp(H * 0.86, H * 0.64, lift)
    arms = 0.2 + 0.6 * lift + 0.2 * meet

    # the two tribes
    F.crowd(ctx, 40, 540, H * 0.96, 9, 250, t, seed=3, colors=("cobalt", "cobalt_d", "g5"), arm_up=arms)
    F.crowd(ctx, 1380, 1880, H * 0.96, 9, 250, t, seed=4, colors=("rust", "rust_d", "g6"), arm_up=arms)

    xa = lerp(W * 0.34, W / 2 - 46, meet)
    xb = lerp(W * 0.66, W / 2 + 46, meet)

    def pair():
        _idol(ctx, xa, base_y + math.sin(t * 1.3) * 6, 0.9, "teal", "teal_d", "red", seed=11)
        _idol(ctx, xb, base_y + math.sin(t * 1.3 + 2) * 6, 0.9, "gold", "gold_d", "red", seed=12)
        text(ctx, "DIOS A", xa, base_y + 58, 40, FONT_CAPS, "ink", alpha=1 - fade)
        text(ctx, "DIOS B", xb, base_y + 58, 40, FONT_CAPS, "ink", alpha=1 - fade)

    _with_alpha(ctx, 1 - fade, pair)

    # the fused idol
    grow = ease_out(win(t, T * 0.60, T * 0.80), 2)
    fs = 0.9 + 0.55 * grow

    def fused():
        _idol(ctx, W / 2, H * 0.66, fs, "teal", "gold", "red", seed=21)

    _with_alpha(ctx, fuse_in, fused)
    if fuse_in > 0.5:
        text(ctx, "DIOS C", W / 2, H * 0.66 + 62, 40, FONT_CAPS, "ink", alpha=fuse_in)

    # collision flash
    fl = win(t, T * 0.58, T * 0.72)
    if 0 < fl < 1:
        glow(ctx, W / 2, H * 0.5, 260 + 380 * fl, "gold_l", 0.6 * (1 - fl))
        stroke(ctx, circle_pts(W / 2, H * 0.5, 140 + 560 * fl, 56), 3 + 10 * (1 - fl), "gold_l", closed=True,
               alpha=1 - fl)

    # fifty name tags orbit the new god, back ones first
    items = []
    n = len(TAG_NAMES)
    for i, name in enumerate(TAG_NAMES):
        t_in = T * 0.70 + i * (T * 0.22 / n)
        k = ease_out(win(t, t_in, t_in + 0.5), 3)
        if k <= 0:
            continue
        ang = 2 * math.pi * i / n + t * 0.16
        x = W / 2 + math.cos(ang) * 620
        y = H * 0.46 + math.sin(ang) * 280
        items.append((math.sin(ang), x, y, name, k))
    for depth, x, y, name, k in sorted(items, key=lambda it: it[0]):
        d = (depth + 1) / 2
        sc = (0.6 + 0.4 * d) * (0.3 + 0.7 * k)
        w = text_width(ctx, name, 22, tracking=0.04) + 26
        with at(ctx, x, y, sc):
            rect = [(-w / 2, -18), (w / 2, -18), (w / 2, 18), (-w / 2, 18)]
            shape(ctx, rect, "g0", 3, alpha=0.5 + 0.5 * d)
            text(ctx, name, 0, 8, 22, FONT_CAPS, "ink", tracking=0.04, alpha=0.5 + 0.5 * d)

    _center_tag(ctx, "DIOS A + DIOS B → DIOS C", H * 0.07, t, size=40, appear=T * 0.12, accent="red")


# ================================================================== 2. world_breaks (s34)
_WB_O = (W * 0.5, H * 0.42)          # where the crack starts
_WB_WORDS = [  # (text, x_frac, y_frac, appear_frac, size, font, colour)
    ("TRAICIÓN", 0.66, 0.26, 0.30, 96, FONT_TITLE, "red_l"),
    ("PÉRDIDA", 0.72, 0.50, 0.46, 96, FONT_TITLE, "teal_l"),
    ("UN SUEÑO QUE MUERE", 0.60, 0.74, 0.60, 58, FONT_CAPS, "gold_l"),
]


def _wb_shards():
    rng = random.Random(34)
    cols, rows = 7, 4
    V = {}
    for j in range(rows + 1):
        for i in range(cols + 1):
            x, y = W * i / cols, H * j / rows
            if 0 < i < cols:
                x += rng.uniform(-80, 80)
            if 0 < j < rows:
                y += rng.uniform(-70, 70)
            V[i, j] = (x, y)
    out = []
    for j in range(rows):
        for i in range(cols):
            a, b, c, d = V[i, j], V[i + 1, j], V[i + 1, j + 1], V[i, j + 1]
            for tri in ((a, b, c), (a, c, d)):
                cx = sum(p[0] for p in tri) / 3
                cy = sum(p[1] for p in tri) / 3
                dx, dy = cx - _WB_O[0], cy - _WB_O[1]
                dist = math.hypot(dx, dy) or 1.0
                out.append(dict(pts=list(tri), c=(cx, cy), dir=(dx / dist, dy / dist), dist=dist,
                                tone=rng.choice(["g1", "g2", "g3"]), spin=rng.uniform(-0.9, 0.9),
                                jit=rng.uniform(0.8, 1.25)))
    dmax = max(s["dist"] for s in out)
    for s in out:
        s["tc"] = 0.10 + 0.34 * (s["dist"] / dmax)   # shards far from the crack fall later
    return out


def _wb_cracks():
    rng = random.Random(35)
    lines = []
    for k in range(10):
        a = k * 2 * math.pi / 10 + rng.uniform(-0.15, 0.15)
        x, y = _WB_O
        pts = [(x, y)]
        for _ in range(7):
            a += rng.uniform(-0.35, 0.35)
            L = rng.uniform(120, 200)
            x += math.cos(a) * L
            y += math.sin(a) * L
            pts.append((x, y))
        lines.append((pts, k / 10.0))
    return lines


def _wb_eyes():
    rng = random.Random(91)
    return [(rng.uniform(0.5, 0.97) * W, rng.uniform(0.08, 0.9) * H, rng.uniform(0.7, 1.4), rng.uniform(0.12, 0.7))
            for _ in range(9)]


_WB_SHARDS = _wb_shards()
_WB_CRACKS = _wb_cracks()
_WB_EYES = _wb_eyes()


@scene("world_breaks")
def world_breaks(ctx, t, T, seg):
    camera(ctx, t, T, zoom=(1.0, 1.05), shake=3.0 * ss(win(t, T * 0.22, T * 0.42)))
    # the void behind the wall
    ctx.set_source(lingrad(ctx, 0, 0, 0, H, [(0, mix("night", "sea", 0.25)), (1, "night")]))
    ctx.paint()
    glow(ctx, _WB_O[0], _WB_O[1], 1000, "sea_l", 0.7)
    for x, y, s, a in _WB_EYES:
        k = ss(win(t, T * a, T * a + 0.12))
        if k <= 0:
            continue
        blink = 0.12 if math.sin(t * 0.7 + x) > 0.985 else 1.0
        _eye(ctx, x, y, s, k * blink)
    F.serpent(ctx, [(W + 200, H * 0.98), (W * 0.86, H * 0.72), (W * 0.74, H * 0.52), (W * 0.63, H * 0.42),
                    (W * 0.57, H * 0.37)], t, thick=90, body="sea_l", belly="teal", spikes_c="ink2",
              head_size=1.0, seed=6, wave=14, open_jaw=0.45 + 0.3 * math.sin(t * 1.7))

    # the wall, cracking into shards that fall away
    for i, s in enumerate(_WB_SHARDS):
        k = ease_in(win(t, T * s["tc"], T * s["tc"] + T * 0.16), 2)
        dx, dy = s["dir"]
        ox = dx * k * 640 * s["jit"]
        oy = dy * k * 380 * s["jit"] + k * k * 1100
        pts = [rot(p, s["spin"] * k, s["c"]) for p in s["pts"]]
        pts = [(x + ox, y + oy) for x, y in pts]
        shape(ctx, pts, s["tone"], 3.5, seed=i)

    # light leaking through the cracks (fades once the shards are gone)
    for pts, order in _WB_CRACKS:
        k = win(t, T * (0.02 + order * 0.06), T * (0.02 + order * 0.06 + 0.10))
        fade = 1 - ss(win(t, T * 0.14, T * 0.34))
        if k > 0 and fade > 0:
            seg_pts = _partial(pts, k)
            stroke(ctx, seg_pts, 9, "gold_l", alpha=0.7 * fade, taper=(0.05, 0.6))
            stroke(ctx, seg_pts, 3, "white", alpha=0.9 * fade, taper=(0.05, 0.6))

    # a picture frame falls off the wall
    fk = ease_in(win(t, T * 0.26, T * 0.48), 2)
    if fk > 0:
        with at(ctx, W * 0.8, H * 0.26 + fk * fk * 1000, 1.0, a=0.35 * fk):
            shape(ctx, [(-120, -90), (120, -90), (120, 90), (-120, 90)], "g4", 6, seed=3)
            fillp(ctx, [(-100, 70), (-40, -20), (10, 40), (60, -10), (100, 70)], "teal_d")
            fillp(ctx, [(-100, -70), (100, -70), (100, -40), (-100, -40)], "teal_l", alpha=0.5)

    # HERO in the room, bust
    expr = "fear" if t > T * 0.42 else "neutral"
    F.character(ctx, W * 0.3, H * 0.44, 1.0, F.HERO, expr, t)

    # words float out of the void
    for i, (s, xf, yf, a, size, font, colr) in enumerate(_WB_WORDS):
        k = ease_out(win(t, T * a, T * a + 0.5), 3)
        if k <= 0:
            continue
        y = yf * H + math.sin(t * 1.1 + i * 2) * 14 + (1 - k) * 40
        text(ctx, s, xf * W, y, size, font, colr, alpha=k)


# ================================================================== 3. freeze (s35)
def _coil(cx, cy):
    """Coiled serpent body from outside in, neck rising toward the rabbit."""
    pts = []
    n = 70
    for i in range(n + 1):
        u = i / n
        a = u * 2 * math.pi * 2.3 + math.pi
        r = 230 - 120 * u
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 0.42 - 60 * u))
    pts += [(cx - 200, cy - 160), (cx - 380, cy - 260), (cx - 470, cy - 270)]
    return pts


def _rabbit(ctx, x, y, s, frost):
    """Original rabbit: long ears, round body, wide frightened eye. Frost overlay when frozen."""
    body = circle_pts(0, -10, 150, 28, ry=110)
    head = circle_pts(118, -130, 80, 26)
    with at(ctx, x, y, s):
        shape(ctx, blade((80, -150), (72, -350), 60, bend=0.04), "g2", 5, seed=1)
        shape(ctx, blade((120, -150), (162, -330), 52, bend=-0.04), "g2", 5, seed=2)
        shape(ctx, body, "g2", 5, seed=3)
        cel(ctx, body, [(-200, 40), (200, 40), (200, 200), (-200, 200)], "g3")
        shape(ctx, circle_pts(-50, -30, 80, 22), "g3", 4, seed=4)
        shape(ctx, head, "g1", 5, seed=5)
        shape(ctx, circle_pts(60, 96, 74, 20, ry=22), "g2", 4, seed=6)
        shape(ctx, circle_pts(-150, -40, 30, 14), "g0", 3, seed=7)
        fillp(ctx, circle_pts(150, -146, 22, 16), "g0")
        fillp(ctx, circle_pts(158, -146, 8, 10), "ink")
        fillp(ctx, [(190, -112), (202, -116), (196, -102)], "red_l")
        stroke(ctx, [(190, -104), (262, -118)], 2.5, "ink")
        stroke(ctx, [(192, -96), (262, -92)], 2.5, "ink")
        if frost > 0:
            fillp(ctx, body, "teal_l", alpha=0.35 * frost)
            fillp(ctx, head, "teal_l", alpha=0.35 * frost)
            for k in range(8):
                a = k * math.pi / 4 + 0.3
                base = (math.cos(a) * 190, math.sin(a) * 150 - 20)
                tip = (base[0] + math.cos(a) * 90, base[1] + math.sin(a) * 90)
                shape(ctx, blade(base, tip, 22), "teal_l", 3, seed=k, alpha=frost)


def _freeze_part1(ctx, t, T):
    bg_studio(ctx, t, seed=35, tone=-0.4)
    camera(ctx, t, T, zoom=(1.0, 1.04), focus=(W * 0.5, H * 0.5))
    frost = ss(win(t, T * 0.12, T * 0.30))
    _rabbit(ctx, W * 0.24, H * 0.8, 0.95, frost)
    jaw = 0.25 + 0.6 * ss(win(t, T * 0.12, T * 0.35))
    F.serpent(ctx, _coil(W * 0.72, H * 0.8), t, thick=76, body="sea_l", belly="teal", spikes_c="ink2",
              head_size=1.05, seed=12, wave=7, open_jaw=jaw)
    _center_tag(ctx, "EL MIEDO PARALIZA", H * 0.07, t, size=40, appear=T * 0.05, accent="teal")


def _freeze_part2(ctx, t, T):
    bg_studio(ctx, t, seed=36, dark=True)
    camera(ctx, t, T, zoom=(1.04, 1.0), focus=(W * 0.5, H * 0.5))
    p = win(t, T * 0.52, T * 0.92)
    front = lerp(H * 1.02, H * 0.0, ease_io(p))          # colour drains upward from the feet
    fx, fy, fh = W * 0.34, H * 0.93, 640

    ctx.save()
    ctx.rectangle(0, 0, W, front)
    ctx.clip()
    F.person(ctx, fx, fy, fh, "rust", "rust_d", pose="stand", t=t, seed=5, head_c="skin2")
    ctx.restore()

    ctx.save()
    ctx.rectangle(0, front, W, H)
    ctx.clip()
    F.person(ctx, fx, fy, fh, "g3", "g5", pose="stand", t=t, seed=5, head_c="g3")
    hatch(ctx, [(fx - 200, fy - 640), (fx + 200, fy - 640), (fx + 200, fy), (fx - 200, fy)], -0.9, 16, 2.0,
          "g6", 0.5, seed=8)
    ctx.restore()
    if 0 < p < 1:
        stroke(ctx, [(0, front), (W, front)], 3, "teal_l", alpha=0.6, taper=(0, 0), wobble=0)

    # the snake-haired silhouette (original design)
    gx, gy = W * 0.73, H * 0.46
    for i in range(9):
        base_a = -math.pi / 2 + (i - 4) * 0.34
        curl = 0.9 * (i - 4) / 4
        pts = []
        for j in range(11):
            u = j / 10
            a = base_a + curl * u * u + math.sin(t * 1.8 + i + u * 4) * 0.12 * u
            R = 150 + 330 * u
            pts.append((gx + math.cos(a) * R * 0.9, gy + math.sin(a) * R * 0.75))
        stroke(ctx, pts, 30, "teal_d", smooth=True, taper=(0.02, 0.3))
        tip, prev = pts[-1], pts[-2]
        ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
        with at(ctx, tip[0], tip[1], 0.9, ang):
            shape(ctx, blade((-6, 0), (30, 0), 24, bend=0.0), "teal", 3, seed=i)
    face = circle_pts(gx, gy, 150, 36, ry=190)
    shape(ctx, face, "g5", 6, seed=2)
    cel(ctx, face, [(gx + 40, gy - 200), (gx + 200, gy - 200), (gx + 200, gy + 200), (gx + 40, gy + 200)], "g6")
    _eye(ctx, gx - 58, gy - 12, 1.25, 1.0)
    _eye(ctx, gx + 58, gy - 12, 1.25, 1.0)
    stroke(ctx, [(gx - 60, gy + 110), (gx, gy + 122), (gx + 60, gy + 110)], 5, "ink", taper=(0.2, 0.2))
    _center_tag(ctx, "CONVERTIDOS EN PIEDRA", H * 0.07, t, size=40, appear=T * 0.7, accent="red")


@scene("freeze")
def freeze(ctx, t, T, seg):
    k = ss(win(t, T * 0.46, T * 0.56))
    _with_alpha(ctx, 1 - k, lambda: _freeze_part1(ctx, t, T))
    _with_alpha(ctx, k, lambda: _freeze_part2(ctx, t, T))


# ================================================================== 4. confront (s36)
_CF_N = 48
_CF_MC = (W * 0.7, H * 0.5)            # monster centre
_CF_BW, _CF_BH = 112, 62               # stone block size
_CF_HOUSE = (W * 0.52, H * 0.84)       # house base centre (on the ground line)
_CF_RNG = random.Random(36)
_CF_R = [270 + 55 * math.sin(2 * math.pi * k / _CF_N * 5 + 0.6) + (40 if k % 2 else 0) + _CF_RNG.uniform(-22, 22)
         for k in range(_CF_N)]


def _cf_pieces():
    rng = random.Random(361)
    pieces = []
    per = _CF_N // 8
    for i in range(8):
        pts = [(0.0, 0.0)]
        for k in range(i * per, (i + 1) * per + 1):
            a = 2 * math.pi * (k % _CF_N) / _CF_N
            r = _CF_R[k % _CF_N]
            pts.append((math.cos(a) * r, math.sin(a) * r))
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        mid = (i + 0.5) * 2 * math.pi / 8
        pieces.append(dict(c=(cx, cy), local=[(x - cx, y - cy) for x, y in pts],
                           dir=(math.cos(mid), math.sin(mid)), spin=rng.uniform(-0.7, 0.7)))
    order = sorted(range(len(pieces)), key=lambda i: pieces[i]["c"][0])
    for slot, idx in enumerate(order):   # leftmost (nearest to HERO) gets the first slot
        pieces[idx]["slot"] = slot
    return pieces


_CF_PIECES = _cf_pieces()


def _cf_slot(j):
    row, col = divmod(j, 4)
    x = _CF_HOUSE[0] + (col - 1.5) * _CF_BW
    y = _CF_HOUSE[1] - _CF_BH / 2 - row * _CF_BH
    return (x, y)


@scene("confront")
def confront(ctx, t, T, seg):
    bg_studio(ctx, t, seed=36, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.06), focus=(W * 0.5, H * 0.5))

    # HERO walks in from the left, then stands with the lantern up
    walk = ease_io(win(t, 0.0, T * 0.45))
    hx = lerp(W * 0.14, W * 0.36, walk)
    hfeet = H * 0.86
    hs = 440
    lantern_x = hx + 70 * hs / 300
    lantern_y = hfeet - 80 * hs / 300
    # light cone toward the monster
    fillp(ctx, [(lantern_x, lantern_y), (W * 0.62, H * 0.2), (W * 0.62, H * 0.9)], "gold_l", alpha=0.08)
    glow(ctx, lantern_x, lantern_y, 420, "gold_l", 0.22)

    # the shadow monster, cracked into eight wedges
    cx, cy = _CF_MC
    sep = ease_out(win(t, T * 0.28, T * 0.42), 3)
    fade_eyes = 1 - ss(win(t, T * 0.26, T * 0.34))
    if fade_eyes > 0:
        _eye(ctx, cx - 70, cy - 60, 1.1, fade_eyes)
        _eye(ctx, cx + 40, cy - 110, 0.9, fade_eyes)
        _eye(ctx, cx + 92, cy - 14, 0.7, fade_eyes)

    for i, p in enumerate(_CF_PIECES):
        tf = T * (0.46 + 0.05 * p["slot"])
        km = ease_io(win(t, tf, tf + T * 0.06))
        cen = (cx + p["c"][0] + p["dir"][0] * sep * 200, cy + p["c"][1] + p["dir"][1] * sep * 200)
        tgt = _cf_slot(p["slot"])
        pos = lerp2(cen, tgt, km)
        pos = (pos[0], pos[1] - math.sin(km * math.pi) * 160)
        ws = _perim(_CF_BW, _CF_BH, len(p["local"]))
        loc = [lerp2(a, b, km) for a, b in zip(p["local"], ws)]
        loc = [rot(q, p["spin"] * sep * (1 - km)) for q in loc]
        pts = [(pos[0] + x, pos[1] + y) for x, y in loc]
        shape(ctx, pts, mix("g6", "g3", km), 5, seed=i + 3)

    # HERO (drawn after the pieces so the lantern light reads over them)
    _hero_fig(ctx, hx, hfeet, hs, t, pose="walk" if walk < 1 else "stand", seed=2, lantern=True)

    # the little house built from the blocks
    base = _CF_HOUSE[1]
    roof_k = ss(win(t, T * 0.84, T * 0.94))
    if roof_k > 0:
        cxh = _CF_HOUSE[0]
        top = base - 2 * _CF_BH
        shape(ctx, [(cxh - 2 * _CF_BW - 12, top), (cxh, top - 170), (cxh + 2 * _CF_BW + 12, top)],
              "red_d", 6, seed=40, alpha=roof_k)
        glow(ctx, cxh, base - 1.5 * _CF_BH, 130, "gold_l", 0.6 * roof_k)
        fillp(ctx, [(cxh - 22, base - 1.5 * _CF_BH - 22), (cxh + 22, base - 1.5 * _CF_BH - 22),
                    (cxh + 22, base - 1.5 * _CF_BH + 22), (cxh - 22, base - 1.5 * _CF_BH + 22)], "gold_l",
              alpha=roof_k)

    # captions in sequence
    if t < T * 0.34:
        caption_tag(ctx, "ABRE LOS OJOS", 100, 110, t, 46, appear=0.0, accent="red")
    elif t < T * 0.61:
        caption_tag(ctx, "ORDENA TUS PALABRAS", 100, 110, t, 46, appear=T * 0.34, accent="teal")
    else:
        caption_tag(ctx, "SAL A SU ENCUENTRO", 100, 110, t, 46, appear=T * 0.61, accent="gold")


# ================================================================== 5. hyperlinks (s37)
_HL_NB = 1200
_HL_BASE = H * 0.84
_HL_X = [W * 0.04 + W * 0.92 * i / (_HL_NB - 1) for i in range(_HL_NB)]


def _hl_bars():
    rng = random.Random(371)
    out, chap = [], 0.5
    for i in range(_HL_NB):
        if i % 18 == 0:                       # structured: one height profile per chapter
            chap = rng.uniform(0.25, 1.0)
        out.append(24 + 200 * chap * rng.uniform(0.35, 1.0))
    return out


def _hl_color(f):
    return mix("teal", "gold", f * 2) if f < 0.5 else mix("gold", "red_l", (f - 0.5) * 2)


def _hl_arcs():
    rng = random.Random(372)
    arcs = []
    for _ in range(420):
        a = rng.randrange(_HL_NB)
        d = int(rng.expovariate(1 / 55.0)) * rng.choice((-1, 1))
        if rng.random() < 0.12:
            d += rng.randrange(300, 900) * rng.choice((-1, 1))
        b = min(max(a + d, 0), _HL_NB - 1)
        if b == a:
            continue
        x1, x2 = _HL_X[a], _HL_X[b]
        y1, y2 = _HL_BASE - _HL_BH[a], _HL_BASE - _HL_BH[b]
        h = min(520, 40 + abs(x2 - x1) * rng.uniform(0.18, 0.3))
        P = ((x1, y1), (x1, y1 - h * 1.33), (x2, y2 - h * 1.33), (x2, y2))
        arcs.append((P, _hl_color(((x1 + x2) / 2) / W)))
    rng.shuffle(arcs)
    return arcs


_HL_BH = _hl_bars()
_HL_ARCS = _hl_arcs()


@scene("hyperlinks")
def hyperlinks(ctx, t, T, seg):
    bg_studio(ctx, t, seed=37, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.03))

    # verse lines grow in from left to right
    ctx.new_path()
    setc(ctx, "g3", 0.55)
    ctx.set_line_width(1.3)
    for i, x in enumerate(_HL_X):
        t0 = T * 0.04 + (i / _HL_NB) * T * 0.22
        g = ease_out(win(t, t0, t0 + T * 0.08), 2)
        if g <= 0:
            continue
        ctx.move_to(x, _HL_BASE)
        ctx.line_to(x, _HL_BASE - _HL_BH[i] * g)
    ctx.stroke()
    setc(ctx, "g2", 0.6)
    ctx.set_line_width(2)
    ctx.move_to(W * 0.03, _HL_BASE)
    ctx.line_to(W * 0.97, _HL_BASE)
    ctx.stroke()

    # cross-reference arcs, drawn progressively (deterministic order)
    n = len(_HL_ARCS)
    for j, (P, colr) in enumerate(_HL_ARCS):
        t0 = T * 0.20 + (j / n) * T * 0.5
        k = win(t, t0, t0 + T * 0.12)
        if k <= 0:
            continue
        p0, p1, p2, p3 = _bez_cut(P, k)
        ctx.new_path()
        ctx.move_to(*p0)
        ctx.curve_to(*p1, *p2, *p3)
        setc(ctx, colr, 0.55)
        ctx.set_line_width(1.6)
        ctx.stroke()

    with hud(ctx):
        num = int(65000 * ease_out(win(t, T * 0.18, T * 0.8), 2))
        text(ctx, f"{num:,}".replace(",", "."), W - 120, 170, 140, FONT_TITLE, "gold_l", align="right",
             alpha=ss(win(t, T * 0.08, T * 0.18)))
    caption_tag(ctx, "65.000 REFERENCIAS CRUZADAS", 100, 110, t, 42, appear=T * 0.30, accent="teal")


# ================================================================== 6. drowning (s38)
_DR_WORDS = ["¿QUÉ?", "SIGNIFICADO", "¿Y SI NO?", "NADA", "TAL VEZ", "TEXTO", "¿CUÁL?", "INTERPRETA", "CAOS",
             "¿POR QUÉ?", "SENTIDO", "¿Y AHORA?", "QUIZÁ", "NADA VALE", "VERDAD?", "?", "¿CUÁL ES?", "TODO"]
_DR_RNG = random.Random(38)
_DR_FRAG = [dict(w=_DR_WORDS[i % len(_DR_WORDS)], a0=i * 2 * math.pi / 18 + _DR_RNG.uniform(-0.3, 0.3),
                 R=_DR_RNG.uniform(260, 600), spd=_DR_RNG.uniform(0.25, 0.5) * (1 if i % 2 else -1),
                 size=_DR_RNG.choice([26, 34, 44, 56]), lift=_DR_RNG.uniform(-40, 40))
            for i in range(26)]


def _surface(t, y0, amp=10):
    return [(x, y0 + math.sin(x * 0.011 + t * 1.6) * amp + math.sin(x * 0.027 - t * 1.1) * amp * 0.5)
            for x in range(-40, W + 61, 60)]


@scene("drowning")
def drowning(ctx, t, T, seg):
    bg_studio(ctx, t, seed=38, dark=True, tone=-0.3)
    camera(ctx, t, T, zoom=(1.0, 1.05))
    fade = win(t, 0, T)
    # light from above, fading
    ctx.set_source(lingrad(ctx, 0, 0, 0, H * 0.6, [(0, col("teal_l", 0.30 * (1 - 0.7 * fade))),
                                                  (1, col("teal_l", 0.0))]))
    ctx.rectangle(0, 0, W, H * 0.6)
    ctx.fill()
    fillp(ctx, [(W * 0.25, -20), (W * 0.55, -20), (W * 0.64, H * 0.4), (W * 0.32, H * 0.4)], "teal_l",
          alpha=0.10 * (1 - 0.7 * fade))

    # the sinking HERO
    hx = W * 0.5
    hy = lerp(H * 0.28, H * 0.84, ease_in(win(t, T * 0.05, T * 0.95), 1.3))
    expr = "fear" if win(t, 0, T) < 0.55 else "closed"
    F.character(ctx, hx, hy, 0.95, F.HERO, expr, t)

    # water body: surface, gradient below
    y0 = H * 0.36
    surf = _surface(t, y0)
    pts = surf + [(W + 40, H + 40), (-40, H + 40)]
    ctx.set_source(lingrad(ctx, 0, y0, 0, H, [(0, col("sea_l", 0.62)), (1, col("night", 0.92))]))
    poly(ctx, pts)
    ctx.fill()
    stroke(ctx, surf, 4, "teal_l", alpha=0.6, taper=(0, 0), wobble=0)

    particles(ctx, t, 30, seed=4, color="g0", region=(W * 0.3, H * 0.4, W * 0.7, H), speed=(0, -60),
              size=(2, 5), alpha=0.5)

    # words and question marks swirling round the head
    for i, f in enumerate(_DR_FRAG):
        a = f["a0"] + t * f["spd"]
        x = hx + math.cos(a) * f["R"]
        y = hy - 40 + math.sin(a) * f["R"] * 0.5 - (t * 6 if i % 4 == 0 else 0) + f["lift"]
        k = ss(win(t, T * 0.04 + i * 0.01, T * 0.12 + i * 0.01))
        if k <= 0:
            continue
        text(ctx, f["w"], x, y, f["size"], FONT_CAPS, "g1", alpha=0.8 * k)


# ================================================================== 7. constraints (s39)
_MZ_NX, _MZ_NY, _MZ_C = 16, 9, 120


def _mz_build():
    rng = random.Random(55)
    edges = []
    box = lambda i, j: 5 <= i <= 10 and 3 <= j <= 5
    for j in range(_MZ_NY):
        for i in range(_MZ_NX):
            if i + 1 < _MZ_NX and (rng.random() < 0.82 or (box(i, j) and box(i + 1, j))):
                edges.append(((i, j), (i + 1, j)))
            if j + 1 < _MZ_NY and (rng.random() < 0.82 or (box(i, j) and box(i, j + 1))):
                edges.append(((i, j), (i, j + 1)))
    return edges


def _mz_path(edges, start, goal):
    adj = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    prev = {start: None}
    q = [start]
    while q:
        u = q.pop(0)
        if u == goal:
            break
        for v in adj.get(u, []):
            if v not in prev:
                prev[v] = u
                q.append(v)
    if goal not in prev:
        return []
    path, u = [], goal
    while u is not None:
        path.append(u)
        u = prev[u]
    return path[::-1]


_MZ_EDGES = _mz_build()
_MZ_LIT = [_mz_path(_MZ_EDGES, (5, 3), (10, 5)), _mz_path(_MZ_EDGES, (6, 5), (9, 3))]
_MZ_KEEP = {frozenset((a, b)) for p in _MZ_LIT for a, b in zip(p, p[1:])}


def _mz_xy(node):
    return (node[0] * _MZ_C + 60, node[1] * _MZ_C + 60)


def _mz_wall(ctx, pts, label, lx, ly, size, k):
    shape(ctx, pts, "ink", 6, seed=int(k * 100))
    with clip(ctx, pts):
        text(ctx, label, lx, ly, size, FONT_CAPS, "g0", tracking=0.06, alpha=ss(k))


@scene("constraints")
def constraints(ctx, t, T, seg):
    bg_studio(ctx, t, seed=12, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.04))
    dim = ss(win(t, T * 0.55, T * 0.8))

    # the maze: many lit paths, then all but the few kept ones go dark
    ctx.new_path()
    for a, b in _MZ_EDGES:
        if frozenset((a, b)) in _MZ_KEEP:
            continue
        (x0, y0), (x1, y1) = _mz_xy(a), _mz_xy(b)
        ctx.move_to(x0, y0)
        ctx.line_to(x1, y1)
    setc(ctx, mix("teal_l", "g4", dim), lerp(0.75, 0.3, dim))
    ctx.set_line_width(7)
    ctx.stroke()
    # the kept paths glow
    for path in _MZ_LIT:
        if len(path) < 2:
            continue
        pts = [_mz_xy(n) for n in path]
        stroke(ctx, pts, 16, "teal", alpha=0.25, taper=(0, 0), wobble=0)
        stroke(ctx, pts, 6, "teal_l", alpha=0.95, taper=(0, 0), wobble=0)
    gx, gy = _mz_xy((10, 5))
    glow(ctx, gx, gy, 140, "gold_l", 0.5)
    fillp(ctx, circle_pts(gx, gy, 12, 12), "gold_l")

    # four walls slide in, closing the funnel
    k1 = ease_out(win(t, T * 0.08, T * 0.28), 3)
    xr = W * 0.3 + (k1 - 1) * W * 0.5
    _mz_wall(ctx, [(-60, -20), (xr, -20), (xr + 24, H + 20), (-60, H + 20)], "TÚ HOY", (xr - 60) / 2 - 10,
             H * 0.5 + 20, 56, k1)
    k2 = ease_out(win(t, T * 0.22, T * 0.42), 3)
    xl = W * 0.7 + (1 - k2) * W * 0.5
    _mz_wall(ctx, [(xl, -20), (W + 60, -20), (W + 60, H + 20), (xl - 24, H + 20)], "TÚ MAÑANA",
             (xl + W) / 2 + 10, H * 0.5 + 20, 56, k2)
    k3 = ease_out(win(t, T * 0.42, T * 0.6), 3)
    yb = H * 0.24 - (1 - k3) * H * 0.4
    _mz_wall(ctx, [(-20, -60), (W + 20, -60), (W + 20, yb), (-20, yb + 20)], "LOS DEMÁS", W / 2,
             (yb - 60) / 2 + 24, 56, k3)
    k4 = ease_out(win(t, T * 0.58, T * 0.78), 3)
    yt = H * 0.76 + (1 - k4) * H * 0.4
    _mz_wall(ctx, [(-20, yt), (W + 20, yt), (W + 20, H + 60), (-20, H + 60)], "EL MUNDO", W / 2,
             (yt + H + 60) / 2 + 20, 56, k4)


# ================================================================== 8. field (s40)
_FD_RNG = random.Random(40)
_FD_GRASS = []
for _ in range(330):
    gx = _FD_RNG.uniform(-40, W + 40)
    gy = _FD_RNG.uniform(H * 0.56, H * 1.02)
    u = (gy - H * 0.56) / (H * 0.46)
    L = (26 + 90 * u) * _FD_RNG.uniform(0.6, 1.1)
    _FD_GRASS.append((gx, gy, L, _FD_RNG.uniform(-0.35, 0.35) * L, 6 + 14 * u, _FD_RNG.random() < 0.5))
_FD_GRASS.sort(key=lambda g: g[1])
_FD_P0 = (W * 0.17, H * 0.84)
_FD_C = (W * 0.45, H * 0.55)
_FD_P2 = (W * 0.8, H * 0.47)
_FD_STAR = (W * 0.8, H * 0.47)


def _fd_bez(u):
    a = (1 - u) ** 2
    b = 2 * (1 - u) * u
    c = u * u
    return (a * _FD_P0[0] + b * _FD_C[0] + c * _FD_P2[0], a * _FD_P0[1] + b * _FD_C[1] + c * _FD_P2[1])


def _star(cx, cy, r_out, r_in):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


@scene("field")
def field(ctx, t, T, seg):
    # dusk sky, then the field
    ctx.set_source(lingrad(ctx, 0, 0, 0, H * 0.56, [(0, mix("night", "cobalt_d", 0.3)),
                                                   (1, mix("cobalt_d", "teal_d", 0.4))]))
    ctx.paint()
    camera(ctx, t, T, zoom=(1.0, 1.04), focus=(W * 0.5, H * 0.6))
    ctx.set_source(lingrad(ctx, 0, H * 0.56, 0, H, [(0, mix("teal_d", "ink", 0.2)), (1, "ink")]))
    poly(ctx, [(-100, H * 0.56), (W + 100, H * 0.56), (W + 100, H + 100), (-100, H + 100)])
    ctx.fill()

    # the star on the horizon
    k_star = ss(win(t, T * 0.30, T * 0.44))
    if k_star > 0:
        pulse = 1 + 0.08 * math.sin(t * 3)
        glow(ctx, _FD_STAR[0], _FD_STAR[1], 320 * k_star, "gold_l", 0.55)
        shape(ctx, _star(_FD_STAR[0], _FD_STAR[1], 40 * pulse, 16 * pulse), "gold_l", 3, seed=5, alpha=k_star)

    # angular grass
    sway_t = t * 1.2
    for gx, gy, L, dx, w, dark in _FD_GRASS:
        sway = math.sin(sway_t + gx * 0.01) * 6
        tip = (gx + dx + sway, gy - L)
        fillp(ctx, blade((gx, gy), tip, w + 4, bend=0.06), "ink" if dark else "teal_d", alpha=0.9)

    # dotted path grows toward the star as HERO walks it
    prog = ease_io(win(t, T * 0.36, T * 0.86))
    n_dots = 30
    for i in range(n_dots):
        u = (i + 1) / (n_dots + 1)
        if prog < u - 0.01:
            continue
        x, y = _fd_bez(u)
        fillp(ctx, circle_pts(x, y, 6, 10), "gold_l" if i % 2 else "teal_l")

    # HERO, at the edge first, then walking the path
    hx, hy = _fd_bez(prog)
    h = lerp(440, 130, prog)
    walking = 0.36 * T < t < 0.9 * T
    glow(ctx, hx, hy, 90, "teal", 0.35)
    _hero_fig(ctx, hx, hy, h, t, pose="walk" if walking else "stand", seed=7)

    # progress gauge (screen space): a bar with an arrow riding on it
    with hud(ctx):
        gx = W - 110
        y_top, y_bot = H * 0.12, H * 0.88
        fillp(ctx, [(gx - 14, y_top), (gx + 14, y_top), (gx + 14, y_bot), (gx - 14, y_bot)], "ink", alpha=0.6)
        yf = y_bot - (y_bot - y_top) * prog
        fillp(ctx, [(gx - 14, yf), (gx + 14, yf), (gx + 14, y_bot), (gx - 14, y_bot)], "gold_l")
        fillp(ctx, [(gx - 30, yf + 10), (gx, yf - 22), (gx + 30, yf + 10)], "teal_l")
        text(ctx, "AVANCE", gx, y_top - 26, 26, FONT_CAPS, "g1", tracking=0.1)


# ================================================================== 9. summit (s41)
_SM_RIDGE = [(-60, H * 0.95), (W * 0.12, H * 0.8), (W * 0.22, H * 0.73), (W * 0.32, H * 0.66),
             (W * 0.4, H * 0.6), (W * 0.48, H * 0.46), (W * 0.55, H * 0.38), (W * 0.62, H * 0.24),
             (W * 0.7, H * 0.34), (W * 0.8, H * 0.44), (W * 0.9, H * 0.6), (W + 60, H * 0.7)]
_SM_CLIMB = _SM_RIDGE[1:8]
_SM_SEG = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(_SM_CLIMB, _SM_CLIMB[1:])]
_SM_LEN = sum(_SM_SEG)


def _sm_at(f):
    """Position and slope angle on the climb at fraction f (0..1) of its length."""
    d = f * _SM_LEN
    for i, L in enumerate(_SM_SEG):
        if d <= L or i == len(_SM_SEG) - 1:
            a, b = _SM_CLIMB[i], _SM_CLIMB[i + 1]
            k = min(1.0, d / L) if L else 0.0
            return lerp2(a, b, k), math.atan2(b[1] - a[1], b[0] - a[0])
        d -= L
    return _SM_CLIMB[-1], 0.0


@scene("summit")
def summit(ctx, t, T, seg):
    d = win(t, 0, T * 0.7)
    sun = (W * 0.62, lerp(H * 0.7, H * 0.3, ease_io(win(t, T * 0.05, T * 0.75))))
    # dawn sky
    ctx.set_source(lingrad(ctx, 0, 0, 0, H * 0.8, [(0, mix("night", "cobalt_d", 0.5 + 0.5 * d)),
                                                  (0.6, mix("cobalt", "rust", 0.3 + 0.4 * d)),
                                                  (1, mix("gold_l", "rust", 0.3))]))
    ctx.paint()
    camera(ctx, t, T, zoom=(1.0, 1.05), focus=(W * 0.5, H * 0.5))
    glow(ctx, sun[0], sun[1], 620, "gold_l", 0.7)
    for k in range(14):
        a = k * 2 * math.pi / 14 + t * 0.04
        fillp(ctx, [sun, (sun[0] + math.cos(a - 0.05) * 1500, sun[1] + math.sin(a - 0.05) * 1500),
                    (sun[0] + math.cos(a + 0.05) * 1500, sun[1] + math.sin(a + 0.05) * 1500)],
              "gold_l", alpha=0.07)
    fillp(ctx, circle_pts(sun[0], sun[1], 110, 40), "gold_l")

    # back range
    back = [(-60, H * 0.8), (W * 0.15, H * 0.6), (W * 0.3, H * 0.7), (W * 0.45, H * 0.5), (W * 0.6, H * 0.6),
            (W * 0.75, H * 0.42), (W * 0.9, H * 0.62), (W + 60, H * 0.55), (W + 60, H + 60), (-60, H + 60)]
    fillp(ctx, back, mix("cobalt_d", "night", 0.3))

    # the steep ridge, with the summit and its snow
    ridge = _SM_RIDGE + [(W + 60, H + 60), (-60, H + 60)]
    shape(ctx, ridge, "g6", 6, seed=9)
    cel(ctx, ridge, [(W * 0.62, H * 0.1), (W * 1.2, H * 0.1), (W * 1.2, H * 1.2), (W * 0.62, H * 1.2)], "ink2")
    stroke(ctx, _SM_RIDGE[1:], 8, "gold_l", alpha=0.8, taper=(0.2, 0.2))
    fillp(ctx, [(W * 0.58, H * 0.3), (W * 0.62, H * 0.24), (W * 0.66, H * 0.3), (W * 0.63, H * 0.29),
                (W * 0.6, H * 0.32)], "g0", alpha=0.9)

    # HERO climbs the ridge
    f = ease_io(win(t, T * 0.10, T * 0.80))
    (px, py), ang = _sm_at(f)
    h = lerp(230, 170, f)
    _hero_fig_lean(ctx, px, py + 3, h, t, ang)

    # the four words at the end, on a dark band
    k_band = ss(win(t, T * 0.78, T * 0.88))
    if k_band > 0:
        fillp(ctx, [(0, H * 0.8), (W, H * 0.8), (W, H * 0.95), (0, H * 0.95)], "night", alpha=0.72 * k_band)
    words = ["ATENCIÓN", "VERDAD", "VALOR", "MUNDO"]
    size = 84
    wd = [text_width(ctx, w, size, FONT_TITLE, tracking=0.06) for w in words]
    sep = 60
    total = sum(wd) + sep * (len(words) - 1)
    x = W / 2 - total / 2
    for i, w in enumerate(words):
        ka = ease_out(win(t, T * (0.80 + i * 0.03), T * (0.80 + i * 0.03) + 0.3), 3)
        text(ctx, w, x, H * 0.9, size, FONT_TITLE, "g0", align="left", tracking=0.06, alpha=ka)
        x += wd[i]
        if i < len(words) - 1:
            text(ctx, "·", x + sep / 2, H * 0.9, size, FONT_TITLE, "gold_l", alpha=ka)
            x += sep


def _hero_fig_lean(ctx, x, y, h, t, ang):
    """HERO on a slope: the figure leans a fraction of the slope angle."""
    with at(ctx, x, y, 1.0, a=ang * 0.3):
        _hero_fig(ctx, 0, 0, h, t, pose="walk", seed=8)
