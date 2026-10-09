"""Record the Italian narration (ElevenLabs eleven_v4, voice Antonio Farina), one file per beat.

Idempotent: existing beats are skipped unless named on the command line.
  python audio/narra.py           # all missing beats
  python audio/narra.py b05 b13   # re-record these
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio", "narrazione")
API = "https://api.elevenlabs.io/v1"


def call(path, payload=None):
    headers = {"Content-Type": "application/json"}
    if os.environ.get("ELEVENLABS_API_KEY"):
        headers["xi-api-key"] = os.environ["ELEVENLABS_API_KEY"]
    req = urllib.request.Request(API + path, data=json.dumps(payload).encode() if payload else None, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs {e.code}: {e.read().decode()[:400]}")


def main(force):
    g = json.load(open(os.path.join(ROOT, "testo", "copione.json"), encoding="utf-8"))
    v = g["voce"]
    os.makedirs(OUT, exist_ok=True)
    beats = g["battute"]
    todo = [b for b in beats if b["id"] in force or (not force and not os.path.exists(os.path.join(OUT, b["id"] + ".mp3")))]
    sub = call("/user/subscription")
    left = sub["character_limit"] - sub["character_count"]
    need = sum(len(b["testo"]) for b in todo)
    print(f"{len(todo)} beats, {need} chars, {left} left")
    if need > left:
        raise SystemExit("not enough characters")
    for i, b in enumerate(beats):
        if b not in todo:
            continue
        payload = {"text": b["testo"], "model_id": v["model_id"], "language_code": v["language_code"],
                   "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}}
        # give the model the neighbouring lines so intonation flows across beats
        if i > 0:
            payload["previous_text"] = beats[i - 1]["testo"]
        if i + 1 < len(beats):
            payload["next_text"] = beats[i + 1]["testo"]
        try:
            res = call(f"/text-to-speech/{v['voice_id']}/with-timestamps?output_format=mp3_44100_128", payload)
        except SystemExit as e:
            if "previous_text" in str(e) or "next_text" in str(e):
                payload.pop("previous_text", None)
                payload.pop("next_text", None)
                res = call(f"/text-to-speech/{v['voice_id']}/with-timestamps?output_format=mp3_44100_128", payload)
            else:
                raise
        open(os.path.join(OUT, b["id"] + ".mp3"), "wb").write(base64.b64decode(res["audio_base64"]))
        json.dump(res.get("normalized_alignment") or res.get("alignment"),
                  open(os.path.join(OUT, b["id"] + ".align.json"), "w", encoding="utf-8"), ensure_ascii=False)
        print("  ", b["id"], len(b["testo"]))


if __name__ == "__main__":
    main(set(sys.argv[1:]))
