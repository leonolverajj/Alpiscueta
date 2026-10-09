"""One expressive line-art person rig, many costumes (all original designs).

omino(pen, x, y, s, t, costume=..., **pose)
  x, y   feet position;  s scale (1 = ~310 px tall);  fx = +1 faces right, -1 left
  pose   walk (0..1), speed, lean, head_tilt, expr, look,
         arm_f / arm_b: (shoulder_angle, elbow_angle) in radians, 0 = pointing right, pi/2 = down
         hold: 'staff' | 'pick' | 'shovel' | 'scroll' | 'quill' | 'groma' | None
"""
import math

from .linea import arc, at, ellipse, lerp, wave
from .personaggi import face, foot, mitten, tube

DOWN = math.pi / 2


def noodle(pen, p0, p2, bend, w=1.1, alpha=1.0, seed=0):
    """A soft rubber-hose limb from p0 to p2, bent sideways by `bend` (px, signed)."""
    mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2
    dx, dy = p2[0] - p0[0], p2[1] - p0[1]
    d = math.hypot(dx, dy) or 1.0
    c = (mx - dy / d * bend, my + dx / d * bend)
    pts = [p0, (lerp(p0[0], c[0], 0.6), lerp(p0[1], c[1], 0.6)), c, (lerp(c[0], p2[0], 0.4), lerp(c[1], p2[1], 0.4)), p2]
    pen.line(pts, w, alpha, seed=seed, taper=0.06)
    return c


def _arm(pen, sh, a1, a2, l1, l2, w, alpha, seed):
    p1 = (sh[0] + math.cos(a1) * l1, sh[1] + math.sin(a1) * l1)
    p2 = (p1[0] + math.cos(a2) * l2, p1[1] + math.sin(a2) * l2)
    # bend amount from the elbow offset relative to the straight line
    ax, ay = p2[0] - sh[0], p2[1] - sh[1]
    d = math.hypot(ax, ay) or 1.0
    off = ((p1[0] - sh[0]) * -ay + (p1[1] - sh[1]) * ax) / d
    noodle(pen, sh, p2, off * 0.9, 1.15, alpha, seed)
    mitten(pen, p2[0] + math.cos(a2) * 5, p2[1] + math.sin(a2) * 5, a2 - DOWN, 8, alpha, seed + 5)
    return p1, (p2[0] + math.cos(a2) * 8, p2[1] + math.sin(a2) * 8)


def _leg(pen, hip, ph, walk, alpha, seed, sandal=True, kneel=0.0, side=1):
    sw = math.sin(ph) * 0.5 * walk
    lift = max(0.0, math.sin(ph + 1.4)) * 16 * walk
    foot_x = hip[0] + math.sin(sw) * 70 + kneel * 40 * side
    foot_y = -lift * 0.6 - kneel * 30 * (side > 0)
    bend = (10 + 22 * max(0.0, math.sin(ph + 1.3)) * walk) + kneel * 40
    noodle(pen, hip, (foot_x, foot_y - 8), bend, 1.15, alpha, seed)
    foot(pen, foot_x - 2, foot_y, 1, alpha, seed + 4, sandal)
    return (foot_x, foot_y)


