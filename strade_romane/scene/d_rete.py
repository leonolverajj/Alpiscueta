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
from motore.linea import H, W, arc, at, back, catmull, clamp, ease_io, ellipse, lerp, morph, resample, smooth, win
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
            pen.line(r.tolist(), w, alpha, reveal, start, smooth_=False, seed=seed + i, step=5.0)


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
    gone = smooth(win(t, 11.4, 12.6))           # procession fades
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
        omino(pen, x, gy(x), 0.95, t, "legionario", walk=1.0, expr="determined", alpha=al * smooth(win(t, 0.9, 1.9)),
              seed=3)
        # the merchant pulling his cart (cart behind him)
        x = xs(680)
        ka = al * smooth(win(t, 1.0, 2.0))
        carretto(pen, x - 236, gy(x - 236), ka, 1.0, 0.0, t, seed=710)
        omino(pen, x, gy(x), 0.92, t, "operaio", walk=1.0, lean=0.2, expr="smile", alpha=ka,
              arm_b=(DOWN + 0.75, DOWN + 0.95), seed=5, talk=5.0 < t < 6.6)
        fumetto(pen, x + 60, gy(x) - 350, win(t, 5.2, 5.8) * (1 - win(t, 7.6, 8.0)), al, "news", t, 720)
        # the pilgrim, with a staff
        x = xs(160)
        omino(pen, x, gy(x), 0.9, t, "agrimensore", walk=1.0, expr="calm", alpha=al * smooth(win(t, 1.1, 2.1)),
              hold="staff", seed=7)
        fumetto(pen, x + 70, gy(x) - 340, win(t, 5.9, 6.5) * (1 - win(t, 7.8, 8.2)), al, "idea", t, 730)
        # the traveller and the mule
        read = smooth(win(t, 9.2, 9.8))
        mulo(pen, xm, gy(xm), 0.95, t, walk=wt, ear=0.2 + 0.7 * smooth(win(t, 10.2, 10.8)),
             alpha=al * smooth(win(t, 1.2, 2.2)))
        omino(pen, xt, gy(xt), 1.05, t, "viandante", walk=wt, expr="squint" if read > 0.5 else "calm",
              look=0.4 * read, head_tilt=-0.12 * read,
              arm_f=(lerp(DOWN - 0.35, -0.1, read), lerp(0.4, -0.5, read)) if read > 0.01 else None,
              hold="scroll" if read > 0.5 else "staff", alpha=al * smooth(win(t, 1.2, 2.2)), seed=2)
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
    unroll = ease_io(win(t, 12.9, 16.4))
    xl = lerp(SC_R - 34, SC_L, unroll)
    if t > 11.8:
        kk = win(t, 11.8, 12.8)
        rullo(pen, SC_R, SC_T, SC_B, kk, vanish, a, 760)
        rullo(pen, xl, SC_T, SC_B, win(t, 12.2, 13.0), vanish, a, 770)
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
                tj = 12.9 + 3.4 * (1 - (x - SC_L) / (SC_R - SC_L)) ** 1.3
                pen.lines(torri(x, y, 0.85), win(t, tj, tj + 0.6), vanish, 0.85 * a, 0.75, seed=840 + j)
            pen.lines(ROT_ROMA, win(t, 14.8, 15.8), vanish, a, 0.9, seed=870)
            ctx.restore()
        # the medieval copyist (right), at a little desk with an inkpot
        km = smooth(win(t, 13.4, 14.6))
        floor = 902
        pen.lines([[(1420, floor + 2), (1760, floor + 2)]], win(t, 13.4, 14.6), vanish, 0.5 * a, 0.8, seed=880)
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
    lift = ease_io(win(t, 11.5, 12.9))
    if lift <= 0:
        return ground
    if unroll <= 0:
        return morph(ground, strada_rotolo(xl + 13), lift, 90)
    return strada_rotolo(xl + 13)


# =====================================================================================  b12 ponti
# World coordinates: the road (deck) at y = 0; the bridge centred at x = 0; the Furlo cliff to the right.
# Scale of the bridge ≈ 21 px per metre (spans ≈ 9-11 m); the tunnel uses the same scale (38 m ≈ 800 px).
SPANS = [196, 214, 232, 214, 196]
PIER = 66
SPRING = 210        # springing line of the arches
WATER = 262
B_L = -(sum(SPANS) + PIER * 4) / 2 - 60
B_R = -B_L
PORTAL_X = 1640     # tunnel mouth (left jamb)
PORTAL_W = 130
TUN_L = 800         # tunnel length in world px (≈ 38 m)


def _arches():
    out, x = [], B_L + 60
    for s in SPANS:
        out.append((x, x + s))
        x += s + PIER
    return out


ARCHES = _arches()


