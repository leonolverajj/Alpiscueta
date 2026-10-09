"""Original characters for 'La Idea de Dios', drawn in the flat-2D ink style.

All coordinates are local: a head is ~200 units tall at s=1, facing right (fx=1).
Use kit.at(ctx, x, y, s, fx=±1) to place them.
"""
import math
import random

from .kit import (P, at, blade, catmull, cel, circle_pts, clip, col, ease_out, fillp, glow, hatch, lerp,
                  mix, poly, setc, shape, spikes, stroke, ss)

# ----------------------------------------------------------------- character presets
HERO = dict(hair="spiky", hair_c="hair_dk", hair_s="ink2", skin="skin", skin_s="skin_s", eye="teal",
            coat="coat", coat_s="coat_s", lining="red", collar="high", armor="steel", strap="g5")
SAGE = dict(hair="long", hair_c="hair_white", hair_s="hair_white_s", skin="skin2", skin_s="skin2_s",
            eye="g5", beard="long", coat=mix("rust", "g5", 0.45), coat_s="rust_d", lining="gold",
            collar="hood", armor=None, strap="gold_d")
NIETZSCHE = dict(hair="swept", hair_c="g5", hair_s="g6", skin="skin", skin_s="skin_s", eye="g6",
                 mustache="huge", coat="g6", coat_s="ink2", lining="g4", collar="suit", armor=None,
                 strap=None, brow="heavy")
STUDENT = dict(hair="short", hair_c="hair_gold", hair_s="hair_gold_s", skin="skin", skin_s="skin_s",
               eye="cobalt", coat="g4", coat_s="g5", lining="cobalt", collar="high", armor=None, strap=None)
RASKOL = dict(hair="messy", hair_c="hair_dk", hair_s="ink2", skin=mix("skin", "g2", 0.35), skin_s="skin_s",
              eye="g5", coat=mix("g5", "rust_d", 0.2), coat_s="g6", lining="g4", collar="ragged", armor=None,
              strap=None, gaunt=True)
LECTURER = dict(hair="side", hair_c="g4", hair_s="g5", skin="skin", skin_s="skin_s", eye="cobalt",
                coat="cobalt_d", coat_s="ink2", lining="g2", collar="suit", armor=None, strap=None, tie="red")
WOMAN = dict(hair="bob", hair_c="hair_dk", hair_s="ink2", skin="skin2", skin_s="skin2_s", eye="gold",
             coat="g0", coat_s="g2", lining="red", collar="high", armor=None, strap="red", lashes=True)


# ----------------------------------------------------------------- head
def _eye(ctx, x, y, w, iris, expr, front=True, lashes=False, t=0.0):
    h = w * 0.62
    if expr in ("closed", "smile_closed"):
        stroke(ctx, [(x - w / 2, y), (x, y + h * 0.3), (x + w / 2, y - 2)], 4.5, smooth=True, taper=(0.3, 0.3))
        return
    blink = 1.0
    ph = (t * 0.37) % 4.0
    if 2.0 < ph < 2.07:
        blink = 0.15
    lid = [(x - w / 2, y - h * 0.15), (x - w * 0.1, y - h * 0.55 * blink), (x + w / 2, y - h * 0.4 * blink)]
    eye_poly = [(x - w / 2, y - h * 0.15), (x - w * 0.1, y - h * 0.55 * blink), (x + w / 2, y - h * 0.4 * blink),
                (x + w * 0.42, y + h * 0.35 * blink), (x - w * 0.05, y + h * 0.48 * blink),
                (x - w * 0.45, y + h * 0.2 * blink)]
    fillp(ctx, eye_poly, "g0")
    with clip(ctx, eye_poly):
        ix = x + (w * 0.08 if front else w * 0.12)
        fillp(ctx, circle_pts(ix, y + h * 0.05, w * 0.3, 20, ry=w * 0.36), iris)
        fillp(ctx, circle_pts(ix, y + h * 0.15, w * 0.3, 20, ry=w * 0.2), mix(iris, "white", 0.35), alpha=0.6)
        fillp(ctx, circle_pts(ix, y + h * 0.02, w * 0.13, 14, ry=w * 0.2), "ink")
        fillp(ctx, circle_pts(ix + w * 0.1, y - h * 0.15, w * 0.07, 10), "white")
        fillp(ctx, [(x - w, y - h), (x + w, y - h), (x + w, y - h * 0.15), (x - w, y + h * 0.05)], "ink",
              alpha=0.18)
    stroke(ctx, lid, w * 0.16 + 2.5, taper=(0.25, 0.1), smooth=True)
    if lashes:
        stroke(ctx, [lid[-1], (lid[-1][0] + w * 0.18, lid[-1][1] - h * 0.25)], 3.5, taper=(0, 0.8))
    stroke(ctx, [(x - w * 0.2, y + h * 0.5 * blink), (x + w * 0.35, y + h * 0.38 * blink)], 2.0,
           taper=(0.5, 0.5), alpha=0.8)


