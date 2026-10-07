# ============================================================
#  ÉTAPE 5 — La voix
#  Voix principale : edge-tts (voix neuronales Microsoft, gratuites,
#  via Internet). Si Internet ne répond pas : repli sur "say" de macOS.
#  Ensuite, un effet « IA » optionnel (effets_voix.py).
#
#  Lister les voix françaises :  edge-tts --list-voices | grep fr-
#  Lancer :  python voix.py
# ============================================================
import asyncio
import os
import subprocess
import tempfile

import config

# Réglages (modifiables ici, ou dans config.py si tu y ajoutes ces lignes)
VOIX_NEURONALE = getattr(config, "VOIX_NEURONALE", "fr-FR-HenriNeural")
VITESSE = getattr(config, "VITESSE_VOIX", "-5%")      # "-10%" plus lent, "+15%" plus rapide
GRAVE = getattr(config, "GRAVE_VOIX", "-8Hz")          # "-15Hz" plus grave, "+0Hz" voix d'origine
VOIX_SECOURS = getattr(config, "VOIX", "Thomas")       # voix macOS si edge-tts échoue
EFFET_VOIX = getattr(config, "EFFET_VOIX", "moyen")    # "aucun", "discret", "moyen", "marque"

_FICHIER = os.path.join(tempfile.gettempdir(), "jarvis_voix.mp3")


async def _generer(texte):
    import edge_tts
    communication = edge_tts.Communicate(texte, VOIX_NEURONALE, rate=VITESSE, pitch=GRAVE)
    await communication.save(_FICHIER)   # crée un fichier mp3 avec la voix


def parler(texte, effet=None):
    """Lit le texte à voix haute et attend la fin."""
    effet = effet or EFFET_VOIX
    try:
        asyncio.run(_generer(texte))                 # 1) texte -> fichier audio
    except Exception as erreur:
        print(f"(voix neuronale indisponible : {erreur} — voix macOS à la place)")
        subprocess.run(["say", "-v", VOIX_SECOURS, texte])
        return

    fichier = _FICHIER
    if effet != "aucun":
        try:
            import effets_voix
            fichier = effets_voix.appliquer(_FICHIER, effet)   # 2) effet « IA »
        except Exception as erreur:
            print(f"(effet de voix indisponible : {erreur})")

    _animer_interface(fichier)                        # l'orbe suivra le rythme de la voix
    subprocess.run(["afplay", str(fichier)])         # 3) on joue le fichier


def _animer_interface(fichier):
    """Envoie à l'interface le 'volume' de la phrase, pour que l'orbe ondule en rythme."""
    try:
        import time
        import effets_voix
        import interface
        interface.enveloppe(effets_voix.enveloppe_fichier(fichier), time.time() + 0.08)
    except Exception:
        pass   # l'interface n'est pas indispensable pour parler


def bip():
    """Petit son pour signaler 'je t'écoute' (sans attendre)."""
    subprocess.Popen(["afplay", "/System/Library/Sounds/Tink.aiff"])


if __name__ == "__main__":
    bip()
    parler("Bonsoir Monsieur. Tous les systèmes sont opérationnels.")
