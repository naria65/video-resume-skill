# Lecteur vidéo pour Claude Code

Un skill [Claude Code](https://claude.com/claude-code) qui permet à Claude de **lire des vidéos** : liens YouTube (et autres sites) ou fichiers locaux. Claude ne peut pas regarder une vidéo. Le skill la transforme en ce qu'il sait lire : une transcription horodatée et des planches d'images avec leur timecode. Ensuite Claude :

- **la résume** : résumé complet, partie par partie, avec les timecodes, les chiffres, noms et citations importants ;
- **s'en sert pour travailler** : suivre un tuto, appliquer une méthode à ton projet, répondre à des questions précises, en citant d'où vient chaque idée (« vidéo X, [12:40] ») ;
- **la retrouve plus tard** : chaque vidéo est rangée dans une bibliothèque où Claude peut chercher, d'une conversation à l'autre.

Pas de commande à retenir : donne un lien ou un fichier et dis ce que tu veux en faire (« résume-moi ça », « fais pareil que dans ce tuto », « qu'est-ce qu'il disait sur… ? »).

## Comment ça marche

1. **Téléchargement** avec [yt-dlp](https://github.com/yt-dlp/yt-dlp) en qualité réduite (480p max), ou lecture directe d'un fichier local.
2. **Transcription** : les sous-titres écrits à la main par l'auteur s'il y en a. Sinon, [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (modèle `large-v3-turbo`) sur la carte graphique, avec repli automatique sur le processeur.
3. **Images** : 36 captures réparties sur la vidéo, regroupées par 9 en planches avec le timecode en jaune.
4. **Ménage** : la vidéo téléchargée est supprimée, seuls le texte et les images restent.
5. **Résumé** écrit par Claude après lecture de la transcription entière et des planches.
6. **Bibliothèque** : tout est rangé dans `~/video-resumes/`, avec un `INDEX.md`. Une vidéo déjà vue n'est jamais retraitée.

Pour chaque vidéo : `resume.md`, `transcript.md`, `info.md`, `segments.json`, `planches/` et `frames/`.

## Installation

### 1. Prérequis

- **Python 3.10 ou plus**
- **ffmpeg** (avec ffprobe) et **yt-dlp** dans le PATH
  - Windows : `winget install Gyan.FFmpeg yt-dlp.yt-dlp`
  - macOS : `brew install ffmpeg yt-dlp`
  - Linux : `sudo apt install ffmpeg` puis `python -m pip install yt-dlp`
- Les modules Python :

```bash
python -m pip install faster-whisper pillow numpy
```

- **Optionnel, pour transcrire sur une carte graphique NVIDIA** (bien plus rapide) :

```bash
python -m pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
```

Sans carte graphique compatible, la transcription passe sur le processeur avec un modèle plus léger : ça marche, en plus lent.

### 2. Installer le skill

Copie ce dépôt dans le dossier des skills de Claude Code, sous le nom `video-resume` :

```bash
git clone https://github.com/naria65/video-resume-skill ~/.claude/skills/video-resume
```

Sous Windows, `~` correspond à `C:\Users\<toi>`. Relance Claude Code : le skill apparaît dans la liste et se déclenche tout seul quand tu donnes une vidéo.

## Utilisation

| Tu dis | Ce qui se passe |
| --- | --- |
| « Résume cette vidéo : <lien> » | Résumé complet dans `resume.md`, avec les points clés dans la réponse |
| « Fais pareil que dans ce tuto » | Claude liste les étapes avec leurs timecodes, puis les applique |
| « Qu'est-ce qu'il disait sur X ? » | Recherche dans la bibliothèque, réponse avec le passage et son timecode |
| « C'est un tuto très visuel » | 60 images au lieu de 36 |
| « C'est un podcast » | Pas d'images, seul l'audio compte |
| « Les sous-titres sont mauvais » | Ignore les sous-titres et réécoute tout avec Whisper |

Les scripts s'utilisent aussi seuls :

```bash
python scripts/analyse_video.py "<lien ou fichier>" [--images 60] [--sans-images] [--langue fr] [--forcer-whisper] [--refaire]
python scripts/bibliotheque.py liste
python scripts/bibliotheque.py cherche <mots-clés>
```

## Limites

- Claude voit des images, pas un film : un geste rapide entre deux captures peut lui échapper.
- C'est de la reconnaissance vocale : les noms propres et termes techniques peuvent être mal entendus. Claude les corrige avec le titre et les images, et signale ce qui reste douteux.
- Les vidéos privées, limitées par l'âge ou par pays ne se téléchargent pas : donne le fichier à la place.
- Le skill et ses consignes sont en français. Les résumés aussi, sauf si tu demandes une autre langue.

## Licence

MIT, voir [LICENSE](LICENSE).
