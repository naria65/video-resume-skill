"""Tests du skill video-resume. Aucun réseau, aucun GPU, aucun modèle Whisper.

Lancer : python -m unittest discover -s tests -v
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import analyse_video  # noqa: E402
import bibliotheque  # noqa: E402
from outils import hms, slug  # noqa: E402

FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")
PIL = importlib.util.find_spec("PIL") is not None

VTT = """WEBVTT
Kind: captions
Language: fr

00:00:01.000 --> 00:00:03.000 align:start position:0%
bonjour à tous <00:00:02.000><c>et bienvenue</c>

00:00:01.000 --> 00:00:03.000
bonjour à tous et bienvenue

00:00:03.500 --> 00:00:06.000
on va parler de <c>mixage</c> audio.
"""


class Outils(unittest.TestCase):
    def test_hms(self):
        self.assertEqual(hms(0), "00:00")
        self.assertEqual(hms(65.9), "01:05")
        self.assertEqual(hms(3725), "1:02:05")

    def test_slug(self):
        self.assertEqual(slug("Mixage : le compresseur !"), "mixage-le-compresseur")
        self.assertEqual(slug("???"), "video")


class SousTitres(unittest.TestCase):
    def test_lire_vtt_dedoublonne_et_nettoie_les_balises(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "subs.fr.vtt"
            f.write_text(VTT, encoding="utf-8")
            segs = analyse_video.lire_vtt(f)
        self.assertEqual([s["texte"] for s in segs],
                         ["bonjour à tous et bienvenue", "on va parler de mixage audio."])
        self.assertEqual(segs[1]["debut"], 3.5)

    def test_transcript_par_paragraphes_horodates(self):
        segs = [{"debut": i * 10.0, "fin": i * 10.0 + 10, "texte": f"Phrase {i}."} for i in range(12)]
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            mots = analyse_video.ecrire_transcription(segs, d)
            texte = (d / "transcript.md").read_text(encoding="utf-8")
            self.assertTrue((d / "segments.json").exists())
        self.assertGreater(mots, 0)
        self.assertIn("**[00:00]**", texte)
        self.assertIn("**[00:50]**", texte)


class Bibliotheque(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self.tmp.name)
        self._ancienne = bibliotheque.RACINE
        bibliotheque.RACINE = self.racine

    def tearDown(self):
        bibliotheque.RACINE = self._ancienne
        self.tmp.cleanup()

    def creer(self, nom, titre, source, segments, resume=None, ident="youtube:abc123"):
        d = self.racine / nom
        d.mkdir(parents=True)
        (d / "segments.json").write_text(json.dumps(segments, ensure_ascii=False), encoding="utf-8")
        (d / "manifeste.json").write_text(json.dumps({
            "schema": 2, "id": ident, "titre": titre, "auteur": "Chaîne test", "source": source,
            "duree": "01:30", "analysee_le": "2026-01-01", "dossier": str(d)}, ensure_ascii=False), encoding="utf-8")
        if resume:
            (d / "resume.md").write_text(resume, encoding="utf-8")
        return d

    def segments_mixage(self):
        # « compresseur » n'apparaît qu'à 24 s (segment 6)
        mots = ["On commence par la prise de son.", "Le gain doit rester bas.", "Ensuite le routage.",
                "Puis les effets de base.", "Un peu de reverb.", "Ça sonne mieux.",
                "Le réglage du compresseur est clé.", "Ajuste le seuil doucement.", "Et le ratio aussi.",
                "Vérifie au casque.", "Fin de la partie.", "On passe au mastering."]
        return [{"debut": i * 4.0, "fin": i * 4.0 + 4, "texte": t} for i, t in enumerate(mots)]

    RESUME = """# Mixage — résumé
Auteur test · 01:30 · https://www.youtube.com/watch?v=abc123

## En bref
Une méthode pour mixer une voix seule, de la prise de son au mastering.

## Déroulé détaillé
Beaucoup de détails sur le gain et le compresseur.

