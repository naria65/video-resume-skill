"""Bibliothèque des vidéos déjà analysées (~/video-resumes).

Usage :
  python bibliotheque.py liste                 toutes les vidéos, avec leur résumé court
  python bibliotheque.py cherche <mots…>       passages qui en parlent, avec timecode
  python bibliotheque.py index                 régénère INDEX.md (après avoir écrit un resume.md)
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

RACINE = Path.home() / "video-resumes"

for flux in (sys.stdout, sys.stderr):
    flux.reconfigure(encoding="utf-8", errors="replace")


def hms(sec):
    sec = int(sec)
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def en_bref(dossier):
    """Section « En bref » du resume.md, ou None si pas encore résumé."""
    f = Path(dossier) / "resume.md"
    if not f.exists():
        return None
    m = re.search(r"^##\s*En bref\s*\n(.*?)(?=^##\s|\Z)", f.read_text(encoding="utf-8"), re.M | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else None


def fiches():
    res = []
    for man in sorted(RACINE.glob("*/manifeste.json")):
        try:
            d = json.loads(man.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        d["dossier"] = str(man.parent)  # le dossier a pu être déplacé/renommé
        d["en_bref"] = en_bref(man.parent)
        res.append(d)
    return res


def trouver(ident):
    return next((f for f in fiches() if f.get("id") == ident), None)


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


def _norm(t):
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def cherche(requete, n=10):
    termes = [t for t in re.findall(r"\w+", _norm(requete)) if len(t) > 2] or [_norm(requete)]
    passages = []
    for f in fiches():
        d = Path(f["dossier"])
        try:
            segs = json.loads((d / "segments.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            segs = []
        # fenêtres glissantes de 6 segments (~20-40 s)
        for i in range(0, max(len(segs) - 5, 1), 3):
            fen = segs[i:i + 6]
            texte = " ".join(s["texte"] for s in fen)
            nt = _norm(texte)
            trouves = sum(1 for t in termes if t in nt)
            if trouves:
                score = trouves * 10 + sum(nt.count(t) for t in termes)
                passages.append((score, f["titre"], d, hms(fen[0]["debut"]), texte))
        if (d / "resume.md").exists():
            for para in re.split(r"\n\s*\n", (d / "resume.md").read_text(encoding="utf-8")):
                nt = _norm(para)
                trouves = sum(1 for t in termes if t in nt)
                if trouves:
                    passages.append((trouves * 10 + 5, f["titre"], d, "résumé", para.strip()))
    passages.sort(key=lambda p: -p[0])
    return passages[:n]


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "liste"
    if cmd == "index":
        print(ecrire_index())
    elif cmd == "liste":
        fs = fiches()
        if not fs:
            print("Bibliothèque vide.")
        for f in fs:
            print(f"- {f.get('titre')} ({f.get('duree')}) — {f['dossier']}")
            print(f"  {f['en_bref'] or '(pas encore résumée)'}")
    elif cmd == "cherche" and len(sys.argv) > 2:
        res = cherche(" ".join(sys.argv[2:]))
        if not res:
            print("Rien trouvé.")
        for score, titre, d, tc, texte in res:
            print(f"### {titre} [{tc}]  —  {d}")
            print(texte[:700] + ("…" if len(texte) > 700 else ""))
            print()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
