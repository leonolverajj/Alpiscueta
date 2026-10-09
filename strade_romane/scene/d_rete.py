"""b09 rete · b11 tabula · b12 ponti · b13 mondo

Map data: Natural Earth 1:50m coastline/land (public domain), simplified into assets/geo/.
Cities are placed at their real coordinates (lon, lat); roads follow their main historical stations.
"""
import json
import math
import os
import random

import cairo
import numpy as np

from motore.film import scena
from motore.linea import (H, W, arc, at, back, catmull, clamp, ease_in, ease_io, ease_out, ellipse, lerp, lerp2, morph,
                          resample, smooth, wave, win)
from motore.omino import DOWN, omino
from motore.personaggi import mulo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEO = os.path.join(ROOT, "assets", "geo")


def _load(name):
    with open(os.path.join(GEO, name), encoding="utf-8") as fh:
        return json.load(fh)


COSTE = [np.array(c, dtype=float) for c in _load("coste_50m.json")]
COSTE_BB = [(c[:, 0].min(), c[:, 1].min(), c[:, 0].max(), c[:, 1].max()) for c in COSTE]
TERRE = [np.array(c, dtype=float) for c in _load("terre_50m.json")]


# =====================================================================================  geography
CITTA = {
    "Roma": (12.49, 41.89), "Capua": (14.25, 41.08), "Benevento": (14.78, 41.13), "Taranto": (17.24, 40.47),
    "Brindisi": (17.94, 40.64), "Rimini": (12.57, 44.06), "Pisa": (10.40, 43.72), "Genova": (8.93, 44.41),
    "Bologna": (11.34, 44.49), "Piacenza": (9.69, 45.05), "Nîmes": (4.36, 43.84), "Narbona": (3.00, 43.18),
    "Durazzo": (19.45, 41.32), "Salonicco": (22.94, 40.64), "Bisanzio": (28.98, 41.01),
}

# main stations of each road (lon, lat)
VIE = {
    "Appia": [(12.49, 41.89), (12.67, 41.72), (13.04, 41.45), (13.25, 41.30), (13.43, 41.36), (13.61, 41.27),
              (13.77, 41.25), (13.88, 41.17), (14.25, 41.08), (14.78, 41.13), (15.01, 41.06), (15.81, 40.96),
              (16.42, 40.82), (17.24, 40.49), (17.64, 40.50), (17.94, 40.64)],
    "Flaminia": [(12.49, 41.89), (12.48, 42.42), (12.52, 42.52), (12.56, 42.64), (12.61, 42.93), (12.79, 43.11),
                 (12.78, 43.23), (12.67, 43.40), (12.65, 43.55), (12.71, 43.64), (12.81, 43.69), (12.95, 43.79),
                 (12.84, 43.87), (12.57, 44.04)],
    "Aurelia": [(12.49, 41.89), (12.20, 42.00), (12.03, 42.08), (11.88, 42.17), (11.80, 42.29), (11.58, 42.45),
                (11.36, 42.50), (11.22, 42.66), (11.13, 42.84), (10.90, 43.07), (10.60, 43.38), (10.53, 43.56),
                (10.43, 43.72), (10.12, 44.10), (9.78, 44.23), (9.47, 44.36), (9.18, 44.45), (8.93, 44.43)],
    "Emilia": [(12.57, 44.06), (12.24, 44.14), (12.04, 44.22), (11.88, 44.29), (11.71, 44.35), (11.34, 44.49),
               (10.93, 44.65), (10.63, 44.70), (10.33, 44.80), (10.06, 44.87), (9.69, 45.05)],
    "Domizia": [(6.75, 44.93), (6.64, 44.90), (6.50, 44.57), (6.08, 44.56), (5.94, 44.20), (5.40, 43.88),
                (5.04, 43.84), (4.64, 43.81), (4.36, 43.84), (3.88, 43.63), (3.22, 43.34), (3.00, 43.18),
                (2.93, 42.72), (2.86, 42.47)],
    "Egnatia": [(19.45, 41.32), (20.08, 41.11), (20.80, 41.12), (21.34, 41.01), (22.05, 40.80), (22.52, 40.76),
                (22.94, 40.64), (23.85, 40.82), (24.29, 41.01), (25.10, 41.02), (25.84, 40.95), (26.40, 40.93),
                (27.20, 40.99), (27.96, 40.99), (28.98, 41.01)],
}
MARE_EGNATIA = [(17.94, 40.64), (18.70, 41.02), (19.45, 41.32)]   # Brindisi -> Durazzo, by sea
ALPI = [(6.95, 44.25), (6.85, 44.85), (7.05, 45.45), (7.75, 45.92), (8.55, 46.30), (9.40, 46.42), (10.30, 46.45),
        (11.10, 46.62), (11.95, 46.62), (12.80, 46.48), (13.60, 46.30)]

C42 = math.cos(math.radians(42.0))


class Vista:
    """Equirectangular camera: (lon0, lat0) at screen (cx, cy), k px per degree of latitude."""

    def __init__(self, lon0, lat0, k, cx=W / 2, cy=H / 2, c=C42):
        self.lon0, self.lat0, self.k, self.cx, self.cy, self.c = lon0, lat0, k, cx, cy, c

    def __call__(self, lon, lat):
        return (self.cx + (lon - self.lon0) * self.k * self.c, self.cy - (lat - self.lat0) * self.k)

    def pts(self, ll):
        return [self(lo, la) for lo, la in ll]

    def arr(self, a):
        return np.column_stack((self.cx + (a[:, 0] - self.lon0) * self.k * self.c, self.cy - (a[:, 1] - self.lat0) * self.k))

    def bbox(self, m=0):
        lo0 = self.lon0 + (-m - self.cx) / (self.k * self.c)
        lo1 = self.lon0 + (W + m - self.cx) / (self.k * self.c)
        la1 = self.lat0 + (self.cy + m) / self.k
        la0 = self.lat0 - (H + m - self.cy) / self.k
        return lo0, la0, lo1, la1


def vista_mix(A, B, u):
    u = clamp(u)
    k = math.exp(lerp(math.log(A.k), math.log(B.k), u))
    # keep the motion feeling like a camera: interpolate the screen position of a fixed geographic anchor
    return Vista(lerp(A.lon0, B.lon0, u), lerp(A.lat0, B.lat0, u), k, lerp(A.cx, B.cx, u), lerp(A.cy, B.cy, u),
                 lerp(A.c, B.c, u))


def runs_inside(xy, m=40):
    """Split a projected polyline (Nx2 array) into the runs that are on screen (with one point of slack)."""
    x, y = xy[:, 0], xy[:, 1]
    ins = (x > -m) & (x < W + m) & (y > -m) & (y < H + m)
    if ins.all():
        return [xy]
    if not ins.any():
        return []
    out = []
    idx = np.flatnonzero(ins)
    # group consecutive indices
    br = np.flatnonzero(np.diff(idx) > 1)
    starts = np.concatenate(([idx[0]], idx[br + 1]))
    ends = np.concatenate((idx[br], [idx[-1]]))
    n = len(xy)
    for s, e in zip(starts, ends):
        s, e = max(0, s - 1), min(n - 1, e + 1)
        if e - s >= 1:
            out.append(xy[s:e + 1])
    return out


def coste(pen, v, reveal=1.0, start=0.0, alpha=0.5, w=0.7, seed=500):
    lo0, la0, lo1, la1 = v.bbox(60)
    for i, (c, bb) in enumerate(zip(COSTE, COSTE_BB)):
        if bb[2] < lo0 or bb[0] > lo1 or bb[3] < la0 or bb[1] > la1:
            continue
        for r in runs_inside(v.arr(c)):
            pen.line(r.tolist(), w, alpha, reveal, start, smooth_=False, seed=seed + i)


def frac_along(ll):
    """Cumulative length fraction at each vertex of a lon/lat polyline (in projected units)."""
    d = [0.0]
    for (a, b), (c, e) in zip(ll, ll[1:]):
        d.append(d[-1] + math.hypot((c - a) * C42, e - b))
    return [x / d[-1] for x in d]


def dashed(pen, pts, alpha, reveal, start, w=0.8, dash=14, gap=10, seed=0):
    from motore.linea import length, trim
    P = catmull(pts) if len(pts) > 2 else pts
    L = length(P)
    n = max(1, int(L / (dash + gap)))
    for i in range(n):
        k0 = i / n
        k1 = k0 + dash / L
        if k0 < reveal and k1 > start:
            pen.line(trim(P, max(k0, start), min(k1, reveal)), w, alpha, seed=seed + i, taper=0.3)


def picco(x, y, s=1.0):
    """A little mountain: one peak with a smaller one leaning on it."""
    return [[(x - 16 * s, y + 6 * s), (x - 2 * s, y - 12 * s), (x + 5 * s, y - 4 * s), (x + 9 * s, y - 8 * s),
             (x + 20 * s, y + 6 * s)]]


def offset_line(pts, d):
    """Polyline offset sideways by d px (positive = to the right of the direction of travel, on screen)."""
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1.0
        out.append((pts[i][0] - dy / L * d, pts[i][1] + dx / L * d))
    return out


# =====================================================================================  b09 rete
V_ITALIA = Vista(12.6, 42.0, 104.0)
V_MEDIT = Vista(15.6, 42.55, 73.0)

