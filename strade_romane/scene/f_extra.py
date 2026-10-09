"""b07p pompei · b11o orazio"""
import math
import random

from motore.film import scena
from motore.linea import H, W, arc, at, clamp, ease_io, ease_out, ellipse, lerp, smooth, wave, win
from motore.omino import DOWN, omino
from motore.personaggi import mulo

ROAD_Y = 790


def _box(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]


def _rbox(cx, cy, w, h, r=10, n=6):
    pts = []
    for (qx, qy, a0) in ((cx + w / 2 - r, cy - h / 2 + r, -math.pi / 2), (cx + w / 2 - r, cy + h / 2 - r, 0.0),
                         (cx - w / 2 + r, cy + h / 2 - r, math.pi / 2), (cx - w / 2 + r, cy - h / 2 + r, math.pi)):
        for k in range(n + 1):
            a = a0 + (math.pi / 2) * k / n
            pts.append((qx + math.cos(a) * r, qy + math.sin(a) * r))
    return pts + [pts[0]]


def _hard(pts, w=1.0, a=1.0):
    return {"p": pts, "smooth": False, "w": w, "a": a}


@scena("pompei")
def pompei(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    y_top, y_bot = 440, 800          # sidewalks of the street (plan view)
    ruts_y = (570, 670)              # the two wheel grooves
    k_plan = win(t, 6.0, 9.0)
    # the film's road line: horizon -> the upper wheel groove
    kr = smooth(win(t, 6.0, 9.5))
    road = [(x, lerp(ROAD_Y, ruts_y[0], kr)) for x in range(-60, W + 61, 60)]
    # --- 1. establishing: Pompeii under Vesuvius
    k_city = win(t, 0.0, 2.5) * (1 - smooth(win(t, 6.0, 7.5)))
    if k_city > 0:
        pen.lines([[(1000, ROAD_Y), (1180, 560), (1260, 500), (1320, 520), (1380, 492), (1460, 560), (1720, ROAD_Y)]],
                  k_city, 0.0, 0.55 * a, 0.9, seed=401)
        pen.lines([[(1320 + 10 * math.sin(t * 0.8 + k), 480 - k * 26) for k in range(7)]], k_city, 0.0, 0.25 * a, 0.7,
                  seed=402)
        houses = []
        for i, (x, h) in enumerate([(300, 120), (470, 150), (640, 110), (820, 140)]):
            top = ROAD_Y - h
            houses += [_hard(_box(x - 70, top, x + 70, ROAD_Y)), _hard([(x - 82, top), (x, top - 44), (x + 82, top)]),
                       _hard([(x - 18, ROAD_Y), (x - 18, ROAD_Y - 52), (x + 18, ROAD_Y - 52), (x + 18, ROAD_Y)], 0.8)]
            if i == 1:   # a little colonnade
                houses += [_hard([(x - 50 + 25 * c, top + 20), (x - 50 + 25 * c, ROAD_Y - 60)], 0.6, 0.8) for c in range(5)]
        pen.lines(houses, k_city, 0.0, 0.85 * a, 1.0, seed=403)
        pen.text("Pompei", 560, 520, 84, k_city * a, reveal=win(t, 1.5, 3.0))
    # --- 2. plan view of a street
    if k_plan > 0:
        curbs = [_hard([(-40, y_top), (W + 40, y_top)]), _hard([(-40, y_bot), (W + 40, y_bot)])]
        curbs += [_hard([(x, y_top - 22), (x, y_top)], 0.5, 0.6) for x in range(0, W + 1, 70)]
        curbs += [_hard([(x, y_bot), (x, y_bot + 22)], 0.5, 0.6) for x in range(30, W + 1, 70)]
        pen.lines(curbs, k_plan, vanish, 0.9, 1.0, seed=410)
        rng = random.Random(41)
        paving = []
        for i in range(60):
            cx, cy = rng.uniform(40, W - 40), rng.uniform(y_top + 30, y_bot - 30)
            if any(abs(cy - ry) < 26 for ry in ruts_y):
                continue
            r = rng.uniform(24, 36)
            n = rng.randint(5, 7)
            ph = rng.uniform(0, 6.28)
            paving.append([(cx + math.cos(ph + 2 * math.pi * j / n) * r, cy + math.sin(ph + 2 * math.pi * j / n) * r * 0.8)
                           for j in range(n + 1)])
        pen.lines(paving, win(t, 7.0, 10.0), vanish, 0.16, 0.6, seed=411)
        pen.text("una strada di Pompei, vista dall'alto", 960, y_bot + 80, 40, a * 0.7 * win(t, 8.0, 9.5),
                 reveal=win(t, 8.0, 9.5))
    # the second groove (the first one is the film's road line), on "solchi"
    k_rut = win(t, 9.5, 12.0)
    if k_rut > 0:
        pen.line([(-40, ruts_y[1]), (W + 40, ruts_y[1])], 1.15, a, k_rut, vanish, smooth_=False, seed=421)
        for ry in ruts_y:
            pen.line([(-40, ry + 9), (W + 40, ry + 9)], 0.5, a * 0.5, k_rut, vanish, smooth_=False, seed=423 + ry)
        pen.text("solchi delle ruote", 330, ruts_y[0] - 26, 44, a * win(t, 11.0, 12.0), reveal=win(t, 11.0, 12.5))
    # stepping stones across the street, on "grandi pietre in fila"
    k_st = win(t, 14.0, 16.0)
    sx = 1180
    stone_y = [505, 620, 735]
    if k_st > 0:
        pen.lines([_rbox(sx, y, 96, 74 if y != 620 else 62, 18) for y in stone_y], k_st, vanish, a, 1.2, seed=430)
        pen.text("pietre per attraversare", sx + 330, 470, 40, a * win(t, 15.0, 16.0), reveal=win(t, 15.0, 16.5))
    # rainwater fills the street, on "acqua piovana"
    k_w = win(t, 20.0, 23.0) * (1 - win(t, T - 4.0, T - 2.0))
    if k_w > 0:
        waves = [[(x, y_top + 34 + i * 44 + 5 * math.sin(x / 40.0 + t * 2 + i)) for x in range(-40, W + 41, 30)]
                 for i in range(8)]
        pen.lines(waves, k_w, 0.0, 0.25 * a, 0.6, seed=440)
    # side-view inset above the street: someone hopping across, feet dry
    k_in = win(t, 16.5, 18.0) * (1 - win(t, T - 5.0, T - 3.5))
    if k_in > 0:
        cx, cy, R = 1500, 225, 160
        pen.line(ellipse(cx, cy, R, R, 48), 0.9, a * k_in, seed=450)
        ctx = pen.ctx
        ctx.save()
        ctx.arc(cx, cy, R - 4, 0, 2 * math.pi)
        ctx.clip()
        wy = cy + 70
        pen.line([(x, wy + 4 * math.sin(x / 18.0 + t * 3)) for x in range(int(cx - R), int(cx + R) + 1, 12)], 0.7,
                 0.7 * a * k_in * smooth(win(t, 18.0, 20.0)), seed=451)
        for j, x0 in enumerate((cx - 80, cx, cx + 80)):
            pen.line(_box(x0 - 26, wy - 26, x0 + 26, wy + 70), 1.0, a * k_in, smooth_=False, seed=452 + j)
        hop = (t * 0.9) % 3.0
        j = min(2, int(hop))
        f = hop - j
        px = lerp(cx - 80 + 80 * j, cx - 80 + 80 * min(2, j + 1), smooth(f)) if j < 2 else cx + 80
        py = wy - 26 - math.sin(min(1.0, f) * math.pi) * 40 * (j < 2)
        omino(pen, px, py, 0.34, t, "operaio", expr="smile", alpha=a * k_in, seed=9, arm_f=(-0.6, -0.9),
              arm_b=(DOWN + 0.8, DOWN + 0.5))
        ctx.restore()
        pen.text("piedi asciutti!", cx - 330, cy + 20, 42, a * k_in, reveal=win(t, 17.5, 18.8))
    # a cart seen from above: wheels in the grooves, through the gaps, on "Le ruote passavano"
    k_cart = win(t, 24.0, T - 1.0)
    if k_cart > 0:
        x = lerp(-320, W + 320, ease_io(k_cart))
        parts = [_hard(_box(x - 130, 585, x + 130, 655))]
        parts += [_rbox(x + dx, ry, 76, 16, 6) for dx in (-70, 70) for ry in ruts_y]
        parts += [_hard([(x + dx, ruts_y[0]), (x + dx, ruts_y[1])], 0.8) for dx in (-70, 70)]
        parts += [_hard([(x + 130, 600), (x + 280, 606)]), _hard([(x + 130, 640), (x + 280, 634)])]
        pen.lines(parts, 1.0, vanish, a, 1.0, seed=460)
        if abs(x - sx) < 300:
            g = 1 - abs(x - sx) / 300
            for ry in ruts_y:
                pen.line([(sx - 120, ry - 30), (sx - 70, ry - 6)], 0.7, a * g, seed=470 + ry)
                pen.line([(sx - 70, ry - 6), (sx - 84, ry - 20)], 0.7, a * g, seed=472 + ry)
    return road


@scena("orazio")
def orazio(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    road = [(x, ROAD_Y) for x in range(-60, W + 61, 60)]
    poet = dict(costume="toga", expr="talk", seed=21)
    # --- 1. the diary: a page writes itself
    k_d = win(t, 0.4, 2.0) * (1 - smooth(win(t, 5.0, 6.2)))
    if k_d > 0:
        page = _hard(_box(700, 160, 1220, 600))
        lines = [[(760, 260 + i * 46), (1160 - (i % 3) * 60, 260 + i * 46)] for i in range(7)]
        pen.lines([page], k_d, 0.0, 0.9 * a, 1.0, seed=501)
        pen.text("Iter Brundisinum", 960, 230, 52, k_d * a, reveal=win(t, 1.2, 2.6))
        for i, l in enumerate(lines):
            pen.line([(p[0], p[1] + 4 * math.sin(p[0] / 25.0)) for p in [l[0], ((l[0][0] + l[1][0]) / 2, l[0][1]), l[1]]],
                     0.6, 0.7 * a * k_d, reveal=win(t, 1.8 + i * 0.35, 2.4 + i * 0.35), seed=502 + i)
    # --- 2. the trip: Roma -> Brindisi with a day counter, the poet walking
    k_trip = win(t, 5.0, 6.5) * (1 - smooth(win(t, 15.5, 17.0)))
    if k_trip > 0:
        mini = [(260, 200), (700, 230), (1100, 210), (1600, 240)]
        pen.line(mini, 0.8, 0.7 * a * k_trip, reveal=win(t, 5.0, 7.0), seed=510)
        for (x, y), name in zip([mini[0], mini[-1]], ["Roma", "Brindisi"]):
            pen.dot(x, y, 5, a * k_trip)
            pen.text(name, x, y - 24, 38, a * k_trip, reveal=win(t, 5.5, 6.5))
        prog = ease_io(win(t, 7.0, 15.0))
        # dot along the mini route
        segs = [(mini[i], mini[i + 1]) for i in range(3)]
        u = prog * 3
        i = min(2, int(u))
        p = (lerp(segs[i][0][0], segs[i][1][0], u - i), lerp(segs[i][0][1], segs[i][1][1], u - i))
        pen.dot(p[0], p[1], 7, a * k_trip)
        day = 1 + int(prog * 14.999)
        pen.text(f"giorno {day}", 960, 330, 56, a * k_trip, reveal=win(t, 7.0, 7.8))
        pen.text("37 a.C.", 300, 330, 44, a * k_trip * 0.8, reveal=win(t, 6.0, 7.0))
        x = lerp(200, 1300, prog)
        omino(pen, x, ROAD_Y, 1.1, t, walk=1.0, alpha=a * k_trip, hold="scroll",
              **dict(poet, expr="smile" if t < 11.5 else "worry"))
        # bad water, crowded inn, rude innkeeper (on "acqua pessima, locande...")
        k_inn = win(t, 12.0, 13.0)
        if k_inn > 0:
            ix = 1560
            inn = [_hard(_box(ix - 150, 560, ix + 150, ROAD_Y)), _hard([(ix - 170, 560), (ix, 470), (ix + 170, 560)]),
                   _hard([(ix - 40, ROAD_Y), (ix - 40, 680), (ix + 40, 680), (ix + 40, ROAD_Y)])]
            pen.lines(inn, k_inn, 0.0, 0.75 * a * k_trip, 1.0, seed=520)
            pen.text("caupona", ix, 620, 40, a * k_trip * k_inn, reveal=k_inn)
            omino(pen, ix + 210, ROAD_Y, 0.9, t, "operaio", fx=-1, expr="determined", alpha=a * k_trip * k_inn,
                  arm_f=(-0.4, -0.8), seed=31, talk=True)
            pen.text("bleah!", x + 80, ROAD_Y - 380, 44, a * k_trip * win(t, 12.2, 12.8), reveal=win(t, 12.2, 12.8))
    # --- 3. night on the canal: barge towed by the mule, frogs and mosquitoes
    k_n = win(t, 16.0, 18.0)
    if k_n > 0:
        kk = k_n * a
        pen.ctx.save()
        pen.ctx.translate(960, 620)
        pen.ctx.scale(1.45, 1.45)
        pen.ctx.translate(-1060, -700)
        z0 = pen.zoom
        pen.zoom = z0 * 1.45
        moon = arc(1620, 170, 46, math.radians(-60), math.radians(200), 24)
        pen.line(moon, 0.9, kk, seed=530)
        pen.line(arc(1645, 160, 40, math.radians(-40), math.radians(180), 20), 0.7, kk * 0.8, seed=531)
        wy = ROAD_Y + 10
        water = [[(x, wy + 18 + i * 22 + 4 * math.sin(x / 50.0 + t * 1.5 + i)) for x in range(-40, W + 41, 40)]
                 for i in range(3)]
        pen.lines(water, k_n, 0.0, 0.35 * a, 0.6, seed=532)
        bank = [(x, wy - 120) for x in range(-40, W + 41, 60)]
        pen.line(bank, 0.8, 0.7 * kk, seed=533)
        drift = (t - 16.0) * 30
        bx = 760 + drift * 0.5
        barge = [(bx - 230, wy - 10), (bx - 200, wy + 34), (bx + 200, wy + 34), (bx + 240, wy - 14)]
        pen.line(barge, 1.1, kk, seed=534)
        # the sleepless poet lying in the barge, eyes wide open
        with at(pen, bx - 60, wy - 6, 1.0, -1.45):
            omino(pen, 0, 0, 0.7, t, "toga", expr="surprise" if (t % 3.0) < 1.5 else "worry", alpha=kk, seed=22,
                  arm_f=(DOWN, DOWN), blink=False)
        # the mule on the bank towing the barge
        mulo(pen, bx + 620, wy - 120, 0.85, t, walk=1.0, ear=-0.3, alpha=kk, load=False, speed=0.5)
        pen.line([(bx + 230, wy - 20), (bx + 420, wy - 90), (bx + 700, wy - 230)], 0.6, 0.8 * kk, seed=535)
        # mosquitoes buzzing around the poet's head
        for i in range(5):
            mx = bx - 40 + 70 * math.sin(t * (2.3 + i * 0.4) + i)
            my = wy - 200 + 40 * math.cos(t * (3.1 + i * 0.3) + i * 2)
            pen.line([(mx - 7, my), (mx - 3, my - 5), (mx, my), (mx + 3, my - 5), (mx + 7, my)], 0.6, kk, seed=540 + i)
            pen.dot(mx, my + 2, 1.8, kk)
        # frogs on lily pads: "cra!"
        for i, fx in enumerate((300, 1250, 1500)):
            pad = ellipse(fx, wy + 30, 46, 10, 18)
            pen.line(pad, 0.7, kk * 0.8, seed=550 + i)
            frog = [(fx - 22, wy + 26), (fx - 18, wy + 4), (fx, wy - 4), (fx + 18, wy + 4), (fx + 22, wy + 26)]
            pen.line(frog, 0.9, kk, seed=560 + i)
            pen.dot(fx - 7, wy + 2, 3, kk)
            pen.dot(fx + 7, wy + 2, 3, kk)
            if (t * 1.3 + i * 0.7) % 2.0 < 0.8:
                pen.text("cra!", fx + 10, wy - 40, 40, kk, reveal=1.0)
        pen.text("zzz...?", bx - 60, wy - 290, 44, kk * win(t, 19.0, 20.0) * 0.8, reveal=win(t, 19.0, 20.0))
        pen.zoom = z0
        pen.ctx.restore()
        yy = 620 + (wy - 700) * 1.45
        road = [(x, lerp(ROAD_Y, yy, smooth(k_n))) for x in range(-60, W + 61, 60)]
    return road
