"""Bibliothèque des vidéos déjà analysées.

Dossier : ~/video-resumes, ou celui de la variable d'environnement VIDEO_RESUMES_DIR.

Commandes :
  liste                              toutes les vidéos, avec leur « En bref »
  cherche <mots…> [-n 10]            passages qui en parlent, avec timecode et lien horodaté
  contexte <cible> [--pour SUJET]    bloc de contexte compact pour reprendre une vidéo dans une session
                   [--max 8000]      (cible = titre, nom de dossier, identifiant ou sujet)
  index                              régénère INDEX.md
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

from outils import hms

RACINE = Path(os.environ.get("VIDEO_RESUMES_DIR") or Path.home() / "video-resumes").expanduser()


# ---------- Lecture des fiches ----------

def section(texte, titre):
    """Contenu de la section « ## titre » d'un markdown, ou None."""
    m = re.search(rf"^##\s*{re.escape(titre)}\s*\n(.*?)(?=^##\s|\Z)", texte, re.M | re.S)
    return m.group(1).strip() if m else None


def en_bref(dossier):
    """Section « En bref » du resume.md, sur une ligne, ou None si pas encore résumé."""
    f = Path(dossier) / "resume.md"
    if not f.exists():
        return None
    s = section(f.read_text(encoding="utf-8"), "En bref")
    return re.sub(r"\s+", " ", s).strip() if s else None


