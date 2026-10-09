"""b14 proverbio · b15 oggi"""
import math
import random

from motore.film import scena
from motore.linea import H, W, arc, at, clamp, ease_io, ease_out, ellipse, lerp, smooth, wave, win
from motore.omino import DOWN, omino
from motore.personaggi import mulo

ROAD_Y = 790


@scena("proverbio")
def proverbio(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    cx, cy = 960, 470
    rng = random.Random(14)
    # a thousand paths (well, a few dozen) converging on Rome
    paths = []
    for i in range(34):
        ang = 2 * math.pi * i / 34 + rng.uniform(-0.05, 0.05)
        R = rng.uniform(900, 1300)
        sx, sy = cx + math.cos(ang) * R, cy + math.sin(ang) * R * 0.75
        mid = (lerp(sx, cx, 0.5) + rng.uniform(-60, 60), lerp(sy, cy, 0.5) + rng.uniform(-40, 40))
        paths.append([(sx, sy), mid, (cx + math.cos(ang) * 40, cy + math.sin(ang) * 30)])
    grow = ease_io(win(t, 0.8, 6.0))
    for i, p in enumerate(paths):
        pen.line(p, 0.7, 0.55 * a, reveal=clamp(grow * 1.3 - (i % 5) * 0.06), start=vanish, seed=200 + i)
    # little Rome at the centre: a dome and two columns
    rome = [arc(cx, cy + 6, 34, math.pi, 2 * math.pi, 16), [(cx - 44, cy + 8), (cx + 44, cy + 8)],
            [(cx - 30, cy + 8), (cx - 30, cy + 40)], [(cx + 30, cy + 8), (cx + 30, cy + 40)],
            [(cx - 48, cy + 42), (cx + 48, cy + 42)]]
    pen.lines(rome, appear * win(t, 1.0, 3.0), vanish, 1.0, 1.0, seed=230)
    pen.text("Roma", cx, cy + 90, 46, a * win(t, 2.5, 3.5), reveal=win(t, 2.5, 3.5))
    # the proverb, handwritten, then its true origin
    k = win(t, 1.6, 4.6)
    pen.text("«Tutte le strade portano a Roma»", cx, 150, 64, a, reveal=k)
    k2 = win(t, 7.2, 9.6)
    if k2 > 0:
        pen.text("mille viae ducunt homines per saecula Romam", cx, 920, 40, a * 0.85, reveal=k2)
        pen.text("Alano di Lilla, ~1175", cx, 975, 34, a * 0.6, reveal=win(t, 9.0, 10.2))
    # a medieval pilgrim walks along the lower-left path towards Rome
    k3 = win(t, 9.5, T)
    if k3 > 0:
        p = paths[14]
        x = lerp(p[0][0], p[1][0], ease_io(k3) * 0.85)
        y = lerp(p[0][1], p[1][1], ease_io(k3) * 0.85)
        omino(pen, x, y, 0.8, t, "monaco", walk=1.0, expr="smile", hold="staff", fx=1,
              alpha=a * smooth(win(t, 9.5, 10.5)), seed=5)
    road = [(lerp(-60, cx - 40, k / 40.0), cy + 6 * math.sin(k / 6.0)) for k in range(41)]
    return road


def car(pen, x, y, s, t, alpha=1.0, reveal=1.0, start=0.0):
    """A small friendly modern car, side view, facing right."""
    with at(pen, x, y, s):
        bump = abs(math.sin(t * 9)) * 1.5
        body = [(-120, -30 - bump), (-118, -62 - bump), (-70, -66 - bump), (-40, -104 - bump), (40, -106 - bump),
                (78, -70 - bump), (118, -62 - bump), (126, -34 - bump), (-120, -30 - bump)]
        win1 = [(-30, -70 - bump), (-10, -96 - bump), (24, -96 - bump), (24, -70 - bump), (-30, -70 - bump)]
        win2 = [(34, -70 - bump), (34, -96 - bump), (58, -94 - bump), (72, -70 - bump), (34, -70 - bump)]
        pen.lines([body, win1, win2], reveal, start, alpha, 1.1, seed=300)
        for wx in (-72, 76):
            pen.line(ellipse(wx, -22, 24, 24, 20), 1.1, alpha, reveal, start, seed=301 + wx)
            ang = -t * 14
            pen.line([(wx + math.cos(ang) * 10, -22 + math.sin(ang) * 10), (wx - math.cos(ang) * 10, -22 - math.sin(ang) * 10)],
                     0.7, alpha, reveal, start, seed=303)
        pen.line([(118, -52 - bump), (128, -52 - bump)], 0.8, alpha, reveal, start, seed=304)


@scena("oggi")
def oggi(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    road = [(x, ROAD_Y + 8 * math.sin(x / 400.0)) for x in range(-60, W + 61, 40)]
    # the modern state road: dashed centre line and a road sign
    dashes = [[(x, ROAD_Y + 24), (x + 50, ROAD_Y + 24)] for x in range(-40, W, 120)]
    pen.lines(dashes, appear * win(t, 0.5, 2.5), vanish, 0.5, 0.8, seed=310)
    pen.line([(x, ROAD_Y + 60) for x in range(-60, W + 61, 60)], 0.8, 0.6 * a, appear, vanish, seed=311)
    signs = [("SS7  Appia", 1.8), ("SS3  Flaminia", 2.6), ("SS1  Aurelia", 3.4), ("SS9  Emilia", 4.2)]
    for i, (name, at_s) in enumerate(signs):
        k = win(t, at_s, at_s + 0.8) * (1 - win(t, at_s + 2.6, at_s + 3.2) if i < 3 else 1)
        if k <= 0:
            continue
        sx = 1500
        pen.lines([[(sx, ROAD_Y), (sx, ROAD_Y - 230)],
                   [(sx - 150, ROAD_Y - 330), (sx + 150, ROAD_Y - 330), (sx + 150, ROAD_Y - 230), (sx - 150, ROAD_Y - 230),
                    (sx - 150, ROAD_Y - 330)]], k, vanish, a, 1.0, seed=320 + i)
        pen.text(name, sx, ROAD_Y - 266, 52, a * k, reveal=k)
    # a little car drives along the line, while the old traveller and his mule walk the same road
    cxp = lerp(-300, 2300, (t / T) ** 0.9)
    car(pen, cxp, ROAD_Y + 8 * math.sin(cxp / 400.0), 1.0, t, a * smooth(win(t, 1.0, 2.0)))
    ghost = smooth(win(t, 7.0, 9.0)) * a
    if ghost > 0:
        gx = lerp(200, 1100, ease_io(win(t, 7.0, T - 1.0)))
        mulo(pen, gx - 260, ROAD_Y + 8 * math.sin((gx - 260) / 400.0), 1.0, t, walk=1.0, ear=0.6, alpha=ghost * 0.85)
        omino(pen, gx, ROAD_Y + 8 * math.sin(gx / 400.0), 1.2, t, "viandante", walk=1.0, expr="smile", hold="staff",
              alpha=ghost)
        k = win(t, 10.0, 11.0)
        if k > 0:
            pen.text("più di 2000 anni dopo", 520, 330, 50, ghost * k * 0.8 * (1 - win(t, T - 10.0, T - 9.0)), reveal=k)
    # the ending: the line keeps going, and the title writes itself
    kt = win(t, T - 9.0, T - 6.0)
    if kt > 0:
        pen.text("La linea che partì da Roma", 960, 230, 92, a * smooth(kt), reveal=kt)
    return road
