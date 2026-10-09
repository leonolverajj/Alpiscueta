set -e
cd /home/user/Alpiscueta/strade_romane
[ -f build/audio/mix.wav ] && [ build/audio/mix.wav -nt testo/copione.json ] || python3 audio/mixa.py
python3 - <<'PY'
import sys; sys.path.insert(0,'.')
from motore.film import render
print(render(0, None, procs=4, name='video'))
PY
ffmpeg -y -v error -i build/video.mp4 -i build/audio/mix.wav -map 0:v -map 1:a -c:v libx264 -preset slow -tune animation -crf 24 -pix_fmt yuv420p -c:a aac -b:a 160k -shortest -movflags +faststart build/La_linea_che_parti_da_Roma.mp4
ls -la build/La_linea_che_parti_da_Roma.mp4
echo FATTO
