"""Generate the gentle sound-effect library with ElevenLabs (sound-generation). Idempotent."""
import json, os, sys, urllib.request, urllib.error
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio", "sfx")
LIB = {
    "matita": ("soft pencil sketching lines on paper, gentle, quiet, close", 4.0),
    "passi_ghiaia": ("slow relaxed footsteps of one person walking on a gravel country road", 6.0),
    "zoccoli_mulo": ("a donkey walking slowly, gentle hoof clops on a dirt road", 6.0),
    "mulo_sbuffo": ("a short gentle snort of a donkey, comic and soft", 1.5),
    "pioggia": ("light gentle rain falling on a muddy country path", 7.0),
    "fango": ("sandals squelching and slipping in thick mud, light comic", 3.0),
    "pergamena": ("an old parchment scroll being unrolled slowly", 2.5),
    "piccone": ("a pickaxe striking stone and earth, rhythmic, soft, outdoors", 5.0),
    "pala_ghiaia": ("a shovel scooping and throwing gravel, outdoors", 4.0),
    "pietra_posata": ("a heavy stone block set down into place on gravel, soft deep thud", 1.5),
    "scalpello": ("a chisel tapping stone softly, a few taps", 3.0),
    "galoppo": ("a single horse galloping past on a stone road, from left to right", 4.0),
    "carro": ("wooden cart wheels rolling slowly on stone paving, creaking", 5.0),
    "penna_oca": ("a quill pen writing on parchment, gentle scratching", 4.0),
    "fiume": ("a gentle river flowing under a stone bridge, calm", 7.0),
    "auto": ("a small modern car passing by gently on a country road", 4.0),
    "uccelli": ("soft morning birdsong in the Italian countryside, sparse", 7.0),
    "vento": ("soft mountain wind, airy and calm", 6.0),
    "mercato": ("distant murmur of a busy ancient street, people and carts, soft", 6.0),
    "tic": ("a soft wooden tick, like a single click of an abacus bead", 0.6),
    "campanella": ("a single soft warm chime, gentle and pleasant", 2.0),
    "soffio": ("a very soft airy whoosh, gentle transition sound", 1.2),
}

def gen(name, prompt, dur):
    path = os.path.join(OUT, name + ".mp3")
    if os.path.exists(path):
        return False
    headers = {"Content-Type": "application/json"}
    if os.environ.get("ELEVENLABS_API_KEY"):
        headers["xi-api-key"] = os.environ["ELEVENLABS_API_KEY"]
    body = json.dumps({"text": prompt, "duration_seconds": dur, "prompt_influence": 0.5}).encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_128",
                                 data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            open(path, "wb").write(r.read())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{name}: {e.code} {e.read().decode()[:300]}")
    return True

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or list(LIB)
    for n in names:
        if gen(n, *LIB[n]):
            print("  ", n)
