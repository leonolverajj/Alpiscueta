"""Flat-2D ink style kit (pycairo).

Look: light grey studio backdrops with big angular slabs, thick brushy ink outlines,
flat fills with hard cel-shadow shapes, sparse hatching, crimson/teal/gold accents and
small teal "UI glyph" boxes. Everything is vector, re-drawn every frame, so shapes can
move, boil and breathe.
"""
import math
import random
from contextlib import contextmanager

import cairo

W, H = 1920, 1080
FPS = 24


# ----------------------------------------------------------------- colour
def hexc(s, a=1.0):
    s = s.lstrip("#")
    return (int(s[0:2], 16) / 255, int(s[2:4], 16) / 255, int(s[4:6], 16) / 255, a)


P = {
    "ink": hexc("#18181f"),
    "ink2": hexc("#2a2a33"),
    "paper": hexc("#f1f0ee"),
    "g0": hexc("#f6f6f5"),
    "g1": hexc("#e3e3e3"),
    "g2": hexc("#cbcbce"),
    "g3": hexc("#a9a9ae"),
    "g4": hexc("#7c7c84"),
    "g5": hexc("#55555e"),
    "g6": hexc("#3a3a43"),
    "red": hexc("#a3303a"),
    "red_d": hexc("#6e1e27"),
    "red_l": hexc("#cf5560"),
    "teal": hexc("#3cc3ae"),
    "teal_l": hexc("#8fe9da"),
    "teal_d": hexc("#1d6f68"),
    "gold": hexc("#d3a443"),
    "gold_l": hexc("#f1d27e"),
    "gold_d": hexc("#8f6a22"),
    "cobalt": hexc("#3f63a6"),
    "cobalt_l": hexc("#6f93cf"),
    "cobalt_d": hexc("#253d6c"),
    "rust": hexc("#c3612f"),
    "rust_d": hexc("#86391a"),
    "skin": hexc("#efd2bb"),
    "skin_s": hexc("#cfa38a"),
    "skin2": hexc("#b98463"),
    "skin2_s": hexc("#8e5f45"),
    "hair_dk": hexc("#26252d"),
    "hair_gold": hexc("#e2c05c"),
    "hair_gold_s": hexc("#b48a2f"),
    "hair_white": hexc("#dcdde3"),
    "hair_white_s": hexc("#9fa1ad"),
    "steel": hexc("#8e929c"),
    "steel_l": hexc("#c4c7cf"),
    "steel_d": hexc("#5d616b"),
    "coat": hexc("#3b3b45"),
    "coat_s": hexc("#26262e"),
    "night": hexc("#14161e"),
    "sea": hexc("#203a46"),
    "sea_l": hexc("#2f5a66"),
    "violet": hexc("#6c4fa3"),
    "white": hexc("#ffffff"),
}


def col(c, a=None):
    """Accept palette key, hex string or tuple; optionally override alpha."""
    if isinstance(c, str):
        c = P[c] if c in P else hexc(c)
    if len(c) == 3:
        c = (*c, 1.0)
    if a is not None:
        c = (c[0], c[1], c[2], c[3] * a)
    return c


def mix(c1, c2, k):
    c1, c2 = col(c1), col(c2)
    return tuple(c1[i] + (c2[i] - c1[i]) * k for i in range(4))


def setc(ctx, c, a=None):
    ctx.set_source_rgba(*col(c, a))


# ----------------------------------------------------------------- maths / easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, k):
    return a + (b - a) * k


def lerp2(p, q, k):
    return (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)


def ss(x):  # smoothstep on [0,1]
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x, p=3):
    x = clamp(x)
    return 1 - (1 - x) ** p


def ease_in(x, p=3):
    return clamp(x) ** p


def ease_io(x):
    x = clamp(x)
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_back(x, s=1.7):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def win(t, a, b):
    """0..1 progress of t inside window [a,b] (seconds or normalized)."""
    return clamp((t - a) / max(1e-6, b - a))


def held(t, fps_draw=12):
    """Quantise time to 'on twos' like hand-drawn animation."""
    return math.floor(t * fps_draw) / fps_draw


def rot(p, a, c=(0, 0)):
    s, k = math.sin(a), math.cos(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * k - y * s, c[1] + x * s + y * k)


