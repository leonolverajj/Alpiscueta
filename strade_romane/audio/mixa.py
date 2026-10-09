"""Final soundtrack: narration + Mendelssohn (CC0, Musopen) + gentle SFX, ducked and loudness-normalised.

Sound effects are cued by *words in the narration*: a cue (visual, phrase, offset, sfx, gain) fires when the
narrator reaches that phrase (exact time from ElevenLabs alignment), so sounds stay aligned with the
pictures, which are warped to the same word timings.
  python audio/mixa.py   ->  build/audio/mix.wav
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from motore.film import XF, timeline  # noqa: E402

SR = 48000
MUS = os.path.join(ROOT, "audio", "musica")
SFX = os.path.join(ROOT, "audio", "sfx")

# (visual, phrase or None for scene start, offset s, sfx, gain dB, fade-out length s or None)
CUES = [
    ("linea", None, 0.3, "matita", -14, None),
    ("linea", None, 0.6, "uccelli", -24, None),
    ("linea", "Ogni volta", 1.5, "passi_ghiaia", -18, None),
    ("linea", "Ogni volta", 1.6, "zoccoli_mulo", -20, None),
    ("linea", "via strata", 0.0, "matita", -18, None),
    ("linea", "Gli inglesi", 0.4, "mulo_sbuffo", -16, None),
    ("linea", "Questa è la storia", 0.5, "passi_ghiaia", -20, None),
    ("fango", None, 0.0, "pioggia", -18, None),
    ("fango", "fango", 0.0, "fango", -14, None),
    ("fango", "Etruschi", 0.0, "vento", -24, None),
    ("fango", "rete", 0.2, "mulo_sbuffo", -18, None),
    ("appio", None, 0.3, "matita", -18, None),
    ("appio", "un'idea", 0.0, "campanella", -18, None),
    ("appio", "una strada solida", 0.0, "pergamena", -14, None),
    ("appio", "Nasce la Via Appia", 0.0, "pietra_posata", -16, None),
    ("appio", "eppure", 0.0, "soffio", -16, None),
    ("regina", None, 0.4, "uccelli", -26, None),
    ("regina", "Brindisi", 0.0, "passi_ghiaia", -20, None),
    ("regina", "regina viarum", 0.0, "campanella", -17, None),
    ("groma", "con la groma", 0.0, "matita", -16, None),
    ("groma", "allineamenti perfetti", 0.3, "tic", -12, None),
    ("groma", "curvare", 0.0, "soffio", -16, None),
    ("cantiere", None, 0.3, "piccone", -18, None),
    ("cantiere", "Una trincea", 0.0, "pala_ghiaia", -16, None),
    ("cantiere", "ghiaia", 0.0, "pala_ghiaia", -18, None),
    ("cantiere", "grandi blocchi", 0.3, "pietra_posata", -14, None),
    ("cantiere", "i basoli", 0.0, "pietra_posata", -16, None),
    ("cantiere", "la pioggia", 0.0, "pioggia", -20, 4.0),
    ("cantiere", "legionari", 0.0, "piccone", -20, None),
    ("tavole", None, 0.4, "scalpello", -18, None),
    ("tavole", "i carri", 0.0, "carro", -16, None),
    ("tavole", "i carri", 2.0, "mulo_sbuffo", -16, None),
    ("pompei", None, 0.3, "uccelli", -26, None),
    ("pompei", "solchi", 0.0, "carro", -20, 3.0),
    ("pompei", "acqua piovana", 0.0, "pioggia", -20, 5.0),
    ("pompei", "bagnarsi i piedi", 0.0, "fango", -18, None),
    ("pompei", "Le ruote passavano", 0.0, "carro", -16, None),
    ("miliario", None, 0.2, "passi_ghiaia", -18, None),
    ("miliario", "una colonna", 0.0, "scalpello", -16, None),
    ("miliario", "Miliario d'oro", 0.0, "campanella", -15, None),
    ("rete", "La Flaminia", 0.0, "matita", -20, None),
    ("rete", "L'Emilia", 0.0, "matita", -20, None),
    ("rete", "la Domizia", 0.0, "matita", -20, None),
    ("posta", None, 0.3, "galoppo", -16, None),
    ("posta", "cambiare i cavalli", 0.5, "mulo_sbuffo", -18, None),
    ("posta", "cinquantina", 0.0, "galoppo", -18, None),
    ("posta", "Tiberio", 0.0, "carro", -16, None),
    ("posta", "una notte", 0.0, "vento", -22, None),
    ("tabula", None, 0.3, "mercato", -24, None),
    ("tabula", None, 0.5, "carro", -20, None),
    ("tabula", "copia medievale", 0.0, "pergamena", -14, None),
    ("tabula", "Tabula Peutingeriana", 0.0, "penna_oca", -18, None),
    ("orazio", None, 0.3, "penna_oca", -18, None),
    ("orazio", "percorse l'Appia", 0.0, "passi_ghiaia", -20, None),
    ("orazio", "osti scortesi", 0.0, "mercato", -24, 3.0),
    ("orazio", "di notte", 0.0, "acqua_canale", -20, None),
    ("orazio", "zanzare", 0.0, "zanzara", -16, None),
    ("orazio", "rane", 0.0, "rane", -18, None),
    ("ponti", None, 0.2, "fiume", -20, None),
    ("ponti", "una galleria", 0.0, "vento", -24, None),
    ("ponti", "aperta al traffico", 0.0, "auto", -16, None),
    ("mondo", None, 0.2, "soffio", -16, None),
    ("mondo", "trecentomila", 0.0, "tic", -12, None),
    ("mondo", "sette volte", 0.0, "campanella", -16, None),
    ("proverbio", None, 0.3, "matita", -18, None),
    ("proverbio", "pellegrini", 0.0, "passi_ghiaia", -20, None),
    ("oggi", None, 0.3, "auto", -16, None),
    ("oggi", "quando viaggi", 0.0, "passi_ghiaia", -20, None),
    ("oggi", "quando viaggi", 0.1, "zoccoli_mulo", -22, None),
    ("oggi", "non si è mai fermata", 1.2, "uccelli", -24, None),
    ("oggi", "non si è mai fermata", 2.0, "campanella", -16, None),
]

# music plan: (first beat id of section, track, source start s)
MUSIC = [("b01", "it3_con_moto.mp3", 0.0), ("b09", "it1_allegro_vivace.mp3", 0.0), ("b11", "it3_con_moto.mp3", None)]


def decode(path, sr=SR, ch=2):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", str(ch), "-ar", str(sr), "-"])
    a = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return a.reshape(-1, ch).T


def add(buf, x, t, gain=1.0):
    i = int(round(t * SR))
    if i < 0:
        x = x[:, -i:]
        i = 0
    j = min(buf.shape[1], i + x.shape[1])
    if j > i:
        buf[:, i:j] += x[:, : j - i] * gain


def phrase_time(b, phrase):
    """Seconds (global) when the narrator starts `phrase` in beat b, from the alignment."""
    if phrase is None:
        return b["start"] - (XF / 2 if b["id"] != "b01" else 0.0)
    al = json.load(open(os.path.join(ROOT, "audio", "narrazione", b["id"] + ".align.json"), encoding="utf-8"))
    text = "".join(al["characters"])
    k = text.find(phrase)
    if k < 0:
        k = text.lower().find(phrase.lower())
    if k < 0:
        raise SystemExit(f"cue phrase not found in {b['id']}: {phrase!r}")
    return b["voice_at"] + al["character_start_times_seconds"][k]


def main():
    tl = timeline()
    total = tl[-1]["start"] + tl[-1]["dur"]
    n = int(total * SR) + SR
    voice = np.zeros((2, n))
    music = np.zeros((2, n))
    sfx = np.zeros((2, n))
    duck = np.zeros(n)
    for b in tl:
        v = decode(os.path.join(ROOT, "audio", "narrazione", b["id"] + ".mp3"))
        add(voice, v, b["voice_at"])
        i0, i1 = int((b["voice_at"] - 0.2) * SR), int((b["voice_at"] + v.shape[1] / SR + 0.25) * SR)
        duck[max(0, i0):i1] = 1.0
    # music sections with 3 s crossfades at the beat boundaries
    byid = {b["id"]: b for b in tl}
    secs = []
    for k, (bid, track, src0) in enumerate(MUSIC):
        a = byid[bid]["start"] - (XF / 2 if bid != "b01" else 0.0)
        z = byid[MUSIC[k + 1][0]]["start"] - XF / 2 if k + 1 < len(MUSIC) else total
        secs.append((a, z, track, src0))
    fade = 3.0
    for k, (a, z, track, src0) in enumerate(secs):
        m = decode(os.path.join(MUS, track))
        dur = (z - a) + (fade if k + 1 < len(secs) else 0.0)
        if src0 is None:      # align the movement's real ending with the end of the film
            src0 = max(0.0, m.shape[1] / SR - dur)
        seg = m[:, int(src0 * SR): int((src0 + dur) * SR)].copy()
        L = seg.shape[1]
        env = np.ones(L)
        fi = int(fade * SR) if k > 0 else int(2.0 * SR)
        env[:fi] = np.linspace(0, 1, fi) ** 1.5
        if k + 1 < len(secs):
            fo = int(fade * SR)
            env[-fo:] *= np.linspace(1, 0, fo) ** 1.5
        add(music, seg * env, a)
    # gentle ducking under the voice
    w = int(0.35 * SR)
    duck = np.convolve(duck, np.ones(w) / w, mode="same")
    music *= 10 ** ((-11.0 * duck) / 20)
    # sound effects from word cues
    byvis = {b["visual"]: b for b in tl}
    cache = {}
    for vis, phrase, off, name, db, fo in CUES:
        b = byvis[vis]
        t = phrase_time(b, phrase) + off
        if name not in cache:
            cache[name] = decode(os.path.join(SFX, name + ".mp3"))
        x = cache[name].copy()
        if fo:
            m = int(fo * SR)
            x = x[:, :m] * np.linspace(1, 0, min(m, x.shape[1]))
        # soft attack so nothing clicks
        a = min(x.shape[1], int(0.02 * SR))
        x[:, :a] *= np.linspace(0, 1, a)
        add(sfx, x, t, 10 ** (db / 20))
    mpeak = np.abs(music).max() or 1
    music *= 0.32 / mpeak
    mix = voice + music + sfx
    mix = np.tanh(mix * 1.05) / np.tanh(1.05)
    out_dir = os.path.join(ROOT, "build", "audio")
    os.makedirs(out_dir, exist_ok=True)
    raw = os.path.join(out_dir, "mix_raw.wav")
    with wave.open(raw, "wb") as wv:
        wv.setnchannels(2)
        wv.setsampwidth(2)
        wv.setframerate(SR)
        wv.writeframes((np.clip(mix.T, -1, 1) * 32767).astype("<i2").tobytes())
    out = os.path.join(out_dir, "mix.wav")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar",
                           str(SR), out])
    print("wrote", out, f"{total / 60:.2f} min")


if __name__ == "__main__":
    main()
