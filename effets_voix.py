# ============================================================
#  EFFET « IA » SUR LA VOIX
#  Le fichier audio de la voix passe par 3 traitements :
#   1. un filtre qui retire les graves (son plus « électronique »)
#   2. une résonance métallique très courte (la touche « IA »)
#   3. une réverbération légère (la voix « remplit » la pièce)
#
#  Écouter les 4 niveaux :  python effets_voix.py
# ============================================================
import tempfile
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

TAUX = 44100

# Les niveaux d'effet : résonance métallique, réverbération, taille de la "pièce"
NIVEAUX = {
    "discret": {"metal": 0.15, "reverb": 0.12, "piece": 0.72, "aigus_max": None},
    "moyen":   {"metal": 0.30, "reverb": 0.20, "piece": 0.78, "aigus_max": None},
    "marque":  {"metal": 0.50, "reverb": 0.30, "piece": 0.82, "aigus_max": 7000},
}


def _charger(chemin):
    """Décode le fichier audio (mp3...) en un signal mono."""
    import av
    conteneur = av.open(str(chemin))
    convertisseur = av.AudioResampler(format="flt", layout="mono", rate=TAUX)
    morceaux = []
    for image in conteneur.decode(conteneur.streams.audio[0]):
        for sortie in convertisseur.resample(image):
            morceaux.append(sortie.to_ndarray().reshape(-1))
    conteneur.close()
    return np.concatenate(morceaux).astype(np.float64)


def _peigne(x, retard_ms, retour):
    """Un écho très court qui se répète : c'est la base de la résonance et de la réverb.
    y[n] = x[n] + retour * y[n - d], calculé par blocs de d échantillons (rapide)."""
    d = max(1, int(TAUX * retard_ms / 1000))
    y = np.copy(x)
    for debut in range(d, len(x), d):
        fin = min(debut + d, len(x))
        y[debut:fin] += retour * y[debut - d:fin - d]
    return y


def _passe_tout(x, retard_ms, g=0.7):
    """Diffuse le son sans changer son timbre (rend la réverb plus douce).
    y[n] = -g x[n] + x[n - d] + g y[n - d], calculé par blocs."""
    d = max(1, int(TAUX * retard_ms / 1000))
    y = -g * x
    for debut in range(d, len(x), d):
        fin = min(debut + d, len(x))
        y[debut:fin] += x[debut - d:fin - d] + g * y[debut - d:fin - d]
    return y


def _reverb(x, piece, decalage_ms=0.0):
    """Réverbération de Schroeder : 4 échos en parallèle puis 2 diffuseurs."""
    echos = sum(_peigne(x, ms + decalage_ms, piece) for ms in (29.7, 37.1, 41.1, 43.7)) / 4
    return _passe_tout(_passe_tout(echos, 5.0), 1.7)


def traiter(signal, niveau="moyen"):
    """Applique l'effet et renvoie un signal stéréo."""
    p = NIVEAUX[niveau]
    x = np.concatenate([signal, np.zeros(int(0.6 * TAUX))])     # place pour la fin de la réverb

    x = sosfilt(butter(2, 110, "highpass", fs=TAUX, output="sos"), x)
    if p["aigus_max"]:
        x = sosfilt(butter(2, p["aigus_max"], "lowpass", fs=TAUX, output="sos"), x)

    metal = _peigne(x, 7.0, 0.35)
    x = x * (1 - p["metal"]) + metal * p["metal"] * 0.6

    gauche = x + _reverb(x, p["piece"]) * p["reverb"]
    droite = x + _reverb(x, p["piece"], decalage_ms=1.3) * p["reverb"]   # léger effet stéréo
    stereo = np.stack([gauche, droite], axis=1)
    return 0.9 * stereo / max(np.abs(stereo).max(), 1e-9)


def enveloppe_fichier(chemin, fps=30):
    """Le 'volume' du fichier audio, 30 valeurs par seconde entre 0 et 1 (pour animer l'orbe)."""
    signal = _charger(chemin)
    taille = TAUX // fps
    n = len(signal) // taille
    if n == 0:
        return []
    blocs = signal[: n * taille].reshape(n, taille)
    rms = np.sqrt((blocs ** 2).mean(axis=1))
    return list(np.clip(rms / max(np.percentile(rms, 95), 1e-9), 0, 1))


def appliquer(fichier_entree, niveau="moyen"):
    """Fichier voix -> fichier .wav avec l'effet. Renvoie le chemin du nouveau fichier."""
    stereo = traiter(_charger(fichier_entree), niveau)
    sortie = Path(tempfile.gettempdir()) / "jarvis_voix_effet.wav"
    with wave.open(str(sortie), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(TAUX)
        w.writeframes((stereo * 32767).astype("<i2").tobytes())
    return sortie


if __name__ == "__main__":
    import subprocess
    import voix
    phrase = "Bonjour Monsieur. Tous les systèmes sont opérationnels."
    voix.EFFET_VOIX = "aucun"
    for niveau in ["aucun", "discret", "moyen", "marque"]:
        print(f"▶︎ Effet : {niveau}")
        voix.parler(phrase, effet=niveau)