def tr(pts, dx=0, dy=0, s=1.0, a=0.0, c=(0, 0), fx=1):
    """Transform point list: flip x, scale, rotate about c, then translate."""
    out = []
    for x, y in pts:
        x, y = x * fx * s, y * s
        if a:
            x, y = rot((x, y), a, c)
        out.append((x + dx, y + dy))
    return out


@contextmanager
def at(ctx, x=0, y=0, s=1.0, a=0.0, fx=1, sy=None):
    ctx.save()
    ctx.translate(x, y)
    if a:
        ctx.rotate(a)
    ctx.scale(s * fx, s if sy is None else sy)
    try:
        yield
    finally:
        ctx.restore()


# ----------------------------------------------------------------- paths
def catmull(pts, closed=False, n=8):
    """Sample a Catmull-Rom spline through pts -> dense polyline."""
    if len(pts) < 3:
        return list(pts)
    P_ = list(pts)
    if closed:
        P_ = [P_[-1]] + P_ + [P_[0], P_[1]]
    else:
        P_ = [P_[0]] + P_ + [P_[-1]]
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t +
                                    (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 +
                                    (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    if not closed:
        out.append(P_[-2])
    return out


def poly(ctx, pts, close=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


def jitter(pts, amp, rng):
    return [(x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)) for x, y in pts]


def ribbon(pts, widths):
    """Polygon of a variable-width stroke along polyline pts."""
    n = len(pts)
    left, right = [], []
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = widths[i] / 2
        left.append((pts[i][0] + nx * w, pts[i][1] + ny * w))
        right.append((pts[i][0] - nx * w, pts[i][1] - ny * w))
    return left + right[::-1]


def resample(pts, step):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(d / step))
        for j in range(1, k + 1):
            out.append(lerp2(a, b, j / k))
    return out


# ----------------------------------------------------------------- ink drawing
def stroke(ctx, pts, w=4.0, color="ink", taper=(0.25, 0.25), smooth=False, closed=False,
           wobble=0.18, seed=0, alpha=None):
    """Brush stroke: variable width, tapered ends, slight pressure wobble."""
    if smooth:
        pts = catmull(pts, closed=closed)
    elif closed:
        pts = list(pts) + [pts[0]]
    pts = resample(pts, 6)
    n = len(pts)
    rng = random.Random(seed)
    phase = rng.uniform(0, 6.28)
    ws = []
    for i in range(n):
        s = i / max(1, n - 1)
        k = 1.0
        if not closed:
            if taper[0] and s < taper[0]:
                k = 0.15 + 0.85 * ss(s / taper[0])
            if taper[1] and s > 1 - taper[1]:
                k = min(k, 0.15 + 0.85 * ss((1 - s) / taper[1]))
        k *= 1 + wobble * math.sin(phase + s * 9.0)
        ws.append(max(0.4, w * k))
    setc(ctx, color, alpha)
    poly(ctx, ribbon(pts, ws))
    ctx.fill()


def shape(ctx, pts, fill=None, ink=4.0, smooth=False, ink_color="ink", seed=0, wobble=0.22, alpha=None):
    """Filled flat shape with brushy ink outline. Returns sampled outline."""
    path = catmull(pts, closed=True) if smooth else list(pts)
    if fill is not None:
        setc(ctx, fill, alpha)
        poly(ctx, path)
        ctx.fill()
    if ink:
        stroke(ctx, path, ink, ink_color, closed=True, wobble=wobble, seed=seed, alpha=alpha)
    return path


def fillp(ctx, pts, color, smooth=False, alpha=None):
    path = catmull(pts, closed=True) if smooth else pts
    setc(ctx, color, alpha)
    poly(ctx, path)
    ctx.fill()


@contextmanager
def clip(ctx, pts, smooth=False):
    ctx.save()
    poly(ctx, catmull(pts, closed=True) if smooth else pts)
    ctx.clip()
    try:
        yield
    finally:
        ctx.restore()


def cel(ctx, base_pts, shade_pts, color, smooth=False, alpha=None):
    """Hard cel shadow: shade_pts filled, clipped to base shape."""
    with clip(ctx, base_pts, smooth):
        fillp(ctx, shade_pts, color, alpha=alpha)


def hatch(ctx, region_pts, angle=-0.9, gap=11, w=1.6, color="ink", alpha=0.55, seed=0, smooth=False,
          length=None):
    """Sparse brushy hatching clipped to a region (shadows / texture)."""
    rng = random.Random(seed)
    xs = [p[0] for p in region_pts]
    ys = [p[1] for p in region_pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    R = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 10
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx
    with clip(ctx, region_pts, smooth):
        o = -R
        while o < R:
            L = length or R
            off = rng.uniform(-L * 0.3, L * 0.3)
            a = (cx + nx * o + dx * (-L + off), cy + ny * o + dy * (-L + off))
            b = (cx + nx * o + dx * (L + off), cy + ny * o + dy * (L + off))
            stroke(ctx, [a, b], w * rng.uniform(0.7, 1.3), color, taper=(0.4, 0.4), wobble=0.1,
                   seed=rng.randint(0, 999), alpha=alpha)
            o += gap * rng.uniform(0.75, 1.3)


def spikes(cx, cy, r_in, r_out, n, a0, a1, rng=None, var=0.25):
    """Zig-zag fan (fur collars, manes, flames, hair clumps)."""
    rng = rng or random.Random(1)
    pts = []
    for i in range(n + 1):
        a = lerp(a0, a1, i / n)
        pts.append((cx + math.cos(a) * r_in, cy + math.sin(a) * r_in))
        if i < n:
            am = lerp(a0, a1, (i + 0.5) / n)
            ro = r_out * rng.uniform(1 - var, 1 + var * 0.5)
            pts.append((cx + math.cos(am) * ro, cy + math.sin(am) * ro))
    return pts


def blade(p0, p1, w, bend=0.0):
    """Leaf/blade polygon from p0 to p1 (hair spikes, flames, feathers)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    m = (p0[0] + dx * 0.45 + nx * bend * L, p0[1] + dy * 0.45 + ny * bend * L)
    return [(p0[0] + nx * w / 2, p0[1] + ny * w / 2), (m[0] + nx * w * 0.35, m[1] + ny * w * 0.35), p1,
            (m[0] - nx * w * 0.35, m[1] - ny * w * 0.35), (p0[0] - nx * w / 2, p0[1] - ny * w / 2)]


def circle_pts(cx, cy, r, n=40, ry=None, a0=0.0):
    ry = r if ry is None else ry
    return [(cx + math.cos(a0 + 2 * math.pi * i / n) * r, cy + math.sin(a0 + 2 * math.pi * i / n) * ry)
            for i in range(n)]


def glow(ctx, x, y, r, color="teal", alpha=0.6):
    c = col(color)
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], alpha)
    g.add_color_stop_rgba(0.35, c[0], c[1], c[2], alpha * 0.45)
    g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def lingrad(ctx, x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c in stops:
        g.add_color_stop_rgba(o, *col(c))
    return g


# ----------------------------------------------------------------- backgrounds
def bg_studio(ctx, t=0.0, seed=1, tone=0.0, slabs=True, drift=1.0, dark=False):
    """Reference-style backdrop: soft grey gradient + big angular slabs + scratches.
    tone: -1 colder/darker .. +1 lighter. dark=True gives the night variant."""
    rng = random.Random(seed)
    if dark:
        top, bot = mix("night", "g6", 0.35 + 0.1 * tone), "night"
        slab_cols = [mix("night", "g6", 0.55), mix("night", "g5", 0.4), mix("night", "g6", 0.25)]
    else:
        top, bot = mix("g2", "g0", 0.55 + 0.35 * tone), mix("g1", "g3", 0.25 - 0.2 * tone)
        slab_cols = ["g2", "g3", mix("g2", "g1", 0.5)]
    ctx.set_source(lingrad(ctx, 0, 0, 0, H, [(0, top), (1, bot)]))
    ctx.paint()
    # radial light pool
    c = col("white") if not dark else col("teal_d")
    g = cairo.RadialGradient(W * 0.55, H * 0.42, 50, W * 0.55, H * 0.42, W * 0.7)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], 0.55 if not dark else 0.18)
    g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    ctx.set_source(g)
    ctx.paint()
    if slabs:
        for i in range(3):
            x0 = rng.uniform(-200, W * 0.6) + math.sin(t * 0.07 * drift + i) * 25 * drift
            y0 = rng.uniform(H * 0.15, H * 0.55)
            w = rng.uniform(600, 1300)
            h = rng.uniform(220, 520)
            sk = rng.uniform(-160, 160)
            pts = [(x0, y0 + h), (x0 + sk * 0.3, y0 + rng.uniform(0, 60)),
                   (x0 + w * 0.35, y0 - rng.uniform(20, 120)), (x0 + w * 0.7, y0 + rng.uniform(-40, 40)),
                   (x0 + w + sk, y0 + rng.uniform(40, 140)), (x0 + w + sk * 1.2, y0 + h)]
            fillp(ctx, pts, slab_cols[i % 3], alpha=0.75)
        # ground band
        fillp(ctx, [(0, H * 0.82), (W, H * 0.78), (W, H), (0, H)], slab_cols[1], alpha=0.35)
    # dry scratches
    for i in range(14):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H)
        L = rng.uniform(40, 160)
        a = rng.uniform(-0.3, 0.3) + (0 if i % 2 else 0.2)
        stroke(ctx, [(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], 1.6,
               "white" if dark else "g4", taper=(0.5, 0.5), seed=i, alpha=0.12 if dark else 0.25)


@contextmanager
def hud(ctx):
    """Draw in screen space (ignores the scene camera)."""
    ctx.save()
    ctx.identity_matrix()
    try:
        yield
    finally:
        ctx.restore()


def ui_glyphs(ctx, t, seed=3, region=(0, H * 0.7, W, H), color="teal", n=7, alpha=0.9):
    """Small outlined boxes that blink in and out (from the reference frames). Screen space."""
    with hud(ctx):
        _ui_glyphs(ctx, t, seed, region, color, n, alpha)


def _ui_glyphs(ctx, t, seed, region, color, n, alpha):
    rng = random.Random(seed)
    x0, y0, x1, y1 = region
    for i in range(n):
        x = rng.uniform(x0, x1)
        y = rng.uniform(y0, y1)
        w = rng.choice([14, 18, 22, 26])
        h = rng.choice([18, 26, 40, 56])
        ph = rng.uniform(0, 10)
        on = 0.5 + 0.5 * math.sin(t * rng.uniform(0.6, 1.4) + ph)
        if on < 0.35:
            continue
        a = alpha * ss((on - 0.35) / 0.3)
        setc(ctx, color, a)
        ctx.set_line_width(2.4)
        ctx.rectangle(x, y + math.sin(t * 0.8 + ph) * 6, w, h)
        ctx.stroke()


def particles(ctx, t, n=40, seed=5, color="g0", region=(0, 0, W, H), speed=(-10, -30), size=(1.5, 4),
              alpha=0.6, shape_="dot"):
    rng = random.Random(seed)
    x0, y0, x1, y1 = region
    for i in range(n):
        bx, by = rng.uniform(x0, x1), rng.uniform(y0, y1)
        vx, vy = speed[0] * rng.uniform(0.5, 1.5), speed[1] * rng.uniform(0.5, 1.5)
        x = x0 + (bx - x0 + vx * t) % (x1 - x0)
        y = y0 + (by - y0 + vy * t) % (y1 - y0)
        r = rng.uniform(*size)
        tw = 0.6 + 0.4 * math.sin(t * 2 + i)
        setc(ctx, color, alpha * tw)
        if shape_ == "dot":
            ctx.arc(x, y, r, 0, 6.283)
            ctx.fill()
        else:
            ctx.rectangle(x, y, r * 2, r * 2)
            ctx.fill()


def speedlines(ctx, cx, cy, t, n=60, r0=300, r1=1500, color="ink", alpha=0.35, seed=9, w=3):
    rng = random.Random(seed + int(t * 12))
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r_a = r0 * rng.uniform(0.9, 1.5)
        p0 = (cx + math.cos(a) * r_a, cy + math.sin(a) * r_a)
        p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1)
        stroke(ctx, [p0, p1], w * rng.uniform(0.5, 1.6), color, taper=(0.9, 0.0), alpha=alpha, seed=i)


# ----------------------------------------------------------------- text
FONT_TITLE = "Cinzel"
FONT_CAPS = "Oswald"
FONT_SERIF = "Cormorant Garamond"


def text(ctx, s, x, y, size, font=FONT_CAPS, color="ink", align="center", bold=True, alpha=None,
         tracking=0.0, italic=False):
    ctx.select_font_face(font, cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    widths = [ctx.text_extents(ch).x_advance for ch in s]
    total = sum(widths) + tracking * size * (len(s) - 1)
    if align == "center":
        x -= total / 2
    elif align == "right":
        x -= total
    setc(ctx, color, alpha)
    for ch, w in zip(s, widths):
        ctx.move_to(x, y)
        ctx.show_text(ch)
        x += w + tracking * size
    return total


def text_width(ctx, s, size, font=FONT_CAPS, bold=True, tracking=0.0):
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    return sum(ctx.text_extents(ch).x_advance for ch in s) + tracking * size * (len(s) - 1)


def caption_tag(ctx, s, x, y, t, size=34, color="ink", accent="red", appear=0.0):
    """Little angular label (like the arm-band stripes in the refs). Screen space."""
    with hud(ctx):
        _caption_tag(ctx, s, x, y, t, size, color, accent, appear)


def _caption_tag(ctx, s, x, y, t, size, color, accent, appear):
    k = ease_out(win(t, appear, appear + 0.5))
    if k <= 0:
        return
    w = text_width(ctx, s, size, tracking=0.08) + 40
    h = size * 1.5
    ww = w * k
    fillp(ctx, [(x - 14, y), (x + ww, y), (x + ww + 14, y + h), (x, y + h)], color, alpha=0.92)
    fillp(ctx, [(x - 14 - 10, y), (x - 14, y), (x, y + h), (x - 10, y + h)], accent)
    if k > 0.6:
        text(ctx, s, x + 20, y + h * 0.72, size, color="g0", align="left", tracking=0.08,
             alpha=ss((k - 0.6) / 0.4))


# ----------------------------------------------------------------- post
_grain_cache = {}


def grain_surface(i):
    if i not in _grain_cache:
        import numpy as np
        rng = np.random.default_rng(100 + i)
        gw, gh = W // 2, H // 2
        n = (rng.normal(0.5, 0.18, (gh, gw)).clip(0, 1) * 255).astype("uint8")
        arr = np.zeros((gh, gw, 4), dtype="uint8")
        arr[..., 0] = arr[..., 1] = arr[..., 2] = n
        arr[..., 3] = 255
        surf = cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, gw, gh)
        _grain_cache[i] = (surf, arr)
    return _grain_cache[i][0]


def post(ctx, t, vignette=0.35, grain=0.10):
    if grain:
        surf = grain_surface(int(t * 12) % 4)
        ctx.save()
        ctx.scale(2, 2)
        ctx.set_operator(cairo.OPERATOR_OVERLAY)
        ctx.set_source_surface(surf, 0, 0)
        ctx.paint_with_alpha(grain)
        ctx.restore()
    if vignette:
        g = cairo.RadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, W * 0.75)
        g.add_color_stop_rgba(0, 0, 0, 0, 0)
        g.add_color_stop_rgba(1, 0.05, 0.05, 0.08, vignette)
        ctx.set_source(g)
        ctx.paint()


def new_frame():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    return surf, ctx


def camera(ctx, t, T, zoom=(1.0, 1.08), pan=((0, 0), (0, 0)), shake=0.0, focus=(W / 2, H / 2)):
    """Slow documentary push-in / pan for the whole scene."""
    k = ease_io(t / max(T, 1e-6))
    z = lerp(zoom[0], zoom[1], k)
    px = lerp(pan[0][0], pan[1][0], k)
    py = lerp(pan[0][1], pan[1][1], k)
    if shake:
        px += math.sin(t * 37) * shake + math.sin(t * 23) * shake * 0.6
        py += math.cos(t * 31) * shake
    ctx.translate(focus[0], focus[1])
    ctx.scale(z, z)
    ctx.translate(-focus[0] + px, -focus[1] + py)
