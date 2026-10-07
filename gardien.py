# ============================================================
#  LE GARDIEN — attend un double clap pour lancer Jarvis
#  Tourne en permanence, consomme très peu.
#   double clap -> lance jarvis.py -> quand Jarvis s'arrête
#   (« au revoir »), le gardien se remet à attendre.
#
#  Toutes les 30 secondes, il vérifie quel micro est actif :
#  si tu branches ou actives un micro après coup, il le prend.
#
#  Lancer :  python gardien.py   (Ctrl+C pour l'arrêter)
# ============================================================
import os
import subprocess
import sys
import time
from pathlib import Path

import sounddevice as sd

from reveil import DetecteurClap, BLOC, SOUS_BLOC
from config import TAUX_ECHANTILLONNAGE as SR

DOSSIER = Path(__file__).parent
VERIFIER_MICRO = 30          # secondes entre deux vérifications du micro
SON_ACTIVATION = "/System/Library/Sounds/Glass.aiff"


def _rafraichir_peripheriques():
    """Fait relire la liste des micros (pour voir un micro branché/activé après coup)."""
    try:
        sd._terminate()
        sd._initialize()
    except Exception:
        pass


def _nom_micro():
    try:
        return sd.query_devices(kind="input")["name"]
    except Exception:
        return None


def attendre_double_clap():
    detecteur = DetecteurClap()
    micro_affiche = None
    while True:
        micro = _nom_micro()
        if micro is None:
            if micro_affiche != "aucun":
                print("🎙️  Aucun micro disponible : j'attends qu'un micro soit activé...")
                micro_affiche = "aucun"
            time.sleep(3)
            _rafraichir_peripheriques()
            continue
        if micro != micro_affiche:
            print(f"🎙️  Micro : {micro}")
            micro_affiche = micro
        try:
            with sd.InputStream(samplerate=SR, channels=1, dtype="int16", blocksize=BLOC) as flux:
                debut = time.time()
                while time.time() - debut < VERIFIER_MICRO:
                    bloc, _ = flux.read(BLOC)
                    bloc = bloc.flatten()
                    for i in range(0, BLOC, SOUS_BLOC):
                        if detecteur.ajouter(bloc[i:i + SOUS_BLOC]):
                            return
        except Exception as e:
            print(f"⚠️  Micro indisponible ({e}), nouvel essai...")
            time.sleep(3)
        _rafraichir_peripheriques()


# Accès depuis ton téléphone / iPad (via Tailscale)
ACCES_DISTANT = True
# Empêche le Mac de se mettre en veille tant que le gardien tourne
# (l'écran peut s'éteindre ; attention : un MacBook capot fermé s'endort quand même)
EMPECHER_VEILLE = True


def main():
    print("=" * 52)
    print("  J.A.R.V.I.S. — gardien actif")
    print("  Double clap pour lancer Jarvis · Ctrl+C pour arrêter")
    print("=" * 52)
    if EMPECHER_VEILLE:
        # caffeinate (outil de macOS) garde le Mac éveillé tant que le gardien vit
        subprocess.Popen(["caffeinate", "-i", "-s", "-w", str(os.getpid())])
        print("☕ Le Mac reste éveillé tant que le gardien tourne")
    if ACCES_DISTANT:
        try:
            import distant
            distant.demarrer()
        except Exception as e:
            print(f"⚠️  Accès distant indisponible : {e}")
    while True:
        attendre_double_clap()
        print(f"\n⚡ Double clap détecté ({time.strftime('%H:%M:%S')}) — lancement de Jarvis\n")
        subprocess.Popen(["afplay", SON_ACTIVATION])
        subprocess.run([sys.executable, str(DOSSIER / "jarvis.py")], cwd=DOSSIER)
        print("\n💤 Jarvis s'est arrêté. Double clap pour le relancer.\n")
        time.sleep(2)            # évite qu'un dernier bruit le relance aussitôt


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGardien arrêté.")
