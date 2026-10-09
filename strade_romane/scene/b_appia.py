"""b03 appio · b04 regina · b05 groma"""
import bisect
import math
import random

import cairo

from motore.film import scena
from motore.linea import W, at, catmull, clamp, ease_io, ease_out, ellipse, lerp, length, rot, smooth, trim, wave, win
from motore.omino import DOWN, omino
from motore.personaggi import mulo

GY = 790                                   # ground / horizon line
ARM_REST = (DOWN - 0.35, 0.4)              # omino's own default (standing)


# ================================================================== small helpers
def ramp(t, a, b):
    return smooth(win(t, a, b))


def pulse(t, a, b, c, d):
    return ramp(t, a, b) * (1.0 - ramp(t, c, d))


def blend(base, *pairs):
    """Blend an arm pose (a1, a2) toward several target poses with weights."""
    a1, a2 = base
    for (p1, p2), w in pairs:
        if w > 0:
            a1, a2 = lerp(a1, p1, w), lerp(a2, p2, w)
    return (a1, a2)


def body_pt(x, y, s, fx, lean, p):
    """Local omino point -> screen (same transform chain as omino)."""
    rx, ry = rot(p, lean * 0.25) if lean else p
    return (x + s * fx * rx, y + s * ry)


def hand_of(x, y, s, t, arm, fx=1, lean=0.0, seed=0):
    bob = wave(t, 0.23, seed) * 1.6
    a1, a2 = arm
    p = (16 + math.cos(a1) * 46 + math.cos(a2) * 50, -186 + bob + math.sin(a1) * 46 + math.sin(a2) * 50)
    return body_pt(x, y, s, fx, lean, p)


def eye_of(x, y, s, t, fx=1, lean=0.0, seed=0):
    bob = wave(t, 0.23, seed) * 1.6
    return body_pt(x, y, s, fx, lean, (36, -259 + bob))


def dashes(pts, dash=18.0, gap=12.0, k0=0.0, k1=1.0):
    """Dashed version of a polyline, only the part between fractions k0..k1."""
    L = length(pts)
    if L <= 1 or k1 <= k0:
        return []
    out, s, step = [], 0.0, dash + gap
    a0, a1 = L * k0, L * k1
    while s < a1:
        a, b = max(s, a0), min(s + dash, a1)
        if b > a + 1.5:
            out.append(trim(pts, a / L, b / L))
        s += step
    return out


def write(pen, s, x, y, size, t, t0, vanish, out=None, alpha=0.92, align="center", dur=None):
    """Handwritten label that writes on at t0 and wipes off (right to left) on vanish / at `out`."""
    d = dur or max(0.6, 0.06 * len(s))
    r = min(ease_io(win(t, t0, t0 + d)), 1.0 - vanish)
    if out is not None:
        r = min(r, 1.0 - ease_io(win(t, out, out + 0.7)))
    if r > 0.002:
        pen.text(s, x, y, size, alpha, align=align, reveal=r)


def clipx(pts, x0=-60.0, x1=W + 60.0):
    out = []
    for a, b in zip(pts, pts[1:]):
        ina, inb = x0 <= a[0] <= x1, x0 <= b[0] <= x1
        if ina:
            if not out:
                out.append(a)
        elif inb:
            xe = x0 if a[0] < x0 else x1
            f = (xe - a[0]) / ((b[0] - a[0]) or 1e-6)
            out.append((xe, a[1] + (b[1] - a[1]) * f))
        if inb:
            out.append(b)
        elif ina:
            xe = x1 if b[0] > x1 else x0
            f = (xe - a[0]) / ((b[0] - a[0]) or 1e-6)
            out.append((xe, a[1] + (b[1] - a[1]) * f))
    return out


def y_on(poly, x):
    xs = [p[0] for p in poly]
    i = clamp(bisect.bisect_left(xs, x), 1, len(poly) - 1)
    a, b = poly[i - 1], poly[i]
    f = clamp((x - a[0]) / ((b[0] - a[0]) or 1e-6))
    return a[1] + (b[1] - a[1]) * f


# ------------------------------------------------------------------ props
def temple(cx, by, w, h, ncol=4):
    st = [[(cx - w / 2 - 12, by), (cx + w / 2 + 12, by)],
          [(cx - w / 2 - 5, by - 9), (cx + w / 2 + 5, by - 9)]]
    for i in range(ncol):
        x = cx - w / 2 + 12 + i * (w - 24) / (ncol - 1)
        st.append({"p": [(x, by - 9), (x, by - 9 - h)], "smooth": False, "w": 0.85})
    top = by - 9 - h
    st.append([(cx - w / 2 - 6, top), (cx + w / 2 + 6, top)])
    st.append({"p": [(cx - w / 2 - 6, top - 13), (cx + w / 2 + 6, top - 13)], "w": 0.8})
    st.append({"p": [(cx - w / 2 - 14, top - 13), (cx, top - 13 - w * 0.27), (cx + w / 2 + 14, top - 13)],
               "smooth": False})
    return st


def tholos(cx, by, w, h):
    st = [[(cx - w / 2 - 8, by), (cx + w / 2 + 8, by)]]
    for i in range(3):
        x = cx - w / 2 + 8 + i * (w - 16) / 2
        st.append({"p": [(x, by), (x, by - h)], "smooth": False, "w": 0.8})
    st.append([(cx - w / 2 - 4, by - h), (cx + w / 2 + 4, by - h)])
    st.append(arc(cx, by - h - 2, w / 2 + 2, math.pi, 2 * math.pi, 16, w * 0.32))
    st.append({"p": [(cx, by - h - 2 - w * 0.32), (cx, by - h - 14 - w * 0.32)], "w": 0.7})
    return st


def arc(cx, cy, r, a0, a1, n=24, ry=None):
    ry = r if ry is None else ry
    return [(cx + math.cos(lerp(a0, a1, i / n)) * r, cy + math.sin(lerp(a0, a1, i / n)) * ry) for i in range(n + 1)]


def cypress(x, y, h, w=11):
    return {"p": [(x, y), (x - w, y - h * 0.35), (x - w * 0.6, y - h * 0.75), (x, y - h), (x + w * 0.6, y - h * 0.75),
                  (x + w, y - h * 0.35), (x, y)], "w": 0.85}