def head(ctx, c, expr="neutral", t=0.0, wind=0.0, look=0.0):
    """Draw a 3/4 head in local coords (origin = centre of face, facing +x).
    c: character preset dict. expr: neutral|smile|shout|grim|closed|smile_closed|fear|awe."""
    rng = random.Random(7)
    skin, skin_s = c["skin"], c["skin_s"]
    hc, hs = c["hair_c"], c.get("hair_s", "ink2")
    sway = math.sin(t * 1.3) * 3 * (1 + wind)

    # back hair mass
    hair = c.get("hair")
    if hair in ("long", "bob", "swept", "messy", "side"):
        if hair == "long":
            back = [(-40, -80), (-85, -40), (-95, 40), (-90, 120 + sway), (-60, 170 + sway * 1.5),
                    (-30, 130), (-20, 60), (0, -40)]
        elif hair == "bob":
            back = [(-30, -85), (-85, -40), (-92, 30), (-80, 80 + sway), (-40, 92), (-30, 40), (10, -40)]
        else:
            back = [(-30, -88), (-80, -55), (-88, 0), (-78, 40), (-50, 20), (0, -40)]
        shape(ctx, back, hs, 4.5, smooth=True, seed=3)
    elif hair == "spiky":
        for i in range(7):
            a = lerp(-2.7, -1.0, i / 6) + math.sin(t * 2 + i) * 0.03 * (1 + wind)
            L = 95 + rng.uniform(-10, 25)
            p0 = (-15 + i * 4, -40)
            p1 = (p0[0] + math.cos(a) * L - 30 - wind * 20, p0[1] + math.sin(a) * L)
            shape(ctx, blade(p0, p1, 46, bend=0.12), hs, 4, seed=10 + i)

    # neck
    neck = [(-34, 50), (24, 50), (32, 140), (-40, 140)]
    shape(ctx, neck, skin, 4.5, seed=1)
    fillp(ctx, [(-34, 50), (24, 50), (28, 96), (-38, 112)], skin_s)

    # ear
    ear = [(-44, -10), (-62, -22), (-70, 0), (-60, 30), (-44, 26)]
    shape(ctx, ear, skin, 3.5, seed=2)
    fillp(ctx, [(-50, -8), (-60, -10), (-58, 15), (-50, 18)], skin_s)

    # face
    face = [(-58, -70), (-14, -92), (44, -80), (62, -40), (66, 2), (58, 28), (44, 60), (20, 88), (4, 92),
            (-24, 66), (-46, 38), (-60, -6)]
    if c.get("gaunt"):
        face = [(x * 0.95, y) for x, y in face]
    shape(ctx, face, skin, 5, seed=4)
    # cel shadow: back side of face + under hair
    cel(ctx, face, [(-70, -90), (-6, -90), (-14, -40), (-26, 10), (-14, 60), (2, 100), (-70, 100)], skin_s)
    cel(ctx, face, [(-70, -90), (70, -90), (70, -44), (20, -36), (-30, -30), (-70, -20)], skin_s, alpha=0.8)
    if c.get("gaunt"):
        stroke(ctx, [(30, 30), (36, 58)], 2.5, "skin_s", taper=(0.5, 0.5))

    # brows
    brow_w = 7 if c.get("brow") == "heavy" else 5
    by = {"grim": 4, "shout": 6, "fear": -6, "awe": -8}.get(expr, 0)
    stroke(ctx, [(16, -26 + by * 0.4), (34, -32 - by * 0.3), (56, -26 + by)], brow_w + 1, taper=(0.1, 0.6),
           smooth=True)
    stroke(ctx, [(-34, -22 + by), (-18, -28), (-2, -26 + by * 0.4)], brow_w, taper=(0.6, 0.1), smooth=True)

    # eyes
    eye_c = c.get("eye", "g5")
    e = expr if expr in ("closed", "smile_closed") else "open"
    _eye(ctx, 34 + look * 3, -4, 40, eye_c, e, True, c.get("lashes", False), t)
    _eye(ctx, -18 + look * 3, -2, 29, eye_c, e, False, c.get("lashes", False), t + 0.02)

    # nose
    stroke(ctx, [(56, 12), (62, 30), (52, 34)], 3, taper=(0.6, 0.3))
    fillp(ctx, [(46, 18), (56, 14), (52, 33), (44, 32)], skin_s, alpha=0.7)

    # mouth
    mx, my = 32, 60
    if expr in ("shout", "awe", "fear"):
        o = {"shout": 1.0, "awe": 0.55, "fear": 0.7}[expr]
        m = [(mx - 22, my - 6), (mx + 18, my - 8), (mx + 14, my + 14 * o), (mx - 4, my + 22 * o), (mx - 20, my + 8 * o)]
        shape(ctx, m, "ink", 3.5, seed=5)
        if expr == "shout":
            fillp(ctx, [(mx - 18, my - 4), (mx + 14, my - 6), (mx + 12, my), (mx - 16, my + 1)], "g0")
            fillp(ctx, [(mx - 8, my + 10), (mx + 8, my + 8), (mx + 4, my + 18), (mx - 6, my + 18)], "red_l")
    elif expr in ("smile", "smile_closed"):
        stroke(ctx, [(mx - 22, my - 8), (mx - 4, my + 4), (mx + 18, my - 6)], 4, taper=(0.3, 0.3), smooth=True)
    elif expr == "grim":
        stroke(ctx, [(mx - 20, my), (mx, my - 3), (mx + 16, my + 2)], 4, taper=(0.3, 0.3))
    else:
        stroke(ctx, [(mx - 18, my - 2), (mx + 14, my - 3)], 3.5, taper=(0.3, 0.3))

    # facial hair
    if c.get("mustache") == "huge":
        m = [(10, 44), (30, 38), (58, 40), (66, 58), (52, 54), (40, 64), (24, 58), (8, 66), (-6, 58)]
        shape(ctx, m, hc, 4, seed=8)
        hatch(ctx, m, angle=1.2, gap=7, w=1.4, alpha=0.5, seed=8)
    if c.get("beard") == "long":
        sw = math.sin(t * 1.1) * 4
        b = [(-44, 40), (-30, 80), (0, 96), (40, 66), (60, 40), (64, 70), (50, 140 + sw), (20, 200 + sw),
             (0, 230 + sw * 1.4), (-20, 180), (-40, 120)]
        shape(ctx, b, hc, 5, smooth=True, seed=9)
        cel(ctx, b, [(-60, 30), (0, 30), (10, 250), (-60, 250)], hs, smooth=True)
        stroke(ctx, [(10, 60), (40, 50), (60, 58)], 6, hc)
    elif c.get("beard") == "stubble":
        hatch(ctx, [(-40, 50), (0, 92), (50, 60), (40, 90), (0, 102), (-40, 70)], 1.4, 5, 1.2, "ink", 0.35, 4)

    # front hair
    if hair == "spiky":
        bangs = [((-30, -70), (-40, -2)), ((-10, -78), (8, -14)), ((12, -78), (40, -20)), ((30, -70), (66, -8)),
                 ((-40, -66), (-60, 10))]
        top = [(-60, -50), (-50, -96), (-10, -118), (40, -108), (66, -70), (70, -40), (40, -50), (0, -60),
               (-40, -50)]
        shape(ctx, top, hc, 5, seed=11)
        for i, (p0, p1) in enumerate(bangs):
            p1 = (p1[0] + sway * 0.8, p1[1])
            shape(ctx, blade(p0, p1, 34, bend=-0.08 if i % 2 else 0.06), hc, 4, seed=20 + i)
        for i in range(6):
            a = lerp(-2.4, -0.4, i / 5)
            p0 = (lerp(-40, 40, i / 5), -90)
            p1 = (p0[0] + math.cos(a) * 70, p0[1] + math.sin(a) * 60 - 10 + sway * 0.4)
            shape(ctx, blade(p0, p1, 36, bend=0.1), hc, 4, seed=30 + i)
        stroke(ctx, [(-20, -96), (20, -100), (44, -84)], 3, "g0", alpha=0.35, taper=(0.4, 0.4))
    elif hair in ("short", "side", "swept", "messy"):
        if hair == "short":
            top = [(-62, -40), (-58, -96), (-10, -116), (44, -104), (68, -64), (60, -40), (40, -56), (20, -44),
                   (0, -60), (-20, -46), (-40, -60)]
        elif hair == "side":
            top = [(-62, -30), (-60, -92), (-14, -114), (40, -106), (68, -70), (66, -46), (30, -64), (-10, -70),
                   (-40, -56)]
        elif hair == "swept":
            top = [(-64, -20), (-66, -90), (-20, -118), (40, -110), (70, -76), (64, -54), (20, -78), (-30, -72),
                   (-50, -40)]
        else:
            top = [(-66, -10), (-70, -80), (-30, -112), (20, -122), (60, -100), (74, -60), (56, -42), (50, -60),
                   (30, -40), (24, -62), (0, -44), (-12, -64), (-36, -40)]
        shape(ctx, top, hc, 5, seed=12)
        cel(ctx, top, [(-80, -130), (-10, -130), (-30, -30), (-80, -30)], hs)
        hatch(ctx, top, 0.6, 12, 1.4, "ink", 0.3, 12)
    elif hair == "long":
        top = [(-64, -30), (-62, -96), (-10, -120), (46, -104), (70, -60), (58, -50), (20, -80), (-20, -76),
               (-46, -50)]
        shape(ctx, top, hc, 5, smooth=True, seed=13)
        cel(ctx, top, [(-80, -130), (-20, -130), (-40, -30), (-80, -30)], hs)
        hatch(ctx, top, -0.4, 10, 1.4, "ink", 0.3, 13)
    elif hair == "bob":
        top = [(-66, 20), (-70, -80), (-20, -116), (40, -108), (72, -60), (74, -10), (60, -40), (40, -70), (10, -50),
               (-20, -66), (-50, -30), (-56, 30)]
        shape(ctx, top, hc, 5, seed=14)
        cel(ctx, top, [(-80, -130), (-20, -130), (-40, 40), (-80, 40)], hs)
        stroke(ctx, [(-30, -100), (20, -104), (50, -86)], 3, "g0", alpha=0.3, taper=(0.4, 0.4))
    elif hair == "bald":
        cel(ctx, face, [(-70, -100), (70, -100), (70, -70), (-70, -56)], skin_s, alpha=0.4)


