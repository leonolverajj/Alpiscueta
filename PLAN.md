# Alpiscueta — "La Idea de Dios" (documental narrado, ~20 min, español)

Source: `source/lecture_biblical_series_I.txt` (Jordan B. Peterson, Biblical Series I).

## Pipeline (to build)
- Spanish narration script, scene by scene (~2,800 words ≈ 20 min).
- Narration: ElevenLabs `eleven_v4`, key read from env var `ELEVENLABS_API_KEY`
  (or injected by the environment's network secret for api.elevenlabs.io).
- Visuals: code-drawn flat 2D ink style (pycairo): grey gradient backdrops, angular
  polygons, thick ink outlines, cel shading, red/teal accents, UI glyph squares.
  Original characters only.
- Procedural ambient score + SFX, mixed with ffmpeg; 1080p render.
