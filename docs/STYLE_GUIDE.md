# Style guide for scene authors

The video is a Spanish narrated documentary drawn entirely in code (pycairo) in a
**flat-2D ink style**: light-grey studio backdrops with big angular slabs, thick brushy black
outlines, flat fills with hard cel-shadow shapes, sparse hatching, accents of crimson, teal and
gold, and little blinking teal "UI glyph" boxes. Dark "night" variant for dramatic/chaos moments.

**All characters are original designs.** Never draw or imitate existing franchise characters
(games, anime, comics, films). Real historical people (Nietzsche, Freud, Jung, Moses as a
biblical figure, Dostoevsky's fictional Raskolnikov) are drawn as stylised generic figures.
Do not draw a likeness of Jordan Peterson — he is a stylised silhouette/back-view lecturer.

## How a scene works
A scene is a function registered with `@scene("visual_name")` in a module under `scenes/`:

```python
from engine.kit import *          # drawing kit
from engine import figures as F   # characters
from . import scene

@scene("raft")
def raft(ctx, t, T, seg):
    # t = seconds into this segment, T = segment length (seconds, ~10-30s)
    bg_studio(ctx, t, seed=12)                 # always paint a full background first
    camera(ctx, t, T, zoom=(1.0, 1.08))        # slow push-in (affects everything drawn after)
    ...draw...
    caption_tag(ctx, "LA BALSA", 100, 110, t, appear=1.0)   # screen-space label
    ui_glyphs(ctx, t, seed=4)                  # screen-space teal glyph boxes
```
Animate with `t`/`T` and the easing helpers so the scene keeps moving the whole time (camera
drift, breathing, things appearing in beats spread over T). Use `win(t, a, b)` for 0..1 progress
inside a time window, `ease_out`, `ease_io`, `ease_back`, `ss` (smoothstep).
Canvas is 1920x1080 (`W`, `H`). Grain, vignette and transitions are added by the renderer.

## Kit API (engine/kit.py) — read the file for full signatures
- Colours: palette keys `ink g0..g6 red red_d red_l teal teal_l teal_d gold gold_l gold_d cobalt
  cobalt_l cobalt_d rust rust_d skin skin_s skin2 skin2_s steel steel_l steel_d coat coat_s night
  sea sea_l violet white paper`, or hex strings; `mix(c1, c2, k)`.
- `shape(ctx, pts, fill, ink=4, smooth=False)` filled polygon + brushy outline (main primitive).
- `fillp(ctx, pts, color, alpha=)` fill only. `stroke(ctx, pts, w, color, taper=, smooth=)` brush line.
- `cel(ctx, base_pts, shade_pts, color)` hard shadow clipped to a shape. `hatch(ctx, region, ...)`.
- `blade(p0, p1, w)` leaf/spike polygon. `spikes(cx, cy, r_in, r_out, n, a0, a1)` zig-zag fan.
- `circle_pts(cx, cy, r, n, ry=)`, `catmull(pts)`, `glow(ctx, x, y, r, color, alpha)`.
- `at(ctx, x, y, s, a, fx)` context manager: translate/scale/rotate/flip.
- `bg_studio(ctx, t, seed, tone, dark=)`, `camera(ctx, t, T, zoom, pan, shake, focus)`.
- `particles(...)`, `speedlines(...)`, `ui_glyphs(...)`, `caption_tag(ctx, text, x, y, t, size, accent=, appear=)`.
- `text(ctx, s, x, y, size, font=FONT_TITLE|FONT_CAPS|FONT_SERIF, color, align, tracking, alpha)`.

## Characters (engine/figures.py)
- `F.character(ctx, x, y, s, preset, expr, t, fx=±1)` bust portrait; (x,y) = face centre; s≈1 → head
  ~200px tall. Presets: `F.HERO` (our recurring protagonist: spiky dark hair, teal eyes, dark coat with
  red collar, steel pauldrons), `F.SAGE`, `F.NIETZSCHE`, `F.STUDENT`, `F.RASKOL`, `F.LECTURER`, `F.WOMAN`.
  Make variants with `dict(F.HERO, coat="red", ...)`. expr: neutral smile shout grim closed
  smile_closed fear awe.
- `F.person(ctx, x, y_feet, h, color, shade, pose="stand|walk|kneel", t, fx, arm_up=0..1)` full figure.
- `F.crowd(ctx, x0, x1, y, n, h, t, seed, colors, pose, arm_up)`.
- `F.hand(...)`, `F.limb(...)`, `F.serpent(ctx, path_pts, t, thick, body, belly, ...)` dragon/snake.
- Examples to copy from: `scenes/core.py`, `scenes/myth.py`.

## Rules
- Only create/edit your own module file. Do not edit `engine/` or other scenes (define local helpers).
- Keep frame render time < 0.4 s (avoid thousands of strokes per frame).
- Compose like a film still: clear focal subject, big shapes, strong silhouettes, light-on-dark or
  dark-on-light contrast, captions short and in Spanish CAPS.
- Preview: `python3 -c "import sys; sys.path.insert(0,'.'); from engine.render import contact_sheet; print(contact_sheet(['s11','s12'], out='build/preview/<module>.png'))"`
  then look at the PNG and iterate until it reads well.