def fiches():
    res = []
    for man in sorted(RACINE.glob("*/manifeste.json")):
        try:
            d = json.loads(man.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        d["dossier"] = str(man.parent)  # le dossier a pu être déplacé ou renommé
        d["en_bref"] = en_bref(man.parent)
        res.append(d)
    return res


def trouver(ident):
    return next((f for f in fiches() if f.get("id") == ident), None)


def resoudre(cible):
    """Vidéos dont le titre, le nom de dossier ou l'identifiant correspond à la cible."""
    c = _norm(cible).strip()
    if not c:
        return []
    return [f for f in fiches()
            if c in _norm(f.get("titre") or "")
            or c in _norm(Path(f["dossier"]).name)
            or c == _norm(f.get("id") or "")]


def ecrire_index():
    RACINE.mkdir(parents=True, exist_ok=True)
    lignes = ["# Bibliothèque vidéo", "",
              "Vidéos déjà analysées. Chaque dossier contient info.md, transcript.md, planches/ et resume.md.", ""]
    for f in sorted(fiches(), key=lambda f: f.get("analysee_le", ""), reverse=True):
        lignes.append(f"## {f.get('titre')}")
        lignes.append(f"{f.get('auteur') or '?'} · {f.get('duree')} · analysée le {f.get('analysee_le', '?')} · "
                      f"[dossier]({Path(f['dossier']).name}/) · {f.get('source')}")
        lignes.append("")
        lignes.append(f["en_bref"] or "_(pas encore de resume.md)_")
        lignes.append("")
    (RACINE / "INDEX.md").write_text("\n".join(lignes), encoding="utf-8")
    return RACINE / "INDEX.md"


# ---------- Recherche ----------

def _norm(t):
    """Minuscules, sans accents."""
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def termes_de(requete):
    t = [m for m in re.findall(r"\w+", _norm(requete)) if len(m) > 2]
    return t or [_norm(requete).strip()]


def lien_horodate(source, sec):
    """Lien vers la vidéo à la seconde voulue, quand le site le permet."""
    if not source:
        return ""
    if sec is None:
        return source
    s = int(sec)
    if not re.match(r"^https?://", source):  # fichier local : on donne le timecode en clair
        return f"{source} @ {hms(s)}"
    p = urlparse(source)
    hote = p.netloc.lower().removeprefix("www.").removeprefix("m.")
    if hote == "youtube.com" and p.path == "/watch":
        v = dict(parse_qsl(p.query)).get("v")
        if v:
            return f"https://youtube.com/watch?{urlencode({'v': v})}&t={s}s"
    if hote == "youtu.be" and p.path.strip("/"):
        return f"https://youtu.be{p.path}?t={s}"
    return source  # autres sites : pas de format de lien commun


def passages_de(f, termes, fenetre=6, pas=3, avec_resume=True):
    """Passages d'une vidéo qui contiennent les termes : fenêtres de transcription et, si demandé, paragraphes du résumé."""
    d = Path(f["dossier"])
    try:
        segs = json.loads((d / "segments.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        segs = []
    source = f.get("source") or ""
    res = []
    for i in range(0, max(len(segs) - fenetre + pas, 1), pas):
        fen = segs[i:i + fenetre]
        if not fen:
            break
        texte = " ".join(s["texte"] for s in fen)
        nt = _norm(texte)
        trouves = sum(1 for t in termes if t in nt)
        if trouves:
            debut = fen[0]["debut"]
            res.append({"score": trouves * 10 + sum(nt.count(t) for t in termes), "debut": debut,
                        "temps": hms(debut), "lien": lien_horodate(source, debut), "texte": texte,
                        "dossier": f["dossier"], "titre": f.get("titre")})
    if avec_resume and (d / "resume.md").exists():
        # paragraphes et puces du résumé, sans les titres de section
        texte_resume = (d / "resume.md").read_text(encoding="utf-8")
        for para in re.split(r"\n\s*\n|\n(?=\s*[-*] )", texte_resume):
            para = re.sub(r"^#+.*$", "", para, flags=re.M).strip()
            nt = _norm(para)
            trouves = sum(1 for t in termes if t in nt)
            if para and trouves:
                res.append({"score": trouves * 10 + 5, "debut": None, "temps": "résumé",
                            "lien": source, "texte": para,
                            "dossier": f["dossier"], "titre": f.get("titre")})
    return res


def selection(passages, n):
    """Meilleurs passages, sans doublons : un seul par tranche de 30 s et par vidéo."""
    passages = sorted(passages, key=lambda p: -p["score"])
    gardes = []
    for p in passages:
        doublon = any(
            g["dossier"] == p["dossier"] and (
                (p["debut"] is not None and g["debut"] is not None and abs(g["debut"] - p["debut"]) < 30)
                or g["texte"] == p["texte"])
            for g in gardes)
        if not doublon:
            gardes.append(p)
        if len(gardes) >= n:
            break
    return gardes


def cherche(requete, n=10, videos=None):
    termes = termes_de(requete)
    tous = []
    for f in (fiches() if videos is None else videos):
        tous += passages_de(f, termes)
    return selection(tous, n)


# ---------- Reprise de contexte ----------

def bloc_contexte(f, sujet, budget):
    """Bloc compact d'une vidéo : cadre, en bref, passages pour le sujet, points clés."""
    d = Path(f["dossier"])
    lignes = [f"## {f.get('titre')}",
              f"{f.get('auteur') or '?'} · {f.get('duree')} · analysée le {f.get('analysee_le', '?')}",
              f"Source : {f.get('source')}",
              f"Dossier : {d}", ""]
    cles = None
    resume = d / "resume.md"
    if resume.exists():
        texte = resume.read_text(encoding="utf-8")
        bref = section(texte, "En bref")
        cles = section(texte, "Points clés à retenir")
        if bref:
            lignes += ["### En bref", bref, ""]
    else:
        lignes += ["_(Pas encore de resume.md : lire transcript.md.)_", ""]
    # le résumé est déjà affiché au-dessus : seuls les passages de transcription sont utiles ici
    passages = selection(passages_de(f, termes_de(sujet), avec_resume=False), 6)
    if passages:
        lignes.append(f"### Passages pour « {sujet} »")
        lignes += [f"- [{p['temps']}]({p['lien']}) {p['texte'][:400]}" for p in passages]
        lignes.append("")
    if cles:  # en dernier : c'est ce qui est coupé en premier si le budget manque
        lignes += ["### Points clés", cles, ""]
    texte = "\n".join(lignes).rstrip() + "\n"
    if len(texte) > budget:
        texte = texte[:budget].rsplit("\n", 1)[0] + "\n… (coupé)\n"
    return texte


def contexte(cible, pour=None, maximum=8000):
    """Bloc de contexte pour reprendre une ou plusieurs vidéos. None si rien ne correspond."""
    videos = resoudre(cible)
    if not videos:
        # pas de titre correspondant : on cherche le sujet dans les transcriptions
        par_dossier = {f["dossier"]: f for f in fiches()}
        vus = []
        for p in cherche(cible, n=50):
            if p["dossier"] not in vus:
                vus.append(p["dossier"])
        videos = [par_dossier[d] for d in vus[:3]]
    if not videos:
        return None
    videos = videos[:3]
    budget = max(maximum // len(videos), 300)
    texte = "\n---\n\n".join(bloc_contexte(f, pour or cible, budget) for f in videos)
    if len(texte) > maximum:
        texte = texte[:maximum].rsplit("\n", 1)[0] + "\n\n… (tronqué : précise --pour ou --max)\n"
    return texte


# ---------- Ligne de commande ----------

def main(argv=None):
    for flux in (sys.stdout, sys.stderr):
        flux.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Bibliothèque des vidéos analysées (skill video-resume).")
    sous = ap.add_subparsers(dest="cmd")
    sous.add_parser("liste", help="toutes les vidéos avec leur « En bref »")
    c = sous.add_parser("cherche", help="passages qui en parlent, avec timecode")
    c.add_argument("mots", nargs="+")
    c.add_argument("-n", type=int, default=10)
    x = sous.add_parser("contexte", help="bloc de contexte compact pour reprendre une vidéo")
    x.add_argument("cible", help="titre, nom de dossier, identifiant, ou sujet")
    x.add_argument("--pour", help="sujet précis à retrouver dans les vidéos")
    x.add_argument("--max", type=int, default=8000, help="taille maximale du bloc, en caractères")
    sous.add_parser("index", help="régénère INDEX.md")
    a = ap.parse_args(argv)

    if a.cmd in (None, "liste"):
        fs = fiches()
        if not fs:
            print("Bibliothèque vide.")
        for f in fs:
            print(f"- {f.get('titre')} ({f.get('duree')}) — {f['dossier']}")
            print(f"  {f['en_bref'] or '(pas encore résumée)'}")
    elif a.cmd == "cherche":
        res = cherche(" ".join(a.mots), n=a.n)
        if not res:
            print("Rien trouvé.")
        for p in res:
            print(f"### {p['titre']} [{p['temps']}] — {p['lien']}")
            print(p["texte"][:700] + ("…" if len(p["texte"]) > 700 else ""))
            print()
    elif a.cmd == "contexte":
        texte = contexte(a.cible, pour=a.pour, maximum=a.max)
        if texte is None:
            print(f"Rien dans la bibliothèque pour « {a.cible} ». Ne pas combler : le dire, ou analyser la vidéo.")
            sys.exit(1)
        print(texte)
    elif a.cmd == "index":
        print(ecrire_index())


if __name__ == "__main__":
    main()
