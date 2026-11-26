"""Vérifie que le skill video-resume est prêt, et dit quoi installer sinon.

Usage : python verifier.py
Code de sortie : 0 si tout ce qui est requis est là, 1 sinon.
"""
import importlib.util
import sys

import bibliotheque
from outils import outil

OK, KO, ATT = "OK", "MANQUANT", "ATTENTION"


def ligne(etat, texte):
    print(f"  [{etat:<9}] {texte}")


def module_present(nom):
    return importlib.util.find_spec(nom) is not None


def main():
    for flux in (sys.stdout, sys.stderr):
        flux.reconfigure(encoding="utf-8", errors="replace")
    requis_manquants = 0

    print("Environnement")
    if sys.version_info >= (3, 10):
        ligne(OK, f"Python {sys.version.split()[0]}")
    else:
        ligne(KO, f"Python {sys.version.split()[0]} : version 3.10 ou plus requise")
        requis_manquants += 1

    print("\nOutils système (requis)")
    for nom in ("ffmpeg", "ffprobe"):
        if outil(nom):
            ligne(OK, nom)
        else:
            ligne(KO, f"{nom} absent du PATH : Windows `winget install Gyan.FFmpeg` · macOS `brew install ffmpeg` · "
                      "Linux `sudo apt install ffmpeg`")
            requis_manquants += 1

    print("\nTéléchargement des liens")
    if outil("yt-dlp"):
        ligne(OK, "yt-dlp")
    else:
        ligne(KO, "yt-dlp absent : `python -m pip install yt-dlp` (les fichiers locaux marchent sans)")
        requis_manquants += 1

    print("\nModules Python (requis)")
    for nom, paquet in (("faster_whisper", "faster-whisper"), ("PIL", "pillow"), ("numpy", "numpy")):
        if module_present(nom):
            ligne(OK, paquet)
        else:
            ligne(KO, f"{paquet} : `python -m pip install {paquet}`")
            requis_manquants += 1

    print("\nTranscription")
    if module_present("ctranslate2"):
        try:
            import ctranslate2
            n = ctranslate2.get_cuda_device_count()
            if n:
                ligne(OK, f"GPU NVIDIA détectée ({n}) : transcription rapide")
            else:
                ligne(ATT, "pas de GPU NVIDIA : transcription sur processeur, plus lente (ça marche quand même)")
        except Exception as e:  # DLL CUDA manquantes, etc.
            ligne(ATT, f"GPU non utilisable ({e}) : repli sur processeur")
    else:
        ligne(ATT, "faster-whisper pas installé : impossible de transcrire ce qui n'a pas de sous-titres")

    print("\nBibliothèque")
    try:
        bibliotheque.RACINE.mkdir(parents=True, exist_ok=True)
        test = bibliotheque.RACINE / ".ecriture-test"
        test.write_text("ok", encoding="utf-8")
        test.unlink()
        ligne(OK, str(bibliotheque.RACINE))
    except OSError as e:
        ligne(KO, f"{bibliotheque.RACINE} non accessible en écriture : {e}")
        requis_manquants += 1

    print()
    if requis_manquants:
        print(f"{requis_manquants} élément(s) requis manquant(s).")
        return 1
    print("Tout est prêt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
