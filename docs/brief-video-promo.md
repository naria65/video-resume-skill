# Brief : vidéo de promotion de `video-resume`

Document destiné à l'agent qui produit la vidéo. Il est autoportant : tout ce qu'il faut savoir sur le produit,
le message, le storyboard, les captures à faire et les critères de livraison est ici.

---

## 1. Le produit en une phrase

`video-resume` est un skill pour Claude Code qui permet à Claude de **travailler avec une vidéo** (tuto, podcast, cours,
conférence, fichier local) et, surtout, de **reprendre son contexte** plus tard, sans la retraiter, en citant le passage exact
au timecode.

- Dépôt : https://github.com/naria65/video-resume-skill (licence MIT)
- Installation : `git clone https://github.com/naria65/video-resume-skill ~/.claude/skills/video-resume`
- Vérification : `python ~/.claude/skills/video-resume/scripts/verifier.py`

## 2. Le message

**Message principal** : *Claude ne peut pas regarder une vidéo. Maintenant il peut la reprendre.*

Le bénéfice qui doit rester dans l'esprit du spectateur : **on revient sur une vidéo vue il y a des semaines, et Claude
retrouve le bon passage, avec le timecode, sans rien retraiter.** Le résumé est secondaire ; la reprise de contexte est
le cœur.

Trois idées à faire passer, dans cet ordre :
1. Claude ne voit pas les vidéos ; ce skill les lui rend lisibles (transcription horodatée + planches d'images).
2. Une fois analysée, une vidéo est rangée dans une bibliothèque : on la reprend en une commande.
3. Chaque idée est citée au timecode : on peut vérifier, revenir à la source.

**Public** : développeurs et créateurs qui utilisent déjà Claude Code, et qui regardent beaucoup de tutos ou de podcasts.
Le ton : direct, concret, sans jargon inutile, sans enthousiasme forcé.

## 3. Contraintes d'honnêteté (non négociables)

Ces règles protègent la crédibilité du projet. Elles priment sur le style.

- **Ne rien promettre que le produit ne fait pas.** Ne pas dire « regarde la vidéo comme un humain », « sans aucune erreur »,
  « instantané », « 100 % gratuit ». Le traitement d'une vidéo prend du temps (quelques minutes pour une heure avec une carte
  NVIDIA, bien plus sur processeur). Claude Code exige un compte. La reconnaissance vocale fait des erreurs, et le skill le dit.
- **Pas de chiffres de précision inventés**, pas de témoignages, pas de nombre d'étoiles GitHub, pas de « des milliers
  d'utilisateurs » tant que ce n'est pas vérifié.
