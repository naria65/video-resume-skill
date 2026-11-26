"""Prépare une vidéo pour que Claude puisse la résumer ou s'en servir comme contexte.

Entrée : une URL (YouTube, etc. : tout ce que yt-dlp sait lire) ou un fichier local.
Sortie, dans le dossier de la vidéo :
  - info.md          métadonnées (titre, auteur, durée, chapitres, description)
  - transcript.md    transcription horodatée, en paragraphes d'environ 45 s
  - segments.json    segments bruts (début, fin, texte) : sert à la recherche
  - frames/          images extraites à intervalle régulier
  - planches/        planches 3x3 légendées avec le timecode
  - manifeste.json   identifiant, source, chemins : sert à la bibliothèque
Le résumé (resume.md) est écrit ensuite par Claude, pas par ce script.

Usage :
  python analyse_video.py <url|fichier> [...] [--out DOSSIER] [--modele large-v3-turbo]
                          [--langue fr] [--images 36] [--sans-images] [--forcer-whisper] [--refaire]
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import site
import subprocess
import sys
import time
import wave
from pathlib import Path

import bibliotheque
from outils import commande, hms, log, run, slug

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

MODELE_CPU = "small"  # repli si le GPU ou son modèle ne marche pas
POLICES = ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf",
           "Helvetica.ttc", "Arial.ttf", "arial.ttf")


# ---------- 1. Récupération ----------

def est_url(s):
    return re.match(r"^https?://", s) is not None


def identifiant(meta, url, src=None):
    if url:
        return f"{meta.get('extractor_key') or 'web'}:{meta.get('id') or url}"
    return f"fichier:{src}:{src.stat().st_size}"


def infos_url(url):
    return json.loads(run(commande("yt-dlp", "-J", "--no-playlist", url)).stdout)


def telecharger(url, dossier, avec_video):
    for vieux in dossier.glob("source.*"):  # reste d'un essai interrompu
        vieux.unlink(missing_ok=True)
    fmt = "bv*[height<=480]+ba/b[height<=480]/b" if avec_video else "ba/b"
    run(commande("yt-dlp", "--no-playlist", "-f", fmt, "-o", str(dossier / "source.%(ext)s"), url))
    fichiers = [f for f in dossier.glob("source.*") if f.suffix not in (".part", ".ytdl")]
    if not fichiers:
        raise RuntimeError("téléchargement échoué")
    return fichiers[0]


def sous_titres_manuels(url, dossier, langues):
    """Sous-titres écrits par un humain (pas les automatiques). None si absents."""
    try:
        run(commande("yt-dlp", "--no-playlist", "--skip-download", "--write-subs",
                     "--sub-langs", ",".join(langues), "--sub-format", "vtt",
                     "-o", str(dossier / "subs.%(ext)s"), url))
    except subprocess.CalledProcessError:
        return None
    vtts = sorted(dossier.glob("subs*.vtt"))
    return vtts[0] if vtts else None


def lire_vtt(chemin):
    segments, debut, fin, lignes = [], None, None, []
    vu = set()

    def secs(t):
        p = [float(x) for x in t.replace(",", ".").split(":")]
        return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]

    def pousser():
        txt = re.sub(r"<[^>]+>", "", " ".join(lignes))
        txt = re.sub(r"\s+", " ", txt).strip()
        if debut is not None and txt and txt not in vu:  # YouTube répète les lignes d'une bouche à l'autre
            vu.add(txt)
            segments.append({"debut": debut, "fin": fin, "texte": txt})

    for ligne in Path(chemin).read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"([\d:.,]+)\s+-->\s+([\d:.,]+)", ligne)
        if m:
            pousser()
            debut, fin, lignes = secs(m.group(1)), secs(m.group(2)), []
        elif ligne.strip() and debut is not None and not ligne.startswith(("WEBVTT", "Kind:", "Language:")):
            lignes.append(ligne.strip())
    pousser()
    return segments


def infos_locales(fichier):
    out = run(commande("ffprobe", "-v", "quiet", "-print_format", "json",
                       "-show_format", "-show_chapters", str(fichier))).stdout
    d = json.loads(out)
    fmt = d.get("format", {})
    tags = {k.lower(): v for k, v in fmt.get("tags", {}).items()}
    return {
        "title": tags.get("title") or Path(fichier).stem,
        "uploader": tags.get("artist") or tags.get("author"),
        "duration": float(fmt.get("duration", 0) or 0),
        "description": tags.get("comment") or tags.get("description"),
        "chapters": [{"start_time": float(c["start_time"]), "title": c.get("tags", {}).get("title", "")}
                     for c in d.get("chapters", [])],
    }


# ---------- 2. Transcription ----------

def ajouter_dll_cuda():
    """Rend les DLL cuBLAS/cuDNN installées par pip visibles pour CTranslate2 (Windows)."""
    if os.name != "nt":
        return
    for base in site.getsitepackages() + [site.getusersitepackages()]:
        for sous in ("nvidia/cublas/bin", "nvidia/cudnn/bin"):
            p = Path(base) / sous
            if p.is_dir():
                os.add_dll_directory(str(p))
                os.environ["PATH"] = str(p) + os.pathsep + os.environ["PATH"]


def transcrire(audio, modele, langue):
    ajouter_dll_cuda()
    import numpy as np
    from faster_whisper import WhisperModel

    # WAV 16 kHz mono produit par ffmpeg : on le lit nous-mêmes (évite PyAV)
    with wave.open(str(audio), "rb") as w:
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    donnees = pcm.astype(np.float32) / 32768.0

    erreurs = []
    for device, compute, nom in (("cuda", "int8_float16", modele), ("cpu", "int8", MODELE_CPU)):
        try:
            log(f"Whisper : modèle {nom} sur {device}…")
            m = WhisperModel(nom, device=device, compute_type=compute)
            segs, info = m.transcribe(donnees, language=langue, vad_filter=True,
                                      beam_size=5, condition_on_previous_text=False)
            segments, t0 = [], time.time()
            for s in segs:
                segments.append({"debut": s.start, "fin": s.end, "texte": s.text.strip()})
                if len(segments) % 50 == 0:
                    log(f"  … {hms(s.end)} transcrit ({time.time() - t0:.0f} s)")
            return segments, info.language
        except Exception as e:  # GPU absent, VRAM pleine, DLL manquante, modèle non téléchargeable…
            erreurs.append(f"{device}/{nom} : {e}")
            log(f"  échec sur {device} : {e}")
    raise RuntimeError(
        "transcription impossible (" + " ; ".join(erreurs) + "). Si le téléchargement du modèle est bloqué "
        "(pare-feu, hors ligne), télécharge-le à l'avance et passe son dossier avec --modele.")


def transcrire_fichier(video, dossier, a):
    audio = dossier / "audio.wav"
    log("Extraction audio…")
    run(commande("ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(audio)))
    try:
        segments, lang = transcrire(audio, a.modele, a.langue)
    finally:
        audio.unlink(missing_ok=True)
    return segments, f"Whisper {a.modele} (langue détectée : {lang})"


def ecrire_transcription(segments, dossier, duree_bloc=45):
    (dossier / "segments.json").write_text(json.dumps(segments, ensure_ascii=False, indent=1), encoding="utf-8")
    blocs, courant, debut = [], [], None
    for s in segments:
        if debut is None:
            debut = s["debut"]
        courant.append(s["texte"])
        if s["fin"] - debut >= duree_bloc and re.search(r"[.!?…]$", s["texte"]):
            blocs.append((debut, " ".join(courant)))
            courant, debut = [], None
    if courant:
        blocs.append((debut, " ".join(courant)))
    lignes = ["# Transcription", ""]
    lignes += [f"**[{hms(d)}]** {t}\n" for d, t in blocs]
    (dossier / "transcript.md").write_text("\n".join(lignes), encoding="utf-8")
    return len(" ".join(s["texte"] for s in segments).split())


# ---------- 3. Images ----------

def extraire_images(video, dossier, duree, nb):
    frames = dossier / "frames"
    frames.mkdir(exist_ok=True)
    pas = max(duree / (nb + 1), 2)
    images, echecs = [], 0
    for i in range(1, nb + 1):
        t = pas * i
        if t >= duree:
            break
        sortie = frames / f"{int(t):06d}s.jpg"
        try:
            run(commande("ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(video),
                         "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "4", str(sortie)))
        except subprocess.CalledProcessError:
            pass
        if sortie.exists():
            images.append((t, sortie))
        else:
            echecs += 1
    if echecs:
        log(f"  {echecs} image(s) n'ont pas pu être extraites")
    return images


def police(taille=22):
    from PIL import ImageFont
    for nom in POLICES:  # noms usuels Linux, Windows, macOS
        try:
            return ImageFont.truetype(nom, taille)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=taille)  # Pillow ≥ 10.1
    except TypeError:
        return ImageFont.load_default()


def planches(images, dossier):
    from PIL import Image, ImageDraw
    sortie = dossier / "planches"
    sortie.mkdir(exist_ok=True)
    fonte = police()
    chemins = []
    for n in range(0, len(images), 9):
        lot = images[n:n + 9]
        vignettes = [Image.open(p).convert("RGB") for _, p in lot]
        w, h = 640, max(v.height for v in vignettes)
        planche = Image.new("RGB", (w * 3, h * ((len(lot) + 2) // 3)), "black")
        d = ImageDraw.Draw(planche)
        for i, ((t, _), v) in enumerate(zip(lot, vignettes)):
            x, y = (i % 3) * w, (i // 3) * h
            planche.paste(v, (x, y))
            d.rectangle([x, y, x + 90, y + 30], fill="black")
            d.text((x + 6, y + 3), hms(t), fill="yellow", font=fonte)
        c = sortie / f"planche_{n // 9 + 1:02d}_{hms(lot[0][0]).replace(':', '-')}.jpg"
        planche.save(c, quality=80)
        chemins.append(c)
    return chemins


# ---------- Principal ----------

def dossier_pour(titre, ident, deja):
    """Dossier de la vidéo : celui de la bibliothèque si elle y est déjà, sinon un nouveau.

    Le suffixe issu de l'identifiant évite que deux vidéos de même titre le même jour s'écrasent.
    """
    if deja:
        return Path(deja["dossier"])
    court = hashlib.sha1(ident.encode("utf-8")).hexdigest()[:6]
    return bibliotheque.RACINE / f"{time.strftime('%Y-%m-%d')}_{slug(titre)}_{court}"


def traiter(source, a, out=None):
    url = est_url(source)
    src = None
    if url:
        log("Lecture des métadonnées…")
        meta = infos_url(source)
    else:
        src = Path(source).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(f"Fichier introuvable : {src}")
        meta = infos_locales(src)

    ident = identifiant(meta, url, src)
    deja = bibliotheque.trouver(ident)
    if deja and not a.refaire:
        log(f"Déjà dans la bibliothèque : {deja['dossier']} (--refaire pour recommencer)")
        deja["deja_vue"] = True
        return deja

    titre = meta.get("title") or "video"
    dossier = Path(out) if out else dossier_pour(titre, ident, deja)
    dossier.mkdir(parents=True, exist_ok=True)
    # --refaire régénère transcription et images, mais garde resume.md et info.md
    for vieux in ("frames", "planches"):
        shutil.rmtree(dossier / vieux, ignore_errors=True)
    duree = float(meta.get("duration") or 0)
    log(f"« {titre} » ({hms(duree)}) → {dossier}")

    # info.md
    lignes = [f"# {titre}", ""]
    for cle, lib in (("uploader", "Chaîne / auteur"), ("upload_date", "Date"),
                     ("webpage_url", "Lien"), ("view_count", "Vues")):
        if meta.get(cle):
            lignes.append(f"- **{lib}** : {meta[cle]}")
    if not url:
        lignes.append(f"- **Fichier** : {src}")
    lignes.append(f"- **Durée** : {hms(duree)}")
    if meta.get("chapters"):
        lignes += ["", "## Chapitres", ""]
        lignes += [f"- {hms(c['start_time'])} — {c.get('title', '')}" for c in meta["chapters"]]
    if meta.get("description"):
        lignes += ["", "## Description", "", meta["description"].strip()]
    (dossier / "info.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")

    # Média
    if url:
        log("Téléchargement…")
        video = telecharger(source, dossier, avec_video=not a.sans_images)
    else:
        video = src

    # Transcription : sous-titres humains si disponibles, sinon Whisper
    segments, origine = None, None
    if url and not a.forcer_whisper:
        langues = [a.langue] if a.langue else ["fr", "fr-FR", "en", "en-US", "en-GB"]
        vtt = sous_titres_manuels(source, dossier, langues)
        if vtt:
            segments, origine = lire_vtt(vtt), f"sous-titres manuels ({vtt.name})"
            log(f"Sous-titres manuels trouvés : {vtt.name}")
    if not segments:
        segments, origine = transcrire_fichier(video, dossier, a)
    mots = ecrire_transcription(segments, dossier)
    log(f"Transcription : {len(segments)} segments, ~{mots} mots ({origine})")

    # Images
    chemins_planches = []
    a_video = run(commande("ffprobe", "-v", "quiet", "-select_streams", "v",
                           "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(video))).stdout.strip()
    if not a.sans_images and a_video and duree > 0:
        log("Extraction des images…")
        images = extraire_images(video, dossier, duree, a.images)
        chemins_planches = planches(images, dossier)
        log(f"{len(images)} images, {len(chemins_planches)} planches")

    # Ménage : la vidéo téléchargée n'est pas gardée
    if url:
        for f in dossier.glob("source.*"):
            f.unlink(missing_ok=True)

    manifeste = {
        "schema": 2, "id": ident, "titre": titre, "auteur": meta.get("uploader"),
        "source": meta.get("webpage_url") or str(src), "duree": hms(duree),
        "analysee_le": time.strftime("%Y-%m-%d"), "dossier": str(dossier),
        "transcription": origine, "mots": mots,
        "fichiers": {"info": "info.md", "transcript": "transcript.md", "segments": "segments.json",
                     "planches": [str(p.relative_to(dossier)) for p in chemins_planches]},
    }
    (dossier / "manifeste.json").write_text(json.dumps(manifeste, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifeste


def main():
    ap = argparse.ArgumentParser(description="Prépare des vidéos pour le skill video-resume.")
    ap.add_argument("sources", nargs="+", help="un ou plusieurs liens / fichiers")
    ap.add_argument("--out", help="dossier de sortie (une seule vidéo)")
    ap.add_argument("--modele", default="large-v3-turbo", help="modèle faster-whisper, ou son dossier local")
    ap.add_argument("--langue", default=None, help="fr, en… (auto si absent)")
    ap.add_argument("--images", type=int, default=36, help="nombre d'images extraites")
    ap.add_argument("--sans-images", action="store_true", help="audio seul (podcast)")
    ap.add_argument("--forcer-whisper", action="store_true",
                    help="ignorer les sous-titres manuels et transcrire quand même")
    ap.add_argument("--refaire", action="store_true", help="retraiter même si déjà dans la bibliothèque")
    a = ap.parse_args()
    if a.out and len(a.sources) > 1:
        sys.exit("--out ne marche qu'avec une seule vidéo")

    resultats = []
    for source in a.sources:
        try:
            resultats.append(traiter(source, a, a.out))
        except Exception as e:
            log(f"ÉCHEC pour {source} : {e}")
            resultats.append({"source": source, "erreur": str(e)})
    bibliotheque.ecrire_index()
    print("\n=== PRÊT ===")
    print(json.dumps(resultats, ensure_ascii=False, indent=1))
    if any("erreur" in r for r in resultats):
        sys.exit(1)


if __name__ == "__main__":
    main()
