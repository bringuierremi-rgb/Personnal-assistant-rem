# ============================================================
#  DIAGNOSTIC — affiche en direct ce que la détection entend
#  Lancer :  python diagnostic_reveil.py   (Ctrl+C pour quitter)
# ============================================================
import numpy as np
import sounddevice as sd
import openwakeword
from openwakeword.model import Model
from config import TAUX_ECHANTILLONNAGE as SR

BLOC = 1280

print("Micro utilisé :", sd.query_devices(kind="input")["name"])

openwakeword.utils.download_models()
modele = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
print("Modèles chargés :", list(modele.models.keys()))
print('\nDis "Hey Jarvis" plusieurs fois. Chaque ligne = 0,5 seconde.\n')

score_max, volume_max, n = 0.0, 0.0, 0
with sd.InputStream(samplerate=SR, channels=1, dtype="int16", blocksize=BLOC) as flux:
    while True:
        bloc, _ = flux.read(BLOC)
        bloc = bloc.flatten()
        scores = modele.predict(bloc)
        score_max = max(score_max, max(scores.values()))
        volume_max = max(volume_max, np.abs(bloc).mean())
        n += 1
        if n % 6 == 0:  # environ toutes les 0,5 s
            barre = "█" * int(score_max * 40)
            print(f"volume {volume_max:6.0f} | score {score_max:.3f} {barre}")
            score_max, volume_max = 0.0, 0.0
