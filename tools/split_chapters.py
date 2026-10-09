"""Encode the film as one mp4 per chapter (each < 30 MB) into entrega/partes. Run after build.py."""
import sys, os, subprocess, unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.render import timeline
segs = timeline()
groups = {}
for s in segs:
    groups.setdefault(s['scene']['cap'], []).append(s)
names = {0: 'apertura'}
for s in segs:
    if s.get('kw'):
        t = unicodedata.normalize('NFKD', s['kw'][1]).encode('ascii', 'ignore').decode().lower().replace(' ', '_')
        names[s['scene']['cap']] = t
os.makedirs('entrega/partes', exist_ok=True)
for cap, ss in sorted(groups.items()):
    lst = f'build/part_{cap}.txt'
    with open(lst, 'w') as f:
        for s in ss:
            f.write(f"file '{os.path.abspath('build/segments/' + s['name'] + '.mp4')}'\n")
    a, b = ss[0]['start'], ss[-1]['start'] + ss[-1]['dur']
    out = f"entrega/partes/{cap:02d}_{names[cap]}.mp4"
    crf = int(sys.argv[1]) if len(sys.argv) > 1 else 23
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                           '-ss', f'{a:.3f}', '-t', f'{b - a:.3f}', '-i', 'build/audio/mix.wav',
                           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-tune', 'animation',
                           '-crf', str(crf), '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                           '-movflags', '+faststart', out])
    print(out, round(os.path.getsize(out) / 2**20, 1), 'MiB', round(b - a, 1), 's', flush=True)