def omino(pen, x, y, s=1.0, t=0.0, costume="viandante", fx=1, alpha=1.0, walk=0.0, speed=1.0, lean=0.0,
          head_tilt=0.0, expr="calm", look=0.0, arm_f=None, arm_b=None, hold=None, kneel=0.0, seed=0,
          blink=True, talk=False):
    L = pen.line
    with at(pen, x, y, s, fx=fx):
        ph = t * 2 * math.pi * 0.85 * speed + seed
        bob = -abs(math.sin(ph)) * 7 * walk + wave(t, 0.23, seed) * 1.6 * (1 - walk) + kneel * 40
        with at(pen, 0, 0, 1.0, lean * 0.25):
            hip = (0, -122 + bob)
            long_robe = costume in ("toga", "monaco")
            # ---- back leg / back arm
            if not long_robe:
                _leg(pen, (hip[0] - 6, hip[1]), ph + math.pi, walk, alpha * 0.85, seed + 10, costume != "moderno",
                     kneel, -1)
            sh_b = (-14, -186 + bob)
            ab = arm_b or (DOWN + 0.2 + math.sin(ph + math.pi) * 0.4 * walk, DOWN + 0.05 + math.sin(ph + math.pi) * 0.25 * walk)
            _arm(pen, sh_b, ab[0], ab[1], 44, 40, 15, alpha * 0.8, seed + 20)
            # ---- body / costume
            _costume_body(pen, costume, bob, t, alpha, seed)
            # ---- front leg
            if not long_robe:
                _leg(pen, (hip[0] + 6, hip[1]), ph, walk, alpha, seed + 30, costume != "moderno", kneel, 1)
            else:
                # feet peeking under the robe
                k = math.sin(ph) * 14 * walk
                foot(pen, -14 - k, -2, 1, alpha * 0.85, seed + 31)
                foot(pen, 12 + k, -2, 1, alpha, seed + 32)
            # ---- head
            with at(pen, 8, -222 + bob, 1.0, head_tilt):
                ex = "talk" if talk else expr
                face(pen, 6, -30, 44, ex, look, t, blink, 1.0, True, seed + 42, alpha)
                _costume_head(pen, costume, t, walk, ph, alpha, seed)
            # ---- front arm
            sh_f = (16, -186 + bob)
            af = arm_f or (DOWN - 0.35 + math.sin(ph) * 0.4 * walk, 0.4 + math.sin(ph) * 0.3 * walk)
            el, hd = _arm(pen, sh_f, af[0], af[1], 46, 42, 16, alpha, seed + 50)
            _hold(pen, hold, hd, af[1], t, alpha, seed)
            # ---- accessories over the body
            if costume == "viandante":
                L([(26, -206 + bob), (-30, -150 + bob)], 0.8, alpha, seed=seed + 60)
                bag = [(-52, -156 + bob), (-26, -152 + bob), (-24, -124 + bob), (-54, -126 + bob), (-52, -156 + bob)]
                L(bag, 0.85, alpha, smooth_=False, seed=seed + 61)
                L([(-52, -146 + bob), (-26, -142 + bob)], 0.6, alpha * 0.8, seed=seed + 62)