def ponte_strokes():
    main, detail, faint = [], [], []
    # coping and cornice under the road (the road line itself is the top of the bridge)
    detail.append([(B_L - 10, 12), (B_R + 10, 12)])
    detail.append([(B_L + 4, 30), (B_R - 4, 30)])
    # arches and piers
    for i, (x0, x1) in enumerate(ARCHES):
        r = (x1 - x0) / 2
        cx = x0 + r
        main.append([(x0, WATER + 8), (x0, SPRING)] + arc(cx, SPRING, r, math.pi, 2 * math.pi, 26) + [(x1, WATER + 8)])
        detail.append(arc(cx, SPRING, r + 22, math.pi * 1.02, math.pi * 1.98, 26))
        for j in range(1, 12):
            ang = math.pi + j * math.pi / 12
            detail.append([(cx + math.cos(ang) * r, SPRING + math.sin(ang) * r),
                           (cx + math.cos(ang) * (r + 22), SPRING + math.sin(ang) * (r + 22))])
    # cutwaters at the piers and the little aediculae (niches with a pediment) above them
    for i in range(4):
        px0, px1 = ARCHES[i][1], ARCHES[i + 1][0]
        pc = (px0 + px1) / 2
        detail.append([(px0 + 4, WATER - 2), (pc, WATER - 28), (px1 - 4, WATER - 2)])
        ny = 74
        detail.append([(pc - 19, ny + 64), (pc - 19, ny + 12), (pc + 19, ny + 12), (pc + 19, ny + 64), (pc - 19, ny + 64)])
        detail.append([(pc - 27, ny + 12), (pc, ny - 7), (pc + 27, ny + 12), (pc - 27, ny + 12)])
        detail.append([(pc - 23, ny + 70), (pc + 23, ny + 70)])
    # abutments down to the banks
    main.append([(B_L - 10, 0), (B_L - 4, 120), (B_L + 60, WATER + 8)])
    main.append([(B_R + 10, 0), (B_R + 4, 120), (B_R - 60, WATER + 8)])
    # a few stone courses on the spandrels
    rng = random.Random(4)
    for k in range(18):
        x = rng.uniform(B_L + 80, B_R - 80)
        y = rng.uniform(40, 66)
        faint.append([(x, y), (x + rng.uniform(26, 50), y)])
    return main, detail, faint


P_MAIN, P_DETAIL, P_FAINT = ponte_strokes()


def roccia_strokes():
    """The Furlo cliff: a near rock face with the tunnel at its foot, strata, the far wall of the gorge."""
    rng = random.Random(76)
    main, detail, far = [], [], []
    face = [(1612, 0), (1598, -70), (1572, -128), (1588, -200), (1552, -290), (1568, -360), (1530, -452),
            (1550, -530), (1506, -612), (1522, -690), (1482, -780), (1560, -832), (1640, -850), (1720, -906),
            (1820, -890), (1900, -942), (2000, -926), (2120, -982), (2260, -962), (2400, -1012), (2600, -990),
            (2900, -1042), (3300, -1000)]
    main.append({"p": face, "smooth": False})
    # below the road: the cliff drops to the river
    main.append({"p": [(1612, 22), (1594, 90), (1622, 168), (1604, 246), (1640, 330)], "smooth": False})
    # retaining wall of the road ledge, left of the cliff
    main.append([(1040, 22), (1612, 22)])
    detail.append([(1050, 22), (1080, 120), (1150, 230), (1200, 330)])
    detail.append([(1080, 56), (1604, 56)])
    # limestone beds: short broken lines roughly parallel, sloping gently
    for row in range(8):
        y0 = -110 - row * 92
        x = 1620 - row * 8 + rng.uniform(0, 40)
        while x < 3000:
            L = rng.uniform(90, 260)
            y = y0 + (x - 1600) * -0.12
            mx_ = x + L / 2
            in_label = 1740 < mx_ < 2560 and -600 < y < -230
            if y > -980 - (x - 1600) * 0.05 and not in_label and \
                    not (PORTAL_X - 30 < x + L and x < PORTAL_X + PORTAL_W + 40 and y > -200):
                detail.append([(x, y), (x + L * 0.5, y - L * 0.06 + rng.uniform(-4, 4)), (x + L, y - L * 0.12)])
            x += L + rng.uniform(40, 140)
    # cracks
    for x0, y0 in ((1700, -380), (2050, -600), (2330, -260), (2700, -480)):
        detail.append({"p": [(x0, y0), (x0 + 12, y0 + 50), (x0 - 4, y0 + 96), (x0 + 10, y0 + 140)], "smooth": False})
    # little shrubs on the ledges of the face
    for x0, y0 in ((1590, -200), (1556, -455), (1525, -690), (1700, -900), (2130, -982)):
        detail.append([(x0, y0), (x0 + 6, y0 - 22)])
        detail.append([(x0 + 4, y0), (x0 + 18, y0 - 16)])
        detail.append([(x0 - 2, y0), (x0 - 12, y0 - 14)])
    # the far wall of the gorge, behind
    far.append({"p": [(940, 6), (990, -60), (1060, -80), (1100, -190), (1180, -210), (1220, -330), (1300, -350),
                      (1330, -480), (1400, -500), (1430, -640), (1480, -660)], "smooth": False})
    far.append({"p": [(1000, -40), (1040, -10)], "smooth": False})
    far.append({"p": [(1120, -170), (1160, -140)], "smooth": False})
    far.append({"p": [(1250, -320), (1290, -290)], "smooth": False})
    # lower rock under the road ledge, down to the river
    for row in range(3):
        y = 90 + row * 80
        detail.append([(1660 + row * 30, y), (1900 + row * 40, y - 12), (2140, y - 20)])
        detail.append([(2300 + row * 60, y - 26), (2600, y - 40)])
    return main, detail, far


