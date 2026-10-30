---
name: video-resume
description: Lire des vidéos (liens YouTube/autres sites ou fichiers locaux .mp4/.mkv/.mov/.mp3…) pour les résumer OU s'en servir comme contexte de travail (suivre un tuto, appliquer une méthode, répondre à des questions dessus). Tient une bibliothèque des vidéos déjà vues (~/video-resumes) où chercher. À utiliser dès que l'utilisateur donne une vidéo, demande de la résumer ou de « s'en servir », ou fait référence à une vidéo / un sujet vu dans une vidéo auparavant.
argument-hint: <url(s) ou chemin(s)> [ce qu'il faut en faire]
---

# Vidéos : résumé et contexte

Tu ne peux pas regarder une vidéo directement. Un script la transforme en choses que tu sais lire :
transcription horodatée, métadonnées, planches d'images légendées avec le timecode.
Tout est rangé dans une **bibliothèque** persistante, réutilisable dans les sessions suivantes.

Scripts : `S = ~/.claude/skills/video-resume/scripts`

## 0. Choisir le mode

- **Résumé** — « résume », « de quoi ça parle » → étapes 1, 2, 3, 5.
- **Contexte** — la vidéo sert à faire autre chose : « fais pareil que dans ce tuto », « applique sa méthode à mon projet »,
  « en t'aidant de ces vidéos, écris… », questions précises sur le contenu → étapes 1, 2, 4 (puis 3 en court).
- **Retrouver** — l'utilisateur parle d'une vidéo déjà vue ou d'un sujet qu'une vidéo de la bibliothèque peut couvrir
  (« la vidéo sur le mixage de l'autre jour », « qu'est-ce que disait le gars sur le sidechain ? ») → étape 6, sans retraiter.

## 1. Préparer la/les vidéo(s)

```bash
python "~/.claude/skills/video-resume/scripts/analyse_video.py" "<url ou chemin>" ["<autre>" …]
```

- Plusieurs vidéos d'un coup : passe-les toutes à la suite.
- Lance-le **en arrière-plan** (`run_in_background`) si > ~10 min de vidéo : 1 h prend quelques minutes avec une carte graphique NVIDIA.
- Une vidéo **déjà dans la bibliothèque n'est pas retraitée** : le script renvoie directement son dossier (`"deja_vue": true`).
  `--refaire` pour forcer.
- Options : `--langue fr` (si la détection auto se trompe), `--images 60` (tuto très visuel),
  `--sans-images` (podcast, seul l'audio compte), `--forcer-whisper` (sous-titres YouTube mauvais),
  `--modele small` (plus rapide, moins précis).
- Le JSON final (après `=== PRÊT ===`) donne le dossier de chaque vidéo. La vidéo téléchargée est supprimée,
  seuls texte et images restent.

## 2. Lire le matériel

Dans le dossier de chaque vidéo :

1. `info.md` — titre, auteur, durée, chapitres, description. Le cadre.
2. `transcript.md` — **en entier**, par morceaux si long (offset/limit). Jamais sur un extrait.
   C'est de la reconnaissance vocale : corrige les noms propres et termes techniques mal reconnus
   avec l'aide du titre, de la description et des images.
3. `planches/*.jpg` — 9 images par planche, timecode en jaune. Regarde-les (au moins une sur deux si > 8) pour
   ce qui n'est pas dit : écrans, réglages, schémas, texte affiché, démonstrations.
   Détail illisible → l'image seule dans `frames/<secondes>s.jpg`.
   En mode contexte pour un tuto (logiciel, montage, réglages), les images sont souvent **plus importantes que l'audio** :
   lis-les toutes.

## 3. Écrire resume.md

Toujours, même en mode contexte (en version plus courte) : c'est ce qui rend la vidéo retrouvable plus tard.
Fichier `resume.md` dans le dossier de la vidéo, en français sauf demande contraire :

```markdown
# <Titre> — résumé
<auteur> · <durée> · <lien ou fichier>

## En bref
3 à 5 phrases : de quoi ça parle, la thèse ou le but, la conclusion.
(Cette section est reprise dans l'index de la bibliothèque : garde-la autonome et précise.)

## Déroulé détaillé
Une section par grande partie (chapitres s'il y en a, sinon découpe par sujet), timecode de début [mm:ss].
Ce qui est expliqué, arguments, exemples, démonstrations, ce qu'on voit quand c'est utile.
Assez détaillé pour que quelqu'un qui n'a pas vu la vidéo sache tout ce qui est dit d'important.

## Points clés à retenir
## Infos précises
Chiffres, dates, prix, noms (personnes, outils, logiciels, plugins), réglages, références, liens cités.
## Citations marquantes
2 à 5, avec timecode.
## Ce que montrent les images
Seulement si le visuel apporte autre chose que l'audio.
## Avis / limites
Optionnel, marqué comme ton analyse.
```

Puis régénère l'index : `python "$S/bibliotheque.py" index`.

Règles : **rien d'inventé** (passage inaudible/ambigu → le dire) ; séparer ce que dit la vidéo de ton avis ;
garder les timecodes ; longueur selon la densité, plutôt trop complet que trop court ;
une consigne de l'utilisateur (« seulement la partie sur X », « en anglais »…) prime.

## 4. Mode contexte : travailler avec la vidéo

- Fais la tâche demandée en t'appuyant sur la **transcription complète et les images**, pas sur le résumé.
- Quand tu appliques quelque chose tiré de la vidéo, cite d'où ça vient : « (vidéo X, [12:40]) ».
- Si la vidéo est floue, incomplète ou contredit le projet de l'utilisateur, dis-le plutôt que de combler.
- Plusieurs vidéos : croise-les, signale les désaccords entre elles.
- Les étapes d'un tuto : liste-les dans l'ordre avec timecodes avant de les exécuter, pour que l'utilisateur puisse vérifier.

## 5. Rendre la main (mode résumé)

Lien cliquable vers `resume.md`, et dans la réponse la section « En bref » + les points clés.
Si la transcription a échoué ou est de mauvaise qualité, dis-le.

## 6. Retrouver dans la bibliothèque

```bash
python "~/.claude/skills/video-resume/scripts/bibliotheque.py" liste
python "~/.claude/skills/video-resume/scripts/bibliotheque.py" cherche <mots-clés>
```

- `liste` : toutes les vidéos avec leur « En bref ». `~/video-resumes\INDEX.md` contient la même chose.
- `cherche` : passages de transcription (avec timecode) et paragraphes de résumé contenant les mots, sans accents ni casse.
  Essaie plusieurs formulations / synonymes, en français et en anglais si la vidéo est en anglais.
- Ensuite ouvre `resume.md` de la bonne vidéo ; pour une question précise, lis la transcription autour du timecode trouvé.
- Réponds en citant la vidéo et le timecode. Si rien ne correspond, dis-le, et ne fais pas semblant de se souvenir.

## Dépannage

- `yt-dlp` échoue (vidéo privée, âge, région) → demande le fichier local ; ou `yt-dlp -U`.
- Erreur CUDA / mémoire GPU → repli automatique sur CPU (modèle small, plus lent).
- Module manquant → `python -m pip install faster-whisper nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*" pillow`.