# ----------------------------------------------------------------- limbs
def limb(ctx, a, b, c_, w0, w1, color, shade=None, ink=4.5, seed=0):
    """Two-segment limb a->b->c_ (shoulder, elbow, wrist)."""
    def seg(p, q, wa, wb, sd):
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        pts = [(p[0] + nx * wa / 2, p[1] + ny * wa / 2), (q[0] + nx * wb / 2, q[1] + ny * wb / 2),
               (q[0] - nx * wb / 2, q[1] - ny * wb / 2), (p[0] - nx * wa / 2, p[1] - ny * wa / 2)]
        shape(ctx, pts, color, ink, seed=sd)
        if shade:
            cel(ctx, pts, [pts[0], pts[1], lerp_pt(pts[1], pts[2], 0.4), lerp_pt(pts[0], pts[3], 0.4)], shade)
        return pts
    wm = (w0 + w1) / 2
    seg(a, b, w0, wm, seed)
    seg(b, c_, wm, w1, seed + 1)
    fillp(ctx, circle_pts(b[0], b[1], wm / 2 - 2, 12), color)


def lerp_pt(p, q, k):
    return (p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k)


def hand(ctx, x, y, a=0.0, s=1.0, color="ink2", kind="fist", fx=1, shade=None):
    """Gloved hand. kind: fist | open | point | grip."""
    with at(ctx, x, y, s, a, fx=fx):
        if kind == "open":
            palm = [(-14, -16), (16, -18), (22, 14), (-10, 20)]
            shape(ctx, palm, color, 4)
            for i, (dx, L) in enumerate([(-10, 40), (0, 46), (10, 44), (19, 36)]):
                shape(ctx, blade((dx, 10), (dx + 4 + i * 3, 10 + L), 12), color, 3.5, seed=i)
            shape(ctx, blade((-12, 0), (-34, 22), 13), color, 3.5)
        elif kind == "point":
            shape(ctx, [(-16, -14), (16, -16), (20, 16), (-14, 18)], color, 4)
            shape(ctx, blade((10, 0), (58, 4), 13), color, 3.5)
        else:
            fist = [(-18, -16), (14, -20), (24, -4), (22, 18), (-6, 22), (-20, 10)]
            shape(ctx, fist, color, 4.5)
            for i in range(3):
                stroke(ctx, [(4 + i * 7, -14), (8 + i * 7, 14)], 2, "g5", alpha=0.6)
        if shade:
            fillp(ctx, [(-18, 4), (22, 4), (22, 20), (-18, 20)], shade, alpha=0.5)


