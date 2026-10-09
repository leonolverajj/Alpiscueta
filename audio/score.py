"""Procedural, original soundtrack + SFX + final mix.

Everything is synthesised with numpy, so there is nothing to license. The score follows the
timeline: one mood per chapter, a boom on every chapter card, a whoosh on every scene wipe,
a big swell on "que exista la luz", and the music ducks under the narration.

  python audio/score.py        ->  build/audio/mix.wav
"""
import json
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from engine.render import timeline  # noqa: E402

SR = 44100
OUT = os.path.join(ROOT, "build", "audio")

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
        "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def hz(name, octave):
    return 440.0 * 2 ** ((NOTE[name] + 12 * (octave + 1) - 69) / 12)


def chord(root, kind, octave=3):
    iv = {"m": [0, 3, 7, 14], "M": [0, 4, 7, 14], "m7": [0, 3, 7, 10], "M7": [0, 4, 7, 11], "sus": [0, 5, 7, 14],
          "add9": [0, 4, 7, 14], "m9": [0, 3, 7, 10, 14], "5": [0, 7, 12]}[kind]
    f0 = hz(root, octave)
    return [f0 * 2 ** (i / 12) for i in iv]


# chapter -> (progression [(root, kind)], seconds per chord, brightness 0..1, arp?, drums?)
MOODS = {
    0: ([("D", "m9"), ("Bb", "M7"), ("F", "add9"), ("C", "sus")], 7.0, 0.35, False, False),
    1: ([("D", "m7"), ("F", "M7"), ("C", "add9"), ("G", "m7")], 6.0, 0.45, True, False),
    2: ([("A", "m"), ("F", "5"), ("E", "m"), ("D", "m")], 6.0, 0.25, False, "pulse"),
    3: ([("Eb", "M7"), ("F", "add9"), ("Ab", "M7"), ("Bb", "sus")], 7.0, 0.6, True, False),
    4: ([("F", "M7"), ("C", "add9"), ("D", "m7"), ("Bb", "M7")], 5.0, 0.55, True, False),
    5: ([("Bb", "M"), ("F", "M"), ("G", "m"), ("Eb", "M")], 6.0, 0.4, False, False),
    6: ([("D", "m"), ("Bb", "5"), ("C", "5"), ("A", "5")], 4.0, 0.35, True, "epic"),
    7: ([("C", "add9"), ("G", "M"), ("A", "m7"), ("F", "M7")], 5.0, 0.6, True, "soft"),
    8: ([("G", "M7"), ("E", "m7"), ("C", "M7"), ("D", "sus")], 6.0, 0.45, True, False),
    9: ([("C", "m"), ("Ab", "M"), ("F", "m"), ("G", "M")], 6.0, 0.3, False, "pulse"),
    10: ([("D", "M"), ("A", "sus"), ("B", "m7"), ("G", "M7")], 6.0, 0.7, True, "soft"),
}


def onepole(x, a):
    """Cheap one-pole low-pass (a in 0..1, higher = darker)."""
    from scipy.signal import lfilter
    return lfilter([1 - a], [1, -a], x)


def pad_voice(freqs, n, bright, rng):
    t = np.arange(n) / SR
    out = np.zeros((2, n))
    for f in freqs:
        for side, det in ((0, -0.004), (1, 0.004)):
            ph = rng.uniform(0, 6.28)
            ff = f * (1 + det)
            # soft saw: a few harmonics with 1/k fall-off
            v = np.zeros(n)
            for k in range(1, 7):
                v += np.sin(2 * np.pi * ff * k * t + ph * k) / k ** (1.6 - bright * 0.6)
            out[side] += v
    env = np.minimum(1, t / 1.6) * np.minimum(1, (t[-1] - t + 1e-3) / 1.6)
    return out * env / (len(freqs) * 3)


def pluck(f, dur, bright=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    v = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) * bright + 0.12 * np.sin(6 * np.pi * f * t))
    return v * np.exp(-t * 3.2) * np.minimum(1, t / 0.004)


def boom(dur=3.0, f=48):
    n = int(dur * SR)
    t = np.arange(n) / SR
    freq = f * (1 + 1.5 * np.exp(-t * 18))
    v = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 2.2)
    noise = np.random.default_rng(1).normal(0, 1, n) * np.exp(-t * 30) * 0.3
    return np.tanh((v + onepole(noise, 0.7)) * 1.6)