def _costume_body(pen, c, bob, t, alpha, seed):
    L = pen.line
    sway = wave(t, 0.5, seed) * 2.5
    if c in ("viandante", "agrimensore", "corriere", "operaio"):
        body = [(-18, -218 + bob), (-38, -188 + bob), (-50, -140 + bob), (-52, -106 + bob + sway),
                (-14, -100 + bob), (20, -102 + bob), (50, -108 + bob - sway), (46, -150 + bob), (34, -192 + bob),
                (22, -218 + bob)]
        L(body, 1.15, alpha, seed=seed + 70)
        L([(-44, -138 + bob), (0, -132 + bob), (42, -138 + bob)], 0.75, alpha * 0.9, seed=seed + 71)
        L([(-10, -200 + bob), (0, -190 + bob), (12, -200 + bob)], 0.6, alpha * 0.7, seed=seed + 72)
        if c == "corriere":   # flying cloak
            fl = wave(t, 1.6, seed) * 10
            L([(-20, -212 + bob), (-70, -190 + bob + fl), (-110, -170 + bob - fl), (-60, -150 + bob)], 0.9, alpha,
              seed=seed + 73)
    elif c == "legionario":
        body = [(-26, -214 + bob), (-38, -176 + bob), (-42, -128 + bob), (-48, -104 + bob + sway),
                (-10, -98 + bob), (22, -100 + bob), (46, -104 + bob - sway), (38, -150 + bob), (34, -186 + bob),
                (26, -214 + bob)]
        L(body, 1.0, alpha, seed=seed + 70)
        for k in range(4):   # segmented armour bands
            yy = -196 + k * 16 + bob
            L([(-36, yy + 4), (0, yy + 8), (36, yy + 2)], 0.75, alpha * 0.9, seed=seed + 74 + k)
        for k in range(5):   # pteruges strips
            xx = -34 + k * 17
            L([(xx, -128 + bob), (xx + 2, -104 + bob)], 0.6, alpha * 0.8, seed=seed + 80 + k)
    elif c == "toga":
        body = [(-26, -214 + bob), (-44, -170 + bob), (-52, -90 + bob), (-56, -10 + sway), (-20, -4),
                (24, -6), (54, -12 - sway), (48, -90 + bob), (38, -170 + bob), (26, -214 + bob)]
        L(body, 1.0, alpha, seed=seed + 70)
        # the toga's diagonal drape and folds
        L([(30, -210 + bob), (-10, -160 + bob), (-40, -100 + bob), (-30, -40)], 0.8, alpha, seed=seed + 71)
        L([(36, -190 + bob), (6, -130 + bob), (0, -60)], 0.6, alpha * 0.75, seed=seed + 72)
        L([(-50, -60), (-30, -50), (-8, -56)], 0.55, alpha * 0.6, seed=seed + 73)
        # a stripe at the hem (praetexta-like border)
        L([(-54, -26 + sway * 0.5), (0, -20), (52, -28 - sway * 0.5)], 0.6, alpha * 0.7, seed=seed + 74)
    elif c == "monaco":
        body = [(-28, -214 + bob), (-48, -160 + bob), (-58, -60 + bob), (-60, -8), (0, -4), (56, -8),
                (52, -80 + bob), (42, -170 + bob), (28, -214 + bob)]
        L(body, 1.0, alpha, seed=seed + 70)
        L([(-50, -130 + bob), (0, -124 + bob), (46, -132 + bob)], 0.7, alpha, seed=seed + 71)
        L([(-6, -124 + bob), (-10, -70 + bob)], 0.6, alpha * 0.8, seed=seed + 72)
    elif c == "moderno":
        body = [(-24, -214 + bob), (-34, -180 + bob), (-36, -126 + bob), (-30, -116 + bob), (30, -116 + bob),
                (36, -126 + bob), (34, -180 + bob), (24, -214 + bob)]
        L(body, 1.0, alpha, seed=seed + 70)
        L([(-30, -116 + bob), (-34, -100 + bob), (34, -100 + bob), (30, -116 + bob)], 0.8, alpha, seed=seed + 71)


def _costume_head(pen, c, t, walk, ph, alpha, seed):
    L = pen.line
    if c == "viandante":
        sway = wave(t, 0.5) * 0.04 + math.sin(ph) * 0.03 * walk
        with at(pen, 2, -66, 1.0, sway):
            L([(-70, 4), (-40, 9), (10, 11), (52, 9), (76, 0)], 1.0, alpha, seed=seed + 90)   # brim
            L([(-36, 7), (-34, -14), (-14, -28), (16, -26), (30, -12), (32, 8)], 1.0, alpha, seed=seed + 91)
            L([(-34, -2), (0, 2), (31, -1)], 0.6, alpha * 0.8, seed=seed + 92)              # hat band
    elif c == "legionario":
        with at(pen, 0, -60, 1.0):
            L(arc(4, 8, 46, math.pi * 1.05, math.pi * 1.98, 20), 1.0, alpha, seed=seed + 90)  # bowl
            L([(-44, 6), (-56, 14), (-50, 26)], 0.9, alpha, seed=seed + 91)                    # neck guard
            L([(-28, 12), (-34, 52), (-22, 60)], 0.8, alpha, seed=seed + 92)                   # cheek piece
            L([(4, -38), (6, -54), (20, -60), (34, -52)], 0.8, alpha, seed=seed + 93)          # crest knob
            L([(-40, 4), (50, 4)], 0.7, alpha, seed=seed + 94)
    elif c == "toga":
        # bald dome with a laurel-ish fringe of hair at the back
        for k in range(6):
            a = math.radians(150 + k * 14)
            L([(6 + math.cos(a) * 40, -30 + math.sin(a) * 40), (6 + math.cos(a) * 49, -30 + math.sin(a) * 47)],
              0.8, alpha, seed=seed + 90 + k)
        L([(30, -52), (34, -58)], 0.5, alpha * 0.6, seed=seed + 97)   # a wrinkle of wisdom
    elif c == "agrimensore":
        L([(-34, -58), (-20, -76), (14, -80), (40, -64), (44, -56)], 0.95, alpha, seed=seed + 90)  # soft cap
        L([(40, -64), (52, -74)], 0.8, alpha, seed=seed + 91)
    elif c == "monaco":
        L([(-42, 20), (-50, -30), (-30, -74), (14, -84), (46, -62), (52, -30), (50, -10)], 1.0, alpha, seed=seed + 90)
    elif c == "corriere":
        L([(-40, -50), (-20, -72), (20, -74), (44, -56), (-40, -50)], 0.9, alpha, seed=seed + 90)
    elif c == "moderno":
        L([(-38, -44), (-30, -66), (0, -76), (30, -68), (44, -50)], 0.9, alpha, seed=seed + 90)   # hair
        L([(26, -36), (46, -36), (50, -26), (30, -24), (26, -36)], 0.7, alpha, seed=seed + 91)    # sunglasses
    elif c == "operaio":
        L([(-40, -50), (-34, -70), (0, -78), (36, -68), (42, -48)], 0.9, alpha, seed=seed + 90)