- **Pas de contenu protégé à l'écran.** N'utilise pas d'extrait d'une vidéo YouTube tierce. Les démonstrations viennent d'une
  vidéo que le projet possède (enregistrement d'écran maison, ou vidéo synthétique du dépôt). Si un exemple réel est indispensable,
  il doit être sous licence libre et credité.
- **Pas d'impersonation** : aucune marque, logo ou personne réelle utilisée comme si elle approuvait le produit.
- **Les limites apparaissent** (au moins une mention, à l'écran ou dans la description) : reconnaissance vocale imparfaite ;
  les vidéos privées ou restreintes ne se téléchargent pas ; usage personnel, pas de redistribution de transcriptions.

## 4. Formats de livraison

| Version | Format | Durée | Plateformes | Son |
| --- | --- | --- | --- | --- |
| Principale | 16:9, 1920×1080, 30 fps | 75 s (65 à 85 s acceptés) | YouTube, LinkedIn, X | voix off français + sous-titres incrustés |
| Verticale | 9:16, 1080×1920, 30 fps | 30 s | Shorts, Reels, TikTok | voix off + sous-titres incrustés |
| Version anglaise | 16:9 | 75 s | YouTube, X | voix off anglais + sous-titres anglais |

**Toutes les versions doivent fonctionner sans le son** : la plupart des gens regardent en silencieux. Les sous-titres sont
donc **incrustés** dans l'image, pas seulement fournis en fichier.

## 5. Storyboard (version principale, 75 s)

Les timecodes sont indicatifs (± 2 s). Le texte à l'écran est court : 6 mots maximum par carton.

| Temps | Plan | Image | Voix off (FR) | Texte à l'écran |
| --- | --- | --- | --- | --- |
| 0:00–0:05 | Accroche | Écran noir, puis le mot apparaît | « Claude ne peut pas regarder une vidéo. » | Claude ne peut pas regarder une vidéo. |
| 0:05–0:09 | Bascule | Le texte s'efface, une phrase remplace | « Avec ce skill, il peut la reprendre. » | Il peut la reprendre. |
| 0:09–0:18 | Le problème | Un navigateur sur un tuto (vidéo maison), puis une question posée à Claude : « tu te souviens du réglage ? » | « Tu as vu le tuto il y a trois semaines. Le réglage, tu ne le retrouves plus. » | Trois semaines plus tard. |
| 0:18–0:26 | Installation | Terminal : la commande `git clone`, puis `verifier.py` qui affiche « Tout est prêt. » | « Un clone, une commande de vérification. » | `git clone` puis `verifier.py` |
| 0:26–0:40 | Analyse | Terminal : `analyse_video.py` défile (« Transcription : … », « images, planches »), puis une planche d'images légendées apparaît | « Le skill transcrit, et range la vidéo dans une bibliothèque. » | Transcription + images, une fois |
| 0:40–0:58 | **Reprise de contexte (plan clé)** | L'utilisateur tape : « reprends la vidéo sur le mixage et applique-la à mon projet ». Claude répond en citant `[00:12]`. Le lien horodaté est visible. | « Trois semaines plus tard, il reprend la vidéo. Il cite le passage exact. » | Reprise sans retraitement |
| 0:58–1:08 | Vérifier | `resume.md` : « En bref » puis « Points clés », une planche avec le timecode en jaune | « Chaque idée a son timecode. On peut vérifier. » | Chaque idée a son timecode |
| 1:08–1:15 | Appel à l'action | Écran final : l'URL du dépôt et la commande d'installation | « Essaie sur ta prochaine vidéo. » | github.com/naria65/video-resume-skill |

### Version verticale (30 s)

| Temps | Plan | Voix off (FR) | Texte |
| --- | --- | --- | --- |
| 0:00–0:03 | Accroche (même image) | « Claude ne peut pas regarder une vidéo. » | Claude ne peut pas regarder une vidéo. |
| 0:03–0:08 | Le problème | « Tu as vu le réglage il y a trois semaines. » | Trois semaines plus tard. |
| 0:08–0:22 | Reprise de contexte | « Il reprend la vidéo, et cite le passage au timecode. » | Reprise sans retraitement |
| 0:22–0:30 | Appel à l'action | « Lien dans la description. » | Lien dans la description |

## 6. Captures à réaliser (ce qui doit être réellement filmé)

Toutes les captures viennent d'une **exécution réelle** du skill. Ne rien simuler à l'écran.

1. **Installation** : `git clone`, puis `python ~/.claude/skills/video-resume/scripts/verifier.py` (sortie réelle).
2. **Analyse** : `python ~/.claude/skills/video-resume/scripts/analyse_video.py <vidéo maison>` (une vidéo dont on possède les droits,
   ou la vidéo synthétique produite par les tests). Capturer les lignes `[video-resume]` et le JSON `=== PRÊT ===`.
3. **Planche d'images** : une planche `planches/planche_01_*.jpg` réellement produite (timecodes en jaune visibles).
4. **Résumé** : un `resume.md` réel, avec la section « En bref » et les « Points clés à retenir » visibles.
5. **Reprise de contexte (plan clé)** : `python ~/.claude/skills/video-resume/scripts/bibliotheque.py contexte "<sujet>" --pour "<sujet précis>"`
   puis une vraie réponse de Claude qui cite le timecode. Le lien horodaté doit être lisible à l'écran.
6. **Recherche** : `python ~/.claude/skills/video-resume/scripts/bibliotheque.py cherche <mots>`.

Consignes de tournage :
- Terminal propre : police grande (au moins 18 pt), thème à contraste élevé, prompt raccourci, pas d'informations personnelles
  (nom d'utilisateur, chemins contenant un nom réel, clés, historique). Remplacer le dossier personnel par `~` si besoin.
- Enregistrer l'écran à 2× quand c'est possible ; couper les temps d'attente ou les accélérer en le signalant (« accéléré »).
- Les captures faites à la main (navigateur, éditeur) doivent être floutées si elles montrent un nom ou une adresse réels.

## 7. Style visuel

- Fond sombre, texte clair, un seul accent de couleur pour les éléments qui comptent (le timecode, le lien, la commande).
  Le jaune des timecodes du skill est un bon point de repère : réutilise-le pour rester fidèle au produit.
- Police sans empattement, lisible à petite taille. Pas plus de deux polices.
- Les commandes sont toujours dans une police monospace, sur fond légèrement distinct.
- Pas d'effets gadgets (zooms répétés, transitions tournantes). Coupes nettes, mouvements lents.
- Mise en page vérifiée à la largeur téléphone pour la version verticale.

## 8. Son

- Voix off : calme, précise, légèrement chaleureuse. Ni robotique exagéré, ni ton publicitaire criard.
- Musique : libre de droits, instrumentale, discrète (elle ne doit pas couvrir la voix). Baisser de 12 dB sous la voix.
- Pas de bruit de clavier amplifié.

## 9. Sous-titres

- Fournir un fichier **SRT** (et VTT) pour chaque version, en plus des sous-titres incrustés.
- Chaque carton de texte reste à l'écran au moins 2 s.
- Les noms propres et commandes doivent être écrits exactement comme dans le dépôt (`video-resume`, `verifier.py`, `bibliotheque.py`).

## 10. Description (à mettre sous la vidéo)

```text
Claude ne peut pas regarder une vidéo. Avec video-resume, il peut la reprendre : il retrouve le passage,
le cite au timecode, et travaille avec, même des semaines plus tard.

Installation :
git clone https://github.com/naria65/video-resume-skill ~/.claude/skills/video-resume

Dépôt, documentation et licence MIT : https://github.com/naria65/video-resume-skill

Limites : la reconnaissance vocale fait des erreurs ; les vidéos privées ne se téléchargent pas ;
usage personnel, ne redistribue pas les transcriptions.

Chapitres :
0:00 Claude ne peut pas regarder une vidéo
0:09 Le problème
0:18 Installation
0:26 Analyse
0:40 Reprise de contexte
0:58 Vérifier
1:08 Essayer
```

## 11. Livrables

1. `promo-principale-16x9.mp4` (75 s, sous-titres incrustés)
2. `promo-verticale-9x16.mp4` (30 s, sous-titres incrustés)
3. `promo-en-16x9.mp4` (version anglaise, facultative mais souhaitée)
4. Fichiers de sous-titres `.srt` pour chaque version
5. Une vignette 1280×720 (texte court + image forte du plan de reprise de contexte)
6. Le script complet de la voix off, en français et en anglais, dans un fichier texte
7. Une liste des sources : musique (titre, auteur, licence), polices (licence), et l'origine de chaque capture
8. Le journal des captures : quelle commande a produit quelle image, et sur quelle vidéo source

## 12. Critères de validation

Avant de livrer, vérifier **chaque point** :

- [ ] Toutes les captures viennent d'une exécution réelle (aucune interface simulée).
- [ ] Aucun contenu protégé d'un tiers à l'écran ; aucune donnée personnelle visible.
- [ ] Le message « Claude ne peut pas regarder une vidéo » apparaît dans les 5 premières secondes.
- [ ] Le plan de reprise de contexte montre un timecode cliquable ou lisible.
- [ ] Les limites sont mentionnées (description ou dernier carton).
- [ ] Aucune promesse chiffrée, aucun témoignage, aucune affirmation non vérifiable.
- [ ] La vidéo se comprend **sans le son** (sous-titres incrustés, cartons lisibles).
- [ ] La durée respecte le format (75 s ± 10 s ; 30 s pour la verticale).
- [ ] L'URL du dépôt et la commande d'installation sont exactes, et vérifiées sur le dépôt.
- [ ] Les versions 16:9 et 9:16 ont été relues à la taille d'un téléphone.

## 13. Ce qui reste à décider (à demander au responsable du projet)

Ne bloque pas sur ces points : prends la valeur par défaut indiquée, et signale-la dans le journal de livraison.

- **Voix** : par défaut, voix off masculine ou féminine indifférente ; si un enregistrement humain est possible, le préférer.
- **Musique** : par défaut, instrumentale libre de droits.
- **Nom de l'auteur à l'écran** : par défaut, aucun nom n'apparaît ; le dépôt porte le nom de l'organisation GitHub.
- **Publication** : ne rien publier. Livrer les fichiers au responsable, qui décide où et quand.
