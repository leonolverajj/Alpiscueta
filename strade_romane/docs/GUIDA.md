# Engine guide — "La linea che partì da Roma"

Look: **thin warm-white line art on black**, smooth and calm, hand-drawn feel (lines draw
themselves on, wobble slightly and "boil" at 10 fps), charming expressive characters. No fills, no
colour, no title cards, no hard cuts. Everything is a line.

## A scene
```python
from motore.film import scena
from motore.linea import *            # Pen helpers, easing, shapes, W, H
from motore.omino import omino, DOWN  # people
from motore.personaggi import mulo, face

@scena("groma")
def groma(pen, t, T, appear, vanish):
    a = 1.0 - vanish                    # use as alpha for characters/text
    pen.lines([stroke1, stroke2], appear, vanish, alpha=1.0, w=1.0, seed=5)   # drawings draw on / retract
    ...
    return road                         # REQUIRED: the road polyline for this scene (screen coords)
```
- `t` local seconds (0 when the scene starts to appear), `T` its visible length (≈ narration + 2.7 s).
  Time beats as fractions of T or absolute seconds from the start; the narration text of the beat
  is in `testo/copione.json` — stage the visuals to land on its words (Italian speech ≈ 13 chars/s,
  starting ≈ 1.3 s after t = 0).
- `appear` 0→1 over the first 1.6 s; `vanish` 0→1 over the last 1.6 s. Pass them to `pen.lines(...,
  reveal=appear, start=vanish)` so drawings draw on and retract like a pen running backwards. Scene-
  specific elements that appear later use `win(t, a, b)` as their own reveal, combined with `vanish`.
- **The road line**: every scene returns one polyline (any shape, ~20–80 points, screen coords). It is
  drawn by the film engine and **morphs** into the next scene's road during transitions. It is the
  thread of the film: horizon road, a trench outline, a route on a map, a circle around the globe…
  Choose it so the morph from the previous scene and into the next looks intentional.
- Canvas 1920×1080, 30 fps. Keep the main subject large; leave breathing space; ground line around
  y ≈ 790 when it is a landscape.

## Pen (motore/linea.py)
- `pen.line(pts, w=1.0, alpha=1.0, reveal=1.0, start=0.0, smooth_=True, closed=False, seed=0)`
- `pen.lines(list_of_strokes, reveal, start, alpha, w, seed)` — one drawing, revealed in order.
- `pen.dot(x, y, r, alpha)`, `pen.text(s, x, y, size, alpha, reveal=…)` handwritten (Caveat font).
- shapes: `ellipse(cx, cy, rx, ry, n)`, `arc(...)`, `catmull`, `resample`, `morph(a, b, k)`, `trim`,
  `xf(pts, dx, dy, s, a)`; easing: `smooth ease_out ease_in ease_io back win wave clamp lerp`.
- `with at(pen, x, y, s, a, fx):` local transform (keeps line width constant).
- Line weights: contours 1.0–1.2, details 0.5–0.8, distant things alpha 0.4–0.6.

## Characters
- `omino(pen, x, y_feet, s, t, costume, walk=0..1, expr=..., look, lean, head_tilt, arm_f=(shoulder, elbow),
  arm_b=..., hold=..., fx=±1, alpha, talk=True)` costumes: viandante (our recurring traveller), toga
  (senator: Appio Claudio), agrimensore, legionario, operaio, corriere, monaco, moderno. hold: staff pick
  shovel scroll quill groma. expr: calm smile grin talk surprise worry squint proud tired determined.
  Angles: 0 = arm pointing right, DOWN = hanging, negative = raised.
- `mulo(pen, x, y, s, t, walk, ear=-1..1, alpha, load)` the traveller's mule (comic relief: ears!).
- Scale ~1.0–1.4 for main characters. Faces read best when the character is ≥ 300 px tall.
- All characters are original designs. Historical people are generic and friendly, no likenesses.

## Taste
Gentle humour and warmth; motion always smooth (ease everything, no pops). Prefer a few big,
clear drawings over many small ones. Handwritten labels in Italian, short, lower case.
Preview: `python3 tools/foglio.py <times...>` or `still(T, path)`.
