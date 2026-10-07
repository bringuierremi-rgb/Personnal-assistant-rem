# ============================================================
#  MUSIQUE VIA APPLE MUSIC — pilotage de l'app Musique de macOS
#  On envoie des ordres AppleScript à l'app Musique avec "osascript" :
#  lancer une playlist, régler son volume, mettre en pause.
#  Même mode d'emploi que MusiqueDeFond : demarrer / volume / arreter.
#
#  1re utilisation : macOS demande si le Terminal peut contrôler
#  « Musique » -> clique sur OK.
#
#  Tester :  python musique_apple.py
# ============================================================
import atexit
import subprocess
import threading
import time


def _applescript(code):
    """Envoie un ordre à macOS et renvoie la réponse (texte)."""
    resultat = subprocess.run(["osascript", "-e", code], capture_output=True, text=True, timeout=15)
    if resultat.returncode != 0:
        raise RuntimeError(resultat.stderr.strip() or "erreur AppleScript")
    return resultat.stdout.strip()


def _musique(ordre):
    return _applescript(f'tell application "Music" to {ordre}')


_en_cours = []          # les lecteurs qui jouent en ce moment


def couper_tout():
    """Coupe net toute musique lancée par Jarvis (appelé aussi quand Jarvis s'arrête)."""
    for lecteur in list(_en_cours):
        try:
            _musique("pause")
            lecteur._regler(lecteur.volume_avant)
        except Exception:
            pass
        _en_cours.remove(lecteur)


atexit.register(couper_tout)      # même en cas de Ctrl+C ou d'erreur


class MusiqueAppleMusic:
    def __init__(self, playlist, aleatoire=True):
        self.playlist = playlist.replace('"', '\\"')
        self.aleatoire = aleatoire
        self.niveau = 0                 # volume actuel de l'app Musique (0 à 100)
        self._fondu_en_cours = None

    def _regler(self, niveau):
        self.niveau = int(max(0, min(100, niveau)))
        _musique(f"set sound volume to {self.niveau}")

    def _fondu(self, cible, duree):
        etapes = max(1, int(duree / 0.15))
        depart = self.niveau
        for i in range(1, etapes + 1):
            self._regler(depart + (cible - depart) * i / etapes)
            time.sleep(duree / etapes)

    def demarrer(self, volume=0.4, fondu=2.0):
        # On mémorise l'état d'avant pour le remettre à la fin
        self.volume_avant = int(_musique("get sound volume"))

        self._regler(0)
        _musique(f"set shuffle enabled to {'true' if self.aleatoire else 'false'}")
        _musique(f'play playlist "{self.playlist}"')
        _en_cours.append(self)
        print(f"   🎵 Apple Music : playlist « {self.playlist} »")
        self.volume(volume, fondu)

    def volume(self, cible, fondu=1.5):
        """Change le volume en douceur, en arrière-plan (0 = muet, 1 = plein volume)."""
        if self._fondu_en_cours and self._fondu_en_cours.is_alive():
            self._fondu_en_cours.join()
        self._fondu_en_cours = threading.Thread(
            target=self._fondu, args=(cible * 100, fondu), daemon=True)
        self._fondu_en_cours.start()

    def arreter(self, fondu=3.0):
        if self._fondu_en_cours and self._fondu_en_cours.is_alive():
            self._fondu_en_cours.join()
        self._fondu(0, fondu)
        _musique("pause")                   # la musique ne joue qu'avec l'interface ouverte
        self._regler(self.volume_avant)     # on remet le volume comme avant
        if self in _en_cours:
            _en_cours.remove(self)


if __name__ == "__main__":
    from config_briefing import PLAYLIST_APPLE_MUSIC, VOLUME_PREPARATION, VOLUME_SOUS_VOIX
    m = MusiqueAppleMusic(PLAYLIST_APPLE_MUSIC)
    print("Volume 'préparation' pendant 6 s...")
    m.demarrer(VOLUME_PREPARATION)
    time.sleep(6)
    print("Volume 'sous la voix' pendant 6 s...")
    m.volume(VOLUME_SOUS_VOIX)
    time.sleep(6)
    print("Fondu de sortie...")
    m.arreter()