# ----------------------------------------------------------------- torso / bust
def bust(ctx, c, t=0.0, wind=0.0, breathe=True, width=1.0):
    """Shoulders + chest + coat in local coords (neck base at (0,140))."""
    b = math.sin(t * 1.6) * 3 if breathe else 0
    coat, coat_s = c["coat"], c["coat_s"]
    collar = c.get("collar")
    W2 = 150 * width
    torso = [(-W2 * 1.02, 300 + b), (-W2 * 0.95, 210 + b), (-W2 * 0.62, 158 + b), (-38, 128), (30, 128),
             (W2 * 0.6, 156 + b), (W2 * 0.96, 206 + b), (W2 * 1.04, 300 + b), (W2 * 0.92, 470), (-W2 * 0.95, 470)]
    for side in (-1, 1):
        sl = [(side * W2 * 0.7, 190 + b), (side * W2 * 1.12, 230 + b), (side * W2 * 1.2, 470), (side * W2 * 0.8, 470)]
        shape(ctx, sl, coat if side > 0 else coat_s, 5.5, seed=38 + side)
        stroke(ctx, [(side * W2 * 0.98, 300 + b), (side * W2 * 1.02, 420)], 3, "ink", alpha=0.6)
    shape(ctx, torso, coat, 5.5, seed=40)
    cel(ctx, torso, [(-W2 - 20, 130), (-30, 130), (-60, 440), (-W2 - 20, 440)], coat_s)
    hatch(ctx, [(-W2, 200), (-50, 160), (-70, 420), (-W2, 420)], -1.0, 13, 1.6, "ink", 0.35, 41)
    # lapels / front opening
    if collar == "suit":
        shape(ctx, [(-24, 140), (20, 140), (40, 250), (-2, 330), (-44, 250)], c.get("lining", "g2"), 4, seed=42)
        if c.get("tie"):
            shape(ctx, [(-8, 148), (8, 148), (14, 260), (0, 300), (-14, 260)], c["tie"], 3.5, seed=43)
        stroke(ctx, [(-40, 145), (-70, 260), (-2, 340)], 4.5)
        stroke(ctx, [(30, 145), (66, 262), (-2, 340)], 4.5)
    elif collar == "high":
        col_l = [(-96, 40 + b), (-40, 96), (-30, 170), (-110, 190 + b)]
        col_r = [(74, 30 + b), (28, 94), (24, 170), (100, 186 + b)]
        shape(ctx, col_l, c.get("lining", "red"), 5, seed=44)
        shape(ctx, col_r, coat, 5, seed=45)
        cel(ctx, col_r, [(20, 60), (90, 60), (90, 120), (20, 110)], coat_s)
        stroke(ctx, [(-6, 150), (-10, 420)], 4)
    elif collar == "hood":
        hood = [(-120, 60), (-60, 20), (40, 40), (90, 120), (60, 170), (-20, 150), (-110, 170)]
        shape(ctx, hood, coat_s, 5, seed=46)
        stroke(ctx, [(-10, 150), (-20, 420)], 4)
    elif collar == "fur":
        rng = random.Random(4)
        fur = spikes(0, 150, 70, 150, 16, math.pi * 1.02, math.pi * 1.98, rng, 0.35)
        shape(ctx, fur + [(120, 200), (-120, 200)], c.get("lining", "g4"), 5, seed=47)
    elif collar == "ragged":
        shape(ctx, [(-70, 130), (-20, 120), (30, 124), (70, 134), (40, 180), (0, 160), (-40, 184)], coat_s, 4.5)
    # armour plates
    if c.get("armor"):
        ar = c["armor"]
        for side in (-1, 1):
            sx = side * W2 * 0.82
            plate = [(sx - 70 * side, 168 + b), (sx + 10 * side, 150 + b), (sx + 60 * side, 190 + b),
                     (sx + 55 * side, 250 + b), (sx - 10 * side, 236 + b)]
            plate = [(p[0], p[1]) for p in plate]
            shape(ctx, plate, ar, 5, seed=50 + side)
            cel(ctx, plate, [(sx - 100, 210 + b), (sx + 100, 200 + b), (sx + 100, 260), (sx - 100, 260)],
                mix(ar, "ink", 0.35))
            stroke(ctx, [(sx - 40 * side, 172 + b), (sx + 30 * side, 168 + b)], 3, "g0", alpha=0.5)
    if c.get("strap"):
        st = [(-W2 * 0.7, 190), (-W2 * 0.55, 182), (W2 * 0.75, 360), (W2 * 0.6, 372)]
        shape(ctx, st, c["strap"], 4, seed=55)
        shape(ctx, [(10, 262), (36, 262), (36, 290), (10, 290)], "steel_l", 3.5, seed=56)


