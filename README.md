# video-resume · Claude lit les vidéos, et reprend leur contexte

[![tests](https://github.com/naria65/video-resume-skill/actions/workflows/tests.yml/badge.svg)](https://github.com/naria65/video-resume-skill/actions/workflows/tests.yml)
[![licence MIT](https://img.shields.io/badge/licence-MIT-green.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)

Un skill pour [Claude Code](https://claude.com/claude-code) qui permet à Claude de **travailler avec une vidéo** :
un tuto YouTube, un podcast, un cours, une conférence, un fichier local.

Claude ne peut pas regarder une vidéo. Ce skill la transforme en ce qu'il sait lire :
une **transcription horodatée** et des **planches d'images** légendées au timecode. Et il range le tout dans une
**bibliothèque** : la prochaine fois que tu reviens sur la vidéo, Claude **reprend son contexte** en quelques secondes,
sans rien retraiter, et te cite le passage exact.

> « Il y a trois semaines j'ai vu une vidéo sur le mixage d'une voix. Reprends-la et applique-la à mon projet. »

Claude retrouve la vidéo, charge son résumé et les passages utiles, puis répond en citant `[12:40]` pour chaque idée.

## Pourquoi c'est utile

- **Suivre un tuto sans le revoir** : Claude liste les étapes avec leurs timecodes, puis les applique à ton projet.
- **Résumer sans perdre les détails** : chiffres, noms, réglages, citations, chacun avec son timecode.
- **Reprendre le contexte d'une vidéo vue il y a longtemps** : une commande, un bloc compact, aucun retraitement.
- **Retrouver un passage** : « qu'est-ce qu'il disait sur le sidechain ? » répond avec la vidéo et le moment exact.
- **Tout rester en local** : la transcription se fait sur ta machine, et les fichiers restent dans `~/video-resumes`.

## Exemple : reprendre le contexte d'une vidéo

Voici le bloc que produit `bibliotheque.py contexte` pour une vidéo de démonstration (données fictives) :

```text
## Mixer une voix seule
Chaîne démo · 01:30 · analysée le 2026-11-26
Source : https://www.youtube.com/watch?v=a1b2c3

### En bref
Une méthode pour mixer une voix seule, du gain à la compression.

### Passages pour « compresseur »
- [00:12](https://youtube.com/watch?v=a1b2c3&t=12s) Ensuite on fait le routage. Passons aux effets. …
  Le compresseur est l'outil central. Règle le seuil à l'oreille. Le ratio autour de 3 pour 1.

### Points clés
- Garder le gain bas à l'entrée.
- Régler le compresseur à l'oreille, ratio d'environ 3:1.
```

Claude lit ce bloc, puis travaille avec : il peut ouvrir la transcription autour de `00:12` si un détail manque.

## Comment ça marche

1. **Récupération** avec [yt-dlp](https://github.com/yt-dlp/yt-dlp) (480p max, la vidéo est supprimée après traitement), ou lecture directe d'un fichier local.
2. **Transcription** : les sous-titres écrits à la main par l'auteur s'il y en a (plus fiables). Sinon [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (`large-v3-turbo`), sur la carte NVIDIA si elle est là, sinon sur le processeur.
3. **Images** : 36 captures réparties sur la vidéo, regroupées par 9 en planches avec le timecode en jaune.
4. **Bibliothèque** : chaque vidéo a son dossier, avec un identifiant. Une vidéo déjà vue n'est jamais retraitée.
5. **Résumé** et **contexte** : écrits par Claude après lecture de la transcription et des images.

Dans chaque dossier : `resume.md`, `transcript.md`, `info.md`, `segments.json`, `manifeste.json`, `planches/`, `frames/`.

## Installation

### 1. Prérequis

| Quoi | Pourquoi | Installation |
| --- | --- | --- |
| Python 3.10+ | scripts | [python.org](https://www.python.org/downloads/) |
| ffmpeg (ffmpeg + ffprobe) | audio, images | Windows : `winget install Gyan.FFmpeg` · macOS : `brew install ffmpeg` · Linux : `sudo apt install ffmpeg` |
| Modules Python | transcription, planches | voir ci-dessous |

```bash
python -m pip install -r requirements.txt
```

Pour une transcription rapide sur carte **NVIDIA** (facultatif) :

```bash
python -m pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
```

Sans carte compatible, la transcription passe sur le processeur avec un modèle plus léger : ça marche, en plus lent.

### 2. Installer le skill

```bash
git clone https://github.com/naria65/video-resume-skill ~/.claude/skills/video-resume
```

Sous Windows, `~` correspond à `C:\Users\<toi>`. Relance Claude Code : le skill apparaît et se déclenche tout seul
quand tu donnes une vidéo.

### 3. Vérifier

```bash
python ~/.claude/skills/video-resume/scripts/verifier.py
```

Le script dit ce qui manque et comment l'installer. Il ne modifie rien.

## Utilisation

| Tu dis | Ce qui se passe |
| --- | --- |
| « Résume cette vidéo : *lien* » | Résumé complet dans `resume.md`, avec les points clés dans la réponse |
| « Fais pareil que dans ce tuto : *lien* » | Claude liste les étapes avec leurs timecodes, puis les applique |
| « Reprends la vidéo sur le mixage » | Contexte rechargé depuis la bibliothèque, sans retraitement |
| « Qu'est-ce qu'il disait sur X ? » | Recherche dans la bibliothèque, réponse avec le passage et son timecode |
| « C'est un tuto très visuel » | 60 images au lieu de 36 |
| « C'est un podcast » | Pas d'images, seul l'audio compte |
| « Les sous-titres sont mauvais » | Ignore les sous-titres et réécoute tout avec Whisper |

### En ligne de commande

Les scripts s'utilisent aussi seuls, sans Claude :

```bash
# analyser (une ou plusieurs vidéos)
python scripts/analyse_video.py "<lien ou fichier>" [--images 60] [--sans-images] [--langue fr] [--forcer-whisper] [--refaire]

# consulter la bibliothèque
python scripts/bibliotheque.py liste
python scripts/bibliotheque.py cherche <mots-clés> [-n 10]
python scripts/bibliotheque.py contexte "<titre ou sujet>" [--pour "<sujet précis>"] [--max 8000]
python scripts/bibliotheque.py index
```

### Configuration

| Réglage | Effet |
| --- | --- |
| `VIDEO_RESUMES_DIR` | dossier de la bibliothèque (par défaut `~/video-resumes`) |
| `--modele` | modèle Whisper, ou le dossier d'un modèle déjà téléchargé (utile hors ligne) |
| `--images N` | nombre d'images extraites (36 par défaut) |

## Limites

- **Claude voit des images, pas un film.** Un geste rapide entre deux captures peut lui échapper.
- **C'est de la reconnaissance vocale.** Les noms propres et termes techniques peuvent être mal entendus. Claude les corrige avec le titre et les images, et signale ce qui reste douteux.
- **Les vidéos privées, limitées par âge ou par pays ne se téléchargent pas.** Donne le fichier à la place.
- **Le modèle Whisper se télécharge une fois** depuis Hugging Face. Hors ligne, passe-le avec `--modele`.
- **Le texte de la transcription est envoyé à Claude** comme tout contenu d'une session. Le traitement audio, lui, reste sur ta machine.

## Respect des auteurs

Ce skill sert à comprendre et à travailler avec une vidéo, pour la personne qui la regarde.
Ne redistribue pas une transcription intégrale, et ne contourne pas les restrictions d'accès d'une plateforme.

## Développement

```bash
python -m unittest discover -s tests -v
```

Les tests n'ont besoin ni de réseau, ni de GPU, ni du modèle Whisper : le pipeline complet tourne sur une vidéo
synthétique, avec la transcription simulée. La CI les lance sur Python 3.10 et 3.12.

Les contributions sont bienvenues : une issue, ou une pull request avec des tests. Voir aussi [CHANGELOG.md](CHANGELOG.md).

## Licence

MIT, voir [LICENSE](LICENSE).
