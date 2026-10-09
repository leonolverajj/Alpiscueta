"""Chapter VI set-pieces: Tiamat, Marduk, the battle, the king who must act as Marduk."""
import math
import random

from engine.kit import (FONT_CAPS, FONT_TITLE, H, W, at, bg_studio, blade, camera, caption_tag, catmull, cel,
                        circle_pts, clip, ease_back, ease_in, ease_io, ease_out, fillp, glow, hatch, lerp, mix,
                        particles, setc, shape, speedlines, spikes, ss, stroke, text, ui_glyphs, win)
from engine import figures as F
from . import scene


def waves(ctx, t, y0, color="sea", n=9, amp=26, seed=0, ink=4.5, crest="g1"):
    rng = random.Random(seed)
    pts = [(-60, H + 60)]
    for i in range(n * 2 + 1):
        x = -60 + i * (W + 120) / (n * 2)
        up = i % 2 == 0
        y = y0 + (-amp if up else amp * 0.4) * rng.uniform(0.6, 1.3) + math.sin(t * 1.4 + i * 0.9) * amp * 0.5
        pts.append((x + math.sin(t + i) * 10, y))
    pts.append((W + 60, H + 60))
    shape(ctx, pts, color, ink, seed=seed)
    for i in range(1, len(pts) - 1, 2):
        x, y = pts[i]
        stroke(ctx, [(x - 40, y + 14), (x, y + 2), (x + 30, y + 10)], 4, crest, alpha=0.7, taper=(0.3, 0.6))


def cuneiform(ctx, x, y, s, seed, color="teal_l", alpha=1.0):
    """A little wedge-script glyph (made-up, cuneiform-like)."""
    rng = random.Random(seed)
    with at(ctx, x, y, s):
        for k in range(rng.randint(2, 4)):
            a = rng.choice([0, math.pi / 2, math.pi / 4, -math.pi / 4])
            ox, oy = rng.uniform(-14, 14), rng.uniform(-14, 14)
            with at(ctx, ox, oy, 1, a):
                fillp(ctx, [(-10, -6), (-10, 6), (14, 0)], color, alpha=alpha)


def marduk(ctx, x, y, s, t, eyes=1.0, mouth_glow=0.0, fx=1, expr="grim"):
    """Original Marduk design: horned crown, square beard, cobalt-gold armour, halo of eyes."""
    c = dict(F.HERO, hair="bald", hair_c="ink2", skin=mix("skin2", "gold", 0.15), skin_s="skin2_s", eye="gold",
             coat="cobalt", coat_s="cobalt_d", lining="gold", collar="fur", armor="gold", strap="gold_d")
    with at(ctx, x, y, s, fx=fx):
        # halo of eyes
        n = 12
        for i in range(n):
            a = -math.pi / 2 + (i - n / 2 + 0.5) * (2 * math.pi / n)
            R = 190
            ex, ey = math.cos(a) * R, -40 + math.sin(a) * R * 0.8
            k = ss(eyes * n - i * 0.7)
            if k <= 0:
                continue
            glow(ctx, ex, ey, 46, "teal", 0.35 * k)
            with at(ctx, ex, ey, 0.6 + 0.4 * k, a + math.pi / 2):
                lid = [(-30, 0), (0, -16 * k), (30, 0), (0, 16 * k)]
                shape(ctx, lid, "g0", 4)
                fillp(ctx, circle_pts(0, 0, 10 * k + 0.1, 14), "teal")
                fillp(ctx, circle_pts(0, 0, 4 * k + 0.1, 10), "ink")
        stroke(ctx, [(math.cos(a) * 190, -40 + math.sin(a) * 152) for a in
                     [i * 2 * math.pi / 60 for i in range(61)]], 3, "teal_l", alpha=0.35 * eyes)
        # body
        F.bust(ctx, c, t, width=1.05)
        with at(ctx, 0, -10, 1.3):
            F.head(ctx, c, expr, t)
            # square Mesopotamian beard
            beard = [(-36, 44), (-16, 84), (14, 94), (48, 64), (60, 44), (58, 128), (36, 150), (-10, 152), (-30, 130)]
            shape(ctx, beard, "ink2", 5)
            for k in range(4):
                stroke(ctx, [(-10 + k * 18, 96), (-8 + k * 18, 140)], 2.5, "g5", alpha=0.6, smooth=False)
            stroke(ctx, [(-30, 40), (-4, 54), (36, 50), (62, 40)], 7, "ink2")
        # horned crown
        with at(ctx, 0, -10, 1.3):
            crown = [(-64, -70), (-54, -150), (-24, -122), (0, -172), (26, -122), (54, -150), (68, -68)]
            shape(ctx, crown, "gold", 5)
            cel(ctx, crown, [(-80, -110), (80, -110), (80, -60), (-80, -60)], "gold_d")
            for k in range(3):
                stroke(ctx, [(-60, -84 - k * 16), (0, -104 - k * 16), (62, -84 - k * 16)], 4, "gold_d", smooth=True)
        if mouth_glow > 0:
            glow(ctx, 40, 60, 90, "teal", 0.6 * mouth_glow)


