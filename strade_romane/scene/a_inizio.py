"""b01 linea · b02 fango"""
import math
import random

from motore.film import scena
from motore.linea import H, W, at, clamp, ease_io, ease_out, ellipse, lerp, smooth, wave, win
from motore.omino import DOWN, omino
from motore.personaggi import mulo

ROAD_Y = 790


def strada(y=ROAD_Y, x0=-60, x1=W + 60, amp=10, f=1 / 300.0, ph=0.0):
    return [(x, y + amp * math.sin(x * f + ph)) for x in range(int(x0), int(x1) + 1, 40)]


def tufts(pen, y, alpha, seed=1, xs=None, reveal=1.0, start=0.0):
    rng = random.Random(seed)
    xs = xs or [rng.uniform(40, W - 40) for _ in range(9)]
    strokes = []
    for x in xs:
        h = rng.uniform(10, 22)
        strokes += [[(x, y), (x - 4, y - h)], [(x + 5, y), (x + 7, y - h * 0.8)], [(x + 10, y), (x + 16, y - h * 0.6)]]
    pen.lines(strokes, reveal, start, alpha * 0.55, 0.7, seed=seed)


@scena("linea")
def linea(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    road = strada()
    # pen nib racing along the line at the very start
    if t < 2.8:
        k = smooth((t - 0.2) / 2.2)
        x = lerp(-60, W + 60, k)
        pen.dot(x, ROAD_Y + 10 * math.sin(x / 300.0), 4.5, 0.9 * (1 - win(t, 2.4, 2.8)))
    # hills far away
    hills = [(1180, 690), (1320, 610), (1440, 640), (1590, 560), (1760, 630), (1990, 590)]
    pen.lines([hills], appear * win(t, 1.0, 3.0), vanish, 0.45, 0.8, seed=11)
    tufts(pen, ROAD_Y + 4, a, 3, [180, 420, 1260, 1500, 1720], win(t, 2.0, 3.5), vanish)
    # the word: strada -> via strata, with three little strata under it
    k1 = win(t, 3.2, 4.4)
    k2 = win(t, 6.0, 7.2)
    if k1 > 0:
        pen.text("strada", 960, 210 - 40 * k2, 104, a * (1 - 0.55 * k2), reveal=k1)
    if k2 > 0:
        pen.text("via strata", 960, 290, 84, a, reveal=k2)
        layers = [[(760 + i * 8, 322 + i * 14), (1160 - i * 8, 322 + i * 14)] for i in range(3)]
        pen.lines(layers, win(t, 7.4, 9.0), vanish, 0.75, 0.8, seed=21)
    # cousins: street, Straße
    k3 = win(t, 10.5, 11.6)
    if k3 > 0:
        pen.text("street", 560, 420, 64, a * 0.9, reveal=k3)
        pen.text("Straße", 1360, 420, 64, a * 0.9, reveal=win(t, 11.4, 12.5))
        pen.lines([[(840, 340), (640, 380)], [(1080, 340), (1280, 380)]], win(t, 10.8, 12.0), vanish, 0.5, 0.7,
                  seed=22)
    # traveller and mule walk in, stop, greet, then point down the road
    walk_in = ease_out(win(t, 3.0, 9.0), 2)
    stop = win(t, 8.6, 9.4)
    x = lerp(-300, 860, walk_in)
    w = 1.0 - stop if t < 9.4 else 0.0
    if t > 15.0:                      # set off again toward the right
        go = ease_io(win(t, 15.5, T))
        x += go * 900
        w = 1.0 if 15.5 < t else 0.0
    greet = smooth(win(t, 9.2, 9.8)) * (1 - smooth(win(t, 11.8, 12.4)))
    point = smooth(win(t, 13.0, 13.6)) * (1 - smooth(win(t, 15.2, 15.6)))
    ya = ROAD_Y + 10 * math.sin(x / 300.0)
    alpha = clamp(win(t, 2.6, 3.6)) * a
    mulo(pen, x - 300, ROAD_Y + 10 * math.sin((x - 300) / 300.0), 1.1, t, walk=w, ear=0.3 + 0.5 * greet,
         alpha=alpha)
    omino(pen, x, ya, 1.25, t, "viandante", walk=w, expr="smile" if greet > 0.2 else ("talk" if point > 0.3 else "calm"),
          arm_f=(lerp(DOWN - 0.35, -1.2, greet), lerp(0.4, -1.6 + 0.3 * math.sin(t * 8), greet)) if greet > 0.01
          else ((lerp(DOWN - 0.35, -0.25, point), lerp(0.4, -0.2, point)) if point > 0.01 else None),
          hold=None if (greet > 0.01 or point > 0.01) else "staff", alpha=alpha, look=point)
    return road


@scena("fango")
def fango(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    # a wobbly, rutted track instead of a road
    road = [(x, ROAD_Y + 14 * math.sin(x / 90.0) + 9 * math.sin(x / 37.0 + 1)) for x in range(-60, W + 61, 30)]
    # rain (season 1) then dust (season 2)
    rain = 1 - win(t, 6.0, 7.0)
    if rain > 0:
        rng = random.Random(4)
        drops = []
        for i in range(70):
            x0 = rng.uniform(0, W)
            y0 = (rng.uniform(0, H) + t * 520) % (ROAD_Y + 40)
            drops.append([(x0, y0), (x0 - 8, y0 + 26)])
        pen.lines(drops, appear, 0.0, 0.35 * rain * a, 0.6, seed=31)
    # puddles
    pud = [ellipse(x, ROAD_Y + 26, 70, 9, 24) for x in (520, 1180, 1500)]
    pen.lines(pud, appear, vanish, 0.6, 0.8, seed=32)
    # the cart stuck in the mud, traveller pulling, mule unimpressed
    sink = 6 * math.sin(t * 1.6)
    cx = 760
    wheel = ellipse(cx, ROAD_Y - 30 + sink * 0.2, 46, 46, 30)
    spokes = [[(cx, ROAD_Y - 30), (cx + 46 * math.cos(k * math.pi / 3 + 0.2), ROAD_Y - 30 + 46 * math.sin(k * math.pi / 3 + 0.2))]
              for k in range(3)]
    bed = [{"p": [(cx - 120, ROAD_Y - 70), (cx + 120, ROAD_Y - 74), (cx + 112, ROAD_Y - 120), (cx - 112, ROAD_Y - 116),
                  (cx - 120, ROAD_Y - 70)], "smooth": False},
           {"p": [(cx - 110, ROAD_Y - 100), (cx + 110, ROAD_Y - 103)], "smooth": False, "w": 0.6, "a": 0.7}]
    pen.lines([wheel] + spokes + bed, appear, vanish, 1.0, 1.0, seed=33)
    pen.lines([[(cx - 140, ROAD_Y - 14), (cx - 90, ROAD_Y - 2), (cx - 40, ROAD_Y - 10)],
               [(cx + 40, ROAD_Y - 8), (cx + 100, ROAD_Y), (cx + 150, ROAD_Y - 12)]], appear, vanish, 0.6, 0.8, seed=34)
    tug = 0.5 + 0.5 * math.sin(t * 2.2)
    al = smooth(win(t, 0.6, 1.6)) * a
    mulo(pen, 1380, ROAD_Y + 6, 1.05, t, walk=0.0, ear=-0.8, alpha=al, load=False)
    omino(pen, 1110 + tug * 10, ROAD_Y + 6, 1.15, t, "viandante", lean=0.35 + 0.1 * tug, expr="worry",
          arm_f=(-0.2, -0.1), arm_b=(0.2, 0.1), alpha=al, seed=2)
    pen.lines([[(1170 + tug * 10, ROAD_Y - 190), (1300, ROAD_Y - 160), (1440, ROAD_Y - 170)]], appear, vanish, 0.7,
              0.8, seed=35)                          # the rope
    pen.lines([[(cx + 120, ROAD_Y - 96), (1080 + tug * 10, ROAD_Y - 190)]], appear, vanish, 0.7, 0.8, seed=36)
    # Etruscan cut passage, faintly, at the left
    k = win(t, 6.5, 9.0)
    if k > 0:
        rock = [[(-20, 560), (80, 520), (170, 540), (200, 620), (210, ROAD_Y)],
                [(400, ROAD_Y), (410, 610), (450, 530), (560, 510), (660, 560)]]
        pen.lines(rock, k, vanish, 0.75, 1.0, seed=37)
        pen.lines([[(30, 600), (150, 590)], [(60, 660), (190, 670)], [(430, 640), (560, 630)], [(420, 700), (600, 690)]],
                  k, vanish, 0.4, 0.7, seed=38)
        pen.text("vie cave etrusche", 300, 470, 40, k * a * 0.8)
    # scattered villages, not connected: a question of a network
    k = win(t, 10.0, 12.0)
    if k > 0:
        for j, (vx, vy) in enumerate([(380, 230), (960, 160), (1560, 250)]):
            house = [{"p": [(vx - 40, vy + 30), (vx - 40, vy), (vx, vy - 26), (vx + 40, vy), (vx + 40, vy + 30), (vx - 40, vy + 30)],
                      "smooth": False},
                     {"p": [(vx - 10, vy + 30), (vx - 10, vy + 12), (vx + 8, vy + 12), (vx + 8, vy + 30)], "smooth": False}]
            pen.lines(house, clamp(k * 1.5 - j * 0.25), vanish, 0.8, 0.9, seed=40 + j)
        q = win(t, 12.5, 13.5)
        if q > 0:
            pen.text("?", 670, 230, 72, q * a * 0.8)
            pen.text("?", 1260, 230, 72, q * a * 0.8)
    return road
