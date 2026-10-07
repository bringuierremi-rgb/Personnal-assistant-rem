# ============================================================
#  ÉTAPE 2 (v2) — Le réveil : double clap et/ou « Hey Jarvis »
#  Le micro est écouté en continu, par tranches de 80 ms.
#   - « Hey Jarvis » : un petit réseau de neurones donne un score de 0 à 1
#   - Clap : on repère un son bref, brutal et riche en aigus
#  Le mode se choisit dans config_reveil.py.
#
#  Tester :  python reveil.py
# ============================================================
import numpy as np
import sounddevice as sd

import config_reveil as cfg
from config import TAUX_ECHANTILLONNAGE as SR, SEUIL_REVEIL

BLOC = 1280          # 80 ms : la taille attendue par la détection « Hey Jarvis »
SOUS_BLOC = 160      # 10 ms : la précision de la détection des claps

_modele = None


def _modele_voix():
    """Charge la détection « Hey Jarvis » seulement si on en a besoin."""
    global _modele
    if _modele is None:
        import openwakeword
        from openwakeword.model import Model
        openwakeword.utils.download_models()
        _modele = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
    return _modele


class DetecteurClap:
    """Reconnaît un enchaînement de claquements de mains."""

    def __init__(self, nombre=None, sensibilite=None, minimum=None,
                 ecart_min=None, ecart_max=None, taux=SR, bavard=False):
        self.nombre = nombre or cfg.NOMBRE_CLAPS
        self.sensibilite = sensibilite or cfg.SENSIBILITE
        self.minimum = minimum or cfg.NIVEAU_MINIMUM
        self.ecart_min = ecart_min or cfg.ECART_MIN
        self.ecart_max = ecart_max or cfg.ECART_MAX
        self.taux = taux
        self.bavard = bavard          # affiche ce qu'il entend (pour régler)
        self.fond = 0.002             # bruit de fond de la pièce, mesuré en continu
        self.candidat = None          # un son brutal en cours d'examen
        self.claps = []               # moments des claps validés
        self.t = 0.0                  # horloge interne, en secondes

    def ajouter(self, bloc):
        """Analyse 10 ms de son. Renvoie True quand la série de claps est complète."""
        x = bloc.astype(np.float32) / 32768.0
        # np.diff garde surtout les aigus : forts pour un clap, faibles pour la voix
        energie = float(np.sqrt(np.mean(np.diff(x) ** 2)))
        volume = float(np.sqrt(np.mean(x ** 2)))           # tout le son, graves compris
        self.t += len(bloc) / self.taux

        if self.candidat is None and self.claps and self.t - self.claps[-1] > self.ecart_max:
            self.claps = []                                  # trop tard : on repart de zéro

        if self.candidat is not None:
            age = self.t - self.candidat["debut"]
            if age <= 0.03:
                self.candidat["pic"] = max(self.candidat["pic"], energie)
                self.candidat["pic_vol"] = max(self.candidat["pic_vol"], volume)
            elif age <= 0.15:
                self.candidat["suite"] = max(self.candidat["suite"], energie)
                self.candidat["suite_vol"] = max(self.candidat["suite_vol"], volume)
            else:
                return self._juger()
            return False

        if energie > max(self.minimum, self.fond * self.sensibilite):
            self.candidat = {"debut": self.t, "pic": energie, "suite": 0.0,
                             "pic_vol": volume, "suite_vol": 0.0}
        else:
            self.fond = max(1e-4, 0.98 * self.fond + 0.02 * energie)
        return False

    def _juger(self):
        """Le son brutal est-il retombé assez vite pour être un clap ?"""
        c, self.candidat = self.candidat, None
        # un clap retombe vite, aigus ET graves ; une consonne (t, p) est suivie d'une voyelle
        bref = c["suite"] < c["pic"] * 0.25 and c["suite_vol"] < c["pic_vol"] * 0.25
        if self.bavard:
            print(f"   son brutal : niveau {c['pic']:.3f} (fond {self.fond:.4f}, "
                  f"x{c['pic'] / self.fond:.0f}) -> {'CLAP' if bref else 'trop long (voix, bruit)'}")
        if not bref:
            return False
        if self.claps and c["debut"] - self.claps[-1] > self.ecart_max:
            self.claps = []                                  # le clap précédent est trop ancien
        if self.claps and c["debut"] - self.claps[-1] < self.ecart_min:
            return False                                     # écho du même clap
        self.claps.append(c["debut"])
        if len(self.claps) >= self.nombre:
            self.claps = []
            return True
        return False


def attendre_mot_reveil(bavard=False):
    """Bloque jusqu'au réveil. Renvoie "clap" ou "voix"."""
    ecouter_voix = cfg.MODE in ("voix", "les_deux")
    ecouter_claps = cfg.MODE in ("clap", "les_deux")
    modele = _modele_voix() if ecouter_voix else None
    if modele:
        modele.reset()
    claps = DetecteurClap(bavard=bavard) if ecouter_claps else None

    with sd.InputStream(samplerate=SR, channels=1, dtype="int16", blocksize=BLOC) as flux:
        while True:
            bloc, _ = flux.read(BLOC)
            bloc = bloc.flatten()
            if claps:
                for i in range(0, BLOC, SOUS_BLOC):
                    if claps.ajouter(bloc[i:i + SOUS_BLOC]):
                        return "clap"
            if modele and max(modele.predict(bloc).values()) > SEUIL_REVEIL:
                return "voix"


if __name__ == "__main__":
    print(f"Mode : {cfg.MODE}. ", end="")
    if cfg.MODE != "voix":
        print(f"Claque {cfg.NOMBRE_CLAPS} fois dans tes mains. ", end="")
    if cfg.MODE != "clap":
        print('Ou dis "Hey Jarvis". ', end="")
    print("(Ctrl+C pour quitter)")
    while True:
        declencheur = attendre_mot_reveil(bavard=True)
        print(f"✅ Réveillé ! ({declencheur})")