def town(cx, by, s=1.0):
    """A little walled town with a gate (Capua, Benevento...)."""
    def P(pts):
        return [(cx + x * s, by + y * s) for x, y in pts]
    st = [P([(-62, 0), (-62, -46), (62, -46), (62, 0)])]
    st.append({"p": P([(-62, -46), (-62, -54), (-50, -54), (-50, -46)]), "smooth": False, "w": 0.7})
    st.append({"p": P([(50, -46), (50, -54), (62, -54), (62, -46)]), "smooth": False, "w": 0.7})
    st.append(P(arc(0, 0, 16, math.pi, 2 * math.pi, 12, 22)))
    st.append({"p": P([(-46, -46), (-46, -74), (-30, -90), (-14, -74), (-14, -46)]), "smooth": False, "w": 0.85})
    st.append({"p": P([(16, -46), (16, -96), (40, -96), (40, -46)]), "smooth": False, "w": 0.85})
    st.append({"p": P([(12, -96), (28, -110), (44, -96)]), "smooth": False, "w": 0.8})
    st.append({"p": P([(-6, -46), (-6, -66), (8, -66), (8, -46)]), "smooth": False, "w": 0.7})
    return st


def roll(pen, x, ybot, r, ang, alpha, depth=38.0, seed=0, w=1.0):
    """A scroll roll lying across the road band, seen in a 3/4 view."""
    if alpha <= 0.01 or r < 1:
        return
    cy = ybot - r
    pen.line(ellipse(x, cy, r, r, 22), w, alpha, closed=True, seed=seed)
    pen.line(arc(x, cy - depth, r, math.pi, 2 * math.pi, 12), 0.75 * w, alpha * 0.75, seed=seed + 1)
    pen.line([(x - r, cy), (x - r, cy - depth)], 0.75 * w, alpha * 0.75, seed=seed + 2)
    pen.line([(x + r, cy), (x + r, cy - depth)], 0.75 * w, alpha * 0.75, seed=seed + 3)
    sp = [(x + math.cos(th + ang) * r * (0.12 + 0.72 * th / (3 * math.pi)),
           cy + math.sin(th + ang) * r * (0.12 + 0.72 * th / (3 * math.pi))) for th in
          [i * 3 * math.pi / 26 for i in range(27)]]
    pen.line(sp, 0.6 * w, alpha * 0.8, seed=seed + 4)


def cloud(cx, cy, s=1.0):
    pts = [(-90, 20), (-96, -4), (-70, -24), (-40, -22), (-22, -46), (14, -50), (36, -30), (64, -36), (92, -12),
           (88, 16), (40, 22), (-20, 24)]
    return [(cx + x * s, cy + y * s) for x, y in pts]


def helmet(pen, x, base, alpha, seed, clip_y, s=1.0):
    """A crested helmet peeking from behind a ridge (clipped at clip_y), with a pair of watchful eyes."""
    ctx = pen.ctx
    ctx.save()
    ctx.rectangle(x - 60 * s, 0, 120 * s, clip_y)
    ctx.clip()
    with at(pen, x, base, s):
        pen.line(arc(0, 0, 17, math.pi, 2 * math.pi, 14, 16), 1.0, alpha, seed=seed)
        pen.line([(-22, 0), (22, 0)], 0.9, alpha, seed=seed + 1)
        pen.line([(-10, -15), (-3, -28), (10, -28), (16, -17)], 0.85, alpha, seed=seed + 2)
        for k in range(3):
            pen.line([(-4 + k * 6, -16), (-2 + k * 6, -25)], 0.5, alpha * 0.7, seed=seed + 3 + k)
        pen.dot(-5, 9, 2.2, alpha)
        pen.dot(6, 9, 2.2, alpha)
    ctx.restore()


def spear(pen, x, base, ang, alpha, seed, clip_y):
    ctx = pen.ctx
    ctx.save()
    ctx.rectangle(x - 60, 0, 120, clip_y)
    ctx.clip()
    tip = (x + math.sin(ang) * 120, base - math.cos(ang) * 120)
    pen.line([(x, base), tip], 0.7, alpha, smooth_=False, seed=seed)
    d = (math.sin(ang), -math.cos(ang))
    n = (-d[1], d[0])
    a = (tip[0] - n[0] * 5, tip[1] - n[1] * 5)
    b = (tip[0] + d[0] * 16, tip[1] + d[1] * 16)
    c = (tip[0] + n[0] * 5, tip[1] + n[1] * 5)
    pen.line([a, b, c], 0.7, alpha, smooth_=False, seed=seed + 1)
    ctx.restore()


# ================================================================== b03 appio
RIDGE = [(1480, 792), (1540, 712), (1580, 728), (1650, 600), (1700, 636), (1790, 562), (1850, 616), (1910, 590),
         (1960, 640), (2000, 624)]
RIDGE_FAR = [(1560, 680), (1640, 600), (1720, 624), (1800, 526), (1880, 566), (1940, 528), (2000, 550)]
PEAKS = [(1650, 600), (1790, 562), (1910, 590)]
AX, AS = 730, 1.55                      # Appio's feet x and scale
X0, XC = 800, 1312                      # road start, where the roll stops (Capua's gate)
BAND = 858                              # near edge of the unrolled plan / road band
ROME = [(-60, 640), (60, 618), (180, 594), (300, 588), (420, 606), (520, 660), (590, 740), (630, 790)]


def appio_pose(t):
    idea = pulse(t, 10.0, 10.4, 10.9, 11.3)
    hold = pulse(t, 10.9, 11.4, 13.25, 13.45)
    wind = pulse(t, 13.05, 13.35, 13.5, 13.75)
    toss = pulse(t, 13.45, 13.75, 14.5, 15.2)
    show = pulse(t, 17.3, 17.9, 19.6, 20.3)
    point = ramp(t, 25.7, 26.5)
    return blend(ARM_REST, ((-0.4, -0.75), idea), ((-0.15, -0.55), hold), ((-0.75, -1.3), wind),
                 ((0.45, 0.35), toss), ((0.3, 0.02), show), ((-0.1, -0.05), point))