# road: draw-on window (s)
RETE_VIE = [
    ("Flaminia", 4.7, 6.6), ("Aurelia", 6.7, 8.8), ("Emilia", 9.0, 10.9), ("Domizia", 16.2, 18.2),
    ("Egnatia", 19.0, 20.6),
]
# road name: anchor (lon, lat), offset px, size
RETE_LABEL = {
    "Appia": ((15.4, 40.6), (8, 54), 52),
    "Flaminia": ((12.85, 42.95), (82, -6), 48),
    "Aurelia": ((11.05, 42.62), (-92, 4), 48),
    "Emilia": ((10.75, 44.70), (-24, -44), 48),
    "Domizia": ((4.9, 43.98), (-10, -56), 44),
    "Egnatia": ((24.6, 41.0), (0, -36), 44),
}
# city -> (time it appears, label offset, size, keeps label after zoom-out)
RETE_CITTA = {
    "Roma": (1.6, (-30, 42), 48, True), "Capua": (2.5, (-38, 38), 30, False),
    "Benevento": (2.9, (30, -20), 30, False), "Taranto": (3.6, (-16, 42), 30, False),
    "Brindisi": (4.0, (24, -20), 30, True), "Rimini": (6.4, (44, -10), 32, True),
    "Pisa": (8.0, (-46, 12), 32, False), "Genova": (8.6, (-14, -24), 32, True),
    "Bologna": (10.1, (18, -22), 30, False), "Piacenza": (10.8, (-54, -14), 30, False),
    "Nîmes": (17.1, (8, 38), 30, True), "Narbona": (17.7, (-34, 34), 30, True),
    "Durazzo": (19.1, (-14, -22), 30, True), "Salonicco": (19.8, (6, 40), 30, True),
    "Bisanzio": (20.5, (6, -22), 32, True),
}