def character(ctx, x, y, s, c, expr="neutral", t=0.0, fx=1, wind=0.0, look=0.0, width=1.0, tilt=0.0):
    """Bust portrait: torso + head. (x, y) = position of the face centre."""
    with at(ctx, x, y, s, tilt, fx=fx):
        bust(ctx, c, t, wind, width=width)
        bob = math.sin(t * 1.6) * 1.5
        with at(ctx, 0, bob):
            head(ctx, c, expr, t, wind, look)


# ----------------------------------------------------------------- simple full figures
def person(ctx, x, y, h=300, color="g5", shade=None, pose="stand", t=0.0, fx=1, head_c=None, ink=4.0,
           seed=0, arm_up=0.0):
    """Stylised full-body figure (crowds, distant characters). (x,y) = feet."""
    s = h / 300
    shade = shade or mix(color, "ink", 0.35)
    sw = math.sin(t * 2 + seed) * 4
    with at(ctx, x, y, s, fx=fx):
        if pose == "walk":
            k = math.sin(t * 5 + seed)
            legs = [((-8, -130), (-20 + k * 18, -60), (-14 + k * 34, 0)), ((8, -130), (14 - k * 16, -62), (6 - k * 30, 0))]
        elif pose == "kneel":
            legs = [((-10, -110), (-50, -60), (-20, 0)), ((10, -110), (40, -50), (70, -6))]
        else:
            legs = [((-12, -130), (-18, -64), (-22, 0)), ((12, -130), (16, -64), (22, 0))]
        for a, b, c_ in legs:
            limb(ctx, a, b, c_, 30, 22, shade, None, ink, seed)
        body = [(-38, -250), (38, -250), (44, -140), (30, -110), (-30, -110), (-44, -140)]
        if pose == "kneel":
            body = [(x0, y0 + 30) for x0, y0 in body]
        shape(ctx, body, color, ink, seed=seed)
        cel(ctx, body, [(-60, -260), (-5, -260), (-15, -100), (-60, -100)], shade)
        oy = 30 if pose == "kneel" else 0
        # arms
        ua = arm_up
        limb(ctx, (-34, -236 + oy), (-50 - ua * 10, -180 + oy - ua * 90), (-46 - ua * 6, -124 + oy - ua * 190),
             22, 18, color, shade, ink, seed + 3)
        limb(ctx, (34, -236 + oy), (50, -180 + oy + sw * 0.5), (52, -126 + oy + sw), 22, 18, color, shade, ink,
             seed + 5)
        # head
        hp = circle_pts(0, -284 + oy, 32, 18, ry=36)
        shape(ctx, hp, head_c or mix("skin", color, 0.15), ink, seed=seed + 7)
        cel(ctx, hp, [(-40, -330 + oy), (-4, -330 + oy), (-10, -240 + oy), (-40, -240 + oy)],
            mix(head_c or "skin", "ink", 0.25))


