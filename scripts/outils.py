"""Fonctions partagées par analyse_video.py, bibliotheque.py et verifier.py."""
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path


def hms(sec):
    """Secondes → « mm:ss » (ou « h:mm:ss » au-delà d'une heure)."""
    sec = int(sec or 0)
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def slug(texte, maxi=60):
    texte = re.sub(r"[^\w\s-]", "", texte, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", texte)[:maxi].strip("-") or "video"


def log(msg):
    print(f"[video-resume] {msg}", flush=True)


class ErreurCommande(subprocess.CalledProcessError):
    """Erreur d'un outil externe, avec la ligne d'erreur utile de son stderr."""

    def __str__(self):
        lignes = (self.stderr or "").strip().splitlines()
        utiles = [l for l in lignes if "ERROR" in l] or lignes[-3:]
        return f"{Path(self.cmd[0]).name} : " + (" | ".join(utiles) or f"code {self.returncode}")


def outil(nom):
    """Commande de base pour lancer `nom`, ou None si introuvable.

    yt-dlp est aussi accepté sous forme de module Python (pip install yt-dlp),
    même quand le script n'est pas dans le PATH (fréquent sous Windows).
    """
    chemin = shutil.which(nom)
    if chemin:
        return [chemin]
    if nom == "yt-dlp" and importlib.util.find_spec("yt_dlp") is not None:
        return [sys.executable, "-m", "yt_dlp"]
    return None


def commande(nom, *args):
    base = outil(nom)
    if base is None:
        raise RuntimeError(f"« {nom} » est introuvable : installe-le (voir le README) ou lance verifier.py")
    return base + [str(a) for a in args]


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode:
        raise ErreurCommande(r.returncode, cmd, r.stdout, r.stderr)
    return r