R_MAIN, R_DETAIL, R_FAR = roccia_strokes()


def portale():
    x0, x1, top = PORTAL_X, PORTAL_X + PORTAL_W, -150
    cx, r = (x0 + x1) / 2, PORTAL_W / 2
    outer = [(x0 - 20, 0), (x0 - 20, top + r)] + arc(cx, top + r, r + 20, math.pi, 2 * math.pi, 22) + \
            [(x1 + 20, top + r), (x1 + 20, 0)]
    inner = [(x0, 0), (x0, top + r)] + arc(cx, top + r, r, math.pi, 2 * math.pi, 22) + [(x1, top + r), (x1, 0)]
    deep = [(x0 + 24, 0), (x0 + 24, top + r + 16)] + arc(cx, top + r + 16, r - 24, math.pi, 2 * math.pi, 16) + \
           [(x1 - 24, top + r + 16), (x1 - 24, 0)]
    deeper = [(x0 + 42, 0), (x0 + 42, top + r + 34)] + arc(cx, top + r + 34, r - 42, math.pi, 2 * math.pi, 12) + \
             [(x1 - 42, top + r + 34), (x1 - 42, 0)]
    return outer, inner, deep, deeper


PORTALE = portale()


def strada_ponti():
    pts = [(-1600, 6), (-1200, 4), (B_L - 10, 0)]
    pts += [(x, 0) for x in range(int(B_L) + 100, int(B_R), 140)]
    pts += [(B_R + 10, 0), (1000, 0), (1300, 0), (PORTAL_X - 20, 0), (PORTAL_X + PORTAL_W / 2, 0)]
    return pts


STRADA_PONTI = strada_ponti()


def cam_ponti(t):
    """(world centre x, y, zoom): overview -> the bridge -> the Furlo cliff."""
    A = (880.0, -190.0, 0.56)
    B = (0.0, 60.0, 1.0)
    C = (1900.0, -130.0, 0.84)
    u = ease_io(win(t, 7.0, 9.4))
    p = (lerp(A[0], B[0], u), lerp(A[1], B[1], u), math.exp(lerp(math.log(A[2]), math.log(B[2]), u)))
    u = ease_io(win(t, 14.2, 17.0))
    p = (lerp(p[0], C[0], u), lerp(p[1], C[1], u), math.exp(lerp(math.log(p[2]), math.log(C[2]), u)))
    d = smooth(win(t, 16.0, 27.5))              # a slow push towards the tunnel during the long hold
    return (p[0] - 60 * d, p[1] + 20 * d, p[2] * (1 + 0.07 * d))


def auto(pen, x, y, alpha, seed, s=1.25):
    """A small round modern car, side view, wheels turning; (x, y) = point under the front bumper."""
    with at(pen, x, y, s):
        body = [(-110, -16), (-112, -36), (-90, -44), (-66, -70), (-14, -72), (10, -46), (34, -40), (38, -18),
                (30, -12)]
        pen.line(body, 1.0, alpha, seed=seed)
        pen.line([(-110, -16), (-96, -12)], 1.0, alpha, seed=seed + 1)
        pen.line([(-58, -12), (-16, -12)], 1.0, alpha, seed=seed + 2)
        pen.line([(-74, -46), (-60, -62), (-40, -63), (-40, -46), (-74, -46)], 0.7, alpha, seed=seed + 3,
                 smooth_=False)
        pen.line([(-34, -63), (-16, -62), (0, -46), (-34, -46), (-34, -63)], 0.7, alpha, seed=seed + 4, smooth_=False)
        for k, wx in enumerate((-77, 4)):
            pen.line(ellipse(wx, -14, 14, 14, 16), 1.0, alpha, seed=seed + 5 + k, closed=True)
            a = -(x + wx * s) / (14 * s)
            pen.line([(wx + math.cos(a) * 7, -14 + math.sin(a) * 7), (wx - math.cos(a) * 7, -14 - math.sin(a) * 7)],
                     0.6, alpha, seed=seed + 7)
        pen.dot(36, -30, 3, alpha)


def bici(pen, x, y, alpha, seed, s=1.0):
    """A bicycle doodle; (x, y) = middle of the wheelbase on the ground."""
    with at(pen, x, y, s):
        r = 30
        wl, wr = (-58, -r), (58, -r)
        strokes = [ellipse(wl[0], wl[1], r, r, 22), ellipse(wr[0], wr[1], r, r, 22),
                   [wl, (-6, -r), (26, -70), (-20, -70), (-6, -r)],
                   [(26, -70), wr], [(26, -70), (30, -84), (44, -88)],
                   [(-20, -70), (-24, -80)], [(-34, -82), (-12, -82)]]
        pen.lines(strokes, 1.0, 0.0, alpha, 0.85, seed=seed)


