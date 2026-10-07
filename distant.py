# ============================================================
#  ACCÈS À DISTANCE — téléphone et iPad (via Tailscale)
#  Tourne dans le gardien, donc en permanence.
#   - Pendant une session Jarvis : relaie tout en direct
#     (orbe, questions, réponses, données).
#   - Le reste du temps : sert le tableau de bord (météo, marchés,
#     emails), avec l'orbe en veille.
#  Il n'écoute que sur ton Mac (127.0.0.1) : c'est Tailscale qui le rend
#  accessible à TES appareils, chiffré, sans jamais l'ouvrir sur Internet.
# ============================================================
import json
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import interface

PORT_DISTANT = 8766

_VEILLE = {"etat": "veille", "question": "", "reponse": "", "niveau": 0.0, "env_id": 0}
_ENVELOPPE_VIDE = {"id": 0, "t0": 0, "fps": 30, "valeurs": []}


def _depuis_jarvis(chemin):
    """Demande l'info à la session Jarvis en cours. None si Jarvis ne tourne pas."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{interface.PORT}{chemin}", timeout=0.4) as r:
            return r.read()
    except Exception:
        return None


def jarvis_actif():
    return _depuis_jarvis("/etat") is not None


class _Guichet(BaseHTTPRequestHandler):
    def do_GET(self):
        chemin = self.path.split("?")[0]
        if chemin == "/etat":
            corps = _depuis_jarvis("/etat") or json.dumps(_VEILLE).encode()
            type_contenu = "application/json"
        elif chemin == "/enveloppe":
            corps = _depuis_jarvis("/enveloppe") or json.dumps(_ENVELOPPE_VIDE).encode()
            type_contenu = "application/json"
        elif chemin == "/donnees":
            corps = _depuis_jarvis("/donnees") or json.dumps(interface._donnees).encode()
            type_contenu = "application/json"
        elif chemin == "/icone.png" and interface._ICONE.exists():
            corps, type_contenu = interface._ICONE.read_bytes(), "image/png"
        else:
            corps, type_contenu = interface._PAGE.read_bytes(), "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, *args):
        pass


def _donnees_hors_session():
    """Quand Jarvis dort, le gardien tient lui-même les données à jour."""
    derniers = {"meteo": 0, "marches": 0, "emails": 0}
    while True:
        if not jarvis_actif():
            try:
                interface.rafraichir(derniers)
            except Exception as e:
                print(f"   (accès distant : données indisponibles — {e})")
        time.sleep(15)


def demarrer():
    serveur = ThreadingHTTPServer(("127.0.0.1", PORT_DISTANT), _Guichet)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    threading.Thread(target=_donnees_hors_session, daemon=True).start()
    print(f"📱 Accès distant prêt sur le port {PORT_DISTANT} (via Tailscale)")
