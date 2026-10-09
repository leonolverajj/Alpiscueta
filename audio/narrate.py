"""Generate the Spanish narration with ElevenLabs (eleven_v4), one file per scene.

Auth: uses ELEVENLABS_API_KEY if set; otherwise relies on the cloud environment's
network secret, which injects the `xi-api-key` header for api.elevenlabs.io.

Idempotent: scenes whose audio already exists are skipped (credits are precious).
  python audio/narrate.py              # all missing scenes
  python audio/narrate.py s05 s31      # force re-generate specific scenes
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio", "narration")
API = "https://api.elevenlabs.io/v1"


def request(path, payload=None):
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        headers["xi-api-key"] = key
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ElevenLabs {e.code}: {e.read().decode()[:400]}")


def main(force):
    g = json.load(open(os.path.join(ROOT, "guion", "guion.json"), encoding="utf-8"))
    voice = g["voice"]
    scenes = g["scenes"]
    os.makedirs(OUT, exist_ok=True)

    sub = request("/user/subscription")
    left = sub["character_limit"] - sub["character_count"]
    todo = [s for s in scenes
            if s["id"] in force or (not force and not os.path.exists(os.path.join(OUT, s["id"] + ".mp3")))]
    need = sum(len(s["text"]) for s in todo)
    print(f"{len(todo)} scenes, {need} chars needed, {left} chars left on plan")
    if need > left:
        raise SystemExit("Not enough characters left; aborting before spending anything.")

    for i, s in enumerate(scenes):
        if s not in todo:
            continue
        payload = {
            "text": s["text"],
            "model_id": voice["model_id"],
            "language_code": voice["language_code"],
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
        }
        res = request(f"/text-to-speech/{voice['voice_id']}/with-timestamps"
                      "?output_format=mp3_44100_128", payload)
        with open(os.path.join(OUT, s["id"] + ".mp3"), "wb") as f:
            f.write(base64.b64decode(res["audio_base64"]))
        with open(os.path.join(OUT, s["id"] + ".align.json"), "w", encoding="utf-8") as f:
            json.dump(res.get("normalized_alignment") or res.get("alignment"), f, ensure_ascii=False)
        print(f"  {s['id']} ok ({len(s['text'])} chars)")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