def cane(pen, x, y, t, alpha, seed, s=1.0):
    """A small trotting dog with a wagging tail; (x, y) = feet, facing right."""
    with at(pen, x, y, s):
        ph = t * 2 * math.pi * 1.6
        b = -abs(math.sin(ph)) * 3
        pen.line([(-30, -34 + b), (-6, -38 + b), (18, -36 + b), (24, -26 + b), (-26, -22 + b), (-30, -34 + b)], 0.9, alpha,
                 seed=seed)
        pen.line([(18, -36 + b), (24, -52 + b), (40, -54 + b), (46, -46 + b), (34, -38 + b), (24, -34 + b)], 0.9, alpha,
                 seed=seed + 1)
        pen.line([(26, -52 + b), (22, -62 + b), (32, -56 + b)], 0.7, alpha, seed=seed + 2)
        pen.dot(36, -48 + b, 1.8, alpha)
        wag = math.sin(t * 14) * 8
        pen.line([(-30, -32 + b), (-42, -44 + b + wag * 0.3), (-46 + wag * 0.4, -54 + b)], 0.8, alpha, seed=seed + 3)
        for k, (lx, p0) in enumerate(((-22, 0.0), (-14, math.pi), (10, math.pi), (18, 0.0))):
            sw = math.sin(ph + p0) * 7
            pen.line([(lx, -24 + b), (lx + sw, 0)], 0.8, alpha, seed=seed + 4 + k)