@scene("tiamat")
def tiamat(ctx, t, T, seg):
    bg_studio(ctx, t, seed=31, dark=True)
    camera(ctx, t, T, zoom=(1.0, 1.12), pan=((0, 30), (-40, -20)), shake=2.5 * ease_in(win(t, T * 0.4, T * 0.6)))
    # storm sky streaks
    for i in range(10):
        y = 80 + i * 45
        stroke(ctx, [(-50, y + math.sin(t + i) * 10), (W + 50, y - 60 + math.sin(t * 0.7 + i) * 10)], 2,
               "teal_d", alpha=0.25, seed=i)
    # cliff with tiny gods
    cliff = [(W * 0.66, H), (W * 0.7, H * 0.55), (W * 0.8, H * 0.5), (W * 0.9, H * 0.53), (W + 40, H * 0.5),
             (W + 40, H)]
    shape(ctx, cliff, "g6", 5)
    F.crowd(ctx, W * 0.74, W * 0.98, H * 0.52, 7, 90, t, seed=4, colors=("g4", "g3", "gold_d"))
    # Tiamat rising
    rise = ease_out(win(t, 0.2, T * 0.45), 2)
    base_y = H * 1.15 - rise * 520
    path = [(-200, H + 80), (200, base_y + 260), (420, base_y + 60), (520, base_y - 160), (700, base_y - 260),
            (900, base_y - 220)]
    F.serpent(ctx, path, t, thick=150, body="sea_l", belly="teal", spikes_c="ink2", head_size=1.3, seed=3,
              wave=10, open_jaw=0.2 + 0.7 * win(t, T * 0.45, T * 0.6))
    waves(ctx, t, H * 0.86, "sea", seed=2)
    waves(ctx, t * 1.2, H * 0.93, mix("sea", "ink", 0.3), seed=5)
    particles(ctx, t, 40, seed=5, color="teal_l", alpha=0.4, speed=(-30, -10))
    caption_tag(ctx, "TIAMAT", 110, 120, t, 40, appear=1.2)
    caption_tag(ctx, "TEHOM · EL ABISMO", 110, 200, t, 30, accent="teal", appear=T * 0.55)
    ui_glyphs(ctx, t, seed=5)


@scene("marduk")
def marduk_scene(ctx, t, T, seg):
    bg_studio(ctx, t, seed=32, tone=0.2)
    camera(ctx, t, T, zoom=(1.12, 1.0), focus=(W / 2, H * 0.45))
    # the electing gods (silhouettes, arms rising)
    up = ease_out(win(t, T * 0.65, T * 0.9))
    F.crowd(ctx, 0, W * 0.28, H * 0.98, 6, 330, t, seed=7, colors=("g4", "g5", "g3"), arm_up=up)
    F.crowd(ctx, W * 0.72, W, H * 0.98, 6, 330, t, seed=8, colors=("g4", "g5", "g3"), arm_up=up)
    eyes = ease_io(win(t, 0.6, T * 0.45))
    speak = win(t, T * 0.45, T)
    marduk(ctx, W / 2, H * 0.47, 1.45, t, eyes, mouth_glow=speak * (0.6 + 0.4 * math.sin(t * 8)))
    # spoken words: wedge glyphs flying out
    if speak > 0:
        for i in range(14):
            k = ((t - T * 0.45) * 0.35 + i / 14) % 1.0
            x = W / 2 + 120 + k * 700 * (1 if i % 2 else 0.8)
            y = H * 0.56 - k * 260 * math.sin(i) + math.sin(t * 2 + i) * 20
            cuneiform(ctx, x, y, 1.2 + k, i, alpha=ss(1 - k) * speak)
    caption_tag(ctx, "MARDUK", 100, 110, t, 44, accent="gold", appear=0.6)
    caption_tag(ctx, "50 NOMBRES", 100, 196, t, 28, appear=1.3)
    ui_glyphs(ctx, t, seed=9)


