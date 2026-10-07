# ============================================================
#  INSTALLATION DU GARDIEN
#  1. Crée « Jarvis.command » : un double-clic dessus ouvre le Terminal
#     et lance le gardien (sans rien taper).
#  2. Le met sur ton Bureau.
#  3. (Si tu acceptes) l'ajoute à l'ouverture de session de ton Mac :
#     le gardien démarre tout seul quand tu allumes l'ordinateur.
#
#  Installer :  python installer_gardien.py
#  Retirer    :  python installer_gardien.py --retirer
# ============================================================
import os
import stat
import subprocess
import sys
from pathlib import Path

DOSSIER = Path(__file__).parent.resolve()
LANCEUR = DOSSIER / "Jarvis.command"
BUREAU = Path.home() / "Desktop" / "Jarvis.command"


def _osascript(code):
    r = subprocess.run(["osascript", "-e", code], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


def creer_lanceur():
    contenu = f"""#!/bin/zsh
# Lanceur du gardien de Jarvis (créé par installer_gardien.py)
cd "{DOSSIER}"
source .venv/bin/activate
python gardien.py
"""
    for chemin in (LANCEUR, BUREAU):
        chemin.write_text(contenu)
        chemin.chmod(chemin.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"✅ Lanceur créé : {chemin}")


def ajouter_ouverture_session():
    _osascript(f'tell application "System Events" to make login item at end '
               f'with properties {{path:"{LANCEUR}", hidden:false}}')
    print("✅ Le gardien démarrera à chaque ouverture de session.")


def retirer():
    try:
        _osascript('tell application "System Events" to delete '
                   '(every login item whose name is "Jarvis.command")')
        print("✅ Retiré de l'ouverture de session.")
    except Exception as e:
        print(f"(ouverture de session : {e})")
    for chemin in (LANCEUR, BUREAU):
        if chemin.exists():
            chemin.unlink()
            print(f"✅ Supprimé : {chemin}")


if __name__ == "__main__":
    if "--retirer" in sys.argv:
        retirer()
        sys.exit()
    if not (DOSSIER / ".venv").exists():
        print("⚠️  Dossier .venv introuvable : lance ce script depuis le dossier de Jarvis.")
        sys.exit(1)
    creer_lanceur()
    reponse = input("\nLancer le gardien automatiquement à l'ouverture de session ? (o/n) ").strip().lower()
    if reponse.startswith("o"):
        try:
            ajouter_ouverture_session()
        except Exception as e:
            print(f"⚠️  Impossible de l'ajouter automatiquement ({e}).")
            print("   Ajoute-le à la main : Réglages Système > Général > Ouverture,")
            print(f"   bouton +, puis choisis : {LANCEUR}")
    print("\nPour démarrer le gardien maintenant : double-clic sur Jarvis.command (sur ton Bureau).")