## Points clés à retenir
- Garder le gain bas à l'enregistrement.
- Le compresseur se règle à l'oreille.
"""

    def test_en_bref_et_liste(self):
        self.creer("2026-01-01_mixage_abc123", "Mixage voix", "https://www.youtube.com/watch?v=abc123",
                   self.segments_mixage(), resume=self.RESUME)
        self.assertIn("mixer une voix seule", bibliotheque.en_bref(self.racine / "2026-01-01_mixage_abc123"))
        self.assertEqual(len(bibliotheque.fiches()), 1)

    def test_recherche_sans_accents_et_sans_doublons(self):
        segs = self.segments_mixage()
        segs[0]["texte"] = "Le métro parisien grince."
        self.creer("v1", "Métro", "https://youtu.be/abc123", segs)
        trouves = bibliotheque.cherche("METRO")
        self.assertEqual(len(trouves), 1)
        self.assertEqual(trouves[0]["temps"], "00:00")
        res = bibliotheque.cherche("compresseur")
        # plusieurs fenêtres chevauchent le passage : une seule doit sortir, avec un lien horodaté
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["lien"], "https://youtu.be/abc123?t=12")

    def test_les_titres_du_resume_ne_sont_pas_des_passages(self):
        self.creer("v1", "Mixage voix", "https://www.youtube.com/watch?v=abc123",
                   self.segments_mixage(), resume=self.RESUME)
        res = bibliotheque.cherche("compresseur", n=20)
        self.assertTrue(res)
        self.assertFalse(any(p["texte"].lstrip().startswith("#") for p in res))
        self.assertTrue(any(p["temps"] == "résumé" for p in res))

    def test_lien_horodate(self):
        f = bibliotheque.lien_horodate
        self.assertEqual(f("https://www.youtube.com/watch?v=abc123", 65.2),
                         "https://youtube.com/watch?v=abc123&t=65s")
        self.assertEqual(f("https://youtu.be/abc123", 5), "https://youtu.be/abc123?t=5")
        self.assertEqual(f("https://exemple.org/video", 5), "https://exemple.org/video")
        self.assertEqual(f("/videos/cours.mp4", 61), "/videos/cours.mp4 @ 01:01")

    def test_contexte_par_titre_contient_en_bref_passages_et_points_cles(self):
        self.creer("v1", "Mixage voix", "https://www.youtube.com/watch?v=abc123",
                   self.segments_mixage(), resume=self.RESUME)
        texte = bibliotheque.contexte("mixage", pour="compresseur")
        self.assertIn("## Mixage voix", texte)
        self.assertIn("### En bref", texte)
        self.assertIn("### Passages pour « compresseur »", texte)
        self.assertIn("&t=", texte)
        self.assertIn("### Points clés", texte)
        self.assertLess(texte.index("### Passages"), texte.index("### Points clés"))

    def test_contexte_par_sujet_si_pas_de_titre(self):
        self.creer("v1", "Autre chose", "https://www.youtube.com/watch?v=abc123", self.segments_mixage())
        texte = bibliotheque.contexte("compresseur")
        self.assertIn("## Autre chose", texte)
        self.assertIn("Pas encore de resume.md", texte)

    def test_contexte_respecte_la_taille_maximale(self):
        self.creer("v1", "Mixage voix", "https://www.youtube.com/watch?v=abc123",
                   self.segments_mixage(), resume=self.RESUME)
        texte = bibliotheque.contexte("mixage", maximum=250)
        self.assertLessEqual(len(texte), 250 + 80)  # + la phrase qui signale la coupe
        self.assertIn("tronqué", texte)

    def test_contexte_inconnu(self):
        self.assertIsNone(bibliotheque.contexte("rien de tel"))

    def test_resoudre_par_identifiant(self):
        self.creer("v1", "Titre", "https://youtu.be/abc123", self.segments_mixage(), ident="youtube:abc123")
        self.assertEqual(len(bibliotheque.resoudre("youtube:abc123")), 1)


@unittest.skipUnless(FFMPEG and PIL, "ffmpeg et Pillow requis")
class PipelineLocal(unittest.TestCase):
    """Fichier local -> planches, manifeste, bibliothèque, sans réseau (transcription simulée)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self._ancienne = bibliotheque.RACINE
        bibliotheque.RACINE = self.base / "bibliotheque"
        self.video = self.base / "demo.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10:duration=40",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=40",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                        str(self.video)], check=True)

    def tearDown(self):
        bibliotheque.RACINE = self._ancienne
        self.tmp.cleanup()

    def args(self, **kw):
        base = dict(refaire=False, langue="fr", images=9, sans_images=False,
                    forcer_whisper=False, modele="large-v3-turbo")
        base.update(kw)
        return argparse.Namespace(**base)

    def test_pipeline_complet_puis_bibliotheque_puis_refaire(self):
        segs = [{"debut": i * 4.0, "fin": i * 4.0 + 4, "texte": f"Phrase {i} sur le mixage."} for i in range(10)]
        with mock.patch.object(analyse_video, "transcrire", return_value=(segs, "fr")):
            m = analyse_video.traiter(str(self.video), self.args())
        dossier = Path(m["dossier"])
        self.assertEqual(m["schema"], 2)
        self.assertTrue((dossier / "info.md").exists())
        self.assertTrue((dossier / "transcript.md").exists())
        self.assertEqual(len(list((dossier / "frames").glob("*.jpg"))), 9)
        self.assertEqual(len(list((dossier / "planches").glob("*.jpg"))), 1)
        self.assertFalse((dossier / "audio.wav").exists())
        self.assertTrue(self.video.exists(), "un fichier local ne doit jamais être supprimé")

        # deuxième passage : déjà vue, rien retraité
        with mock.patch.object(analyse_video, "transcrire") as t:
            again = analyse_video.traiter(str(self.video), self.args())
        t.assert_not_called()
        self.assertTrue(again["deja_vue"])

        # la bibliothèque retrouve la vidéo et son contexte
        (dossier / "resume.md").write_text("# T\n\n## En bref\nUn test.\n", encoding="utf-8")
        self.assertEqual(bibliotheque.en_bref(dossier), "Un test.")
        self.assertIn("## demo", bibliotheque.contexte("demo") or "")

        # --refaire régénère les images mais garde le résumé, dans le même dossier
        with mock.patch.object(analyse_video, "transcrire", return_value=(segs, "fr")):
            redo = analyse_video.traiter(str(self.video), self.args(refaire=True))
        self.assertEqual(Path(redo["dossier"]), dossier)
        self.assertTrue((dossier / "resume.md").exists())
        self.assertEqual(len(list((dossier / "frames").glob("*.jpg"))), 9)


class Verificateur(unittest.TestCase):
    def test_verifier_s_execute(self):
        env = {**os.environ, "VIDEO_RESUMES_DIR": tempfile.gettempdir()}
        r = subprocess.run([sys.executable, str(SCRIPTS / "verifier.py")], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        self.assertIn(r.returncode, (0, 1))
        self.assertIn("Python", r.stdout)


if __name__ == "__main__":
    unittest.main()
