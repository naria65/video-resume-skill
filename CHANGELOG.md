# Changelog

## 0.2.0

Reprise de contexte et fiabilité.

### Ajouté
- `bibliotheque.py contexte` : bloc compact et borné pour reprendre une vidéo dans une session (cadre, en bref,
  passages avec timecode cliquable, points clés), avec `--pour` pour un sujet précis et `--max` pour la taille.
- Liens horodatés dans les résultats de recherche (YouTube, youtu.be).
- `verifier.py` : diagnostic de l'installation, avec les commandes à lancer pour corriger.
- `outils.py` : fonctions partagées ; `yt-dlp` est aussi trouvé quand il est installé comme module Python.
- Variable `VIDEO_RESUMES_DIR` pour choisir le dossier de la bibliothèque.
- `requirements.txt`, tests (`python -m unittest discover -s tests`) et CI GitHub Actions.
- `docs/brief-video-promo.md` : brief de la vidéo de présentation.

### Corrigé
- Dans SKILL.md, `python "~/..."` ne développait pas `~` : les commandes sont réécrites.
- Les titres de section du résumé (« ## Points clés… ») n'apparaissent plus comme des passages.
- Deux vidéos de même titre le même jour ne s'écrasent plus (le dossier reçoit un suffixe issu de l'identifiant).
- `--refaire` conserve `resume.md` et `info.md`, et ne mélange plus les anciennes images avec les nouvelles.
- La police des planches est trouvée sous Linux, Windows et macOS (au lieu de tomber sur une police minuscule).
- Un échec de transcription indique la cause (modèle non téléchargeable) et la marche à suivre.
- Le code de sortie vaut 1 si une vidéo a échoué.

## 0.1.0

Première version : analyse (transcription, images, planches), bibliothèque, recherche.
