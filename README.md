# La Idea de Dios — documental narrado (≈20 min, español)

A 20-minute Spanish documentary adapted from Jordan B. Peterson's lecture *Biblical Series I:
Introduction to the Idea of God* (2017). Everything is generated in code:

| Part | How |
|---|---|
| Script | `guion/guion.json`: 54 scenes in 10 chapters, written in Spanish from `source/lecture_biblical_series_I.txt` |
| Narration | ElevenLabs **Eleven v4**, voice *Salvatore*: `audio/narrate.py` → `audio/narration/*.mp3` (+ word timings) |
| Art | Flat-2D ink style drawn frame by frame with pycairo (`engine/kit.py`, `engine/figures.py`, `scenes/*.py`) |
| Music & SFX | Original score synthesised with numpy (`audio/score.py`): a mood per chapter, booms, whooshes, ducking under the voice |
| Subtitles | `.srt` generated from the ElevenLabs character alignment |

All characters are original designs.

## Build

```bash
pip install -r requirements.txt            # pycairo, numpy, scipy (+ ffmpeg on PATH)
# fonts used (OFL): assets/fonts/*.ttf — install them (e.g. copy to ~/.fonts && fc-cache -f)
python audio/narrate.py                    # only needed if audio/narration is missing (uses ELEVENLABS_API_KEY)
python build.py                            # renders all segments, mixes audio, writes build/La_Idea_de_Dios.mp4 + .srt
```

Re-render only some scenes after editing them (by scene id or visual name):

```bash
python build.py s31 battle
python build.py --audio                    # rebuild only the soundtrack and re-mux
python -c "import sys; sys.path.insert(0,'.'); from engine.render import contact_sheet; print(contact_sheet(['s12','s13']))"
```

Change a line of narration: edit `guion/guion.json`, then `python audio/narrate.py s12` (re-generates only
that scene, checking your remaining ElevenLabs characters first), then `python build.py --audio s12`.

## Layout
- `engine/kit.py` drawing kit: brushy ink outlines, cel shading, studio backdrops, glyph boxes, camera, text.
- `engine/figures.py` original characters (HERO, SAGE, NIETZSCHE, WOMAN…), crowds, serpents/dragons.
- `engine/render.py` audio-driven timeline, chapter cards, slab wipes, parallel segment rendering.
- `scenes/` one function per visual; `docs/SCENE_BRIEFS.md` describes each one, `docs/STYLE_GUIDE.md` the rules.
