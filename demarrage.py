# ============================================================
#  MUSIQUE DE DÉMARRAGE
#  lancer()  : démarre la musique (fichier ou Apple Music)
#  conclure(): attend la fin de la séquence de projection, baisse la
#              musique, fait parler Jarvis, puis fondu de sortie.
#
#  Tester :  python demarrage.py
# ============================================================
import threading
import time
from pathlib import Path

import config_demarrage as cfg


def lancer():
    """Démarre la musique. Renvoie le lecteur (ou None si rien à jouer)."""
    if not cfg.ACTIVE:
        return None
    try:
        if cfg.SOURCE == "apple_music":
            from musique_apple import MusiqueAppleMusic
            lecteur = MusiqueAppleMusic(cfg.PLAYLIST, aleatoire=False)
        else:
            chemin = Path(__file__).with_name(cfg.FICHIER)
            if not chemin.exists():
                print(f"   🎵 Pas de musique de démarrage : place ton fichier sous le nom « {cfg.FICHIER} »")
                return None
            from musique import MusiqueDeFond
            lecteur = MusiqueDeFond(cfg.FICHIER)
        lecteur.demarrer(cfg.VOLUME, fondu=1.0)
        lecteur.debut = time.time()
        return lecteur
    except Exception as e:
        print(f"   ⚠️  Musique de démarrage indisponible : {e}")
        return None


def _arreter(lecteur, fondu):
    try:
        lecteur.arreter(fondu=fondu)
    except Exception as e:
        print(f"   ⚠️  Arrêt de la musique : {e}")


def conclure(lecteur, dire, phrase="Jarvis en ligne, Monsieur.", question=None):
    """Laisse la séquence se terminer, baisse la musique, salue.
    Si une question suit, la musique s'éteint PENDANT la question :
    dès que Jarvis a fini de parler, il peut t'écouter."""
    if lecteur is None:
        dire(phrase if not question else f"{phrase} {question}")
        return
    try:
        reste = cfg.DUREE_MINIMUM - (time.time() - lecteur.debut)
        if reste > 0:
            time.sleep(reste)
        lecteur.volume(cfg.VOLUME_SOUS_VOIX, fondu=1.2)
        time.sleep(1.2)
        dire(phrase)
    except Exception:
        _arreter(lecteur, 1.0)
        raise
    if question:
        fondu = threading.Thread(target=_arreter, args=(lecteur, 2.0), daemon=True)
        fondu.start()                      # fondu en arrière-plan...
        dire(question)                     # ...pendant que Jarvis pose la question
        fondu.join()
    else:
        _arreter(lecteur, cfg.FONDU_SORTIE)


if __name__ == "__main__":
    from voix import parler
    print("Musique de démarrage...")
    conclure(lancer(), parler)
