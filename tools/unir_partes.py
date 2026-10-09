"""Une las 11 partes de "La Idea de Dios" en un solo video.

Uso (Windows):
    python unir_partes.py
    python unir_partes.py "C:\\otra\\carpeta"

- Busca los archivos 00_*.mp4 ... 10_*.mp4 en la carpeta y los une en orden, sin recomprimir
  (tarda segundos y no pierde calidad).
- Si en la carpeta está La_Idea_de_Dios.srt, agrega los subtítulos en español como pista
  opcional (se activan desde el reproductor).
- Necesita ffmpeg. Si no lo tienes instalado, el script instala automáticamente el paquete
  "imageio-ffmpeg" (trae ffmpeg incluido) con pip.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

CARPETA = r"C:\Users\j-hop\Downloads\La_idea_de_Dios"
SALIDA = "La_Idea_de_Dios_completo.mp4"


def encontrar_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
    except ImportError:
        print("ffmpeg no está instalado; instalando imageio-ffmpeg con pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "imageio-ffmpeg"])
        import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def main():
    carpeta = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else CARPETA)
    if not os.path.isdir(carpeta):
        sys.exit(f"No encuentro la carpeta: {carpeta}")

    partes = [f for f in os.listdir(carpeta) if re.match(r"^\d{2}_.*\.mp4$", f, re.IGNORECASE)]
    partes.sort(key=lambda f: int(f[:2]))
    if not partes:
        sys.exit("No encontré archivos tipo 00_apertura.mp4 ... 10_sea_la_luz.mp4 en la carpeta.")
    numeros = [int(f[:2]) for f in partes]
    faltan = [n for n in range(0, max(numeros) + 1) if n not in numeros]
    if faltan:
        print(f"Aviso: faltan las partes {faltan}; se unirán solo las que hay.")
    print("Partes, en orden:")
    for f in partes:
        print("  ", f)

    ffmpeg = encontrar_ffmpeg()
    salida = os.path.join(carpeta, SALIDA)

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as lista:
        for f in partes:
            ruta = os.path.join(carpeta, f).replace("\\", "/").replace("'", "'\\''")
            lista.write(f"file '{ruta}'\n")
        nombre_lista = lista.name

    cmd = [ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", nombre_lista]
    srt = os.path.join(carpeta, "La_Idea_de_Dios.srt")
    if os.path.exists(srt):
        cmd += ["-i", srt, "-map", "0:v", "-map", "0:a", "-map", "1:s", "-c:s", "mov_text",
                "-metadata:s:s:0", "language=spa"]
        print("Agregando subtítulos en español (pista opcional).")
    cmd += ["-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", salida]

    print("Uniendo...")
    try:
        subprocess.check_call(cmd)
    finally:
        os.remove(nombre_lista)
    mb = os.path.getsize(salida) / 2 ** 20
    print(f"Listo: {salida} ({mb:.0f} MB)")


if __name__ == "__main__":
    main()
