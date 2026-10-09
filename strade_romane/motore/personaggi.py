"""Original line-art characters with expressive faces and simple rigs.

Coordinates: feet at (0, 0), y grows downwards, characters face +x. Sizes are in px at s=1
(an adult is ~300 px tall). Every function takes the Pen, a pose dict and the time.
"""
import math

from .linea import arc, at, ellipse, lerp, noise1, rot, wave


# ----------------------------------------------------------------- face
def face(pen, cx, cy, r, expr="calm", look=0.0, t=0.0, blink=True, nose=1.0, brows=True, seed=0, alpha=1.0):
    """Three-quarter face looking right, with a big friendly nose.
    expr: calm smile grin talk surprise worry squint proud tired determined."""
    L = pen.line
    # head: a soft egg, slightly wider at the cheek
    head = [(cx + math.cos(a) * r * (1.0 + 0.06 * math.cos(a)), cy + math.sin(a) * r * 1.04)
            for a in [math.radians(-12 + i * 12) for i in range(31)]]
    L(head, 1.1, alpha, seed=seed)
    # nose: a round bump sticking out on the right
    a0, a1 = math.radians(-14), math.radians(28)
    n0 = (cx + math.cos(a0) * r * 1.05, cy + math.sin(a0) * r)
    n1 = (cx + math.cos(a1) * r * 1.02, cy + math.sin(a1) * r)
    k = r * 0.44 * nose
    L([n0, (n0[0] + k * 0.9, n0[1] + r * 0.02), (n0[0] + k * 1.15, n0[1] + r * 0.20), (n1[0] + k * 0.5, n1[1] + r * 0.02),
       (n1[0] - r * 0.02, n1[1] - r * 0.02)], 1.0, alpha, seed=seed + 1)
    # ear
    # eye
    ex, ey = cx + r * 0.50 + look * r * 0.05, cy - r * 0.16
    closed = blink and ((t * 0.31 + seed * 0.37) % 3.4) < 0.12
    if expr in ("squint", "proud", "smile_closed") or closed:
        L([(ex - r * 0.12, ey + r * 0.01), (ex, ey + r * 0.06), (ex + r * 0.11, ey + r * 0.01)], 0.95, alpha,
          seed=seed + 2)
    elif expr == "surprise":
        L(ellipse(ex, ey, r * 0.12, r * 0.14, 14), 0.85, alpha, seed=seed + 2)
        pen.dot(ex + r * 0.03, ey + r * 0.01, r * 0.06, alpha)
    else:
        pen.dot(ex, ey, r * 0.095, alpha)
    # brow
    if brows:
        lift = {"surprise": 0.12, "worry": 0.06, "determined": -0.05, "proud": 0.04, "tired": -0.03}.get(expr, 0.0)
        tilt = {"worry": -0.08, "determined": 0.09, "tired": -0.05}.get(expr, 0.0)
        by = ey - r * (0.27 + lift)
        L([(ex - r * 0.17, by + tilt * r), (ex - r * 0.02, by - r * 0.04), (ex + r * 0.14, by - tilt * r * 0.5)],
          1.0, alpha, seed=seed + 3)
    # mouth (under the nose)
    mx, my = cx + r * 0.62, cy + r * 0.48
    if expr in ("smile", "proud", "smile_closed"):
        L([(mx - r * 0.22, my - r * 0.05), (mx - r * 0.06, my + r * 0.08), (mx + r * 0.10, my - r * 0.03)], 0.95,
          alpha, seed=seed + 4)
    elif expr == "grin":
        L([(mx - r * 0.24, my - r * 0.07), (mx - r * 0.04, my + r * 0.13), (mx + r * 0.14, my - r * 0.05),
           (mx - r * 0.24, my - r * 0.07)], 0.95, alpha, seed=seed + 4)
    elif expr in ("talk", "surprise"):
        o = 0.45 + 0.55 * abs(math.sin(t * 8.5)) if expr == "talk" else 1.0
        L(ellipse(mx - r * 0.05, my, r * 0.08, r * 0.03 + r * 0.07 * o, 12), 0.9, alpha, seed=seed + 4)
    elif expr == "worry":
        L([(mx - r * 0.2, my + r * 0.05), (mx - r * 0.05, my - r * 0.02), (mx + r * 0.08, my + r * 0.04)], 0.9,
          alpha, seed=seed + 4)
    elif expr == "determined":
        L([(mx - r * 0.2, my), (mx + r * 0.08, my - r * 0.02)], 0.95, alpha, seed=seed + 4)
    else:
        L([(mx - r * 0.18, my), (mx - r * 0.04, my + r * 0.035), (mx + r * 0.08, my)], 0.9, alpha, seed=seed + 4)