@scena("rete")
def rete(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    zo = ease_io(win(t, 13.6, 16.6))          # 0 = Italy, 1 = Mediterranean
    v = vista_mix(V_ITALIA, V_MEDIT, zo)
    # coastlines
    coste(pen, v, smooth(win(t, 0.0, 2.6)), vanish, 0.42, 0.7)
    # the sea's name, faint
    if t > 7.2:
        x, y = v(11.75, 39.75)
        pen.text("mar Tirreno", x, y, 36, 0.4 * a * smooth(win(t, 7.2, 8.4)) * (1 - 0.4 * zo), reveal=win(t, 7.2, 8.6))
    # the Alps, a chain of little peaks, when we go "beyond the Alps"
    if t > 14.0:
        strokes = []
        for lo, la in ALPI:
            strokes += picco(*v(lo, la), 0.95)
        pen.lines(strokes, win(t, 14.0, 16.0), vanish, 0.5, 0.75, seed=880)
    # roads drawing on
    for name, t0, t1 in RETE_VIE:
        if t < t0:
            continue
        pen.line(v.pts(VIE[name]), 1.0, 0.95, ease_io(win(t, t0, t1)), vanish, seed=600 + len(name))
    # the sea crossing Brindisi -> Durazzo
    if t > 18.5:
        dashed(pen, v.pts(MARE_EGNATIA), 0.7 * a, ease_io(win(t, 18.5, 19.1)), vanish, 0.7, 10, 9, seed=640)
    # road names
    for name, ((lo, la), (dx, dy), sz) in RETE_LABEL.items():
        t0 = 2.0 if name == "Appia" else next(r[1] for r in RETE_VIE if r[0] == name) + 0.5
        if t < t0:
            continue
        x, y = v(lo, la)
        pen.text(name, x + dx, y + dy, sz, a * smooth(win(t, t0, t0 + 0.5)), reveal=win(t, t0, t0 + 0.9))
    # Emilia -> Emilia-Romagna: a soft bracket under the road, and the region's name written along it
    if t > 11.4:
        k = ease_io(win(t, 11.4, 12.4))
        fade = a * (1 - smooth(win(zo, 0.0, 0.6)))
        em = v.pts(VIE["Emilia"])[::-1]                  # Piacenza -> Rimini
        br = offset_line(catmull(em, n=6), 24)
        pen.line(br, 0.6, 0.6 * fade, k, vanish, seed=650)
        mid = br[len(br) // 2]
        p0, p1 = br[0], br[-1]
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        if t > 11.9:
            with at(pen, mid[0] - math.sin(ang) * 34, mid[1] + math.cos(ang) * 34, 1.0, ang):
                pen.text("Emilia-Romagna", 0, 0, 32, 0.8 * fade * smooth(win(t, 11.9, 12.5)), reveal=win(t, 11.9, 13.0))
    # cities
    for name, (t0, (dx, dy), sz, keep) in RETE_CITTA.items():
        if t < t0:
            continue
        x, y = v(*CITTA[name])
        k = back(win(t, t0, t0 + 0.45))
        r = (6.5 if name == "Roma" else 4.6) * k
        pen.dot(x, y, r, a)
        if name == "Roma":
            pen.line(ellipse(x, y, 13 * k, 13 * k, 20), 0.7, 0.7 * a, seed=660, closed=True)
        fa = a * (1.0 if keep else 1 - zo)
        if fa > 0.01:
            pen.text(name, x + dx, y + dy, sz * (1 - 0.12 * zo), 0.8 * fa * smooth(win(t, t0, t0 + 0.4)),
                     reveal=win(t, t0 + 0.05, t0 + 0.7))
    # "→ Spagna" at the end of the Domitia
    if t > 17.9:
        x, y = v(2.86, 42.47)
        k = win(t, 17.9, 18.7)
        pen.line([(x - 6, y + 14), (x - 30, y + 46), (x - 70, y + 64)], 0.75, 0.7 * a, k, vanish, seed=670)
        pen.line([(x - 58, y + 52), (x - 72, y + 64), (x - 56, y + 72)], 0.75, 0.7 * a, win(t, 18.4, 18.7), vanish,
                 seed=671)
        pen.text("Spagna", x - 84, y + 82, 32, 0.7 * a * smooth(win(t, 18.3, 18.9)), align="right",
                 reveal=win(t, 18.3, 19.1))
    return [v(lo, la) for lo, la in resample(VIE["Appia"], 40)]


# =====================================================================================  b11 tabula
ROAD_Y = 790
SC_T, SC_B = 330, 606            # scroll strip top / bottom
SC_L, SC_R = 112, 1420           # left roller (fully unrolled) / right roller
SC_RD = 468                      # the main road on the scroll


def ry_rotolo(x):
    return SC_RD + 9 * math.sin((x - SC_L) / 118.0) + 5 * math.sin((x - SC_L) / 41.0 + 1.0)


def strada_rotolo(x0=SC_L, x1=SC_R - 13):
    xs = list(np.linspace(x0, x1, max(2, int((x1 - x0) / 22) + 1)))
    return [(x, ry_rotolo(x)) for x in xs]


def torri(x, y, s=1.0):
    """Two little towers with pointed roofs joined by a wall: a stylised town vignette."""
    return [[(x - 12 * s, y), (x - 12 * s, y - 20 * s), (x - 7 * s, y - 27 * s), (x - 2 * s, y - 20 * s),
             (x - 2 * s, y)],
            [(x + 4 * s, y), (x + 4 * s, y - 20 * s), (x + 9 * s, y - 27 * s), (x + 14 * s, y - 20 * s),
             (x + 14 * s, y)],
            [(x - 2 * s, y - 10 * s), (x + 4 * s, y - 10 * s)]]


ROMA_X = 770


def _contenuto_rotolo():
    rng = random.Random(21)
    big, light = [], []        # strokes at full ink / faint
    # two stretched "seas" as thin bands, top and bottom, with long thin islands
    for y0 in (SC_T + 22, SC_B - 34):
        for dy in (0, 14):
            big.append([(x, y0 + dy + 3 * math.sin(x / 70.0 + dy)) for x in range(SC_L + 14, SC_R - 13, 30)])
        for i in range(6):
            x = rng.uniform(SC_L + 60, SC_R - 80)
            light.append(ellipse(x, y0 + 7, rng.uniform(14, 34), 3.0, 14))
    # station hooks along the road and little town vignettes
    towns = []
    x = SC_L + 60
    while x < SC_R - 50:
        y = ry_rotolo(x)
        if abs(x - ROMA_X) > 50:
            big.append([(x - 6, y + 1), (x - 1, y - 9), (x + 7, y - 9)])
            if rng.random() < 0.45 and abs(x - ROMA_X) > 90:
                towns.append((x + 2, y - 14))
        x += rng.uniform(80, 118)
    # two secondary roads, one above and one below, linked to the main one
    up_y, dn_y = SC_RD - 52, SC_RD + 50

    def uy(x):
        return up_y + 6 * math.sin(x / 90.0)

    def dy_(x):
        return dn_y + 6 * math.sin(x / 77.0 + 2)
    light.append([(x, uy(x)) for x in range(SC_L + 14, SC_R - 13, 24)])
    light.append([(x, dy_(x)) for x in range(SC_L + 14, SC_R - 13, 24)])
    for x0 in (300, 560, 1010, 1240):
        light.append([(x0, uy(x0)), (x0 + 24, (uy(x0) + ry_rotolo(x0 + 48)) / 2), (x0 + 48, ry_rotolo(x0 + 48))])
    for x0 in (210, 640, 900, 1160):
        light.append([(x0, ry_rotolo(x0)), (x0 + 22, (ry_rotolo(x0) + dy_(x0 + 44)) / 2), (x0 + 44, dy_(x0 + 44))])
    # mountains: rows of soft humps between the top sea and the upper road
    for xs in (190, 430, 1000, 1190):
        for j in range(4):
            x = xs + j * 30
            light.append([(x - 16, SC_T + 74), (x - 6, SC_T + 62), (x + 6, SC_T + 61), (x + 16, SC_T + 74)])
    # rivers running from the top sea down to the bottom sea
    for x0 in (350, 1110):
        light.append([(x0 + 12 * math.sin(y / 28.0), y) for y in range(SC_T + 40, SC_B - 34, 10)])
    # Rome: a circle with an enthroned figure, roads radiating from it
    rx, ryy = ROMA_X, ry_rotolo(ROMA_X)
    rome = [ellipse(rx, ryy, 30, 30, 26), ellipse(rx, ryy - 9, 5.5, 5.5, 12),
            [(rx - 10, ryy + 15), (rx - 9, ryy + 1), (rx, ryy - 3), (rx + 9, ryy + 1), (rx + 10, ryy + 15)],
            [(rx - 14, ryy + 17), (rx + 14, ryy + 17)],
            [(rx - 6, ryy - 17), (rx - 3, ryy - 22), (rx, ryy - 18), (rx + 3, ryy - 22), (rx + 6, ryy - 17)]]
    for k in range(10):
        ang = -math.pi / 2 + k * 2 * math.pi / 10 + 0.2
        light.append([(rx + math.cos(ang) * 34, ryy + math.sin(ang) * 34),
                      (rx + math.cos(ang) * 62, ryy + math.sin(ang) * 46)])
    return big, light, towns, rome


ROT_BIG, ROT_LIGHT, ROT_TOWNS, ROT_ROMA = _contenuto_rotolo()


def rullo(pen, x, y0, y1, reveal, start, alpha, seed):
    r = 13
    strokes = [[(x - r, y0 - 6), (x - r, y1 + 6)], [(x + r, y0 - 6), (x + r, y1 + 6)],
               ellipse(x, y0 - 6, r, 5, 16), ellipse(x, y1 + 6, r, 5, 16),
               [(x, y0 - 11), (x, y0 - 26)], ellipse(x, y0 - 32, 6, 6, 12),
               [(x, y1 + 11), (x, y1 + 26)], ellipse(x, y1 + 32, 6, 6, 12)]
    pen.lines(strokes, reveal, start, alpha, 1.0, seed=seed)


def carretto(pen, x, y, alpha, reveal, start, t, seed=0):
    """A two-wheeled handcart with amphorae; (x, y) = wheel contact on the ground. Shaft points right."""
    r = 34
    ang = x / r
    wheel = ellipse(x, y - r, r, r, 26)
    spokes = [[(x + math.cos(ang + k * math.pi / 3) * r * 0.9, y - r + math.sin(ang + k * math.pi / 3) * r * 0.9),
               (x - math.cos(ang + k * math.pi / 3) * r * 0.9, y - r - math.sin(ang + k * math.pi / 3) * r * 0.9)]
              for k in range(3)]
    bed = [(x - 90, y - 52), (x + 70, y - 52), (x + 76, y - 76), (x - 96, y - 76), (x - 90, y - 52)]
    shaft = [(x + 72, y - 62), (x + 158, y - 128)]
    amph = []
    for j, ax in enumerate((-64, -28, 8, 42)):
        bob = math.sin(t * 6 + j) * 1.5
        b = [(x + ax - 3, y - 76), (x + ax - 12, y - 96 + bob), (x + ax - 10, y - 118 + bob),
             (x + ax - 4, y - 128 + bob), (x + ax - 4, y - 136 + bob), (x + ax + 4, y - 136 + bob),
             (x + ax + 4, y - 128 + bob), (x + ax + 10, y - 118 + bob), (x + ax + 12, y - 96 + bob), (x + ax + 3, y - 76)]
        amph.append(b)
    pen.lines([wheel] + spokes + [bed, shaft] + amph, reveal, start, alpha, 1.0, seed=seed)


def xf_rot(pts, a):
    s, c = math.sin(a), math.cos(a)
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


def fumetto(pen, x, y, k, alpha, kind, t, seed):
    """A small speech bubble with a doodle inside: 'news' (lines) or 'idea' (a little star)."""
    if k <= 0 or alpha <= 0.01:
        return
    s = back(k)
    with at(pen, x, y, s):
        body = ellipse(0, 0, 54, 34, 30)
        tail = [(-18, 28), (-30, 52), (-2, 32)]
        pen.line(body, 0.85, alpha, closed=True, seed=seed)
        pen.line(tail, 0.85, alpha, seed=seed + 1)
        if kind == "news":
            for j in range(3):
                pen.line([(-30, -12 + j * 12), (24 - j * 10, -12 + j * 12 + 1)], 0.6, alpha * 0.8, seed=seed + 3 + j)
        else:
            star = [(math.cos(-math.pi / 2 + i * 4 * math.pi / 5) * 16, math.sin(-math.pi / 2 + i * 4 * math.pi / 5) * 16)
                    for i in range(6)]
            pen.line(xf_rot(star, t * 0.6), 0.8, alpha, seed=seed + 3, smooth_=False)


ITINERARIO = [("Roma", ""), ("Aricia", "XVI"), ("Tres Tabernae", "XVII"), ("Forum Appii", "X"),
              ("Tarracina", "XVIII")]


def x_viandante(t):
    """The traveller walks in at a steady pace, then slows to a stop (no pops)."""
    v, t1, dec = 104.0, 7.0, 2.6
    if t < t1:
        return -230 + v * t
    tau = min(t - t1, dec)
    return -230 + v * t1 + v * (tau - tau * tau / (2 * dec))


@scena("tabula")
def tabula(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    ground = [(x, ROAD_Y + 6 * math.sin(x / 260.0)) for x in range(-60, W + 61, 40)]

    def gy(x):
        return ROAD_Y + 6 * math.sin(x / 260.0)

    # ---------------------------------------------------------------- part 1: the procession
    gone = smooth(win(t, 11.5, 12.9))           # procession fades
    if gone < 1:
        al = a * (1 - gone)
        v = 104.0

        def xs(x0):
            return x0 + v * t + 70 * max(0.0, t - 7.0) ** 1.6     # the others speed off after 7 s
        xt = x_viandante(t)
        wt = 1.0 - smooth(win(t, 8.8, 9.6))
        xm = xt - 330
        # the soldier
        x = xs(1120)
        omino(pen, x, gy(x), 0.95, t, "legionario", walk=1.0, expr="determined", alpha=al * smooth(win(t, 0.2, 1.4)),
              seed=3)
        # the merchant pulling his cart (cart behind him)
        x = xs(680)
        ka = al * smooth(win(t, 0.3, 1.5))
        carretto(pen, x - 236, gy(x - 236), ka, 1.0, 0.0, t, seed=710)
        omino(pen, x, gy(x), 0.92, t, "operaio", walk=1.0, lean=0.2, expr="smile", alpha=ka,
              arm_b=(DOWN + 0.75, DOWN + 0.95), seed=5, talk=5.0 < t < 6.6)
        fumetto(pen, x + 60, gy(x) - 350, win(t, 5.2, 5.8) * (1 - win(t, 7.6, 8.0)), al, "news", t, 720)
        # the pilgrim, with a staff
        x = xs(160)
        omino(pen, x, gy(x), 0.9, t, "agrimensore", walk=1.0, expr="calm", alpha=al * smooth(win(t, 0.4, 1.6)),
              hold="staff", seed=7)
        fumetto(pen, x + 70, gy(x) - 340, win(t, 5.9, 6.5) * (1 - win(t, 7.8, 8.2)), al, "idea", t, 730)
        # the traveller and the mule
        read = smooth(win(t, 9.2, 9.8))
        mulo(pen, xm, gy(xm), 0.95, t, walk=wt, ear=0.2 + 0.7 * smooth(win(t, 10.2, 10.8)),
             alpha=al * smooth(win(t, 0.5, 1.7)))
        omino(pen, xt, gy(xt), 1.05, t, "viandante", walk=wt, expr="squint" if read > 0.5 else "calm",
              look=0.4 * read, head_tilt=-0.12 * read,
              arm_f=(lerp(DOWN - 0.35, -0.1, read), lerp(0.4, -0.5, read)) if read > 0.01 else None,
              hold="scroll" if read > 0.5 else "staff", alpha=al * smooth(win(t, 0.5, 1.7)), seed=2)
        # the itinerary: a list of stops and distances, written on cue
        if t > 9.3:
            kc = ease_io(win(t, 9.3, 10.0))
            cx, cy = xt + 150, 236
            # a parchment sheet with curled ends, held up by its corner
            top = [(cx - 6, cy + 10), (cx + 120, cy + 4), (cx + 260, cy + 8), (cx + 390, cy + 2)]
            bot = [(cx + 6, cy + 326), (cx + 130, cy + 320), (cx + 270, cy + 328), (cx + 396, cy + 322)]
            sheet = [top, [top[-1], (cx + 393, cy + 160), bot[-1]], bot[::-1], [bot[0], (cx + 2, cy + 170), top[0]]]
            curls = [[(cx - 6, cy + 10), (cx - 14, cy - 4), (cx, cy - 12), (cx + 12, cy - 2), (cx + 6, cy + 8)],
                     [(cx + 396, cy + 322), (cx + 406, cy + 336), (cx + 392, cy + 344), (cx + 380, cy + 334)]]
            pen.lines(sheet, kc, 0.0, al, 0.9, seed=740)
            pen.lines(curls, kc, 0.0, al * 0.8, 0.8, seed=745)
            pen.text("itinerarium", cx + 192, cy + 56, 44, al * kc, reveal=win(t, 9.6, 10.3))
            for j, (nm, mp) in enumerate(ITINERARIO):
                tj = 10.0 + j * 0.4
                yy = cy + 112 + j * 46
                pen.text(nm, cx + 30, yy, 34, al * 0.9, align="left", reveal=win(t, tj, tj + 0.5))
                if mp:
                    pen.text(mp, cx + 356, yy, 34, al * 0.9, align="right", reveal=win(t, tj + 0.25, tj + 0.6))
    # ---------------------------------------------------------------- part 2: the Tabula
    unroll = ease_io(win(t, 13.6, 17.0))
    xl = lerp(SC_R - 34, SC_L, unroll)
    if t > 12.3:
        kk = win(t, 12.3, 13.3)
        rullo(pen, SC_R, SC_T, SC_B, kk, vanish, a, 760)
        rullo(pen, xl, SC_T, SC_B, win(t, 12.8, 13.6), vanish, a, 770)
        if unroll > 0.001:
            pen.line([(xl + 13, SC_T), (SC_R - 13, SC_T)], 1.0, a, 1.0, vanish, seed=780)
            pen.line([(xl + 13, SC_B), (SC_R - 13, SC_B)], 1.0, a, 1.0, vanish, seed=781)
            # content, visible only where the scroll is open
            ctx = pen.ctx
            ctx.save()
            ctx.rectangle(xl + 14, 0, W, H)
            ctx.clip()
            pen.lines(ROT_BIG, 1.0, vanish, 0.85 * a, 0.8, seed=800)
            pen.lines(ROT_LIGHT, 1.0, vanish, 0.5 * a, 0.65, seed=820)
            for j, (x, y) in enumerate(ROT_TOWNS):
                tj = 13.6 + 3.4 * (1 - (x - SC_L) / (SC_R - SC_L)) ** 1.3
                pen.lines(torri(x, y, 0.85), win(t, tj, tj + 0.6), vanish, 0.85 * a, 0.75, seed=840 + j)
            pen.lines(ROT_ROMA, win(t, 15.4, 16.4), vanish, a, 0.9, seed=870)
            ctx.restore()
        # the medieval copyist (right), at a little desk with an inkpot
        km = smooth(win(t, 14.0, 15.2))
        floor = 902
        pen.lines([[(1420, floor + 2), (1760, floor + 2)]], win(t, 14.0, 15.2), vanish, 0.5 * a, 0.8, seed=880)
        wri = math.sin(t * 6.0) * 0.1 * (1 - smooth(win(t, 21.5, 22.2)))
        look_up = smooth(win(t, 21.6, 22.4))
        omino(pen, 1572, floor, 1.25, t, "monaco", fx=-1, alpha=a * km,
              expr="smile" if look_up > 0.5 else "squint", head_tilt=lerp(0.16, -0.05, look_up),
              arm_f=(-0.42 + wri * 0.3, -0.62 + wri), hold="quill", seed=9)
        # labels
        mid = (SC_L + SC_R) / 2
        if t > 17.9:
            pen.text("Tabula Peutingeriana", mid, 236, 68, a, reveal=win(t, 17.9, 19.0))
        if t > 19.7:
            k = ease_io(win(t, 19.7, 20.8))
            y = 690
            x0, x1 = SC_L - 6, SC_R + 6
            pen.line([(mid, y), (lerp(mid, x0, k), y)], 0.8, 0.85 * a, 1.0, vanish, seed=890)
            pen.line([(mid, y), (lerp(mid, x1, k), y)], 0.8, 0.85 * a, 1.0, vanish, seed=891)
            ke = win(t, 20.6, 20.9)
            for xx, sg in ((x0, 1), (x1, -1)):
                pen.line([(xx + 16 * sg, y - 10), (xx, y), (xx + 16 * sg, y + 10)], 0.8, 0.85 * a, ke, vanish,
                         seed=892)
            pen.text("≈ 6,75 m", mid, y + 60, 50, a * smooth(win(t, 20.2, 20.8)), reveal=win(t, 20.2, 21.0))
        if t > 22.4:
            pen.text("oggi a Vienna", mid, 292, 38, 0.8 * a, reveal=win(t, 22.4, 23.3))
    # ---------------------------------------------------------------- the road: ground -> reeled in -> unrolled
    lift = ease_io(win(t, 12.0, 13.6))
    if lift <= 0:
        return ground
    if unroll <= 0:
        return morph(ground, strada_rotolo(xl + 13), lift, 90)
    return strada_rotolo(xl + 13)


# =====================================================================================  b12 ponti
# world coordinates: road deck at y = 0; bridge centred at x = 0; the Furlo rock to the right
SPANS = [196, 214, 232, 214, 196]
PIER = 66
SPRING = 210        # springing line of the arches
WATER = 262
B_L = -(sum(SPANS) + PIER * 4) / 2 - 60
B_R = -B_L
PORTAL_X = 1640     # tunnel mouth (left edge)
TUN_L = 800         # tunnel length in world px (≈ 38 m at ~21 px/m, the bridge's scale)


def _arches():
    out, x = [], B_L + 60
    for i, s in enumerate(SPANS):
        out.append((x, x + s))
        x += s + PIER
    return out


ARCHES = _arches()


def ponte_strokes():
    main, detail, faint = [], [], []
    # parapet and cornice
    main.append([(B_L - 20, -40), (B_R + 20, -40)])
    main.append([(B_L - 20, -40), (B_L - 26, 0)])
    main.append([(B_R + 20, -40), (B_R + 26, 0)])
    detail.append([(B_L, 18), (B_R, 18)])
    # arches and piers
    prev = B_L - 40
    for i, (x0, x1) in enumerate(ARCHES):
        r = (x1 - x0) / 2
        cx = x0 + r
        main.append([(x0, WATER + 8), (x0, SPRING)] + arc(cx, SPRING, r, math.pi, 2 * math.pi, 26) + [(x1, WATER + 8)])
        # voussoirs: an outer ring and radial joints
        detail.append(arc(cx, SPRING, r + 22, math.pi, 2 * math.pi, 26))
        for j in range(1, 12):
            ang = math.pi + j * math.pi / 12
            detail.append([(cx + math.cos(ang) * r, SPRING + math.sin(ang) * r),
                           (cx + math.cos(ang) * (r + 22), SPRING + math.sin(ang) * (r + 22))])
        prev = x1
    # cutwaters at the piers and the little aediculae (niches with a pediment) above them
    for i in range(4):
        px0 = ARCHES[i][1]
        px1 = ARCHES[i + 1][0]
        pc = (px0 + px1) / 2
        detail.append([(px0 + 4, WATER - 4), (pc, WATER - 30), (px1 - 4, WATER - 4)])
        ny = 70
        detail.append([(pc - 20, ny + 66), (pc - 20, ny + 12), (pc + 20, ny + 12), (pc + 20, ny + 66), (pc - 20, ny + 66)])
        detail.append([(pc - 28, ny + 12), (pc, ny - 8), (pc + 28, ny + 12), (pc - 28, ny + 12)])
        detail.append([(pc - 24, ny + 72), (pc + 24, ny + 72)])
    # abutments down to the banks
    main.append([(B_L - 26, 0), (B_L - 10, 120), (B_L + 60, WATER + 8)])
    main.append([(B_R + 26, 0), (B_R + 10, 120), (B_R - 60, WATER + 8)])
    # a few stone courses on the spandrels
    rng = random.Random(4)
    for k in range(16):
        x = rng.uniform(B_L + 80, B_R - 80)
        y = rng.uniform(32, 70)
        faint.append([(x, y), (x + rng.uniform(26, 50), y)])
    return main, detail, faint


P_MAIN, P_DETAIL, P_FAINT = ponte_strokes()


def roccia_strokes():
    main, detail, far = [], [], []
    # the front rock spur the tunnel goes through, with the road ledge at y = 0
    face = [(1290, 300), (1350, 150), (1420, 60), (1470, -30), (1540, -110), (1600, -260), (1700, -420),
            (1830, -560), (1990, -640), (2150, -600), (2300, -500), (2440, -420), (2600, -440), (2800, -560),
            (3000, -620), (3200, -560)]
    main.append(face)
    # cliff below the road down to the river
    main.append([(1300, 30), (1340, 140), (1320, 240), (1360, 300)])
    main.append([(1300, 30), (3300, 30)])
    # strata in the limestone (diagonal bands)
    for k in range(9):
        x0 = 1700 + k * 150
        detail.append([(x0, -60 - (k % 3) * 40), (x0 + 120, -260 - (k % 3) * 40), (x0 + 210, -420)])
    for k in range(6):
        x0 = 1450 + k * 280
        detail.append([(x0, 90), (x0 + 140, 70), (x0 + 260, 110)])
    # the far wall of the gorge (fainter, behind)
    far.append([(1180, 300), (1220, -200), (1320, -560), (1450, -780), (1620, -840), (1800, -800), (1980, -900),
                (2200, -880), (2400, -760), (2700, -820), (3100, -760)])
    far.append([(1260, -260), (1360, -500), (1500, -640)])
    return main, detail, far


R_MAIN, R_DETAIL, R_FAR = roccia_strokes()


def portale():
    x0, x1, top = PORTAL_X, PORTAL_X + 120, -128
    cx = (x0 + x1) / 2
    outer = [(x0 - 18, 0), (x0 - 18, top + 20)] + arc(cx, top + 20, (x1 - x0) / 2 + 18, math.pi, 2 * math.pi, 20) + \
            [(x1 + 18, top + 20), (x1 + 18, 0)]
    inner = [(x0, 0), (x0, top + 32)] + arc(cx, top + 32, (x1 - x0) / 2, math.pi, 2 * math.pi, 20) + [(x1, top + 32), (x1, 0)]
    deep = [(x0 + 22, 0), (x0 + 22, top + 52)] + arc(cx, top + 52, (x1 - x0) / 2 - 22, math.pi, 2 * math.pi, 16) + \
           [(x1 - 22, top + 52), (x1 - 22, 0)]
    return outer, inner, deep


PORTALE = portale()


def strada_ponti():
    pts = [(-1500, 8), (-1150, 4), (B_L - 26, 0)]
    pts += [(x, 0) for x in range(int(B_L), int(B_R) + 1, 120)]
    pts += [(B_R + 26, 0), (1000, 2), (1300, 2), (PORTAL_X - 40, 0), (PORTAL_X + 30, 0)]
    return pts


STRADA_PONTI = strada_ponti()


def cam_ponti(t):
    """(world centre x, y, zoom)"""
    A = (650.0, -240.0, 0.54)        # overview: bridge and mountain
    B = (0.0, 40.0, 1.0)             # the bridge
    C = (1820.0, -170.0, 0.86)       # the Furlo rock
    u = ease_io(win(t, 7.0, 9.4))
    p = (lerp(A[0], B[0], u), lerp(A[1], B[1], u), math.exp(lerp(math.log(A[2]), math.log(B[2]), u)))
    u = ease_io(win(t, 14.2, 17.0))
    p = (lerp(p[0], C[0], u), lerp(p[1], C[1], u), math.exp(lerp(math.log(p[2]), math.log(C[2]), u)))
    return p


def auto(pen, x, y, t, alpha, seed):
    """A small modern car, side view, wheels turning; (x, y) = front-wheel contact point."""
    body = [(x - 104, y - 14), (x - 106, y - 34), (x - 84, y - 40), (x - 62, y - 62), (x - 12, y - 64), (x + 12, y - 40),
            (x + 34, y - 34), (x + 36, y - 16), (x + 28, y - 12)]
    pen.line(body, 1.0, alpha, seed=seed)
    pen.line([(x - 104, y - 14), (x - 92, y - 12)], 1.0, alpha, seed=seed + 1)
    pen.line([(x - 52, y - 12), (x - 12, y - 12)], 1.0, alpha, seed=seed + 2)
    pen.line([(x - 70, y - 40), (x - 56, y - 56), (x - 36, y - 57), (x - 36, y - 40), (x - 70, y - 40)], 0.7, alpha,
             seed=seed + 3, smooth_=False)
    pen.line([(x - 30, y - 57), (x - 14, y - 56), (x + 2, y - 40), (x - 30, y - 40), (x - 30, y - 57)], 0.7, alpha,
             seed=seed + 4, smooth_=False)
    for wx in (x - 72, x + 8 - 8):
        pen.line(ellipse(wx, y - 12, 13, 13, 16), 1.0, alpha, seed=seed + 5)
        a = -wx / 13.0
        pen.line([(wx + math.cos(a) * 6, y - 12 + math.sin(a) * 6), (wx - math.cos(a) * 6, y - 12 - math.sin(a) * 6)],
                 0.6, alpha, seed=seed + 6)
    pen.dot(x + 32, y - 28, 3, alpha)


def bici(pen, x, y, alpha, seed):
    """A bicycle doodle, (x, y) = middle of the wheelbase on the ground."""
    r = 30
    wl, wr = (x - 58, y - r), (x + 58, y - r)
    strokes = [ellipse(wl[0], wl[1], r, r, 22), ellipse(wr[0], wr[1], r, r, 22),
               [wl, (x - 6, y - r), (x + 26, y - 70), (x - 20, y - 70), (x - 6, y - r)],
               [(x + 26, y - 70), wr], [(x + 26, y - 70), (x + 30, y - 84), (x + 44, y - 88)],
               [(x - 20, y - 70), (x - 24, y - 80)], [(x - 34, y - 82), (x - 12, y - 82)]]
    pen.lines(strokes, 1.0, 0.0, alpha, 0.85, seed=seed)


@scena("ponti")
def ponti(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    cx, cy, z = cam_ponti(t)
    ox, oy = W / 2 - cx * z, H / 2 - cy * z

    def S(p):
        return (ox + p[0] * z, oy + p[1] * z)

    with at(pen, ox, oy, z):
        # the river: banks and flowing ripples
        kb = win(t, 0.2, 2.2)
        pen.lines([[(-1700, WATER + 30), (-1180, WATER + 34), (-900, WATER + 10), (-780, WATER + 12)],
                   [(780, WATER + 12), (980, WATER + 30), (1240, WATER + 44)]], kb, vanish, 0.6, 0.8, seed=900)
        rng = random.Random(7)
        rip = []
        for i in range(26):
            x0 = rng.uniform(-860, 860)
            y0 = WATER + rng.uniform(18, 120)
            ph = rng.uniform(0, 6.28)
            dx = (t * 26 + x0 + 400) % 1720 - 860
            L = 40 + 20 * math.sin(t * 1.3 + ph)
            rip.append([(dx, y0), (dx + L * 0.5, y0 - 3), (dx + L, y0)])
        pen.lines(rip, win(t, 0.6, 2.6), vanish, 0.38, 0.6, seed=905)
        # reflections of the arches, broken and shimmering
        refl = []
        for i, (x0, x1) in enumerate(ARCHES):
            r = (x1 - x0) / 2
            c = x0 + r
            for j in range(4):
                yy = WATER + 18 + j * 16
                hw = r * (0.9 - j * 0.18) + 6 * math.sin(t * 2 + i + j)
                refl.append([(c - hw, yy), (c - hw * 0.4, yy + 1)])
                refl.append([(c + hw * 0.4, yy + 1), (c + hw, yy)])
        pen.lines(refl, win(t, 1.6, 3.4), vanish, 0.22, 0.6, seed=910)
        # the bridge
        kp = win(t, 0.4, 3.6)
        pen.lines(P_MAIN, kp, vanish, 1.0, 1.0, seed=920)
        pen.lines(P_DETAIL, win(t, 2.0, 9.6), vanish, 0.7, 0.75, seed=930)
        pen.lines(P_FAINT, win(t, 8.0, 10.0), vanish, 0.35, 0.6, seed=950)
        # the mountain, the gorge and the tunnel
        km = win(t, 3.6, 6.4)
        pen.lines(R_FAR, km, vanish, 0.35, 0.8, seed=960)
        pen.lines(R_MAIN, km, vanish, 0.95, 1.0, seed=970)
        pen.lines(R_DETAIL, win(t, 5.0, 8.0), vanish, 0.45, 0.65, seed=980)
        kt = win(t, 5.0, 7.0)
        pen.lines([PORTALE[0], PORTALE[1]], kt, vanish, 1.0, 1.0, seed=990)
        pen.lines([PORTALE[2]], kt, vanish, 0.45, 0.7, seed=993)
        # river at the bottom of the gorge
        rip2 = []
        for i in range(14):
            x0 = 1420 + ((i * 197 + t * 22) % 1800)
            y0 = 330 + (i * 37) % 120
            rip2.append([(x0, y0), (x0 + 26, y0 - 2), (x0 + 52, y0)])
        pen.lines(rip2, win(t, 4.0, 6.0), vanish, 0.32, 0.6, seed=995)
        # the tunnel, as a dashed line through the rock, and its length
        if t > 20.4:
            k = ease_io(win(t, 20.4, 21.8))
            dashed(pen, [(PORTAL_X + 60, -40), (PORTAL_X + 60 + TUN_L, -40)], 0.6 * a, k, vanish, 0.7, 16, 12, seed=1000)
            yy = -250
            pen.line([(PORTAL_X + 60, yy), (PORTAL_X + 60 + TUN_L * k, yy)], 0.8, 0.85 * a, 1.0, vanish, seed=1010)
            if k > 0.95:
                for xx, sg in ((PORTAL_X + 60, 1), (PORTAL_X + 60 + TUN_L, -1)):
                    pen.line([(xx + 18 * sg, yy - 12), (xx, yy), (xx + 18 * sg, yy + 12)], 0.8, 0.85 * a, seed=1011)
                    pen.line([(xx, yy - 18), (xx, yy + 18)], 0.6, 0.6 * a, seed=1012)
        # people today crossing the bridge: someone walking a bicycle
        if 10.6 < t < 19.0:
            kx = win(t, 11.0, 18.5)
            px = lerp(B_L + 120, B_R - 40, kx)
            al = a * smooth(win(t, 10.6, 11.4))
            bici(pen, px + 120, -2, al, 1020)
            omino(pen, px, 0, 0.62, t, "moderno", walk=1.0, speed=0.8, expr="smile", alpha=al,
                  arm_f=(-0.05, 0.25), seed=11)
        # the car driving into the tunnel
        if t > 22.2:
            u = ease_in(win(t, 22.4, 25.6), 1.6)
            x = lerp(1000, PORTAL_X + 260, u)
            ctx = pen.ctx
            ctx.save()
            ctx.rectangle(-5000, -2000, PORTAL_X + 50 + 5000, 4000)
            ctx.clip()
            auto(pen, x, 0, t, a * smooth(win(t, 22.2, 22.8)), 1030)
            ctx.restore()
            # headlight glow moving inside the tunnel
            if PORTAL_X + 50 < x:
                g = win(x, PORTAL_X + 50, PORTAL_X + 250)
                pen.dot(x + 34, -28, 3.0, 0.5 * a * (1 - g * 0.5))
    # labels (screen space)
    if t > 7.8:
        p = S((0, -150))
        pen.text("Ponte di Tiberio", p[0], p[1], 64, a, reveal=win(t, 7.8, 8.9))
        pen.text("Rimini", p[0], p[1] + 58, 40, 0.8 * a, reveal=win(t, 8.9, 9.6))
    if t > 11.0:
        p = S((0, -150))
        pen.text("21 d.C.", p[0] + 330, p[1] + 58, 40, 0.8 * a, reveal=win(t, 11.0, 11.8))
    if t > 15.4:
        p = S((1120, -320))
        pen.text("via Flaminia", p[0], p[1], 36, 0.6 * a, reveal=win(t, 15.4, 16.4))
    if t > 16.7:
        p = S((PORTAL_X + 60 + TUN_L / 2, -330))
        pen.text("Galleria del Furlo", p[0], p[1] - 30, 60, a, reveal=win(t, 16.7, 17.9))
        if t > 18.9:
            pen.text("76 d.C.", p[0], p[1] + 22, 40, 0.8 * a, reveal=win(t, 18.9, 19.6))
    if t > 21.4:
        p = S((PORTAL_X + 60 + TUN_L / 2, -140))
        pen.text("≈ 38 m", p[0], p[1], 46, a * smooth(win(t, 21.4, 22.0)), reveal=win(t, 21.4, 22.2))
    return [S(p) for p in STRADA_PONTI]


# =====================================================================================  b13 mondo
# major towns of the empire around 150 AD (lon, lat): seeds of the procedural web
NODI = [
    (12.49, 41.89), (9.19, 45.46), (13.37, 45.77), (12.20, 44.42), (12.57, 44.06), (11.34, 44.49), (8.93, 44.41),
    (10.40, 43.72), (14.25, 40.85), (14.25, 41.08), (17.94, 40.64), (17.24, 40.47), (15.65, 38.11), (15.55, 38.19),
    (15.29, 37.07), (13.36, 38.12), (12.44, 37.80), (9.11, 39.22), (8.40, 40.84), (9.45, 42.10), (5.37, 43.30),
    (4.63, 43.68), (4.36, 43.84), (3.00, 43.18), (1.44, 43.60), (-0.58, 44.84), (4.83, 45.76), (4.30, 46.95),
    (2.35, 48.86), (4.03, 49.26), (2.30, 49.89), (1.61, 50.73), (6.64, 49.75), (8.27, 50.00), (6.96, 50.94),
    (7.75, 48.58), (6.02, 47.24), (7.72, 47.53), (6.18, 49.12), (5.86, 51.84), (0.34, 46.58), (0.69, 47.39),
    (-1.68, 48.11), (2.40, 47.08), (3.08, 45.78), (-0.63, 45.75), (-0.09, 51.51), (0.90, 51.89), (-1.08, 53.96),
    (-2.89, 53.19), (-0.54, 53.23), (-2.24, 51.86), (-3.53, 50.72), (-2.95, 51.61), (-2.93, 54.89), (-1.97, 51.71),
    (-2.65, 52.67), (-1.08, 51.36), (1.31, 51.13), (-1.31, 51.06), (1.25, 41.12), (2.17, 41.39), (-0.88, 41.65),
    (-6.34, 38.92), (-4.78, 37.88), (-5.98, 37.39), (-6.29, 36.53), (-0.99, 37.60), (-4.02, 39.86), (-6.06, 42.46),
    (-5.57, 42.60), (-8.43, 41.55), (-9.14, 38.72), (-0.38, 39.47), (-7.56, 43.01), (-1.64, 42.81), (-4.42, 36.72),
    (-3.37, 41.78), (-7.86, 38.01), (-8.49, 40.10), (0.62, 41.62), (3.12, 42.13), (10.32, 36.85), (7.75, 36.88),
    (6.61, 36.37), (6.26, 35.49), (8.12, 35.40), (10.71, 35.30), (10.64, 35.83), (10.10, 33.88), (14.29, 32.64),
    (13.18, 32.89), (12.48, 32.80), (2.19, 36.61), (3.06, 36.75), (-5.81, 35.78), (-5.55, 34.07), (-6.82, 34.01),
    (21.86, 32.82), (20.07, 32.12), (29.92, 31.20), (32.57, 31.04), (31.25, 29.85), (32.65, 25.70), (32.90, 24.09),
    (31.81, 26.48), (30.88, 27.81), (5.41, 36.19), (6.47, 35.48), (5.08, 36.75), (23.73, 37.98), (22.88, 37.91),
    (22.43, 37.07), (21.73, 38.25), (20.73, 39.01), (19.45, 41.32), (19.47, 40.72), (22.94, 40.64), (22.42, 39.64),
    (24.29, 41.01), (28.98, 41.01), (27.96, 40.98), (26.56, 41.68), (24.75, 42.14), (23.32, 42.70), (21.90, 43.32),
    (20.46, 44.82), (19.61, 44.97), (21.21, 44.74), (22.83, 43.81), (24.47, 43.70), (25.38, 43.61), (27.27, 44.12),
    (27.58, 43.31), (27.91, 43.20), (28.65, 44.17), (21.43, 42.00), (21.97, 41.55), (16.37, 45.48), (15.87, 46.42),
    (14.51, 46.05), (16.48, 43.54), (15.23, 44.12), (17.63, 43.05), (19.04, 47.56), (16.92, 48.11), (16.37, 48.21),
    (18.18, 47.75), (16.62, 47.23), (14.37, 46.70), (13.05, 47.80), (14.47, 48.22), (10.90, 48.37), (10.31, 47.73),
    (9.75, 47.50), (8.22, 47.48), (7.04, 46.88), (11.12, 46.07), (10.99, 45.44), (11.88, 45.41), (7.69, 45.07),
    (7.32, 45.74), (10.03, 45.13), (13.52, 43.62), (13.58, 42.85), (13.84, 42.12), (14.78, 41.13), (15.80, 40.64),
    (16.25, 39.30), (17.13, 39.08), (15.00, 40.42), (11.88, 43.46), (11.25, 43.77), (12.39, 43.11), (12.74, 42.73),
    (23.57, 46.07), (23.59, 46.77), (23.19, 47.18), (22.78, 45.51), (22.66, 44.63), (24.43, 44.14), (29.92, 40.77),
    (29.72, 40.43), (27.89, 40.39), (27.18, 39.12), (27.14, 38.42), (27.34, 37.94), (28.04, 38.49), (29.11, 37.84),
    (30.17, 38.07), (32.86, 39.93), (32.48, 37.87), (34.90, 36.92), (35.48, 38.73), (37.02, 39.75), (35.83, 40.65),
    (35.15, 42.03), (36.33, 41.29), (39.72, 41.00), (39.66, 40.03), (38.33, 38.35), (38.53, 37.53), (30.71, 36.89),
    (31.19, 38.31), (30.52, 39.79), (29.06, 40.18), (31.42, 41.28), (33.62, 40.60), (34.38, 40.00), (33.23, 37.18),
    (36.16, 36.20), (37.16, 36.20), (37.88, 37.06), (38.27, 34.55), (36.72, 34.73), (36.29, 33.51), (35.50, 33.89),
    (35.20, 33.27), (34.89, 32.50), (35.23, 31.78), (34.45, 31.50), (35.44, 30.33), (36.48, 32.52), (35.89, 32.28),
    (35.93, 31.95), (35.00, 29.53), (35.78, 35.52), (36.40, 35.42), (33.90, 35.18), (32.41, 34.77), (24.95, 35.06),
    (25.16, 35.30), (23.65, 35.45), (9.69, 45.05), (10.33, 44.80),
]

# a rough outline of the empire c. 150 AD, used only as a mask for the procedural web
IMPERO = [(-5.2, 56.2), (-2.0, 56.1), (2.0, 56.0), (4.5, 53.0), (6.5, 51.9), (7.2, 50.6), (8.6, 50.4), (9.3, 49.8),
          (9.7, 48.8), (11.0, 49.1), (12.1, 49.0), (13.5, 48.6), (16.4, 48.3), (18.8, 47.8), (19.1, 47.6),
          (19.0, 46.0), (20.4, 45.2), (21.5, 46.3), (22.4, 47.1), (23.4, 47.5), (24.5, 47.1), (25.5, 46.3),
          (25.4, 45.0), (25.0, 44.0), (27.0, 44.1), (28.0, 44.3), (29.6, 45.3), (31.0, 45.0), (36.0, 42.5),
          (41.6, 41.6), (40.2, 40.0), (39.4, 38.8), (38.6, 37.6), (38.4, 36.5), (39.2, 35.6), (38.8, 33.6),
          (37.4, 31.0), (36.4, 29.0), (34.8, 27.5), (35.9, 23.6), (33.0, 22.8), (31.0, 23.6), (29.2, 29.0),
          (25.0, 30.6), (20.0, 30.0), (18.0, 30.4), (15.0, 30.4), (11.0, 31.6), (9.4, 33.0), (7.6, 33.8), (5.0, 34.6),
          (2.5, 35.0), (-1.5, 34.6), (-4.4, 33.8), (-7.2, 33.6), (-11.0, 34.0), (-11.0, 44.0), (-10.0, 50.0),
          (-6.5, 49.8), (-5.4, 52.0), (-5.6, 53.5)]


def _maschera():
    """Rasterise land ∩ empire into a 10 px/deg grid over lon -15..50, lat 20..60."""
    gw, gh = 650, 400
    surf = cairo.ImageSurface(cairo.FORMAT_A8, gw, gh)
    ctx = cairo.Context(surf)

    def P(lo, la):
        return ((lo + 15) * 10, (60 - la) * 10)
    for poly in TERRE:
        ctx.move_to(*P(*poly[0]))
        for p in poly[1:]:
            ctx.line_to(*P(*p))
        ctx.close_path()
    ctx.set_source_rgba(0, 0, 0, 1)
    ctx.fill()
    land = np.ndarray((gh, surf.get_stride()), np.uint8, surf.get_data())[:, :gw].copy()
    surf2 = cairo.ImageSurface(cairo.FORMAT_A8, gw, gh)
    ctx2 = cairo.Context(surf2)
    ctx2.move_to(*P(*IMPERO[0]))
    for p in IMPERO[1:]:
        ctx2.line_to(*P(*p))
    ctx2.close_path()
    ctx2.fill()
    emp = np.ndarray((gh, surf2.get_stride()), np.uint8, surf2.get_data())[:, :gw].copy()
    return land > 127, emp > 127


LAND, EMP = _maschera()


def _on(lo, la, grid):
    i, j = int((60 - la) * 10), int((lo + 15) * 10)
    return 0 <= i < grid.shape[0] and 0 <= j < grid.shape[1] and bool(grid[i, j])


def _rete():
    """Procedural web: real towns + random villages on land inside the empire, linked to near neighbours."""
    rng = random.Random(150)
    nodes = list(NODI)
    tries = 0
    while len(nodes) < len(NODI) + 330 and tries < 20000:
        tries += 1
        lo, la = rng.uniform(-10, 41), rng.uniform(23, 56)
        if _on(lo, la, LAND) and _on(lo, la, EMP):
            if all(math.hypot((lo - x) * 0.77, la - y) > 0.55 for x, y in nodes[-60:]):
                nodes.append((lo, la))
    P = np.array(nodes)
    Q = np.column_stack((P[:, 0] * 0.77, P[:, 1]))
    edges = set()
    for i in range(len(nodes)):
        d = np.hypot(Q[:, 0] - Q[i, 0], Q[:, 1] - Q[i, 1])
        d[i] = 1e9
        kk = 4 if i < len(NODI) else 3
        for j in np.argsort(d)[:kk]:
            if d[j] > 3.2:
                continue
            a, b = nodes[i], nodes[j]
            ok = sum(_on(lerp(a[0], b[0], f), lerp(a[1], b[1], f), LAND) for f in (0.2, 0.35, 0.5, 0.65, 0.8))
            if ok >= 4:
                edges.add((min(i, j), max(i, j)))
    # prune edges that make tiny angles with a shorter edge at the same node (keeps it road-like)
    adj = {}
    for i, j in edges:
        adj.setdefault(i, []).append(j)
        adj.setdefault(j, []).append(i)

    def ang(i, j):
        return math.atan2(Q[j, 1] - Q[i, 1], Q[j, 0] - Q[i, 0])

    def ln(i, j):
        return math.hypot(Q[j, 0] - Q[i, 0], Q[j, 1] - Q[i, 1])
    drop = set()
    for i, nb in adj.items():
        for x in nb:
            for y in nb:
                if x < y:
                    da = abs((ang(i, x) - ang(i, y) + math.pi) % (2 * math.pi) - math.pi)
                    if da < 0.38:
                        drop.add((min(i, x), max(i, x)) if ln(i, x) > ln(i, y) else (min(i, y), max(i, y)))
    edges = sorted(edges - drop)
    # distance from Rome along the web (Dijkstra), with invisible sea hops between pieces
    n = len(nodes)
    g = [[] for _ in range(n)]
    for i, j in edges:
        g[i].append((j, ln(i, j)))
        g[j].append((i, ln(i, j)))
    for i in range(n):        # sea hops: every node also links weakly to its 2 nearest (cost x1.6)
        d = np.hypot(Q[:, 0] - Q[i, 0], Q[:, 1] - Q[i, 1])
        d[i] = 1e9
        for j in np.argsort(d)[:2]:
            g[i].append((j, d[j] * 1.6))
            g[j].append((i, d[j] * 1.6))
    import heapq

    def dijkstra():
        dist = [1e9] * n
        dist[0] = 0.0
        hq = [(0.0, 0)]
        while hq:
            dd, i = heapq.heappop(hq)
            if dd > dist[i]:
                continue
            for j, w in g[i]:
                if dd + w < dist[j]:
                    dist[j] = dd + w
                    heapq.heappush(hq, (dist[j], j))
        return dist
    dist = dijkstra()
    while max(dist) > 1e8:     # islands of the web not yet reached: one sea hop from the nearest reached node
        reach = np.array([d < 1e8 for d in dist])
        R_, U_ = np.flatnonzero(reach), np.flatnonzero(~reach)
        D = np.hypot(Q[R_][:, None, 0] - Q[U_][None, :, 0], Q[R_][:, None, 1] - Q[U_][None, :, 1])
        r, u = np.unravel_index(np.argmin(D), D.shape)
        g[R_[r]].append((U_[u], D[r, u] * 1.6))
        dist = dijkstra()
    out = []
    for i, j in edges:
        if dist[j] < dist[i]:
            i, j = j, i
        a, b = nodes[i], nodes[j]
        L = ln(i, j)
        off = rng.uniform(-0.09, 0.09) * L
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        nx, ny = -(b[1] - a[1]), (b[0] - a[0])
        nn = math.hypot(nx, ny) or 1
        mid = (mx + nx / nn * off, my + ny / nn * off)
        out.append(dict(p=np.array([a, mid, b]), d0=dist[i], L=L, solid=False))
    # ~2.7 % of the total length stays "known precisely": a few scattered short pieces
    tot = sum(e["L"] for e in out)
    order = list(range(len(out)))
    rng.shuffle(order)
    acc = 0.0
    for k in order:
        if acc > 0.027 * tot:
            break
        if out[k]["L"] < 1.6:
            out[k]["solid"] = True
            acc += out[k]["L"]
    dmax = max(e["d0"] + e["L"] for e in out)
    return out, dmax


RETE, RETE_DMAX = _rete()
RETE_KM = 299171


def _v3(lon, lat):
    lo, la = np.radians(lon), np.radians(lat)
    return np.stack((np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)), -1)


class Globo:
    """Blend between an equirectangular map (h = 0) and an orthographic globe (h = 1)."""

    def __init__(self, lon_c, lat_c, R, cx, cy, h):
        self.lon_c, self.lat_c, self.R, self.cx, self.cy, self.h = lon_c, lat_c, R, cx, cy, h
        self.k = R * math.pi / 180.0
        self.c = math.cos(math.radians(lat_c))

    def arr(self, a):
        lon, lat = a[..., 0], a[..., 1]
        px = self.cx + (lon - self.lon_c) * self.k * self.c
        py = self.cy - (lat - self.lat_c) * self.k
        if self.h <= 0:
            return np.stack((px, py), -1), np.ones(lon.shape)
        lo, la = np.radians(lon - self.lon_c), np.radians(lat)
        p0 = math.radians(self.lat_c)
        x = self.R * np.cos(la) * np.sin(lo)
        y = self.R * (math.cos(p0) * np.sin(la) - math.sin(p0) * np.cos(la) * np.cos(lo))
        dep = math.sin(p0) * np.sin(la) + math.cos(p0) * np.cos(la) * np.cos(lo)
        sx, sy = self.cx + x, self.cy - y
        h = self.h
        return np.stack((px + (sx - px) * h, py + (sy - py) * h), -1), dep

    def __call__(self, lon, lat):
        p, d = self.arr(np.array([[lon, lat]], float))
        return (float(p[0, 0]), float(p[0, 1]))

    def vec(self, v3):
        """Orthographic projection of unit vectors (N x 3) -> screen xy, depth."""
        lo = math.radians(self.lon_c)
        p0 = math.radians(self.lat_c)
        e = np.array([-math.sin(lo), math.cos(lo), 0.0])                     # east
        n = np.array([-math.sin(p0) * math.cos(lo), -math.sin(p0) * math.sin(lo), math.cos(p0)])  # north
        c = np.array([math.cos(p0) * math.cos(lo), math.cos(p0) * math.sin(lo), math.sin(p0)])    # towards us
        return np.column_stack((self.cx + self.R * (v3 @ e), self.cy - self.R * (v3 @ n))), v3 @ c


def _runs_mask(xy, mask):
    out, cur = [], []
    for p, m in zip(xy, mask):
        if m:
            cur.append(p)
        elif cur:
            if len(cur) > 1:
                out.append(cur)
            cur = []
    if len(cur) > 1:
        out.append(cur)
    return out


GC_LON, GC_LAT = 16.0, 39.5
# the yarn: 7.5 laps around the Earth, each one (nearly) a great circle through Rome, slowly turning
YARN_TURNS = 7.47
_ROMA3 = _v3(12.49, 41.89)
_E = np.cross(np.array([0, 0, 1.0]), _ROMA3)
_E /= np.linalg.norm(_E)
_N = np.cross(_ROMA3, _E)


def yarn(s1, s0=0.0, step=1 / 110):
    s = np.arange(s0, s1, step)
    s = np.append(s, s1)
    th = 2 * math.pi * s
    psi = 0.35 + math.pi * s / YARN_TURNS * 0.94
    tang = np.outer(np.cos(psi), _E) + np.outer(np.sin(psi), _N)
    return np.outer(np.cos(th), _ROMA3) + np.sin(th)[:, None] * tang


def cam_mondo(t):
    # stage 1: zoom out from Italy over the empire;  stage 2: curl into a globe;  stage 3: lean in
    u1 = ease_io(win(t, 1.6, 7.0))
    k1 = math.exp(lerp(math.log(92.0), math.log(33.0), u1))
    lon = lerp(12.7, GC_LON, u1)
    lat = lerp(42.9, GC_LAT + 2.0, u1)
    cx, cy = W / 2, H / 2 - 30 * u1
    u2 = ease_io(win(t, 14.6, 17.4))
    h = smooth(win(t, 14.9, 17.0))
    R = math.exp(lerp(math.log(k1 * 180 / math.pi), math.log(320.0), u2))
    lat = lerp(lat, GC_LAT, u2)
    cx, cy = lerp(cx, 760.0, u2), lerp(cy, 520.0, u2)
    u3 = ease_io(win(t, 19.8, 21.8))
    R = R * lerp(1.0, 1.28, u3)
    cx = lerp(cx, 780.0, u3)
    cy = lerp(cy, 560.0, u3)
    lon = lon + 4.0 * u2 - 4.0 * u2 * win(t, 17.4, 24.0)  # a gentle turn of the globe
    return Globo(lon, lat, R, cx, cy, h)


def _fmt(n):
    return f"{n:,}".replace(",", ".")


def grat(g):
    """Meridians and parallels on the globe (front-facing parts)."""
    out = []
    for lo in range(-180, 180, 30):
        ll = np.column_stack((np.full(61, lo, float), np.linspace(-90, 90, 61)))
        xy, d = g.arr(ll)
        out += _runs_mask(xy.tolist(), d > 0.02)
    for la in (-60, -30, 0, 30, 60):
        ll = np.column_stack((np.linspace(-180, 180, 121), np.full(121, la, float)))
        xy, d = g.arr(ll)
        out += _runs_mask(xy.tolist(), d > 0.02)
    return out


VIE_ARR = {k: np.array(v, float) for k, v in VIE.items()}


@scena("mondo")
def mondo(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    g = cam_mondo(t)
    h = g.h
    # --- coastlines (map, then globe)
    rv = smooth(win(t, 0.0, 2.4))
    m = 50
    for i, c in enumerate(COSTE):
        xy, dep = g.arr(c)
        if h > 0:
            vis = dep > 0.0
            if not vis.any():
                continue
            # far coasts (other continents) only appear as the globe forms
            far = (np.abs(((c[:, 0] - g.lon_c + 180) % 360) - 180) > 55) | (c[:, 1] < 15) | (c[:, 1] > 65)
            al = 0.42 if not far.any() else 0.42 * h * h
            if al < 0.01:
                continue
            for r in _runs_mask(xy.tolist(), vis):
                pen.line(r, 0.7, al, rv, vanish, smooth_=False, seed=500 + i)
        else:
            bb = COSTE_BB[i]
            if bb[2] < -40 or bb[0] > 70 or bb[3] < 0 or bb[1] > 75:
                continue
            for r in runs_inside(xy, m):
                pen.line(r.tolist(), 0.7, 0.42, rv, vanish, smooth_=False, seed=500 + i)
    # --- globe outline and graticule
    if h > 0.05:
        kg = smooth(win(h, 0.3, 1.0))
        pen.line(ellipse(g.cx, g.cy, g.R, g.R, 72), 1.0, 0.75 * a * kg, 1.0, vanish, closed=True, seed=1100)
        gr = grat(g)
        pen.lines(gr, kg, vanish, 0.16 * a, 0.55, seed=1110)
    # --- the six main roads (quick recap at the start)
    for j, (name, ll) in enumerate(VIE_ARR.items()):
        if name == "Flaminia":
            continue
        xy, dep = g.arr(ll)
        rv = ease_io(win(t, 0.6 + j * 0.35, 2.2 + j * 0.35))
        dots = smooth(win(t, 20.6, 22.0))
        pen.line(xy.tolist(), 0.95, 0.9 * a * (1 - dots), rv, vanish, seed=1200 + j)
        if dots > 0:
            _punti(pen, xy.tolist(), 0.8 * a * dots)
    # --- the web grows out of Rome
    grow = ease_io(win(t, 4.6, 14.2)) * RETE_DMAX
    dots = smooth(win(t, 20.6, 22.0))
    ksolid = win(t, 21.2, 22.0)
    if grow > 0:
        for e in RETE:
            if grow <= e["d0"]:
                continue
            r = clamp((grow - e["d0"]) / e["L"])
            xy, dep = g.arr(e["p"])
            pts = xy.tolist()
            if e["solid"]:
                pen.line(pts, 0.75 + 0.35 * ksolid, (0.62 + 0.38 * ksolid) * a, r, vanish, seed=1300)
            else:
                if dots < 1:
                    pen.line(pts, 0.55, 0.62 * a * (1 - dots), r, vanish, seed=1300)
                if dots > 0:
                    _punti(pen, pts, 0.55 * a * dots)
    # --- counter: the length of the web
    km = RETE_KM * clamp(grow / RETE_DMAX) if grow > 0 else 0
    if t > 4.8:
        kc = smooth(win(t, 4.8, 5.6))
        s = "≈ " + _fmt(int(round(km / 1000.0)) * 1000) + " km"
        x, y = (W / 2, 968)
        u2 = ease_io(win(t, 14.6, 17.4))
        x, y = lerp(x, 1490, u2), lerp(y, 300, u2)
        sz = lerp(76, 64, u2)
        pen.text(s, x, y, sz, a * kc)
        cap = smooth(win(t, 6.6, 7.4)) * (1 - u2)
        if cap > 0.01:
            pen.text("Itiner-e · 2025", W / 2 - 24, 1030, 32, 0.6 * a * cap, align="right", reveal=win(t, 6.6, 7.6))
        cap2 = smooth(win(t, 11.6, 12.4)) * (1 - u2)
        if cap2 > 0.01:
            pen.text("strade dell'impero, ~150 d.C.", W / 2 + 24, 1030, 32, 0.6 * a * cap2, align="left",
                     reveal=win(t, 11.6, 12.8))
    # --- the yarn: more than seven times around the Earth
    road_circle = ellipse(g.cx, g.cy, g.R + 22, g.R + 22, 90, a0=-math.pi * 0.7)
    s1 = YARN_TURNS * ease_io(win(t, 16.6, 19.6))
    s0 = YARN_TURNS * smooth(win(t, 19.9, 21.0))
    if s1 > 0.002 and s0 < YARN_TURNS - 0.01:
        v3 = yarn(s1, s0)
        xy, dep = g.vec(v3)
        pts = xy.tolist()
        for r in _runs_mask(pts, dep > 0):
            pen.line(r, 0.95, 0.95 * a, seed=1400)
        for r in _runs_mask(pts, dep <= 0):
            pen.line(r, 0.6, 0.22 * a, seed=1401)
        if s1 < YARN_TURNS - 0.01:
            pen.dot(pts[-1][0], pts[-1][1], 5, a)
    # lap counter and caption
    if t > 16.6:
        laps = YARN_TURNS * ease_io(win(t, 16.6, 19.6))
        n = int(laps + 1e-6)
        s = f"× {n}" if laps < YARN_TURNS - 0.01 else "× 7,5"
        kz = smooth(win(t, 16.6, 17.2))
        pen.text(s, 1490, 470, 92, a * kz)
        pen.text("più di 7 volte", 1490, 548, 40, 0.85 * a, reveal=win(t, 17.6, 18.4))
        pen.text("il giro della Terra", 1490, 594, 40, 0.85 * a, reveal=win(t, 18.0, 18.9))
    if t > 21.2:
        k = win(t, 21.2, 22.2)
        x0, y0 = 1330, 760
        pen.line([(x0, y0), (x0 + 70, y0)], 1.2, a, k, vanish, seed=1500)
        pen.text("tracciato esatto: ~2,7%", x0 + 92, y0 + 10, 38, a, align="left", reveal=win(t, 21.4, 22.4))
        _punti(pen, [(x0, y0 + 56), (x0 + 70, y0 + 56)], 0.8 * a * smooth(k))
        pen.text("ricostruito", x0 + 92, y0 + 66, 38, 0.7 * a, align="left", reveal=win(t, 21.9, 22.7))
    # --- road: the Flaminia on the map, which becomes a ring around the globe
    fl, _ = g.arr(VIE_ARR["Flaminia"])
    fl = fl.tolist()
    u = ease_io(win(t, 15.4, 17.2))
    if u <= 0:
        return fl
    if u >= 1:
        return road_circle
    return morph(fl, road_circle, u, 120)


def _punti(pen, pts, alpha, step=9.0):
    """Dotted rendition of a polyline (an uncertain route)."""
    if alpha <= 0.01:
        return
    from motore.linea import resample_step
    P = resample_step(pts, step)
    for x, y in P[1:-1]:
        pen.dot(x, y, 1.6, alpha)
