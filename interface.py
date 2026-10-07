# ============================================================
#  ÉTAPE 7 (v2) — L'interface visuelle immersive
#  Un mini serveur web tourne sur ton Mac uniquement (127.0.0.1).
#  La page interface.html lui demande :
#   /etat       -> ce que fait Jarvis + le niveau du micro (20 fois par seconde)
#   /enveloppe  -> le "volume" de la phrase que Jarvis prononce, pour que
#                  l'orbe ondule exactement au rythme de sa voix
#   /donnees    -> météo, marchés, emails non lus (mis à jour en arrière-plan)
#
#  Tester seul (démo des états) :  python interface.py
# ============================================================
import atexit
import json
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 8765
_PAGE = Path(__file__).with_name("interface.html")
_ICONE = Path(__file__).with_name("icone.png")

# État partagé entre Jarvis (qui écrit) et la page (qui lit)
_etat = {"etat": "veille", "question": "", "reponse": "", "niveau": 0.0, "env_id": 0}
_enveloppe = {"id": 0, "t0": 0.0, "fps": 30, "valeurs": []}
_donnees = {"meteo": None, "marches": [], "emails": {}, "maj": None, "maj_marches": None}

RAFRAICHIR_METEO = 15 * 60     # secondes
RAFRAICHIR_MARCHES = 60        # cours en direct chaque minute (l'historique 1 an : chaque heure)
RAFRAICHIR_EMAILS = 10 * 60


class _Guichet(BaseHTTPRequestHandler):
    """Répond aux demandes du navigateur."""

    def do_GET(self):
        if self.path.startswith("/etat"):
            corps, type_contenu = json.dumps(_etat).encode(), "application/json"
        elif self.path.startswith("/enveloppe"):
            corps, type_contenu = json.dumps(_enveloppe).encode(), "application/json"
        elif self.path.startswith("/donnees"):
            corps, type_contenu = json.dumps(_donnees).encode(), "application/json"
        elif self.path.startswith("/icone.png") and _ICONE.exists():
            corps, type_contenu = _ICONE.read_bytes(), "image/png"
        else:
            corps, type_contenu = _PAGE.read_bytes(), "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, *args):
        pass  # pas de messages dans le Terminal à chaque requête


# ---------- Données des panneaux, rafraîchies en arrière-plan ----------
def _boucle_donnees():
    derniers = {"meteo": 0, "marches": 0, "emails": 0}
    while True:
        rafraichir(derniers)
        time.sleep(10)


def rafraichir(derniers):
    """Met à jour ce qui doit l'être (météo, marchés, emails). Utilisé aussi par le gardien."""
    if True:
        maintenant = time.time()
        if maintenant - derniers["meteo"] > RAFRAICHIR_METEO:
            try:
                from meteo import meteo_donnees
                _donnees["meteo"] = meteo_donnees()
            except Exception as e:
                print(f"   (interface : météo indisponible — {e})")
            derniers["meteo"] = maintenant
        if maintenant - derniers["marches"] > RAFRAICHIR_MARCHES:
            try:
                from marches import cotations_temps_reel
                nouvelles = cotations_temps_reel()
                if nouvelles:                       # si Yahoo ne répond pas, on garde les dernières
                    _donnees["marches"] = nouvelles
                    _donnees["maj_marches"] = time.strftime("%H:%M:%S")
            except Exception as e:
                print(f"   (interface : marchés indisponibles — {e})")
            derniers["marches"] = maintenant
        if maintenant - derniers["emails"] > RAFRAICHIR_EMAILS:
            try:
                import gmail_outils
                from config_emails import COMPTES_GMAIL
                dossier = Path(__file__).parent
                _donnees["emails"] = {
                    compte: gmail_outils.compter_non_lus(compte)
                    for compte in COMPTES_GMAIL
                    if (dossier / f"token_{compte}.json").exists()   # seulement si déjà autorisé
                }
            except Exception as e:
                print(f"   (interface : emails indisponibles — {e})")
            derniers["emails"] = maintenant
        _donnees["maj"] = time.strftime("%H:%M")


# ---------- Ouverture en plein écran ----------
# Un site web n'a pas le droit de se mettre seul en plein écran (sécurité des navigateurs).
# On ouvre donc nous-mêmes une fenêtre "application" dédiée, déjà en plein écran.
NAVIGATEURS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
PROFIL = Path.home() / ".jarvis_navigateur"     # profil séparé : ne touche pas à ton navigateur habituel
_fenetre = None