@scena("ponti")
def ponti(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    cx, cy, z = cam_ponti(t)
    ox, oy = W / 2 - cx * z, H / 2 - cy * z

    def S(p):
        return (ox + p[0] * z, oy + p[1] * z)

    with at(pen, ox, oy, z):
        # ---- the river under the bridge: banks, flowing ripples, broken reflections
        kb = win(t, 0.2, 2.2)
        pen.lines([[(-1800, WATER + 40), (-1300, WATER + 36), (-940, WATER + 14), (B_L + 40, WATER + 10)],
                   [(B_R - 40, WATER + 10), (900, WATER + 26), (1060, WATER + 60)]], kb, vanish, 0.55, 0.8, seed=900)
        rng = random.Random(7)
        rip = []
        for i in range(26):
            x0 = rng.uniform(-900, 900)
            y0 = WATER + rng.uniform(22, 130)
            ph = rng.uniform(0, 6.28)
            dx = (t * 24 + x0 + 900) % 1800 - 900
            L = 40 + 18 * math.sin(t * 1.3 + ph)
            rip.append([(dx, y0), (dx + L * 0.5, y0 - 3), (dx + L, y0)])
        pen.lines(rip, win(t, 0.6, 2.6), vanish, 0.36, 0.6, seed=905)
        refl = []
        for i, (x0, x1) in enumerate(ARCHES):
            r = (x1 - x0) / 2
            c = x0 + r
            for j in range(4):
                yy = WATER + 20 + j * 17
                hw = r * (0.92 - j * 0.18) + 6 * math.sin(t * 2 + i + j)
                refl.append([(c - hw, yy), (c - hw * 0.4, yy + 1)])
                refl.append([(c + hw * 0.4, yy + 1), (c + hw, yy)])
        pen.lines(refl, win(t, 1.6, 3.4), vanish, 0.2, 0.6, seed=910)
        # ---- the bridge
        pen.lines(P_MAIN, win(t, 0.4, 3.4), vanish, 1.0, 1.0, seed=920)
        pen.lines(P_DETAIL, win(t, 2.0, 9.6), vanish, 0.7, 0.75, seed=930)
        pen.lines(P_FAINT, win(t, 8.0, 10.0), vanish, 0.35, 0.6, seed=950)
        # ---- the cliff, the gorge, the tunnel
        km = win(t, 3.4, 6.2)
        pen.lines(R_FAR, km, vanish, 0.3, 0.8, seed=960)
        pen.lines(R_MAIN, km, vanish, 0.95, 1.0, seed=970)
        pen.lines(R_DETAIL, win(t, 4.6, 8.0), vanish, 0.42, 0.65, seed=980)
        kt = win(t, 4.8, 6.8)
        pen.lines([PORTALE[0], PORTALE[1]], kt, vanish, 1.0, 1.0, seed=990)
        pen.lines([PORTALE[2], PORTALE[3]], kt, vanish, 0.4, 0.7, seed=993)
        rip2 = []
        pen.lines([[(1250, 350), (1650, 344), (2400, 350), (3200, 346)]], win(t, 3.8, 5.8), vanish, 0.45, 0.8, seed=994)
        for i in range(16):
            x0 = 1250 + ((i * 197 + t * 22) % 2000)
            y0 = 380 + (i * 37) % 90
            rip2.append([(x0, y0), (x0 + 26, y0 - 2), (x0 + 52, y0)])
        pen.lines(rip2, win(t, 3.8, 5.8), vanish, 0.3, 0.6, seed=995)
        # ---- the tunnel through the rock, and its length
        if t > 20.4:
            k = ease_io(win(t, 20.4, 21.8))
            x0, x1 = PORTAL_X + PORTAL_W / 2, PORTAL_X + TUN_L
            dashed(pen, [(x0, -60), (x1, -60)], 0.55 * a, k, vanish, 0.7, 16, 12, seed=1000)
            yy = -300
            pen.line([(x0, yy), (lerp(x0, x1, k), yy)], 0.8, 0.85 * a, 1.0, vanish, seed=1010)
            ke = win(t, 21.6, 21.9)
            for xx, sg in ((x0, 1), (x1, -1)):
                pen.line([(xx + 18 * sg, yy - 12), (xx, yy), (xx + 18 * sg, yy + 12)], 0.8, 0.85 * a, ke, vanish,
                         seed=1011)
                pen.line([(xx, yy + 20), (xx, yy + 200)], 0.5, 0.35 * a, ke, vanish, seed=1012)
        # ---- today: someone walking a bicycle across the bridge, a dog trotting along
        if 10.4 < t < 19.0:
            kx = win(t, 10.6, 19.0)
            px = lerp(B_L + 40, B_R + 120, kx)
            al = a * smooth(win(t, 10.4, 11.2))
            bici(pen, px + 84, -1, al, 1020, 0.72)
            omino(pen, px, 0, 0.44, t, "moderno", walk=1.0, speed=0.9, expr="smile", alpha=al,
                  arm_f=(-0.1, 0.15), seed=11)
            cane(pen, px - 90, 0, t, al, 1040, 0.9)
        # ---- the car driving into the tunnel
        if t > 22.2:
            u = win(t, 22.3, 25.8)
            x = lerp(760, PORTAL_X + 300, u * (0.4 + 0.6 * u))
            ctx = pen.ctx
            ctx.save()
            ctx.rectangle(-5000, -2000, PORTAL_X + PORTAL_W + 5000, 4000)
            ctx.clip()
            inside = smooth(win(x, PORTAL_X + 20, PORTAL_X + 160))
            auto(pen, x, 0, a * smooth(win(t, 22.2, 22.8)) * (1 - 0.65 * inside), 1030)
            ctx.restore()
    # ---- labels (screen space)
    if t > 7.8:
        x, y = S((0, -300))
        pen.text("Ponte di Tiberio", x, y, 66, a, reveal=win(t, 7.8, 8.9))
        pen.text("Rimini", x - 16, y + 62, 42, 0.8 * a, align="right", reveal=win(t, 8.9, 9.6))
        if t > 11.0:
            pen.text("·  21 d.C.", x - 4, y + 62, 42, 0.8 * a, align="left", reveal=win(t, 11.0, 11.8))
    if t > 15.4:
        x, y = S((1180, 96))
        pen.text("via Flaminia", x, y, 38, 0.65 * a, reveal=win(t, 15.4, 16.4))
    if t > 16.7:
        x, y = S((PORTAL_X + TUN_L / 2 + 40, -500))
        pen.text("Galleria del Furlo", x, y, 64, a, reveal=win(t, 16.7, 17.9))
        if t > 18.9:
            pen.text("76 d.C.", x, y + 56, 42, 0.8 * a, reveal=win(t, 18.9, 19.6))
    if t > 21.4:
        x, y = S((PORTAL_X + TUN_L / 2 + 30, -300))
        pen.text("≈ 38 m", x, y - 22, 48, a * smooth(win(t, 21.4, 22.0)), reveal=win(t, 21.4, 22.2))
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
    """Procedural web: real towns + random villages on land inside the empire, joined by a spanning tree of
    short land links plus a few loops between major towns. Grows outward from Rome."""
    rng = random.Random(150)
    nodes = list(NODI)
    NM = len(NODI)
    tries = 0
    while len(nodes) < NM + 300 and tries < 20000:
        tries += 1
        lo, la = rng.uniform(-10, 41), rng.uniform(23, 56)
        if _on(lo, la, LAND) and _on(lo, la, EMP):
            if all(math.hypot((lo - x) * 0.77, la - y) > 0.6 for x, y in nodes):
                nodes.append((lo, la))
    n = len(nodes)
    P = np.array(nodes)
    Q = np.column_stack((P[:, 0] * 0.77, P[:, 1]))

    def ln(i, j):
        return math.hypot(Q[j, 0] - Q[i, 0], Q[j, 1] - Q[i, 1])
    cand = {}
    for i in range(n):
        d = np.hypot(Q[:, 0] - Q[i, 0], Q[:, 1] - Q[i, 1])
        d[i] = 1e9
        for j in np.argsort(d)[:6]:
            if d[j] > 3.4:
                continue
            a, b = nodes[i], nodes[j]
            ok = sum(_on(lerp(a[0], b[0], f), lerp(a[1], b[1], f), LAND) for f in (0.2, 0.35, 0.5, 0.65, 0.8))
            if ok >= 4:
                cand[(min(i, j), max(i, j))] = float(d[j])
    # Kruskal: a spanning tree of the shortest links
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    edges = set()
    for (i, j), L in sorted(cand.items(), key=lambda kv: kv[1]):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj
            edges.add((i, j))
    for (i, j), L in sorted(cand.items()):
        if (i, j) not in edges and rng.random() < (0.55 if (i < NM and j < NM) else 0.08):
            edges.add((i, j))
    # prune links making a tiny angle with a shorter one at the same node (keeps it road-like)
    adj = {}
    for i, j in edges:
        adj.setdefault(i, []).append(j)
        adj.setdefault(j, []).append(i)

    def ang(i, j):
        return math.atan2(Q[j, 1] - Q[i, 1], Q[j, 0] - Q[i, 0])
    drop = set()
    for i, nb in adj.items():
        for x in nb:
            for y in nb:
                if x < y:
                    da = abs((ang(i, x) - ang(i, y) + math.pi) % (2 * math.pi) - math.pi)
                    if da < 0.4:
                        drop.add((min(i, x), max(i, x)) if ln(i, x) > ln(i, y) else (min(i, y), max(i, y)))
    edges = sorted(edges - drop)
    # distance from Rome along the web (Dijkstra), with invisible sea hops between separate pieces
    g = [[] for _ in range(n)]
    for i, j in edges:
        g[i].append((j, ln(i, j)))
        g[j].append((i, ln(i, j)))
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
    while max(dist) > 1e8:
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
        off = rng.uniform(-0.08, 0.08) * L
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        nx, ny = -(b[1] - a[1]), (b[0] - a[0])
        nn = math.hypot(nx, ny) or 1
        c = (mx + nx / nn * off, my + ny / nn * off)
        q = [((1 - u) ** 2 * a[0] + 2 * u * (1 - u) * c[0] + u * u * b[0],
              (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * c[1] + u * u * b[1]) for u in (0, 0.25, 0.5, 0.75, 1.0)]
        out.append(dict(p=np.array(q), d0=dist[i], L=L, solid=False))
    # ~2.7 % of the total length stays "known precisely": a few scattered short pieces
    tot = sum(e["L"] for e in out)
    order = list(range(len(out)))
    rng.shuffle(order)
    acc = 0.0
    for k in order:
        if acc > 0.027 * tot:
            break
        if out[k]["L"] < 1.5:
            out[k]["solid"] = True
            acc += out[k]["L"]
    dmax = max(e["d0"] + e["L"] for e in out)
    return out, dmax


RETE, RETE_DMAX = _rete()
RETE_P = np.array([e["p"] for e in RETE])          # (edges, 5, 2) lon/lat, gently curved
RETE_D0 = np.array([e["d0"] for e in RETE])
RETE_L = np.array([e["L"] for e in RETE])
RETE_KM = 299171            # Itiner-e (2025): total length of the reconstructed network, km
EARTH_KM = 40075


class Globo:
    """Blend between an equirectangular map (h = 0) and an orthographic globe (h = 1).
    k = R·π/180 px per degree so that the two agree at the centre."""

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
        h = self.h
        return np.stack((px + (self.cx + x - px) * h, py + (self.cy - y - py) * h), -1), dep


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


# the yarn: 7.47 laps (299,171 / 40,075 km). Each lap is a great circle tilted 70° to the line of sight; the
# tilt direction turns a full revolution over all the laps, so the string wraps the globe evenly.
YARN_TURNS = RETE_KM / EARTH_KM
YARN_TAU = math.radians(70.0)


def yarn_xy(g, s1, s0=0.0, step=1 / 140):
    """Screen points and depth of the yarn between laps s0..s1 on globe g."""
    s = np.arange(s0, s1, step)
    s = np.append(s, s1)
    phi = 0.35 + 2 * math.pi * s / YARN_TURNS
    th = math.pi / 2 + 2 * math.pi * s                  # starts at the centre of the disc: Rome
    tau = math.pi / 2 + (YARN_TAU - math.pi / 2) * np.clip(s / 0.7, 0, 1) ** 0.7
    ct, st = np.cos(tau), np.sin(tau)
    # in screen axes (x right, y up, z towards us): A in the screen plane, B mostly towards the viewer
    Ax, Ay = -np.sin(phi), np.cos(phi)
    Bx, By, Bz = -ct * np.cos(phi), -ct * np.sin(phi), st
    x = np.cos(th) * Ax + np.sin(th) * Bx
    y = np.cos(th) * Ay + np.sin(th) * By
    z = np.sin(th) * Bz
    return np.column_stack((g.cx + g.R * x, g.cy - g.R * y)), z


GLOBE_R, GLOBE_X, GLOBE_Y = 340.0, 800.0, 540.0
GC_LON = 16.0
COL_X = 1470.0                        # text column next to the globe


def cam_mondo(t):
    """Stage 1: zoom out from Italy over the empire. Stage 2: the map curls into a globe.
    Stage 3: it uncurls back into the map of the empire."""
    u1 = ease_io(win(t, 1.6, 7.0))
    k = math.exp(lerp(math.log(92.0), math.log(33.0), u1))
    lon, lat = lerp(12.7, 16.0, u1), lerp(42.9, 41.2, u1)
    cx, cy = W / 2, lerp(H / 2, 520.0, u1)
    u2 = ease_io(win(t, 14.9, 17.3))
    h = smooth(win(t, 14.5, 16.6))
    R = math.exp(lerp(math.log(k * 180 / math.pi), math.log(GLOBE_R), u2))
    lon, lat = lerp(lon, 12.49, u2), lerp(lat, 41.89, u2)       # the globe is centred on Rome
    cx, cy = lerp(cx, GLOBE_X, u2), lerp(cy, GLOBE_Y, u2)
    u3 = ease_io(win(t, 19.9, 21.9))
    h *= 1 - smooth(win(t, 19.9, 21.6))
    R = math.exp(lerp(math.log(R), math.log(28.0 * 180 / math.pi), u3))
    lon, lat = lerp(lon, 16.0, u3), lerp(lat, 41.0, u3)
    cx, cy = lerp(cx, W / 2, u3), lerp(cy, 470.0, u3)
    return Globo(lon, lat, R, cx, cy, h)


def _fmt(n):
    return f"{n:,}".replace(",", ".")


def grat(g):
    """Meridians and parallels on the globe (front-facing parts)."""
    out = []
    for lo in range(-180, 180, 30):
        ll = np.column_stack((np.full(61, lo, float), np.linspace(-90, 90, 61)))
        xy, d = g.arr(ll)
        out += _runs_mask(xy.tolist(), d > 0.03)
    for la in (-60, -30, 0, 30, 60):
        ll = np.column_stack((np.linspace(-180, 180, 121), np.full(121, la, float)))
        xy, d = g.arr(ll)
        out += _runs_mask(xy.tolist(), d > 0.03)
    return out


VIE_ARR = {k: np.array(v, float) for k, v in VIE.items()}


def _punti(pen, pts, alpha, step=6.0, r=1.25):
    """Dotted rendition of a polyline (a reconstructed, uncertain route): fine, evenly spaced dots."""
    if alpha <= 0.01:
        return
    from motore.linea import resample_step
    P = resample_step(pts, step)
    ctx = pen.ctx
    from motore.linea import INK
    ctx.set_source_rgba(INK[0], INK[1], INK[2], alpha)
    for x, y in P[1:-1]:
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.new_sub_path()
    ctx.fill()


@scena("mondo")
def mondo(pen, t, T, appear, vanish):
    a = 1.0 - vanish
    g = cam_mondo(t)
    h = g.h
    u2 = ease_io(win(t, 14.9, 17.3))
    u3 = ease_io(win(t, 19.9, 21.9))
    # --- coastlines (map, then globe, then map again)
    rv = smooth(win(t, 0.0, 2.4))
    for i, c in enumerate(COSTE):
        bb = COSTE_BB[i]
        near = bb[0] > GC_LON - 60 and bb[2] < GC_LON + 60 and bb[1] > 10 and bb[3] < 70
        if h <= 0.001:
            if not near and not (bb[2] > -40 and bb[0] < 70 and bb[3] > 0 and bb[1] < 75):
                continue
            xy, _ = g.arr(c)
            for r in runs_inside(xy, 50):
                pen.line(r.tolist(), 0.7, 0.42, rv, vanish, smooth_=False, seed=500 + i, step=5.5)
            continue
        al = 0.42 if near else 0.42 * h * h
        if al < 0.01:
            continue
        xy, dep = g.arr(c)
        vis = dep > 0.0
        if not vis.any():
            continue
        for r in _runs_mask(xy.tolist(), vis):
            pen.line(r, 0.7, al, rv, vanish, smooth_=False, seed=500 + i, step=6.0)
    # --- globe graticule (the outline of the globe is the road itself)
    if h > 0.05:
        kg = smooth(win(h, 0.35, 1.0))
        pen.lines(grat(g), kg, vanish, 0.15 * a, 0.55, seed=1110)
    dots = smooth(win(t, 20.8, 22.0))
    ksolid = smooth(win(t, 21.2, 22.0))
    # --- the six main roads (a quick recap at the start)
    for j, (name, ll) in enumerate(VIE_ARR.items()):
        xy, dep = g.arr(ll)
        if name != "Flaminia":
            rv_ = ease_io(win(t, 0.6 + j * 0.3, 2.0 + j * 0.3))
            pen.line(xy.tolist(), 0.95, 0.9 * a * (1 - dots), rv_, vanish, seed=1200 + j)
        if dots > 0:
            _punti(pen, xy.tolist(), 0.85 * a * dots, 7.0, 1.6)
    # --- the web grows out of Rome
    grow = ease_io(win(t, 4.6, 14.2)) * RETE_DMAX
    if grow > 0:
        XY, DEP = g.arr(RETE_P)
        live = np.flatnonzero(RETE_D0 < grow)
        for k in live:
            e = RETE[k]
            if h > 0 and DEP[k].min() < 0:
                continue
            x, y = XY[k, :, 0], XY[k, :, 1]
            if x.max() < -20 or x.min() > W + 20 or y.max() < -20 or y.min() > H + 20:
                continue
            r = min(1.0, (grow - e["d0"]) / e["L"])
            pts = XY[k].tolist()
            if e["solid"]:
                pen.line(pts, 0.6 + 0.6 * ksolid, (0.62 + 0.38 * ksolid) * a, r, vanish, smooth_=False, seed=1300)
            else:
                if dots < 1:
                    pen.line(pts, 0.55, 0.62 * a * (1 - dots), r, vanish, smooth_=False, seed=1300, step=5.0)
                if dots > 0:
                    _punti(pen, pts, 0.7 * a * dots)
    # --- counter: the length of the web
    if t > 4.8:
        km = RETE_KM * clamp(grow / RETE_DMAX)
        s = "≈ " + _fmt(int(round(km / 1000.0)) * 1000) + " km"
        x, y = lerp(W / 2, COL_X, u2), lerp(968, 330, u2)
        pen.text(s, x, y, lerp(78, 66, u2), a * smooth(win(t, 4.8, 5.6)) * (1 - u3))
        cap = smooth(win(t, 6.6, 7.4)) * (1 - u2)
        if cap > 0.01:
            pen.text("Itiner-e · 2025", W / 2 - 24, 1030, 32, 0.6 * a * cap, align="right", reveal=win(t, 6.6, 7.6))
        cap2 = smooth(win(t, 11.6, 12.4)) * (1 - u2)
        if cap2 > 0.01:
            pen.text("strade dell'impero, ~150 d.C.", W / 2 + 24, 1030, 32, 0.6 * a * cap2, align="left",
                     reveal=win(t, 11.6, 12.8))
    # --- the yarn: more than seven times around the Earth
    s1 = YARN_TURNS * ease_io(win(t, 16.6, 19.6))
    s0 = YARN_TURNS * smooth(win(t, 19.6, 20.5))
    if s1 > 0.002 and s0 < YARN_TURNS - 0.01 and h > 0.9:
        xy, dep = yarn_xy(g, s1, s0)
        pts = xy.tolist()
        for r in _runs_mask(pts, dep <= 0):
            pen.line(r, 0.55, 0.2 * a, seed=1401, step=8.0)
        for r in _runs_mask(pts, dep > 0):
            pen.line(r, 0.9, 0.9 * a, seed=1400, step=6.0)
        if s1 < YARN_TURNS - 0.01:
            pen.dot(pts[-1][0], pts[-1][1], 5, a * (1.0 if dep[-1] > 0 else 0.35))
    if t > 16.6:
        laps = YARN_TURNS * ease_io(win(t, 16.6, 19.6))
        fa = a * smooth(win(t, 16.6, 17.2)) * (1 - u3)
        s = f"× {min(7, max(1, math.ceil(laps - 1e-6)))}" if laps < YARN_TURNS - 0.01 else "× 7,5"
        pen.text(s, COL_X, 520, 96, fa)
        pen.text("più di 7 volte", COL_X, 606, 42, 0.85 * fa, reveal=win(t, 17.6, 18.4))
        pen.text("il giro della Terra", COL_X, 654, 42, 0.85 * fa, reveal=win(t, 18.0, 18.9))
    # --- legend: what we know precisely
    if t > 21.2:
        k = win(t, 21.2, 22.0)
        x0, y0 = W / 2 - 230, 918
        pen.line([(x0, y0 - 10), (x0 + 70, y0 - 10)], 1.25, a, k, vanish, seed=1500)
        pen.text("tracciato esatto: ~2,7%", x0 + 96, y0, 40, a, align="left", reveal=win(t, 21.4, 22.4))
        _punti(pen, [(x0, y0 + 46), (x0 + 70, y0 + 46)], 0.85 * a * smooth(k), 7.0, 1.6)
        pen.text("ricostruito", x0 + 96, y0 + 56, 40, 0.7 * a, align="left", reveal=win(t, 21.9, 22.7))
    # --- the road: the Flaminia on the map -> the outline of the Earth -> the Appia on the map
    fl = g.arr(VIE_ARR["Flaminia"])[0].tolist()
    circle = ellipse(g.cx, g.cy, g.R, g.R, 96, a0=-math.pi * 0.62)
    ap = g.arr(np.array(resample(VIE["Appia"], 40)))[0].tolist()
    m1 = ease_io(win(t, 16.0, 17.3))
    m2 = ease_io(win(t, 20.0, 21.9))
    if m1 <= 0:
        return fl
    if m1 < 1:
        return morph(fl, circle, m1, 120)
    if m2 <= 0:
        return circle
    if m2 < 1:
        return morph(circle, ap, m2, 120)
    return ap