# ----------------------------------------------------------------- limbs
def limb(pen, p0, a1, l1, a2, l2, w=1.0, alpha=1.0, seed=0):
    """Two-segment limb drawn as a single bent stroke. Angles in radians from +x (0 = right, pi/2 = down)."""
    p1 = (p0[0] + math.cos(a1) * l1, p0[1] + math.sin(a1) * l1)
    p2 = (p1[0] + math.cos(a2) * l2, p1[1] + math.sin(a2) * l2)
    pen.line([p0, p1, p2], w, alpha, seed=seed)
    return p1, p2


def hand(pen, x, y, r=7, alpha=1.0, seed=0):
    pen.line(ellipse(x, y, r, r * 0.9, 12), 0.85, alpha, seed=seed)


def tube(pen, pts, w0, w1, alpha=1.0, seed=0, lw=0.95, cap_end=False):
    """A soft limb/tube: two side lines following a smooth centre line (line-art volume)."""
    from .linea import catmull, resample
    C = resample(catmull(pts, n=8), 18)
    left, right = [], []
    n = len(C)
    for i in range(n):
        a = C[max(0, i - 1)]
        b = C[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / d, dx / d
        w = lerp(w0, w1, i / (n - 1)) / 2
        left.append((C[i][0] + nx * w, C[i][1] + ny * w))
        right.append((C[i][0] - nx * w, C[i][1] - ny * w))
    pen.line(left, lw, alpha, seed=seed, taper=0.08)
    pen.line(right, lw, alpha, seed=seed + 1, taper=0.08)
    if cap_end:
        e = C[-1]
        pen.line([left[-1], (e[0] + (e[0] - C[-2][0]) * 0.6, e[1] + (e[1] - C[-2][1]) * 0.6), right[-1]], lw, alpha,
                 seed=seed + 2, taper=0.1)
    return C


def mitten(pen, x, y, a=0.0, r=9, alpha=1.0, seed=0, open_=False):
    """Little round hand with a thumb, rotated by a (direction the arm points)."""
    pts = ellipse(0, 0, r, r * 0.82, 14)
    pts = [rot(p, a) for p in pts]
    pen.line([(x + p[0], y + p[1]) for p in pts], 0.9, alpha, seed=seed)
    th = [rot(p, a) for p in [(-2, -r * 0.7), (r * 0.2, -r * 1.35), (r * 0.7, -r * 0.9)]]
    pen.line([(x + p[0], y + p[1]) for p in th], 0.85, alpha, seed=seed + 1)


def foot(pen, x, y, fx=1, alpha=1.0, seed=0, sandal=True):
    pts = [(x - 9 * fx, y - 10), (x - 10 * fx, y), (x + 20 * fx, y), (x + 22 * fx, y - 5), (x + 8 * fx, y - 11)]
    pen.line(pts, 0.95, alpha, seed=seed)
    if sandal:
        pen.line([(x - 2 * fx, y - 11), (x + 4 * fx, y - 2)], 0.6, alpha * 0.8, seed=seed + 1)


# ----------------------------------------------------------------- the traveller
def viandante(pen, x, y, s=1.0, t=0.0, walk=0.0, expr="calm", look=0.0, wave_hand=0.0, fx=1, alpha=1.0,
              speed=1.0, hat=True, stick=True, point=0.0):
    """Our guide: a small round traveller with a wide-brimmed hat (petasos), a satchel and a staff.
    walk: 0 = standing, 1 = walking (blend). point: raise front arm to point ahead."""
    with at(pen, x, y, s, fx=fx):
        ph = t * 2 * math.pi * 0.9 * speed
        bob = -abs(math.sin(ph)) * 6 * walk + wave(t, 0.25) * 1.5 * (1 - walk)
        L = pen.line
        hip = (0, -118 + bob)
        # legs
        for side, k in ((1, 0.0), (-1, math.pi)):
            sw = math.sin(ph + k) * 0.5 * walk
            knee_bend = max(0.0, math.sin(ph + k + 1.2)) * 0.7 * walk
            a1 = math.pi / 2 + sw
            a2 = a1 - knee_bend * 0.9 + 0.05
            p1, p2 = limb(pen, (hip[0] + side * 6, hip[1]), a1, 60, a2, 58, 1.0, alpha, seed=10 + side)
            # sandal
            L([(p2[0] - 6, p2[1] + 1), (p2[0] + 16, p2[1] + 1)], 1.0, alpha, seed=12 + side)
        # tunic: soft bell shape
        top = (0, -212 + bob)
        tunic = [(-30, -200 + bob), (-40, -150 + bob), (-48, -108 + bob + wave(t, 0.6) * 2),
                 (-10, -102 + bob), (22, -104 + bob), (46, -110 + bob - wave(t, 0.6) * 2), (36, -160 + bob),
                 (26, -202 + bob)]
        L(tunic, 1.0, alpha, seed=20)
        L([(-44, -132 + bob), (0, -128 + bob), (40, -134 + bob)], 0.8, alpha * 0.9, seed=21)   # belt
        # satchel strap + bag
        L([(20, -200 + bob), (-26, -140 + bob)], 0.8, alpha, seed=22)
        bag = [(-46, -150 + bob), (-26, -146 + bob), (-24, -122 + bob), (-48, -124 + bob)]
        L(bag + [bag[0]], 0.85, alpha, smooth_=False, seed=23)
        # back arm (swinging)
        sw = math.sin(ph + math.pi) * 0.45 * walk
        limb(pen, (-6, -196 + bob), math.pi / 2 + 0.25 + sw, 44, math.pi / 2 + 0.05 + sw * 0.6, 40, 0.95,
             alpha * 0.85, seed=30)
        # front arm (staff, wave or point)
        if point > 0:
            a1 = lerp(math.pi / 2 - 0.3, -0.35, point)
            a2 = lerp(math.pi / 2 - 0.5, -0.30, point)
        elif wave_hand > 0:
            a1 = lerp(math.pi / 2 - 0.3, -1.3, wave_hand)
            a2 = lerp(math.pi / 2 - 0.5, -1.7 + 0.35 * math.sin(t * 9), wave_hand)
        else:
            sw = math.sin(ph) * 0.35 * walk
            a1 = math.pi / 2 - 0.45 + sw
            a2 = 0.25 + sw * 0.5
        p1, p2 = limb(pen, (8, -196 + bob), a1, 44, a2, 38, 1.0, alpha, seed=31)
        hand(pen, p2[0], p2[1], 7, alpha, seed=32)
        if stick and point <= 0 and wave_hand <= 0:
            L([(p2[0] + 4, p2[1] - 46), (p2[0] + 2, p2[1] + 4), (p2[0] + 4 + 10 * math.sin(ph) * walk, -2)],
              1.0, alpha, smooth_=False, seed=33)
        # neck + head
        L([(4, -212 + bob), (8, -226 + bob)], 0.9, alpha, seed=40)
        hx, hy = 10, -262 + bob
        face(pen, hx, hy, 36, expr, look, t, seed=41, alpha=alpha)
        if hat:
            # petasos: wide brim + low dome, with a little sway
            sway = wave(t, 0.5) * 0.04 + math.sin(ph) * 0.03 * walk
            brim = [(-62, 0), (-30, 6), (20, 7), (64, 1)]
            dome = [(-30, 3), (-26, -26), (-2, -40), (22, -30), (28, 4)]
            with at(pen, hx - 2, hy - 30, 1.0, sway):
                L(brim, 1.0, alpha, seed=42)
                L(dome, 1.0, alpha, seed=43)
                L([(-62, 0), (-70, 4)], 0.8, alpha, seed=44)


# ----------------------------------------------------------------- the mule
def mulo(pen, x, y, s=1.0, t=0.0, walk=0.0, expr="calm", ear=0.0, fx=1, alpha=1.0, load=True, speed=1.0):
    """A patient mule with very expressive ears. ear: -1 droopy .. +1 perked."""
    with at(pen, x, y, s, fx=fx):
        L = pen.line
        ph = t * 2 * math.pi * 0.9 * speed
        bob = -abs(math.sin(ph)) * 4 * walk
        # legs (4): soft curved strokes with little hooves
        for i, (lx, k) in enumerate([(-66, 0.0), (-46, math.pi), (44, math.pi), (62, 0.0)]):
            sw = math.sin(ph + k) * 0.38 * walk
            lift = max(0.0, math.sin(ph + k + 1.3)) * 12 * walk
            p0 = (lx, -96 + bob)
            fxp = lx + math.sin(sw) * 46
            bend = (8 if i < 2 else -8) + 14 * max(0.0, math.sin(ph + k + 1.3)) * walk
            mx, my = (p0[0] + fxp) / 2 + bend, (p0[1] - lift) / 2 - 4
            L([p0, (mx, my), (fxp, -6 - lift)], 1.0, alpha * (0.8 if i in (1, 2) else 1.0), seed=60 + i)
            L([(fxp - 6, -2 - lift), (fxp + 8, -2 - lift), (fxp + 7, -9 - lift), (fxp - 5, -9 - lift)], 0.9,
              alpha * (0.8 if i in (1, 2) else 1.0), seed=64 + i)
        # body: a round barrel with a soft belly and a gentle back dip
        body = [(-84, -104 + bob), (-92, -134 + bob), (-70, -156 + bob), (-20, -150 + bob), (30, -156 + bob),
                (74, -150 + bob), (90, -126 + bob), (80, -100 + bob), (40, -86 + bob), (-10, -82 + bob),
                (-56, -88 + bob), (-84, -104 + bob)]
        L(body, 1.1, alpha, seed=70)
        # tail (swishing)
        sw = wave(t, 0.7) * 10
        L([(-88, -122 + bob), (-104, -110 + bob + sw * 0.3), (-110 + sw * 0.5, -84 + bob)], 0.9, alpha, seed=71)
        L([(-110 + sw * 0.5, -84 + bob), (-114 + sw * 0.6, -70 + bob), (-104 + sw * 0.5, -72 + bob)], 0.8, alpha,
          seed=72)
        # neck and head
        nod = math.sin(ph * 1.0) * 0.06 * walk + wave(t, 0.2) * 0.03
        with at(pen, 76, -140 + bob, 1.0, nod):
            L([(0, 0), (26, -46), (44, -70)], 1.0, alpha, seed=73)
            L([(10, 12), (36, -28), (58, -50)], 1.0, alpha, seed=74)
            # head: long muzzle
            head = [(40, -72), (66, -78), (96, -62), (110, -40), (102, -26), (80, -28), (56, -40), (48, -54)]
            L(head + [head[0]], 1.0, alpha, seed=75)
            pen.dot(98, -36, 2.4, alpha)                       # nostril
            pen.dot(66, -62, 3.4, alpha)                       # eye
            if expr == "smile":
                L([(84, -26), (96, -22), (104, -28)], 0.8, alpha, seed=76)
            # ears: long, expressive
            for k, (ox, sp) in enumerate([(52, -0.15), (60, 0.12)]):
                droop = -ear
                a = -math.pi / 2 - 0.45 + sp + droop * 0.6 + wave(t, 0.33, k) * 0.06
                tip = (ox + math.cos(a) * 52, -74 + math.sin(a) * 52)
                L([(ox - 6, -72), (lerp(ox, tip[0], 0.5) - 8, lerp(-74, tip[1], 0.5)), tip,
                   (lerp(ox, tip[0], 0.5) + 6, lerp(-74, tip[1], 0.5)), (ox + 6, -74)], 0.9, alpha, seed=77 + k)
            # mane
            for k in range(4):
                L([(14 + k * 9, -14 - k * 14), (6 + k * 9, -26 - k * 14)], 0.7, alpha * 0.8, seed=80 + k)
        # load (two packs + blanket)
        if load:
            L([(-40, -148 + bob), (-36, -176 + bob), (24, -178 + bob), (30, -148 + bob)], 1.0, alpha, seed=84)
            L(ellipse(-50, -128 + bob, 18, 22, 18), 0.9, alpha, seed=85)
            L([(-30, -176 + bob), (-40, -160 + bob), (-10, -150 + bob)], 0.6, alpha * 0.7, seed=86)