def _ouvrir_plein_ecran(url):
    global _fenetre
    for chemin in NAVIGATEURS:
        if Path(chemin).exists():
            # une ancienne fenêtre Jarvis encore ouverte ferait ignorer le plein écran : on la ferme
            subprocess.run(["pkill", "-f", f"user-data-dir={PROFIL}"], capture_output=True)
            time.sleep(0.5)
            # --kiosk : plein écran fiable sur Mac (pour quitter la fenêtre : Cmd + Q)
            _fenetre = subprocess.Popen(
                [chemin, f"--user-data-dir={PROFIL}", "--kiosk", f"--app={url}",
                 "--no-first-run", "--no-default-browser-check"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            atexit.register(_fermer_fenetre)            # la fenêtre se ferme avec Jarvis
            print(f"   🖥️  Interface : {Path(chemin).stem} en plein écran")
            return
    # Pas de Chrome/Brave/Edge : Safari au premier plan, puis le raccourci plein écran
    script = f'''
        tell application "Safari"
            activate
            make new document with properties {{URL:"{url}"}}
        end tell
        delay 2
        tell application "Safari" to activate
        delay 0.3
        tell application "System Events" to keystroke "f" using {{control down, command down}}
    '''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    atexit.register(fermer_fenetre)                     # l'onglet se ferme avec Jarvis
    if r.returncode != 0:
        print("   ⚠️  Plein écran Safari refusé par macOS. Pour l'autoriser :")
        print("      Réglages Système > Confidentialité et sécurité > Accessibilité > coche « Terminal »")
        print("      (en attendant : clique dans la page Jarvis, elle passera en plein écran)")
    else:
        print("   🖥️  Interface : Safari en plein écran")


_fermeture_volontaire = False


def fermer_fenetre():
    """Ferme la fenêtre de l'interface (Chrome/Brave/Edge ou onglet Safari)."""
    global _fermeture_volontaire
    _fermeture_volontaire = True
    if _fenetre is not None:
        if _fenetre.poll() is None:
            _fenetre.terminate()
        subprocess.run(["pkill", "-f", f"user-data-dir={PROFIL}"], capture_output=True)
    else:
        _fermer_onglets_safari()


def _fermer_onglets_safari():
    """Parcourt chaque fenêtre et chaque onglet de Safari, et ferme ceux de Jarvis."""
    script = f'''
        if application "Safari" is running then
            tell application "Safari"
                set nbFermes to 0
                repeat with w in (every window)
                    set nb to count of tabs of w
                    repeat with i from nb to 1 by -1
                        try
                            if URL of tab i of w contains "localhost:{PORT}" then
                                close tab i of w
                                set nbFermes to nbFermes + 1
                            end if
                        end try
                    end repeat
                end repeat
                return nbFermes
            end tell
        end if
        return 0
    '''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"   ⚠️  Fermeture de Safari impossible : {r.stderr.strip()}")
    else:
        print(f"   🖥️  Onglets Jarvis fermés dans Safari : {r.stdout.strip() or 0}")


_fermer_fenetre = fermer_fenetre      # ancien nom, gardé pour compatibilité


def quand_fermee(action):
    """Lance 'action' si tu fermes toi-même la fenêtre (Cmd + Q)."""
    def surveiller():
        while _fenetre is None:
            time.sleep(1)
        _fenetre.wait()
        if not _fermeture_volontaire:
            print("\n🖥️  Fenêtre de l'interface fermée.")
            action()
    threading.Thread(target=surveiller, daemon=True).start()


# ---------- Ce que Jarvis appelle ----------
def demarrer(ouvrir_navigateur=True, donnees=True, plein_ecran=True):
    """Lance le serveur en arrière-plan et ouvre la page."""
    serveur = ThreadingHTTPServer(("127.0.0.1", PORT), _Guichet)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    if donnees:
        threading.Thread(target=_boucle_donnees, daemon=True).start()
    if ouvrir_navigateur:
        url = f"http://localhost:{PORT}"
        if plein_ecran:
            try:
                _ouvrir_plein_ecran(url)
                return
            except Exception as e:
                print(f"   (plein écran indisponible : {e})")
        webbrowser.open(url)


def etat(nom, question=None, reponse=None):
    """Change ce qu'affiche l'interface."""
    _etat["etat"] = nom
    if question is not None:
        _etat["question"] = question
    if reponse is not None:
        _etat["reponse"] = reponse
    if nom != "ecoute":
        _etat["niveau"] = 0.0


def niveau(valeur):
    """Niveau du micro en direct (0 à 1), pendant que tu parles."""
    _etat["niveau"] = round(max(0.0, min(1.0, float(valeur))), 3)


def enveloppe(valeurs, debut, fps=30):
    """Transmet le 'volume' de la phrase que Jarvis va prononcer, et l'heure de début."""
    _enveloppe.update(id=_enveloppe["id"] + 1, t0=debut * 1000, fps=fps,
                      valeurs=[round(float(v), 3) for v in valeurs])
    _etat["env_id"] = _enveloppe["id"]


if __name__ == "__main__":
    import math
    import random
    demarrer()
    print("Démo de l'interface (Ctrl+C pour quitter)")
    print("Touches dans la page : T = texte, M = mode minimal, F = plein écran")
    while True:
        print("  -> veille")
        etat("veille", "", "")
        time.sleep(5)
        print("  -> écoute (niveau de micro simulé)")
        etat("ecoute", "", "")
        for i in range(40):
            niveau(abs(math.sin(i / 3)) * random.uniform(0.4, 1.0))
            time.sleep(0.1)
        print("  -> réflexion")
        etat("reflexion", "Quel temps fera-t-il demain ?", "")
        time.sleep(4)
        print("  -> parole (voix simulée)")
        valeurs = [abs(math.sin(i / 4)) * random.uniform(0.3, 1.0) * (1 if (i // 25) % 3 else 0.15)
                   for i in range(30 * 6)]
        enveloppe(valeurs, time.time())
        etat("parole", None, "Un ciel dégagé, Monsieur. Vous pourrez laisser le parapluie.")
        time.sleep(6)