def _hold(pen, hold, hd, a2, t, alpha, seed):
    L = pen.line
    x, y = hd
    if hold == "staff":
        L([(x + 2, y - 60), (x + 2, y + 120)], 1.0, alpha, smooth_=False, seed=seed + 100)
    elif hold == "pick":
        L([(x - 30, y + 40), (x + 40, y - 50)], 1.0, alpha, smooth_=False, seed=seed + 100)
        L([(x + 10, y - 66), (x + 44, y - 50), (x + 66, y - 18)], 1.0, alpha, seed=seed + 101)
    elif hold == "shovel":
        L([(x - 20, y - 50), (x + 30, y + 70)], 1.0, alpha, smooth_=False, seed=seed + 100)
        L([(x + 20, y + 66), (x + 46, y + 108), (x + 56, y + 70), (x + 38, y + 58)], 0.95, alpha, seed=seed + 101)
    elif hold == "scroll":
        L([(x - 6, y - 14), (x + 30, y - 22), (x + 34, y + 2), (x - 2, y + 10), (x - 6, y - 14)], 0.9, alpha,
          seed=seed + 100)
        L([(x + 32, y - 22), (x + 40, y - 10), (x + 34, y + 2)], 0.7, alpha, seed=seed + 101)
    elif hold == "quill":
        L([(x, y), (x + 26, y - 40), (x + 34, y - 52)], 0.9, alpha, seed=seed + 100)
        L([(x + 20, y - 30), (x + 36, y - 56), (x + 30, y - 36)], 0.6, alpha, seed=seed + 101)
    elif hold == "groma":
        # the surveyor's groma: a staff with a rotating cross and four plumb lines
        L([(x + 6, y - 150), (x + 6, y + 120)], 1.0, alpha, smooth_=False, seed=seed + 100)
        cx, cy = x + 6, y - 150
        r = 46
        a = wave(t, 0.1, seed) * 0.08
        for k in range(4):
            ang = a + k * math.pi / 2
            ex, ey = cx + math.cos(ang) * r, cy + math.sin(ang) * r * 0.3
            L([(cx, cy), (ex, ey)], 0.9, alpha, smooth_=False, seed=seed + 102 + k)
            sw = wave(t, 0.7, k) * 2
            L([(ex, ey), (ex + sw, ey + 70)], 0.5, alpha * 0.8, smooth_=False, seed=seed + 106 + k)
            pen.dot(ex + sw, ey + 74, 3.4, alpha)