@scena("appio")
def appio(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    road = [(x, GY) for x in range(-60, W + 61, 40)]

    # --- Rome on its hill (draws on with the scene)
    rome = [{"p": ROME, "w": 1.05}] + temple(292, 592, 206, 128, 5) + tholos(488, 640, 82, 62) + [
        cypress(96, 618, 150, 13), cypress(140, 606, 108, 11), cypress(566, 712, 116, 11)]
    pen.lines(rome, ease_io(win(t, 0.2, 3.6)), vanish, 0.92, 1.0, seed=101)
    write(pen, "Roma", 300, 880, 58, t, 3.7, vanish, alpha=0.8)
    write(pen, "312 a.C.", 300, 210, 92, t, 1.6, vanish)

    # --- the Samnite mountains, with helmets and spears peeking
    km = ease_io(win(t, 3.9, 6.2))
    pen.lines([RIDGE_FAR], km, vanish, 0.3, 0.8, seed=111, smooth_=False)
    pen.lines([RIDGE], km, vanish, 0.7, 1.05, seed=112, smooth_=False)
    duck = ramp(t, 26.7, 27.1) * (1.0 - 0.45 * ramp(t, 28.5, 29.4))
    for i, (px, py) in enumerate(PEAKS):
        up = ramp(t, 5.4 + i * 0.4, 6.3 + i * 0.4) * (1 - duck) * a
        if up > 0.01:
            bob = 2.5 * wave(t, 0.6, i * 2.1)
            helmet(pen, px, py + 34 - 40 * up + bob, 0.8, 120 + i * 5, py - 1, 1.45)
            if i != 1:
                sx = px + 34
                sy = y_on(RIDGE, sx)
                spear(pen, sx, sy + 70 - 80 * up, 0.08 * wave(t, 0.4, i), 0.6, 140 + i * 3, sy - 1)

    # --- Appio Claudio walks out of Rome
    al = ramp(t, 7.3, 8.4) * a
    walk = 1.0 - ramp(t, 8.6, 9.4)
    x = lerp(AX - 120, AX, ease_out(win(t, 7.3, 9.3), 2))
    arm = appio_pose(t)
    if al > 0.01:
        expr, talk = "calm", False
        if 7.3 <= t < 10.0:
            expr = "proud"
        elif 10.0 <= t < 10.9:
            expr = "surprise"
        elif 10.9 <= t < 13.1:
            talk = True
        elif 13.1 <= t < 14.3:
            expr = "grin"
        elif 14.3 <= t < 21.3:
            expr = "smile"
        elif 21.3 <= t < 23.2:
            expr = "proud"
        elif 23.2 <= t < 25.7:
            expr = "smile"
        elif 25.7 <= t < 27.8:
            expr = "squint"
        elif t >= 27.8:
            expr = "proud"
        tilt = -0.12 * ramp(t, 25.7, 26.5) + 0.06 * pulse(t, 10.9, 11.3, 13.0, 13.3)
        hop = 24 * math.sin(math.pi * win(t, 10.02, 10.42))
        omino(pen, x, GY - hop, AS, t, "toga", walk=walk, expr=expr, talk=talk, arm_f=arm, alpha=al, head_tilt=tilt,
              seed=3)
        hx, hy = hand_of(x, GY - hop, AS, t, arm, seed=3)
        # the idea: a few little rays around the head
        if 10.0 < t < 11.4:
            hc = (x + 14 * AS, GY - 252 * AS)
            k = ramp(t, 10.05, 10.4)
            rays = [[(hc[0] + math.cos(g) * (82 + 8 * k), hc[1] + math.sin(g) * (82 + 8 * k)),
                     (hc[0] + math.cos(g) * (104 + 16 * k), hc[1] + math.sin(g) * (104 + 16 * k))]
                    for g in (-2.55, -2.1, -1.65, -1.2, -0.75)]
            pen.lines(rays, k, ramp(t, 10.9, 11.3), al * 0.9, 0.9, seed=150)
        # the scroll in his hand
        if t < 13.6:
            g = ramp(t, 10.95, 11.4)
            roll(pen, hx + 8, hy + 18, 16 * (0.4 + 0.6 * g), 0.3 * wave(t, 0.5), al * g, depth=30, seed=160)

    # --- the scroll is tossed and unrolls into the road, all the way to Capua
    R0, R1 = 30.0, 17.0
    if t >= 13.6:
        fly = win(t, 13.6, 14.2)
        rr = lerp(R0, R1, ease_io(win(t, 14.2, 18.4)))
        gone = ramp(t, 21.2, 22.0)
        if fly < 1:
            hx0, hy0 = hand_of(x, GY, AS, 13.6, appio_pose(13.6), seed=3)
            f = ease_io(fly)
            px = lerp(hx0 + 8, X0 + R0, f)
            pyb = lerp(hy0 + 18, BAND, f) - 140 * math.sin(math.pi * fly)
            roll(pen, px, pyb, lerp(16, R0, f), fly * 6, a, depth=lerp(30, BAND - GY, f), seed=160)
            xr = X0 + R0
        else:
            u = ease_io(win(t, 14.2, 18.4))
            xr = lerp(X0 + R0, XC, u)
            ang = (xr - X0 - R0) / 24.0
            dt = t - 14.2
            squash = 1.0 - 0.1 * math.exp(-dt * 8) * math.sin(dt * 30)
            roll(pen, xr, BAND, rr * squash, ang, a * (1 - gone), depth=BAND - GY, seed=160, w=1.1)
        xe = max(X0, xr - rr * 0.6)
        if xe > X0 + 2 and fly >= 1:
            pen.line([(X0, BAND), (xe, BAND)], 1.1, a, seed=170, start=vanish)
            pen.line([(X0 + 6, GY), (X0, BAND)], 0.9, a, seed=171, start=vanish)
            mid = (GY + BAND) / 2 + 2
            dl = dashes([(X0 + 14, mid), (xe - 4, mid)], 22, 14, 0.0, 1.0 - vanish)
            pen.lines(dl, 1.0, 0.0, a * (1 - 0.9 * ramp(t, 21.4, 22.4)), 0.85, seed=172)
        if t > 18.2:
            pen.line([(XC + R1 - 6, GY), (XC + R1, BAND)], 0.9, a * ramp(t, 18.2, 18.8), seed=173)
        # Via Appia is born: two courses of paving stones run along the sheet
        kp = ease_io(win(t, 21.3, 22.7))
        if kp > 0:
            rng = random.Random(7)
            midy = (GY + BAND) / 2
            mid = [(xx, midy + rng.uniform(-3, 3)) for xx in range(X0 + 4, XC + 12, 26)]
            stones = [{"p": mid, "w": 0.6}]
            for row, (ya, yb) in enumerate(((GY + 3, midy - 2), (midy + 2, BAND - 3))):
                xj = X0 + 18 + row * 22
                while xj < XC + 4:
                    j1 = rng.uniform(-7, 7)
                    stones.append({"p": [(xj + j1, ya), (xj + j1 * 0.2 + rng.uniform(-4, 4), (ya + yb) / 2),
                                         (xj - j1 * 0.6, yb)], "w": 0.6})
                    xj += rng.uniform(34, 50)
            pen.lines(stones, kp, vanish, 0.8 * a, 1.0, seed=180)

    # --- Capua at the end of the line
    pen.lines(town(1408, GY, 1.35), ease_io(win(t, 17.0, 18.7)), vanish, 0.9, 1.0, seed=190)
    write(pen, "Capua", 1408, 916, 58, t, 18.5, vanish, alpha=0.8)

    # --- weather: a little rain cloud that the road does not care about
    kc = pulse(t, 15.8, 16.5, 18.2, 18.9)
    if kc > 0:
        cl = [(px + 14 * wave(t, 0.15), py) for px, py in cloud(1060, 520, 1.1)]
        pen.lines([{"p": cl, "closed": True}], ramp(t, 15.8, 16.6), ramp(t, 18.2, 18.9), 0.75 * a, 1.0, seed=200)
        rain = ramp(t, 16.3, 16.7) * (1 - ramp(t, 17.8, 18.3))
        if rain > 0:
            rng = random.Random(5)
            drops = []
            for i in range(18):
                x0 = rng.uniform(970, 1150)
                y0 = 562 + ((rng.uniform(0, 220) + t * 460) % 220)
                drops.append([(x0, y0), (x0 - 4, y0 + 20)])
            pen.lines(drops, 1.0, 0.0, 0.5 * rain * a, 0.65, seed=210)

    # --- "più di 200 km" dimension line under the road
    kd = ease_io(win(t, 19.1, 20.1))
    if kd > 0:
        st = ramp(t, 23.6, 24.4)
        dim = [{"p": [(X0, 892), (X0, 920)], "w": 0.7}, [(X0, 906), (XC + R1, 906)],
               {"p": [(XC + R1, 892), (XC + R1, 920)], "w": 0.7}]
        pen.lines(dim, kd, max(vanish, st), 0.6 * a, 0.85, seed=220)
        write(pen, "più di 200 km", (X0 + XC) / 2, 966, 56, t, 19.4, vanish, out=23.6, alpha=0.88)

    write(pen, "Via Appia", 1180, 240, 124, t, 21.9, vanish)

    # --- il Cieco: eyes shut, he points, and the line goes perfectly straight
    if t > 25.6 and al > 0.01:
        write(pen, "«il Cieco»", x - 150, 300, 58, t, 25.9, vanish, alpha=0.8)
        tip = hand_of(x, GY, AS, t, arm, seed=3)
        k = ease_io(win(t, 26.4, 28.3))
        sight = [(tip[0] + 18, tip[1] + 2), (W + 80, tip[1] + 2)]
        pen.lines(dashes(sight, 16, 12, 0.0, k), 1.0, 0.0, 0.95 * a, 0.95, seed=230)
    return road


# ================================================================== b04 regina
CAM_END = 2000.0
# end-state screen coordinates (u); during the pan everything is drawn at x = u + (CAM_END - cam)
ROAD_U = [(-2140, 790), (-1500, 790), (-800, 790), (-260, 790), (40, 786), (220, 758), (400, 702), (560, 664),
          (690, 656), (830, 676), (990, 730), (1130, 776), (1260, 796), (1380, 804), (1470, 810)]
ROAD_UP = catmull(ROAD_U, n=10)
PINES = [(-1900, 1.0), (-1700, 0.85), (-1180, 1.05), (-420, 0.95), (90, 1.0), (430, 1.1), (800, 0.88)]
STONES = list(range(-2000, 1300, 230))


def pine_crown(x, y, s=1.0, seed=0):
    """Screen ellipse (cx, cy, rx, ry) covering a stone pine's crown (for fake occlusion)."""
    lean = random.Random(seed).uniform(-0.12, 0.12)
    H = 175 * s
    return (x + lean * H + 4 * s, y - H - 40 * s, 132 * s, 40 * s)


def umbrella_pine(x, y, s=1.0, seed=0):
    """Stone pine of the Appia Antica: tall leaning trunk, forked branches, a flat clumpy crown."""
    rng = random.Random(seed)
    lean = rng.uniform(-0.12, 0.12)
    H = 175 * s
    top = (x + lean * H, y - H)
    tr = [(x, y), (x + lean * H * 0.4 + 3 * s, y - H * 0.5), top]
    br = [{"p": [top, (top[0] - 30 * s, top[1] - 16 * s), (top[0] - 52 * s, top[1] - 22 * s)], "w": 0.75},
          {"p": [top, (top[0] + 26 * s, top[1] - 14 * s), (top[0] + 50 * s, top[1] - 24 * s)], "w": 0.75},
          {"p": [(x + lean * H * 0.75, y - H * 0.78), (x + lean * H * 0.75 - 30 * s, y - H * 0.9)], "w": 0.6}]
    cx, cy = top[0] + 4 * s, top[1] - 22 * s          # underside of the crown
    w = 118 * s
    under = [(cx - w, cy + 2 * s), (cx - w * 0.5, cy + 6 * s), (cx, cy + 3 * s), (cx + w * 0.5, cy + 7 * s),
             (cx + w, cy + 1 * s)]
    lobes = [(cx - w, cy + 2 * s), (cx - w * 0.92, cy - 22 * s), (cx - w * 0.62, cy - 38 * s),
             (cx - w * 0.3, cy - 36 * s), (cx - w * 0.08, cy - 50 * s), (cx + w * 0.3, cy - 46 * s),
             (cx + w * 0.55, cy - 34 * s), (cx + w * 0.82, cy - 30 * s), (cx + w * 1.02, cy - 12 * s), (cx + w, cy + 1 * s)]
    tex = [{"p": [(cx - w * 0.55, cy - 14 * s), (cx - w * 0.3, cy - 18 * s), (cx - w * 0.1, cy - 12 * s)], "w": 0.5,
            "a": 0.6},
           {"p": [(cx + w * 0.2, cy - 22 * s), (cx + w * 0.45, cy - 18 * s)], "w": 0.5, "a": 0.6}]
    return [tr] + br + [{"p": lobes, "w": 0.95}, {"p": under, "w": 0.75}] + tex


def milestone(x, y):
    return [{"p": [(x - 7, y), (x - 7, y - 30)] + arc(x, y - 30, 7, math.pi, 2 * math.pi, 8)[1:] + [(x + 7, y)],
             "w": 0.8}]


def tomb(x, y):
    return [[(x - 78, y), (x - 78, y - 34), (x + 78, y - 34), (x + 78, y)],
            [(x - 62, y - 34), (x - 62, y - 100), (x + 62, y - 100), (x + 62, y - 34)],
            {"p": [(x - 62, y - 88), (x + 62, y - 88)], "w": 0.6},
            {"p": arc(x, y - 100, 62, math.pi, 2 * math.pi, 14, 16), "w": 0.8}]


def ship(pen, x, y, s, t, ph, reveal, start, alpha, seed):
    bob = 4 * math.sin(t * 1.3 + ph)
    with at(pen, x, y + bob, s, 0.035 * math.sin(t * 1.0 + ph + 1)):
        st = [[(-74, -14), (-54, 12), (44, 12), (72, -18)],
              {"p": [(-74, -14), (-88, -34), (-78, -46), (-66, -36)], "w": 0.8},
              {"p": [(-64, -9), (62, -12)], "w": 0.6},
              {"p": [(0, -11), (0, -132)], "smooth": False},
              {"p": [(-46, -118), (46, -118)], "w": 0.9},
              [(-44, -116), (-54, -74), (-42, -38)], [(44, -116), (56, -74), (42, -38)],
              {"p": [(-42, -38), (0, -31), (42, -38)], "w": 0.8},
              {"p": [(0, -132), (16, -138), (0, -144)], "w": 0.6}]
        for k in range(4):
            st.append({"p": [(-36 + k * 22, 10), (-46 + k * 22, 32)], "w": 0.55})
        pen.lines(st, reveal, start, alpha, 1.0, seed=seed)


def laurel(cx, cy, r):
    st = []
    for side in (-1, 1):
        a0, a1 = math.pi / 2 + side * 0.25, math.pi / 2 + side * 2.55
        br = [(cx + math.cos(lerp(a0, a1, i / 20)) * r, cy + math.sin(lerp(a0, a1, i / 20)) * r) for i in range(21)]
        st.append(br)
        for i in range(1, 10):
            f = i / 9.6
            ang = lerp(a0, a1, f)
            px, py = cx + math.cos(ang) * r, cy + math.sin(ang) * r
            tang = ang + side * math.pi / 2
            for o in (-1, 1):
                d = tang + o * 0.55 * side
                ln = 26 - 9 * f
                tip = (px + math.cos(d) * ln, py + math.sin(d) * ln)
                nx, ny = -math.sin(d) * 6.5, math.cos(d) * 6.5
                mid = ((px + tip[0]) / 2, (py + tip[1]) / 2)
                st.append({"p": [(px, py), (mid[0] + nx, mid[1] + ny), tip, (mid[0] - nx, mid[1] - ny), (px, py)],
                           "w": 0.7})
    st.append({"p": [(cx - 8, cy + r + 2), (cx - 22, cy + r + 22), (cx - 12, cy + r + 26)], "w": 0.7})
    st.append({"p": [(cx + 8, cy + r + 2), (cx + 22, cy + r + 22), (cx + 12, cy + r + 26)], "w": 0.7})
    return st


def crown(cx, by, s=1.0):
    pts = [(-56, 0), (-64, -50), (-30, -20), (0, -62), (30, -20), (64, -50), (56, 0)]
    P = [(cx + x * s, by + y * s) for x, y in pts]
    return [{"p": P, "smooth": False}, [(cx - 58 * s, by), (cx + 58 * s, by)],
            {"p": [(cx - 57 * s, by - 11 * s), (cx + 57 * s, by - 11 * s)], "w": 0.6}]


def arrow(x0, y0, x1, y1, head=16):
    d = math.atan2(y1 - y0, x1 - x0)
    return [[(x0, y0), (x1, y1)],
            {"p": [(x1 - math.cos(d - 0.45) * head, y1 - math.sin(d - 0.45) * head), (x1, y1),
                   (x1 - math.cos(d + 0.45) * head, y1 - math.sin(d + 0.45) * head)], "smooth": False}]


def ridge_pts(u0, u1, base, amp, sd):
    pts = []
    n = 60
    for i in range(n + 1):
        u = lerp(u0, u1, i / n)
        env = clamp((1360 - u) / 520.0)
        h = amp * (0.62 + 0.25 * math.sin(u / 210.0 + sd) + 0.13 * math.sin(u / 77.0 + sd * 3))
        pts.append((u, base - env * h + (1 - env) * 10))
    return pts


@scena("regina")
def regina(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    pan = 0.5 - 0.5 * math.cos(math.pi * win(t, 0.4, 6.9))
    cam = (CAM_END - 60) * pan + 60 * smooth(win(t, 4.0, T))
    off = CAM_END - cam

    def rv(u):                     # elements draw on as they enter from the right
        return min(appear, clamp((W + 40 - (u + off)) / 300.0))

    # --- where the traveller and the mule are (needed early: the far ridges pass behind them)
    al = ramp(t, 6.9, 8.0) * a
    go = ease_out(win(t, 6.9, 12.8), 1.6)
    xt = lerp(960, 1220, go) + off
    xm = xt - 205
    yt, ym = y_on(ROAD_UP, xt - off) + 3, y_on(ROAD_UP, xm - off) + 4

    # --- far ridges (parallax), floating high above the road; hidden behind crowns, column and people
    ctx = pen.ctx
    ctx.save()
    ctx.rectangle(-300, -300, W + 600, 1700)
    holes = []
    for i, (u, sc) in enumerate(PINES):
        if -260 < u + off < W + 160:
            cx, cy, rx, ry = pine_crown(u + off, y_on(ROAD_UP, u) - 1, sc, i)
            holes.append((cx, cy, rx, ry))
    if al > 0.01:
        holes += [(xt + 6, yt - 150, 62, 150), (xm + 10, ym - 110, 140, 90)]
    for cx, cy, rx, ry in holes:
        ctx.new_sub_path()
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(rx, ry)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
    ctx.rectangle(1372 + off, 486, 76, 330)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.clip()
    for f, al_, base, amp, sd in ((0.15, 0.2, 540, 120, 4), (0.32, 0.36, 612, 190, 1)):
        o = off * f
        pts = ridge_pts(max(-60 - o, -2400), min(1380, W + 60 - o), base, amp, sd)
        pen.lines([[(u + o, y) for u, y in pts]], appear, vanish, al_, 0.85, seed=300 + sd)
    ctx.restore()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)

    # --- the world that travels by
    with at(pen, off, 0):
        for i, u in enumerate(STONES):
            if -120 < u + off < W + 60:
                pen.lines(milestone(u, y_on(ROAD_UP, u) + 2), rv(u), vanish, 0.6, 1.0, seed=310 + i)
        for i, (u, s) in enumerate(PINES):
            if -260 < u + off < W + 160:
                pen.lines(umbrella_pine(u, y_on(ROAD_UP, u) - 1, s, i), rv(u - 80), vanish, 0.85, 1.0, seed=330 + i)
        if -1350 + off > -200:
            pen.lines(tomb(-1420, GY), rv(-1500), vanish, 0.8, 1.0, seed=350)
        if -700 + off > -160:
            pen.lines(town(-760, GY, 1.2), rv(-840), vanish, 0.85, 1.0, seed=355)
            write(pen, "Capua", -760, 870, 52, t, 0.0, vanish, alpha=0.65 * min(1.0, rv(-840) * 1.5))
        if -60 + off > -200:
            pen.lines(town(-150, GY, 1.0), rv(-220), vanish, 0.8, 1.0, seed=360)
            write(pen, "Benevento", -150, 870, 52, t, 0.0, vanish, alpha=0.65 * min(1.0, rv(-220) * 1.5))

        # --- Brindisi: the terminal column, the quay, the sea and two ships
        if 1300 + off < W + 60:
            k = rv(1380)
            cb = 806
            colm = [[(1386, cb), (1434, cb)], {"p": [(1390, cb - 10), (1430, cb - 10)], "w": 0.8},
                    {"p": [(1397, cb - 10), (1399, cb - 296)], "smooth": False},
                    {"p": [(1423, cb - 10), (1421, cb - 296)], "smooth": False},
                    {"p": [(1388, cb - 296), (1392, cb - 310), (1428, cb - 310), (1432, cb - 296), (1388, cb - 296)],
                     "w": 0.9},
                    {"p": [(1380, cb - 312), (1440, cb - 312)], "w": 0.9},
                    {"p": [(1404, cb - 120), (1406, cb - 240)], "w": 0.45, "a": 0.6},
                    {"p": [(1414, cb - 60), (1415, cb - 200)], "w": 0.45, "a": 0.6}]
            pen.lines(colm, k, vanish, 0.92, 1.0, seed=370)
            pen.lines([[(1470, 810), (1506, 810), (1506, 838)]], rv(1480), vanish, 0.8, 1.0, seed=371)
            waves = []
            for row in range(5):
                yy = 846 + row * 34
                for j in range(5):
                    x0 = 1536 + j * 108 + (row % 2) * 54 + 10 * math.sin(t * 0.7 + row + j)
                    wv = [(x0 + i * 6, yy + 3.5 * math.sin(i * 0.7 + t * 2.0 + j)) for i in range(9)]
                    waves.append({"p": wv, "a": 0.9 - row * 0.13, "w": 0.75})
            pen.lines(waves, rv(1530), vanish, 0.75, 1.0, seed=372)
            ship(pen, 1690, 840, 1.25, t, 0.0, rv(1600), vanish, 0.92, 380)
            ship(pen, 1900, 814, 0.7, t, 2.0, rv(1840), vanish, 0.5, 390)
            write(pen, "Brindisi", 1410, 452, 60, t, 5.3, vanish)
            write(pen, "mare Adriatico", 1760, 1030, 40, t, 6.6, vanish, alpha=0.55)

    # --- Roma -> Brindisi, over 500 km (in the sky, then it makes room for the queen)
    kd = ease_io(win(t, 7.0, 8.3))
    if kd > 0:
        out = ramp(t, 10.3, 11.0)
        pen.lines(arrow(290, 300, 1300, 300, 20), kd, max(vanish, out), 0.7 * a, 0.9, seed=400)
        write(pen, "Roma", 200, 314, 54, t, 6.9, vanish, out=10.3, alpha=0.85)
        write(pen, "oltre 500 km", 795, 268, 66, t, 7.4, vanish, out=10.3)

    # --- regina viarum, with a crown landing on it
    kc = ease_io(win(t, 11.0, 11.9))
    CX = 780
    if kc > 0:
        drop = 1.0 - ease_out(win(t, 11.0, 11.9), 3) - 0.08 * math.sin(win(t, 11.75, 12.3) * math.pi)
        pen.lines(crown(CX, 182 - 60 * drop, 1.25), kc, vanish, 0.95 * a, 1.05, seed=410)
        sp = pulse(t, 11.8, 12.1, 12.4, 12.9)
        if sp > 0:
            rays = [[(CX + math.cos(g) * 96, 150 + math.sin(g) * 70), (CX + math.cos(g) * 122, 150 + math.sin(g) * 90)]
                    for g in (-2.65, -2.2, -0.95, -0.5)]
            pen.lines(rays, ramp(t, 11.8, 12.1), ramp(t, 12.4, 12.9), 0.7 * a, 0.75, seed=415)
    write(pen, "regina viarum", CX, 312, 118, t, 11.2, vanish)
    write(pen, "la regina delle strade", CX, 380, 46, t, 12.5, vanish, alpha=0.6)

    # --- 2024: a laurel wreath
    kl = ease_io(win(t, 14.2, 15.8))
    if kl > 0:
        pen.lines(laurel(1690, 250, 88), kl, vanish, 0.85 * a, 0.9, seed=420)
        write(pen, "2024", 1690, 272, 66, t, 14.9, vanish)
        write(pen, "patrimonio dell'umanità", 1690, 400, 40, t, 16.3, vanish, alpha=0.7)

    # --- the traveller and his mule come down to the sea
    if al > 0.01:
        w = 1.0 - ramp(t, 12.1, 12.8)
        perk = pulse(t, 11.2, 11.7, 13.4, 14.2) + pulse(t, 16.3, 16.8, 18.0, 18.6)
        mulo(pen, xm, ym, 0.8, t, walk=w, ear=-0.2 + 1.1 * perk, alpha=al, expr="smile" if perk > 0.3 else "calm")
        wavek = pulse(t, 16.4, 16.9, 18.2, 18.8)
        omino(pen, xt, yt, 0.85, t, "viandante", walk=w, alpha=al, expr="smile" if t > 12.4 else "calm", look=0.6,
              arm_f=(lerp(DOWN - 0.35, -1.2, wavek), lerp(0.4, -1.6 + 0.35 * math.sin(t * 8), wavek))
              if wavek > 0.01 else None, hold=None if wavek > 0.01 else "staff", seed=5)

    road = [(x + off, y) for x, y in ROAD_UP]
    return clipx(road)


# ================================================================== b05 groma
SX = 600                                   # groma staff x
GTOP = 330                                 # top of the staff
GR = 128                                   # half-length of the cross arms
PL = 150                                   # plumb line length
MX, MS = 330, 1.75                         # surveyor feet x, scale
BUMP_X, BUMP_W, BUMP_H = 1520.0, 430.0, 104.0
EYE_ARM = (DOWN - 0.12, 0.9)               # arm relaxed while sighting


def bump(x):
    d = (x - BUMP_X) / BUMP_W
    if abs(d) >= 1:
        return 0.0
    return (0.5 + 0.5 * math.cos(math.pi * d)) ** 1.1


def groma_draw(pen, t, k_staff, k_cross, k_plumb, start, alpha, t_drop):
    """The surveyor's groma: staff, bracket, rotating cross and four swinging plumb lines."""
    st = [{"p": [(SX - 3, GY + 4), (SX - 3, GTOP)], "smooth": False, "w": 1.15},
          {"p": [(SX + 3, GY - 30), (SX + 3, GTOP + 6)], "smooth": False, "w": 0.6, "a": 0.7},
          {"p": [(SX - 9, GY - 30), (SX, GY + 8), (SX + 9, GY - 30)], "smooth": False, "w": 0.85}]
    pen.lines(st, k_staff, start, alpha, 1.0, seed=500)
    cx, cy = SX + 46, GTOP - 10
    th = 0.2 + 0.05 * wave(t, 0.07)
    ends = [(cx + math.cos(th + k * math.pi / 2) * GR, cy + math.sin(th + k * math.pi / 2) * GR * 0.3)
            for k in range(4)]
    cr = [{"p": [(SX - 3, GTOP), (SX + 10, GTOP - 12), (cx, cy)], "w": 1.0},
          {"p": [ends[2], ends[0]], "smooth": False, "w": 1.1}, {"p": [ends[3], ends[1]], "smooth": False}]
    pen.lines(cr, k_cross, start, alpha, 1.0, seed=505)
    if k_cross > 0.95:
        pen.dot(cx, cy, 5.0, alpha * min(1.0, (k_cross - 0.95) * 20) * (1 - start))
    bobs = []
    if k_plumb > 0:
        L = PL * ease_out(k_plumb, 2)
        dt = max(0.0, t - t_drop)
        amp = 0.035 + 0.2 * math.exp(-dt * 1.0)
        for k, e in enumerate(ends):
            sw = amp * math.sin(dt * 2.6 + k * 1.3) + 0.04 * wave(t, 0.31, k)
            b = (e[0] + math.sin(sw) * L, e[1] + math.cos(sw) * L)
            pen.line([e, b], 0.6, alpha * 0.9 * (1 - start), smooth_=False, seed=510 + k)
            bobs.append(b)
            q = min(1.0, k_plumb * 3) * (1 - start)
            pen.line([(b[0] - 7, b[1]), (b[0], b[1] + 16), (b[0] + 7, b[1]), (b[0] - 7, b[1])], 0.8, alpha * q,
                     smooth_=False, seed=515 + k)
    return ends, bobs


def reeds(x, y, s=1.0):
    st = []
    for i, (dx, h, lean) in enumerate([(-14, 70, -0.15), (0, 92, 0.03), (12, 64, 0.2), (22, 48, 0.32)]):
        tip = (x + dx * s + math.sin(lean) * h * s, y - math.cos(lean) * h * s)
        st.append({"p": [(x + dx * s, y), ((x + dx * s + tip[0]) / 2 + lean * 6, (y + tip[1]) / 2), tip], "w": 0.7})
        if i in (0, 1):
            st.append({"p": ellipse(tip[0] - math.sin(lean) * 14 * s, tip[1] + 14 * s, 4 * s, 11 * s, 10),
                       "w": 0.7})
    return st


def write_route(pen, a_txt, b_txt, cx, y, size, t, t0, vanish, out=None):
    """'A -> B' with a drawn arrow (the handwriting font has no arrow glyph)."""
    write(pen, a_txt, cx - 46, y, size, t, t0, vanish, out=out, align="right")
    k = ease_io(win(t, t0 + 0.6, t0 + 1.0))
    if k > 0:
        o = ramp(t, out, out + 0.6) if out is not None else 0.0
        pen.lines(arrow(cx - 28, y - size * 0.28, cx + 28, y - size * 0.28, 13), k, max(vanish, o), 0.85, 0.85,
                  seed=599)
    write(pen, b_txt, cx + 46, y, size, t, t0 + 0.9, vanish, out=out, align="left")


@scena("groma")
def groma(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    kcurve = ease_io(win(t, 24.4, 26.6))
    road = [(x, GY + kcurve * BUMP_H * bump(x)) for x in range(-60, W + 61, 24)]

    # --- the groma draws itself on
    t_drop = 6.6
    ends, bobs = groma_draw(pen, t, ease_io(win(t, 4.3, 5.4)), ease_io(win(t, 5.3, 6.5)), win(t, 6.5, 7.0),
                            vanish, a, t_drop)

    # --- the surveyor
    al = ramp(t, 0.2, 1.6) * a
    think = pulse(t, 0.0, 0.1, 3.9, 4.6)
    p_asta = pulse(t, 7.9, 8.4, 8.9, 9.3)
    p_croce = pulse(t, 8.9, 9.3, 9.6, 10.0)
    p_fili = pulse(t, 9.6, 10.0, 11.0, 11.5)
    sight = pulse(t, 11.2, 11.9, 20.2, 20.9)
    trace = pulse(t, 24.2, 24.7, 26.6, 27.2)
    tr = ease_io(win(t, 24.6, 26.4))
    lean = 0.28 * sight
    arm = blend(ARM_REST, ((0.6, -1.75), think), ((0.35, 0.0), p_asta), ((-0.85, -0.75), p_croce),
                ((-0.1, 0.15), p_fili), (EYE_ARM, sight),
                ((lerp(-0.75, -0.2, tr), lerp(-0.95, 0.05, tr)), trace))
    expr = "calm"
    if 4.0 <= t < 11.4:
        expr = "smile"
    elif 11.4 <= t < 20.4:
        expr = "squint"
    elif 20.4 <= t < 21.9:
        expr = "smile"
    elif 21.9 <= t < 24.3:
        expr = "surprise"
    elif 24.3 <= t < 26.6:
        expr = "grin"
    elif t >= 26.6:
        expr = "proud"
    back = ramp(t, 21.9, 22.6) * (1 - ramp(t, 24.0, 25.0))
    mx = MX - 16 * back
    omino(pen, mx, GY, MS, t, "agrimensore", expr=expr, arm_f=arm, alpha=al, lean=lean - 0.12 * back,
          head_tilt=0.08 * think - 0.06 * back, seed=7, look=0.5)

    # --- "Ma come si costruisce una strada così?" - a question mark over his head
    kq = ramp(t, 1.6, 2.3)
    if kq > 0 and t < 5.0:
        qx, qy = mx + 40 * MS, GY - 330 * MS + 6 * wave(t, 0.7)
        out = ramp(t, 4.0, 4.6)
        q = [[(qx - 16, qy - 30), (qx - 10, qy - 46), (qx + 6, qy - 50), (qx + 18, qy - 38), (qx + 14, qy - 22),
              (qx + 2, qy - 12), (qx, qy + 4)]]
        pen.lines(q, kq, max(vanish, out), 0.9 * a, 1.1, seed=528)
        if kq > 0.95 and out < 0.9:
            pen.dot(qx + 1, qy + 20, 4.0, 0.9 * a * (1 - out))

    # --- labels: asta, croce, fili a piombo
    labs = [("asta", (SX + 6, 600), (676, 616), (690, 630), 8.0),
            ("croce", (ends[3][0] + 6, ends[3][1] - 6), (750, 214), (764, 218), 9.0),
            ("fili a piombo", (bobs[0][0] + 10, bobs[0][1] + 6) if bobs else (SX + 180, 480), (842, 520),
             (856, 534), 9.6)]
    for i, (s, p0, p1, tp, t0) in enumerate(labs):
        k = ease_io(win(t, t0, t0 + 0.5))
        if k > 0:
            pen.lines([[p0, p1]], k, max(vanish, ramp(t, 11.0, 11.6)), 0.55 * a, 0.7, seed=530 + i)
            write(pen, s, tp[0], tp[1], 56, t, t0 + 0.2, vanish, out=11.0, alpha=0.88, align="left")

    # --- the helper far away with his pole
    hs = 0.74
    ah = ramp(t, 10.2, 11.2) * (1 - ramp(t, 20.0, 21.4)) * a
    if ah > 0.01:
        hx = lerp(1840, 1690, ease_out(win(t, 10.2, 11.8), 2)) + 60 * ease_io(win(t, 20.0, 21.6))
        hx += -40 * pulse(t, 11.9, 12.3, 12.4, 12.9) - 14 * ramp(t, 12.4, 12.9)
        hw = clamp(1.0 - ramp(t, 11.3, 11.9) + 0.6 * pulse(t, 11.9, 12.1, 12.7, 12.9) + ramp(t, 20.0, 20.3))
        okw = pulse(t, 13.0, 13.4, 14.0, 14.5)
        harm = (DOWN - 0.75, -0.35)
        omino(pen, hx, GY, hs, t, "operaio", fx=-1, walk=hw, alpha=ah, arm_f=harm,
              arm_b=(lerp(DOWN + 0.2, -1.3, okw), lerp(DOWN + 0.05, -1.9 + 0.3 * math.sin(t * 9), okw)) if okw > 0.01
              else None, expr="smile" if okw > 0.2 else "calm", seed=11)
        ph = hand_of(hx, GY, hs, t, harm, fx=-1, seed=11)
        pole_top = (ph[0], 448)
        fl = 5 * wave(t, 1.3)
        pen.line([(ph[0], GY), pole_top], 1.0, ah, smooth_=False, seed=540)
        pen.line([pole_top, (ph[0] + 40, 460 + fl), (ph[0], 476)], 0.85, ah, seed=541)
        for k in range(4):
            pen.line([(ph[0] - 4, 520 + k * 60), (ph[0] + 4, 520 + k * 60)], 0.7, ah * 0.7, seed=542 + k)
        # sight line: eye -> plumbs -> pole
        ks = ease_io(win(t, 11.8, 12.9))
        if ks > 0 and sight > 0.5:
            e = eye_of(mx, GY, MS, t, lean=lean, seed=7)
            sl = [(e[0] + 30, e[1] + 2), pole_top]
            pen.lines(dashes(sl, 18, 12, 0.0, ks), 1.0, 0.0, 0.85 * ah * (1 - ramp(t, 19.8, 20.6)), 0.8, seed=545)
            fk = win(t, 12.85, 13.5)
            if 0 < fk < 1:
                pen.line(ellipse(pole_top[0], pole_top[1], 12 + 34 * fk, 12 + 34 * fk, 24), 0.7,
                         0.7 * (1 - fk) * ah, closed=True, seed=546)
    # stakes along the line
    for i, sx in enumerate((900, 1150, 1400)):
        k = ease_io(win(t, 13.2 + i * 0.35, 13.7 + i * 0.35))
        if k > 0:
            pen.lines([{"p": [(sx, GY - 70), (sx, GY - 4), (sx + 3, GY + 6)], "smooth": False},
                       {"p": [(sx - 8, GY - 70), (sx + 8, GY - 70)], "w": 0.8},
                       {"p": [(sx, GY - 66), (sx + 22, GY - 60), (sx, GY - 52)], "w": 0.6}], k,
                      max(vanish, ramp(t, 20.2, 21.0)), 0.85, 0.95, seed=550 + i)

    # --- the marsh and the straight road growing along the line
    for i, rx in enumerate((800, 1030, 1270, 1530, 1790)):
        pen.lines(reeds(rx, GY - 1, 1.0 + 0.15 * (i % 2)), ease_io(win(t, 14.4 + i * 0.25, 15.4 + i * 0.25)),
                  max(vanish, ramp(t, 21.0, 21.8)), 0.5, 0.8, seed=560 + i)
    g = ease_io(win(t, 14.6, 18.6))
    if g > 0:
        # near edge widens where the road swings toward us (perspective)
        low = [(x, y + 26 + 34 * kcurve * bump(x)) for x, y in road]
        pen.line(low, 1.0, a, reveal=g, start=vanish, seed=570)
        rng = random.Random(9)
        joints = []
        xj = -40.0
        while xj < W + 40:
            j1 = rng.uniform(-6, 6)
            b = kcurve * bump(xj)
            y0 = GY + BUMP_H * b
            sp = (xj - BUMP_X) * 0.12 * b
            joints.append({"p": [(xj + j1, y0 + 3), (xj - j1 * 0.5 + sp, y0 + 24 + 34 * b)], "w": 0.6})
            xj += rng.uniform(30, 44) * (1 + 0.3 * b)
        pen.lines(joints, g, vanish, 0.65 * a, 1.0, seed=575)

    write_route(pen, "Paludi Pontine", "Terracina", 1180, 190, 66, t, 14.6, vanish, out=21.0)
    kd = ease_io(win(t, 17.9, 18.9))
    if kd > 0:
        out = ramp(t, 21.0, 21.6)
        dim = [{"p": [(700, 872), (700, 900)], "w": 0.7}, [(700, 886), (1840, 886)],
               {"p": [(1840, 872), (1840, 900)], "w": 0.7}]
        pen.lines(dim, kd, max(vanish, out), 0.6 * a, 0.85, seed=580)
        write(pen, "circa 60 km in rettilineo", 1270, 950, 56, t, 18.1, vanish, out=21.0, alpha=0.88)

    # --- the mountain says no; the road says: fine, I'll curve
    km = ease_io(win(t, 21.6, 23.4))
    if km > 0:
        mt = [(1150, 790), (1230, 712), (1290, 676), (1350, 580), (1410, 516), (1470, 446), (1520, 478),
              (1560, 526), (1610, 496), (1650, 514), (1720, 604), (1800, 700), (1890, 790)]
        # the mountain's foot comes toward us; at first it sits right on the straight road
        foot = [(x, GY - 6 + (BUMP_H * 0.72) * bump(x) * (0.35 + 0.65 * kcurve)) for x in range(1160, 1881, 40)]
        hatch = [{"p": [(1450, 520), (1404, 600), (1414, 690)], "w": 0.6, "a": 0.7},
                 {"p": [(1600, 556), (1578, 640)], "w": 0.6, "a": 0.6},
                 {"p": [(1330, 720), (1306, 776)], "w": 0.6, "a": 0.6},
                 {"p": [(1700, 650), (1690, 740)], "w": 0.6, "a": 0.6}]
        hatch += [{"p": [(x, GY + 10 + 50 * bump(x) * kcurve), (x + 18, GY - 4 + 50 * bump(x) * kcurve)],
                   "w": 0.5, "a": 0.55 * kcurve} for x in range(1300, 1760, 46)]
        pen.lines([mt, {"p": foot, "w": 0.75, "a": 0.7}] + hatch, km, vanish, 0.85, 1.05, seed=590)
        # the straight line the road would have taken, now only a ghost
        gh = ramp(t, 24.4, 25.2)
        if gh > 0:
            pen.lines(dashes([(1110, GY), (1930, GY)], 10, 14), 1.0, 0.0, 0.4 * gh * a, 0.6, seed=595)
    return road
