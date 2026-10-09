"""Shared scenes: placeholder, chapter cards, title, end card."""
import math
import random

from engine.kit import (FONT_CAPS, FONT_SERIF, FONT_TITLE, H, W, at, bg_studio, blade, camera, circle_pts, clip,
                        ease_back, ease_io, ease_out, fillp, glow, hatch, lerp, mix, particles, setc, shape, ss,
                        stroke, text, text_width, ui_glyphs, win)
from engine import figures as F
from . import scene


@scene("placeholder")
def placeholder(ctx, t, T, seg):
    bg_studio(ctx, t, seed=11)
    text(ctx, seg["visual"].upper(), W / 2, H / 2, 90, color="g5", tracking=0.1)
    ui_glyphs(ctx, t)


@scene("chapter")
def chapter(ctx, t, T, seg):
    """Ink slam: big Roman numeral, title slides in under a crimson slash, teal glyphs."""
    num, title = seg["kw"]
    setc(ctx, "night")
    ctx.paint()
    rng = random.Random(len(title))
    # drifting dark slabs
    for i in range(4):
        x = -300 + i * 560 + math.sin(t * 0.4 + i) * 30 - t * 18
        fillp(ctx, [(x, 0), (x + 380, 0), (x + 180, H), (x - 200, H)], mix("night", "g6", 0.25 + 0.12 * (i % 2)))
    with at(ctx, W / 2, H / 2, 1.0 + 0.04 * ease_io(t / T)):
        k = ease_back(win(t, 0.15, 0.7), 2.2)
        # numeral
        with at(ctx, 0, -60, 0.6 + 0.4 * k):
            text(ctx, num, 4, 14, 260, FONT_TITLE, "red_d", alpha=k * 0.9)
            text(ctx, num, 0, 0, 260, FONT_TITLE, "g0", alpha=k)
        # crimson slash
        ks = ease_out(win(t, 0.45, 0.9), 3)
        stroke(ctx, [(-560 * ks, 70), (560 * ks, 52)], 16, "red", taper=(0.15, 0.3), seed=3)
        # title
        kt = ease_out(win(t, 0.65, 1.3), 3)
        ctx.save()
        ctx.rectangle(-W / 2, 70, W, 140)
        ctx.clip()
        text(ctx, title, 0, 170 - (1 - kt) * 90, 74, FONT_CAPS, "g0", tracking=0.12, alpha=kt)
        ctx.restore()
    ui_glyphs(ctx, t * 2, seed=7, region=(0, H * 0.72, W, H * 0.95), n=10)
    particles(ctx, t, 30, seed=3, color="teal_l", alpha=0.35, speed=(6, -14))


@scene("title")
def title(ctx, t, T, seg):
    """Main title: an open glowing book, light rays, title drawn letter by letter."""
    bg_studio(ctx, t, seed=4, dark=True)
    camera(ctx, t, T, zoom=(1.08, 1.0))
    cx, cy = W / 2, H * 0.62
    # rays
    for i in range(14):
        a = -math.pi / 2 + (i - 6.5) * 0.16 + math.sin(t * 0.5 + i) * 0.02
        L = 900 + 120 * math.sin(t * 1.3 + i * 2)
        pts = [(cx, cy), (cx + math.cos(a - 0.035) * L, cy + math.sin(a - 0.035) * L),
               (cx + math.cos(a + 0.035) * L, cy + math.sin(a + 0.035) * L)]
        fillp(ctx, pts, "gold_l", alpha=0.10 + 0.05 * math.sin(t * 2 + i))
    glow(ctx, cx, cy - 40, 520, "gold", 0.55)
    _open_book(ctx, cx, cy, 1.25, t)
    # title text
    k = win(t, 1.0, 3.2)
    s = "LA IDEA DE DIOS"
    n = int(len(s) * k + 0.999)
    text(ctx, s[:n], W / 2, H * 0.26, 128, FONT_TITLE, "g0", tracking=0.06)
    ks = ease_out(win(t, 2.6, 3.4))
    stroke(ctx, [(W / 2 - 420 * ks, H * 0.30), (W / 2 + 420 * ks, H * 0.295)], 8, "red", taper=(0.2, 0.2))
    kk = ease_out(win(t, 3.2, 4.2))
    text(ctx, "EL ORIGEN DE LOS RELATOS QUE NOS FORMARON", W / 2, H * 0.36, 34, FONT_CAPS, "g2", tracking=0.25,
         alpha=kk)
    particles(ctx, t, 60, seed=8, color="gold_l", alpha=0.5, speed=(4, -22), region=(W * 0.2, 0, W * 0.8, H))
    ui_glyphs(ctx, t, seed=2, n=6)


def _open_book(ctx, cx, cy, s, t, pages_turn=True):
    with at(ctx, cx, cy, s):
        # cover
        shape(ctx, [(-330, 10), (0, 40), (330, 10), (340, 50), (0, 82), (-340, 50)], "red_d", 6)
        # page blocks
        for side in (-1, 1):
            pg = [(0, 30), (side * 300, -10), (side * 315, -150), (side * 30, -120), (0, -100)]
            shape(ctx, pg, "g0", 5, seed=2 + side)
            for k in range(7):
                y = -110 + k * 13
                stroke(ctx, [(side * 50, y + 10 - k), (side * 270, y - 25 - k * 0.5)], 2.2, "g4", alpha=0.7,
                       taper=(0.2, 0.2), seed=k)
            stroke(ctx, [(side * 10, 34), (side * 305, 0)], 3, "g3")
        if pages_turn:
            k = (t * 0.35) % 1.0
            a = math.pi * ease_io(k)
            x = math.cos(a) * 290
            lift = math.sin(a) * 120
            pg = [(0, -100), (x, -130 - lift * 0.7), (x * 1.02, -10 - lift * 0.4), (0, 30)]
            shape(ctx, pg, "g1" if x > 0 else "g2", 4, seed=9)
        stroke(ctx, [(0, -100), (0, 34)], 5)


@scene("end")
def end_card(ctx, t, T, seg):
    """Final card: three commands appear, then the title returns."""
    bg_studio(ctx, t, seed=21, dark=True)
    lines = ["ABRE LOS OJOS.", "HABLA CON VERDAD.", "Y HAZ UN MUNDO."]
    times = [0.4, 1.7, 3.0]
    for i, (l, a) in enumerate(zip(lines, times)):
        k = ease_out(win(t, a, a + 0.6))
        y = H * 0.36 + i * 120
        text(ctx, l, W / 2, y + (1 - k) * 30, 84 if i < 2 else 96, FONT_TITLE, "g0" if i < 2 else "gold_l",
             tracking=0.06, alpha=k)
    ks = ease_out(win(t, 3.6, 4.4))
    stroke(ctx, [(W / 2 - 380 * ks, H * 0.36 + 300), (W / 2 + 380 * ks, H * 0.36 + 296)], 7, "red")
    kf = ss(win(t, T - 4.0, T - 2.4))
    if kf > 0:
        setc(ctx, "night", kf)
        ctx.paint()
        text(ctx, "LA IDEA DE DIOS", W / 2, H / 2 + 20, 96, FONT_TITLE, "g0", tracking=0.06, alpha=kf)
        text(ctx, "Basado en la conferencia de Jordan B. Peterson — Biblical Series I (2017)", W / 2, H / 2 + 90, 26,
             FONT_SERIF, "g3", bold=False, alpha=kf * 0.9, italic=True)
    ui_glyphs(ctx, t, seed=4, n=8)
    kb = ss(win(t, T - 1.2, T))
    if kb > 0:
        setc(ctx, "ink", kb)
        ctx.paint()
