# ============================================================
#  MUSIQUE DE FOND — pour le briefing
#  - Joue un fichier audio en boucle (mp3, m4a, wav...) ou, à défaut,
#    une nappe d'ambiance générée par Jarvis lui-même.
#  - Le volume peut changer en douceur pendant la lecture (fondu),
#    ce qui permet de baisser la musique quand Jarvis parle.
#
#  Tester :  python musique.py
# ============================================================
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd

TAUX = 44100   # qualité CD


# ---------- 1. Charger un fichier audio ----------
def _charger_fichier(chemin, max_secondes=300):
    """Décode un fichier audio en tableau stéréo (av est déjà installé avec Whisper)."""
    import av
    conteneur = av.open(str(chemin))
    flux = conteneur.streams.audio[0]
    convertisseur = av.AudioResampler(format="flt", layout="stereo", rate=TAUX)
    morceaux, total = [], 0
    for image in conteneur.decode(flux):
        for sortie in convertisseur.resample(image):
            morceau = sortie.to_ndarray().reshape(-1, 2)
            morceaux.append(morceau)
            total += len(morceau)
        if total > max_secondes * TAUX:
            break
    conteneur.close()
    return np.concatenate(morceaux).astype(np.float32)


# ---------- 2. Ou composer une ambiance (si aucun fichier) ----------
def _ambiance_par_defaut():
    """Nappe cinématographique douce, en boucle parfaite de 24 secondes.
    4 accords (la mineur, fa, do, sol) qui se fondent les uns dans les autres."""
    duree_accord = 6.0
    accords = [
        [110.00, 220.00, 261.63, 329.63],   # la mineur
        [87.31, 174.61, 220.00, 261.63],    # fa majeur
        [130.81, 196.00, 261.63, 329.63],   # do majeur
        [98.00, 196.00, 246.94, 293.66],    # sol majeur
    ]
    n_total = int(len(accords) * duree_accord * TAUX)
    n_fenetre = int(2 * duree_accord * TAUX)
    t = np.arange(n_fenetre) / TAUX
    enveloppe = np.sin(np.pi * t / (2 * duree_accord)) ** 2   # monte puis descend
    sortie = np.zeros((n_total, 2), dtype=np.float64)

    for k, accord in enumerate(accords):
        son = np.zeros((n_fenetre, 2))
        for i, f in enumerate(accord):
            poids = 0.5 if i == 0 else 0.25
            for canal, desaccord in ((0, 0.997), (1, 1.003)):    # léger chorus stéréo
                son[:, canal] += poids * np.sin(2 * np.pi * f * desaccord * t)
                son[:, canal] += 0.06 * np.sin(2 * np.pi * f * 2 * t)   # harmonique
        son *= (0.85 + 0.15 * np.sin(2 * np.pi * 0.2 * t))[:, None]       # ondulation lente
        son *= enveloppe[:, None]
        debut = int(k * duree_accord * TAUX)
        indices = (debut + np.arange(n_fenetre)) % n_total                # boucle sans coupure
        np.add.at(sortie, indices, son)

    sortie /= np.abs(sortie).max()
    return (0.6 * sortie).astype(np.float32)


# ---------- 3. Le lecteur ----------
class MusiqueDeFond:
    def __init__(self, fichier=None):
        chemin = Path(__file__).with_name(fichier) if fichier else None
        self.audio = None
        if chemin and chemin.exists():
            try:
                self.audio = _charger_fichier(chemin)
                print(f"   🎵 Musique : {chemin.name}")
            except Exception as e:
                print(f"   ⚠️  Impossible de lire {chemin.name} ({e}), ambiance par défaut.")
        if self.audio is None:
            self.audio = _ambiance_par_defaut()
            print("   🎵 Musique : ambiance par défaut")
        self.position = 0
        self.gain = 0.0          # volume actuel
        self.cible = 0.0         # volume visé
        self.vitesse = 1.0       # variation de volume par seconde
        self.flux = None
        self._verrou = threading.Lock()

    def _remplir(self, sortie, nb, _temps, _statut):
        """Appelée en continu par la carte son : on lui donne la suite de la musique."""
        indices = (self.position + np.arange(nb)) % len(self.audio)
        self.position = (self.position + nb) % len(self.audio)
        with self._verrou:
            ecart = self.cible - self.gain
            pas_max = self.vitesse * nb / TAUX
            fin = self.gain + float(np.clip(ecart, -pas_max, pas_max))
            gains = np.linspace(self.gain, fin, nb, dtype=np.float32)
            self.gain = fin
        sortie[:] = self.audio[indices] * gains[:, None]

    def demarrer(self, volume=0.4, fondu=2.0):
        self.position, self.gain = 0, 0.0
        self.volume(volume, fondu)
        self.flux = sd.OutputStream(samplerate=TAUX, channels=2, dtype="float32",
                                    callback=self._remplir)
        self.flux.start()

    def volume(self, cible, fondu=1.5):
        """Change le volume en douceur (0 = muet, 1 = plein volume)."""
        with self._verrou:
            self.cible = cible
            self.vitesse = max(abs(cible - self.gain), 0.01) / max(fondu, 0.05)

    def arreter(self, fondu=3.0):
        """Fondu de sortie puis arrêt."""
        if not self.flux:
            return
        self.volume(0.0, fondu)
        time.sleep(fondu + 0.3)
        self.flux.stop()
        self.flux.close()
        self.flux = None


if __name__ == "__main__":
    from config_briefing import MUSIQUE_BRIEFING, VOLUME_PREPARATION, VOLUME_SOUS_VOIX
    m = MusiqueDeFond(MUSIQUE_BRIEFING)
    print("Volume 'préparation' pendant 6 s...")
    m.demarrer(VOLUME_PREPARATION)
    time.sleep(6)
    print("Volume 'sous la voix' pendant 6 s...")
    m.volume(VOLUME_SOUS_VOIX)
    time.sleep(6)
    print("Fondu de sortie...")
    m.arreter()