def whoosh(dur=0.7, seed=0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(seed).normal(0, 1, n)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    dark, bright = onepole(noise, 0.985), onepole(noise, 0.86)
    return (dark * 4 * (1 - env) + bright * env) * env * 2.2


def riser(dur=3.0, seed=2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(seed).normal(0, 1, n)
    v = onepole(noise, 0.9) * (t / dur) ** 2 * 2
    tone = np.sin(2 * np.pi * (200 + 600 * (t / dur) ** 2) * t) * (t / dur) ** 3 * 0.15
    return v + tone


def drum_hit(kind):
    if kind == "low":
        return boom(1.2, 55) * 0.8
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(3).normal(0, 1, n)
    return onepole(noise, 0.5) * np.exp(-t * 22) * 0.5


def add(buf, x, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if i >= buf.shape[1] or i + len(x if x.ndim == 1 else x[0]) <= 0:
        return
    if x.ndim == 1:
        x = np.vstack([x * (1 - max(0, pan)), x * (1 + min(0, pan))])
    j = min(buf.shape[1], i + x.shape[1])
    buf[:, i:j] += x[:, : j - i] * gain


def decode(path):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"])
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def build():
    os.makedirs(OUT, exist_ok=True)
    segs = timeline()
    total = segs[-1]["start"] + segs[-1]["dur"]
    n = int(total * SR) + SR
    music = np.zeros((2, n))
    sfx = np.zeros((2, n))
    voice = np.zeros((2, n))
    rng = np.random.default_rng(7)

    # chapter spans
    spans = []
    for s in segs:
        cap = s["scene"]["cap"]
        if spans and spans[-1][0] == cap:
            spans[-1][2] = s["start"] + s["dur"]
        else:
            spans.append([cap, s["start"], s["start"] + s["dur"]])

    for cap, a, b in spans:
        prog, cdur, bright, arp, drums = MOODS[cap]
        tt, k = a, 0
        while tt < b:
            d = min(cdur, b - tt) + 1.6
            root, kind = prog[k % len(prog)]
            fr = chord(root, kind, 3)
            add(music, pad_voice(fr, int(d * SR), bright, rng), tt, 0.55)
            add(music, pad_voice([fr[0] / 2], int(d * SR), 0.2, rng), tt, 0.5)  # bass drone
            if arp:
                step = 0.5 if cap != 6 else 0.25
                notes = [f * 2 for f in fr] + [fr[1] * 4]
                q = 0.0
                j = 0
                while q < cdur and tt + q < b:
                    f = notes[[0, 1, 2, 3, 2, 1][j % 6] % len(notes)]
                    add(music, pluck(f, 1.6, bright), tt + q, 0.10 if cap != 6 else 0.07,
                        pan=0.3 * np.sin(j))
                    q += step
                    j += 1
            if drums:
                bpm_step = {"pulse": 1.0, "epic": 0.5, "soft": 1.0}[drums]
                q = 0.0
                j = 0
                while q < cdur and tt + q < b:
                    if drums == "epic":
                        if j % 4 in (0, 3) or (j % 8 == 6):
                            add(music, drum_hit("low"), tt + q, 0.5)
                        if j % 2 == 1:
                            add(music, drum_hit("tick"), tt + q, 0.25)
                    elif drums == "pulse":
                        add(music, drum_hit("low"), tt + q, 0.28)
                    else:
                        if j % 2 == 0:
                            add(music, drum_hit("low"), tt + q, 0.18)
                    q += bpm_step
                    j += 1
            tt += cdur
            k += 1

    # SFX: wipes, chapter booms, risers, special moments
    for i, s in enumerate(segs):
        if i > 0:
            add(sfx, whoosh(0.8, i), s["start"] - 0.4, 0.22)
        if s["visual"] == "chapter":
            add(sfx, riser(2.5, i), s["start"] - 2.5, 0.10)
            add(sfx, boom(3.5, 44), s["start"] + 0.15, 0.55)
        if s["visual"] == "battle":
            add(sfx, boom(4.0, 38), s["start"] + s["dur"] * 0.36, 0.8)
            add(sfx, riser(s["dur"] * 0.33, 9), s["start"], 0.12)
        if s["visual"] == "title":
            add(sfx, boom(4.0, 40), s["start"] + 1.0, 0.6)
        if s["visual"] == "light":
            add(sfx, riser(2.0, 11), s["start"], 0.15)
            add(sfx, boom(5.0, 36), s["start"] + s["narr"] * 0.55 + 0.6, 0.6)
        if s["visual"] == "empires_fall":
            for f in (0.12, 0.27, 0.42):
                add(sfx, boom(2.0, 60), s["start"] + s["dur"] * f, 0.25)

    # narration
    duck = np.zeros(n)
    for s in segs:
        if s["visual"] == "chapter":
            continue
        v = decode(os.path.join(ROOT, "audio", "narration", s["scene"]["id"] + ".mp3"))
        add(voice, v, s["voice_at"], 1.0)
        i0 = int((s["voice_at"] - 0.25) * SR)
        i1 = int((s["voice_at"] + len(v) / SR + 0.2) * SR)
        duck[max(0, i0):i1] = 1.0
    # smooth the ducking envelope (~0.4 s)
    k = int(0.4 * SR)
    duck = np.convolve(duck, np.ones(k) / k, mode="same")
    music *= (1.0 - 0.72 * duck)

    # normalise music bus, then mix
    music /= max(1e-9, np.abs(music).max()) / 0.5
    mix = voice * 1.0 + music * 0.42 + sfx * 0.9
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    data = (np.clip(mix.T, -1, 1) * 32767).astype("<i2")
    raw = os.path.join(OUT, "mix_raw.wav")
    import wave
    with wave.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    final = os.path.join(OUT, "mix.wav")
    subprocess.check_call(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                           "-ar", str(SR), final])
    print("wrote", final, f"{total / 60:.2f} min")
    return final


if __name__ == "__main__":
    build()
