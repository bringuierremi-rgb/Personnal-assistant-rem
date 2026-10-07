# ============================================================
#  ÉTAPE 1 — Vérifier que Python entend ton micro
#  et trouver le bon SEUIL_SILENCE pour config.py
#  Lancer :  python test_micro.py
# ============================================================
import numpy as np
import sounddevice as sd
from config import TAUX_ECHANTILLONNAGE as SR


def mesurer(secondes):
    """Enregistre quelques secondes et renvoie (audio, volume moyen)."""
    audio = sd.rec(int(secondes * SR), samplerate=SR, channels=1, dtype="int16")
    sd.wait()  # attend la fin de l'enregistrement
    # Le son = une suite de nombres. Leur valeur absolue moyenne = le "volume".
    return audio, np.abs(audio).mean()


print("1/2 — Reste SILENCIEUX pendant 3 secondes...")
_, volume_silence = mesurer(3)
print(f"     Volume du silence : {volume_silence:.0f}")

print("2/2 — PARLE normalement pendant 3 secondes...")
audio, volume_voix = mesurer(3)
print(f"     Volume de ta voix : {volume_voix:.0f}")

if volume_voix < 50:
    print("\n⚠️  Presque rien capté. Va dans Réglages Système > Confidentialité > Micro")
    print("    et autorise le Terminal (ou VS Code), puis relance.")
else:
    conseil = int((volume_silence + volume_voix) / 2)
    print(f"\n✅ Micro OK. Conseil : mets SEUIL_SILENCE = {conseil} dans config.py")

print("\nJe te rejoue ce que j'ai entendu...")
sd.play(audio, SR)
sd.wait()
