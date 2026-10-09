"""White line-art on black: the drawing core.

Every visible thing is a *stroke*: a smooth polyline drawn as a thin, slightly tapered,
hand-wobbled ribbon of warm white. Strokes can be revealed progressively (as if drawn by a pen),
erased, morphed into other strokes, and gently "boil" like hand-drawn animation.
"""
import math
import random
from contextlib import contextmanager

import cairo

W, H = 1920, 1080
FPS = 30
BG = (0.043, 0.043, 0.050)
INK = (0.955, 0.935, 0.895)
LINE = 2.7          # base pen width in px at zoom 1
BOIL_FPS = 10       # how often the hand-drawn wobble changes


# ----------------------------------------------------------------- easing & maths
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, k):
    return a + (b - a) * k


def lerp2(p, q, k):
    return (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)


def win(t, a, b):
    return clamp((t - a) / max(1e-6, b - a))


def smooth(x):
    x = clamp(x)
    return x * x * x * (x * (x * 6 - 15) + 10)


def ease_out(x, p=3):
    x = clamp(x)
    return 1 - (1 - x) ** p


def ease_in(x, p=2):
    return clamp(x) ** p


def ease_io(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def back(x, s=1.4):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def wave(t, f=1.0, ph=0.0):
    return math.sin(2 * math.pi * f * t + ph)


def rot(p, a):
    s, c = math.sin(a), math.cos(a)
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def xf(pts, dx=0.0, dy=0.0, s=1.0, a=0.0, sx=None, sy=None):
    """Scale (or sx/sy), rotate, translate a point list."""
    sx = s if sx is None else sx
    sy = s if sy is None else sy
    out = []
    for x, y in pts:
        x, y = x * sx, y * sy
        if a:
            x, y = rot((x, y), a)
        out.append((x + dx, y + dy))
    return out


# 1-D value noise (smooth, deterministic)
_NOISE = [random.Random(99).uniform(-1, 1) for _ in range(4096)]


def noise1(x, seed=0):
    i = int(math.floor(x))
    f = x - i
    a = _NOISE[(i + seed * 131) % 4096]
    b = _NOISE[(i + 1 + seed * 131) % 4096]
    f = f * f * (3 - 2 * f)
    return a + (b - a) * f


# ----------------------------------------------------------------- curves
def catmull(pts, closed=False, n=10):
    if len(pts) < 3:
        return list(pts)
    P = list(pts)
    P = [P[-1]] + P + [P[0], P[1]] if closed else [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(P[-2] if not closed else P[1])
    return out


def arc(cx, cy, r, a0, a1, n=24, ry=None):
    ry = r if ry is None else ry
    return [(cx + math.cos(lerp(a0, a1, i / n)) * r, cy + math.sin(lerp(a0, a1, i / n)) * ry) for i in range(n + 1)]


def ellipse(cx, cy, rx, ry=None, n=36, a0=0.0):
    ry = rx if ry is None else ry
    pts = [(cx + math.cos(a0 + 2 * math.pi * i / n) * rx, cy + math.sin(a0 + 2 * math.pi * i / n) * ry) for i in range(n)]
    return pts + [pts[0]]


def length(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def resample(pts, n):
    """Exactly n points evenly spaced along the polyline."""
    if len(pts) < 2:
        return [pts[0]] * n
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(seg) or 1e-6
    out, i, acc = [], 0, 0.0
    for k in range(n):
        d = total * k / (n - 1)
        while i < len(seg) - 1 and acc + seg[i] < d:
            acc += seg[i]
            i += 1
        f = (d - acc) / (seg[i] or 1e-6)
        out.append(lerp2(pts[i], pts[i + 1], clamp(f)))
    return out


def resample_step(pts, step):
    n = max(2, int(length(pts) / step) + 1)
    return resample(pts, n)


def morph(a, b, k, n=120):
    A, B = resample(a, n), resample(b, n)
    return [lerp2(p, q, k) for p, q in zip(A, B)]


def trim(pts, k0, k1):
    """Sub-polyline between fractions k0..k1 of its length."""
    if k1 <= k0:
        return []
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    total = sum(seg)
    if total <= 0:
        return list(pts)
    d0, d1 = k0 * total, k1 * total
    out, acc = [], 0.0
    for i, L in enumerate(seg):
        a, b = pts[i], pts[i + 1]
        s0, s1 = acc, acc + L
        if s1 >= d0 and s0 <= d1:
            fa = clamp((d0 - s0) / (L or 1e-6))
            fb = clamp((d1 - s0) / (L or 1e-6))
            pa, pb = lerp2(a, b, fa), lerp2(a, b, fb)
            if not out:
                out.append(pa)
            out.append(pb)
        acc = s1
    return out


# ----------------------------------------------------------------- the pen
class Pen:
    """Holds the cairo context and global time (for boil)."""

    def __init__(self, ctx, t):
        self.ctx = ctx
        self.t = t
        self.boil_t = math.floor(t * BOIL_FPS)
        self.zoom = 1.0   # set by the camera so line width stays constant on screen

    def line(self, pts, w=1.0, alpha=1.0, reveal=1.0, start=0.0, smooth_=True, closed=False, seed=0,
             wob=1.0, taper=0.18, color=None, step=4.0):
        """Draw a pen stroke. reveal/start: fraction drawn (pen moving) / erased from the start."""
        if alpha <= 0.003 or reveal <= start or len(pts) < 2:
            return
        P = catmull(pts, closed) if (smooth_ and len(pts) > 2) else list(pts)
        if reveal < 1.0 or start > 0.0:
            P = trim(P, start, reveal)
            if len(P) < 2:
                return
        P = resample_step(P, step / max(0.3, self.zoom ** 0.5))
        n = len(P)
        width = LINE * w / self.zoom
        amp = 0.55 * wob / self.zoom
        sd = seed * 7 + (self.boil_t % 3) * 1013
        ws, out = [], []
        L = 0.0
        for i in range(n):
            if i:
                L += math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1])
            u = i / (n - 1)
            k = 1.0
            if not closed and taper:
                if u < taper:
                    k = 0.25 + 0.75 * math.sin(u / taper * math.pi / 2)
                if u > 1 - taper:
                    k = min(k, 0.25 + 0.75 * math.sin((1 - u) / taper * math.pi / 2))
            k *= 0.88 + 0.24 * noise1(L / 60.0, seed)
            ws.append(width * k)
            out.append(L)
        # wobble along the normal (hand) + boil
        pts = []
        for i in range(n):
            a = P[max(0, i - 1)]
            b = P[min(n - 1, i + 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]
            d = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / d, dx / d
            o = amp * (noise1(out[i] / 45.0, sd) + 0.5 * noise1(out[i] / 13.0, sd + 5))
            pts.append((P[i][0] + nx * o, P[i][1] + ny * o, nx, ny))
        left = [(x + nx * w_ / 2, y + ny * w_ / 2) for (x, y, nx, ny), w_ in zip(pts, ws)]
        right = [(x - nx * w_ / 2, y - ny * w_ / 2) for (x, y, nx, ny), w_ in zip(pts, ws)]
        c = color or INK
        ctx = self.ctx
        ctx.set_source_rgba(c[0], c[1], c[2], alpha)
        ctx.move_to(*left[0])
        for p in left[1:]:
            ctx.line_to(*p)
        for p in reversed(right):
            ctx.line_to(*p)
        ctx.close_path()
        ctx.fill()
        # round caps
        for (x, y, _, _), w_ in ((pts[0], ws[0]), (pts[-1], ws[-1])):
            ctx.arc(x, y, w_ / 2, 0, 2 * math.pi)
            ctx.fill()

    def lines(self, strokes, reveal=1.0, start=0.0, alpha=1.0, w=1.0, seed=0, **kw):
        """Draw a list of strokes as ONE drawing: reveal runs through them in order, by length."""
        if reveal <= start:
            return
        lens = [max(1.0, length(s if not isinstance(s, dict) else s["p"])) for s in strokes]
        tot = sum(lens)
        acc = 0.0
        for i, (s, L) in enumerate(zip(strokes, lens)):
            a0, a1 = acc / tot, (acc + L) / tot
            acc += L
            r = clamp((reveal - a0) / (a1 - a0))
            st = clamp((start - a0) / (a1 - a0))
            if isinstance(s, dict):
                self.line(s["p"], s.get("w", 1.0) * w, s.get("a", 1.0) * alpha, r, st, seed=seed + i,
                          smooth_=s.get("smooth", True), closed=s.get("closed", False), **kw)
            else:
                self.line(s, w, alpha, r, st, seed=seed + i, **kw)

    def dot(self, x, y, r=3.0, alpha=1.0, color=None):
        c = color or INK
        self.ctx.set_source_rgba(c[0], c[1], c[2], alpha)
        self.ctx.arc(x, y, r / max(0.5, self.zoom ** 0.3), 0, 2 * math.pi)
        self.ctx.fill()

    def text(self, s, x, y, size=48, alpha=1.0, align="center", font="Caveat", bold=False, reveal=1.0):
        """Handwritten-looking text, revealed left to right."""
        ctx = self.ctx
        ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(size)
        ext = ctx.text_extents(s)
        x0 = x - ext.x_advance / 2 if align == "center" else (x - ext.x_advance if align == "right" else x)
        if reveal < 1:
            ctx.save()
            ctx.rectangle(x0 - 10, y - size * 1.4, (ext.x_advance + 20) * clamp(reveal), size * 2.2)
            ctx.clip()
        ctx.set_source_rgba(INK[0], INK[1], INK[2], alpha)
        ctx.move_to(x0, y)
        ctx.show_text(s)
        if reveal < 1:
            ctx.restore()
        return ext.x_advance


@contextmanager
def at(pen, x=0.0, y=0.0, s=1.0, a=0.0, fx=1):
    ctx = pen.ctx
    ctx.save()
    ctx.translate(x, y)
    if a:
        ctx.rotate(a)
    ctx.scale(s * fx, s)
    z = pen.zoom
    pen.zoom = z * s
    try:
        yield
    finally:
        pen.zoom = z
        ctx.restore()


def new_frame():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*BG)
    ctx.paint()
    return surf, ctx


# ----------------------------------------------------------------- finishing
_grain = {}


def finish(ctx, t, grain=0.05, vignette=0.55):
    """Very light film grain + soft vignette (keeps the black velvety, not flat)."""
    import numpy as np
    i = int(t * 12) % 6
    if i not in _grain:
        rng = np.random.default_rng(7 + i)
        gw, gh = W // 2, H // 2
        n = (rng.normal(0.5, 0.2, (gh, gw)).clip(0, 1) * 255).astype("uint8")
        arr = np.zeros((gh, gw, 4), dtype="uint8")
        arr[..., 0] = arr[..., 1] = arr[..., 2] = n
        arr[..., 3] = 255
        _grain[i] = (cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, gw, gh), arr)
    ctx.save()
    ctx.identity_matrix()
    ctx.scale(2, 2)
    ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
    ctx.set_source_surface(_grain[i][0], 0, 0)
    ctx.paint_with_alpha(grain)
    ctx.restore()
    ctx.save()
    ctx.identity_matrix()
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, W * 0.72)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, vignette)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
