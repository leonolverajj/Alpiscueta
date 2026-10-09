"""Contact sheet of frames. Usage:
  python3 tools/foglio.py --beat b05 [--n 6] [--out build/anteprime/b05.png]
  python3 tools/foglio.py 12.5 30 61        (absolute seconds)
"""
import argparse, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PIL import Image
from motore.film import timeline, draw_frame, XF

ap = argparse.ArgumentParser()
ap.add_argument("times", nargs="*", type=float)
ap.add_argument("--beat")
ap.add_argument("--n", type=int, default=6)
ap.add_argument("--out")
a = ap.parse_args()
tl = timeline()
times = list(a.times)
if a.beat:
    b = next(x for x in tl if x["id"] == a.beat or x["visual"] == a.beat)
    t0, t1 = b["start"] - XF / 2, b["start"] + b["dur"] + XF / 2
    times = [t0 + (t1 - t0) * (k + 0.5) / a.n for k in range(a.n)]
ims = []
for T in times:
    s = draw_frame(tl, T)
    im = Image.frombuffer("RGBA", (1920, 1080), bytes(s.get_data()), "raw", "BGRA", 0, 1).convert("RGB")
    ims.append(im.resize((640, 360)))
cols = 3
rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (640 * cols, 380 * rows), (30, 30, 30))
from PIL import ImageDraw
d = ImageDraw.Draw(sheet)
for i, (im, T) in enumerate(zip(ims, times)):
    x, y = (i % cols) * 640, (i // cols) * 380
    sheet.paste(im, (x, y + 20))
    d.text((x + 6, y + 4), f"t={T:.1f}s", fill=(200, 200, 200))
out = a.out or os.path.join(ROOT, "build", "anteprime", (a.beat or "foglio") + ".png")
os.makedirs(os.path.dirname(out), exist_ok=True)
sheet.save(out)
print(out)