@scene("battle")
def battle(ctx, t, T, seg):
    """0-35% charge, 35-50% strike flash, 50-100% the dragon's pieces become sky and earth."""
    k_charge = win(t, 0, T * 0.35)
    k_flash = win(t, T * 0.33, T * 0.5)
    k_world = ease_io(win(t, T * 0.5, T * 0.95))
    bg_studio(ctx, t, seed=33, dark=k_world < 0.5)
    camera(ctx, t, T, zoom=(1.0, 1.06), shake=8 * (1 - k_flash) * (k_flash > 0))
    if k_world < 1:
        with at(ctx, 0, 0):
            a = 1 - k_world
            # dragon (splitting)
            gap = ease_out(k_flash) * 160 + k_world * 400
            ctx.save()
            ctx.push_group()
            path = [(W + 200, H * 0.95), (W * 0.85, H * 0.7), (W * 0.72, H * 0.45), (W * 0.62, H * 0.32),
                    (W * 0.55, H * 0.3)]
            F.serpent(ctx, path, t, thick=140, body="sea_l", belly="teal", head_size=1.2, seed=8, wave=8,
                      open_jaw=0.8)
            grp = ctx.pop_group()
            # top half moves up, bottom half moves down
            for sgn in (-1, 1):
                ctx.save()
                if k_flash > 0:
                    ctx.rectangle(-500, H * 0.5 if sgn > 0 else -500, W + 1000, H + 500 if sgn > 0 else H * 0.5 + 500)
                    ctx.clip()
                ctx.translate(0, sgn * gap)
                ctx.set_source(grp)
                ctx.paint_with_alpha(a)
                ctx.restore()
            ctx.restore()
            # Marduk leaping in from the left
            mx = lerp(-400, W * 0.42, ease_out(k_charge, 2))
            my = H * 0.55 - math.sin(k_charge * math.pi) * 160
            if k_world < 0.4:
                speedlines(ctx, W * 0.5, H * 0.45, t, 50, 380, 1400, "teal_l" if k_flash > 0 else "ink",
                           alpha=0.35 * (1 - k_world * 2.5))
                with at(ctx, mx, my, 0.9, -0.25 * (1 - k_flash)):
                    F.person(ctx, 0, 200, 420, "cobalt", "cobalt_d", "walk", t, arm_up=1.0, head_c=mix("skin2", "gold", .2))
                    stroke(ctx, [(-40, -230), (60 + k_flash * 380, -380 - k_flash * 60)], 14, "teal_l", taper=(0.1, 0.0))
                    glow(ctx, 60 + k_flash * 380, -380, 120, "teal", 0.7)
    if 0 < k_flash < 1:
        setc(ctx, "white", (1 - k_flash) ** 2 * 0.9)
        ctx.paint()
    if k_world > 0:
        # the made world: dome of sky (upper half of the beast) over the earth (lower half)
        a = ss(k_world * 1.5)
        dome = [(W * 0.08, H * 0.72)] + [(W / 2 + math.cos(u) * W * 0.42, H * 0.72 - math.sin(u) * H * 0.55)
                                          for u in [math.pi - i * math.pi / 30 for i in range(31)]]
        shape(ctx, dome, mix("sea_l", "cobalt_l", 0.5), 6, alpha=a)
        for i in range(30):
            rng = random.Random(i)
            fillp(ctx, circle_pts(W / 2 + rng.uniform(-700, 700), H * 0.25 + rng.uniform(-80, 260), 3, 6), "g0",
                  alpha=a * 0.8 * (0.5 + 0.5 * math.sin(t * 3 + i)))
        earth = [(W * 0.04, H * 0.74), (W * 0.3, H * 0.69), (W * 0.5, H * 0.71), (W * 0.7, H * 0.68),
                 (W * 0.96, H * 0.74), (W * 0.9, H * 0.84), (W * 0.1, H * 0.84)]
        shape(ctx, earth, "rust", 6, alpha=a)
        cel(ctx, earth, [(0, H * 0.78), (W, H * 0.76), (W, H), (0, H)], "rust_d")
        F.crowd(ctx, W * 0.3, W * 0.7, H * 0.72, 9, 60, t, seed=3, colors=("g6", "g5"))
        caption_tag(ctx, "ORDEN DESDE EL CAOS", W * 0.5 - 220, H * 0.88, t, 36, appear=T * 0.75)
    ui_glyphs(ctx, t, seed=10)


@scene("king_marduk")
def king_marduk(ctx, t, T, seg):
    bg_studio(ctx, t, seed=34, tone=0.1)
    camera(ctx, t, T, zoom=(1.0, 1.1), focus=(W * 0.5, H * 0.4))
    # Marduk's ghost behind the king
    ctx.push_group()
    marduk(ctx, W * 0.5, H * 0.38, 1.6, t, eyes=ease_io(win(t, 0.5, T * 0.5)))
    g = ctx.pop_group()
    ctx.set_source(g)
    ctx.paint_with_alpha(0.28)
    king = dict(F.SAGE, hair="short", hair_c="ink2", beard="long", coat="red", coat_s="red_d", lining="gold",
                collar="fur", eye="g6", skin="skin2", skin_s="skin2_s")
    F.character(ctx, W * 0.5, H * 0.52, 1.1, king, "grim", t)
    with at(ctx, W * 0.5, H * 0.52, 1.1):
        crown = [(-60, -80), (-52, -130), (-20, -110), (0, -140), (20, -110), (52, -130), (62, -80)]
        shape(ctx, crown, "gold", 5)
    caption_tag(ctx, "VER EN TODAS DIRECCIONES", 90, H * 0.74, t, 34, accent="teal", appear=T * 0.35)
    caption_tag(ctx, "HABLAR CON VERDAD", 90, H * 0.84, t, 34, accent="gold", appear=T * 0.55)
    ui_glyphs(ctx, t, seed=11)