def crowd(ctx, x0, x1, y, n, h, t=0.0, seed=0, colors=("g4", "g5", "g3"), pose="stand", arm_up=0.0, jitter_y=20):
    rng = random.Random(seed)
    items = []
    for i in range(n):
        items.append((rng.uniform(x0, x1), y + rng.uniform(-jitter_y, jitter_y), h * rng.uniform(0.85, 1.12),
                      rng.choice(colors), rng.randint(0, 999), rng.choice([-1, 1])))
    for (x, yy, hh, cc, sd, fx) in sorted(items, key=lambda it: it[1]):
        person(ctx, x, yy, hh, cc, pose=pose, t=t, fx=fx, seed=sd, arm_up=arm_up * rng.uniform(0.6, 1.0))


# ----------------------------------------------------------------- creatures
def serpent(ctx, path, t=0.0, thick=60, body="teal_d", belly="teal", spikes_c="ink2", head_size=1.0,
            spike_every=3, seed=0, wave=12.0, glow_eye=True, open_jaw=0.3, ink=5):
    """Serpent / sea dragon along a polyline 'path' (head at path[-1])."""
    pts = catmull(path, n=10)
    # wave motion
    moved = []
    for i, (x, y) in enumerate(pts):
        k = i / max(1, len(pts) - 1)
        moved.append((x, y + math.sin(t * 2.2 - k * 9) * wave * (0.3 + k)))
    pts = moved
    n = len(pts)
    widths = [thick * (0.15 + 0.85 * math.sin(min(1.0, (i / (n - 1)) * 1.15) * math.pi * 0.5))
              if i < n * 0.9 else thick * 0.9 for i in range(n)]
    from .kit import ribbon
    rb = ribbon(pts, widths)
    shape(ctx, rb, body, ink, seed=seed)
    # belly band
    bel = ribbon([(x, y + 0) for x, y in pts], [w * 0.45 for w in widths])
    half = len(bel) // 2
    belly_poly = bel[half:] + list(reversed(rb[len(rb) // 2:]))[: 0]
    with clip(ctx, rb):
        for i in range(0, n - 1, 2):
            p, q = pts[i], pts[i + 1]
            dx, dy = q[0] - p[0], q[1] - p[1]
            L = math.hypot(dx, dy) or 1
            nx, ny = -dy / L, dx / L
            w = widths[i]
            stroke(ctx, [(p[0] + nx * w * 0.1, p[1] + ny * w * 0.1), (p[0] + nx * w * 0.5, p[1] + ny * w * 0.5)],
                   3, belly, alpha=0.9, taper=(0.2, 0.2))
        fillp(ctx, bel[:half] + list(reversed([(x, y) for x, y in rb[:len(rb) // 2]])), mix(body, "ink", 0.3),
              alpha=0.5)
    # dorsal spikes
    for i in range(2, n - 6, spike_every):
        p, q = pts[i], pts[i + 1]
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = widths[i] / 2
        base = (p[0] - nx * w, p[1] - ny * w)
        tip = (base[0] - nx * w * 0.9 - dx / L * w * 0.5, base[1] - ny * w * 0.9 - dy / L * w * 0.5)
        shape(ctx, blade(base, tip, w * 0.6), spikes_c, 3.5, seed=i)
    # head
    hx, hy = pts[-1]
    dx, dy = pts[-1][0] - pts[-4][0], pts[-1][1] - pts[-4][1]
    ang = math.atan2(dy, dx)
    with at(ctx, hx, hy, head_size * thick / 60, ang):
        jaw = open_jaw * (0.7 + 0.3 * math.sin(t * 3))
        upper = [(-30, -36), (40, -40), (110, -18), (128, 0), (80, 2), (20, 10), (-30, 20)]
        lower = [(-20, 14), (30, 14 + jaw * 10), (100, 20 + jaw * 60), (60, 36 + jaw * 40), (-10, 40)]
        shape(ctx, lower, mix(body, "ink", 0.25), ink, seed=seed + 1)
        if jaw > 0.1:
            fillp(ctx, [(20, 10), (110, 6), (100, 18 + jaw * 60), (30, 16)], "red_d")
            for k in range(6):
                fillp(ctx, [(30 + k * 14, 4), (38 + k * 14, 4), (34 + k * 14, 16)], "g0")
        shape(ctx, upper, body, ink, seed=seed + 2)
        cel(ctx, upper, [(-40, -10), (130, -6), (130, 30), (-40, 30)], mix(body, "ink", 0.3))
        for k in range(4):
            shape(ctx, blade((-10 - k * 10, -30 + k * 4), (-80 - k * 20, -70 + k * 20), 18, 0.1), spikes_c, 3.5,
                  seed=k)
        ex, ey = 50, -18
        fillp(ctx, [(ex - 16, ey), (ex + 6, ey - 8), (ex + 18, ey + 2), (ex - 4, ey + 6)], "gold_l")
        fillp(ctx, [(ex + 2, ey - 6), (ex + 6, ey - 6), (ex + 6, ey + 5), (ex + 2, ey + 5)], "ink")
        if glow_eye:
            glow(ctx, ex, ey, 40, "gold", 0.5)
        stroke(ctx, [(ex - 22, ey - 10), (ex + 24, ey - 12)], 5)
