# ============================================================
#  ÉTAPE 8 — La connexion à Gmail (lecture seule)
#  - La 1re fois, une page Google s'ouvre pour autoriser l'accès.
#  - Google donne alors un "jeton" (token_perso.json, token_sci.json)
#    qui évite de se reconnecter à chaque fois.
#  - Autorisation demandée : LECTURE SEULE. Jarvis ne peut rien
#    envoyer, supprimer ni modifier.
# ============================================================
import base64
import html
import re
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config_emails import COMPTES_GMAIL

DOSSIER = Path(__file__).parent
IDENTIFIANTS = DOSSIER / "credentials.json"     # téléchargé depuis Google Cloud
AUTORISATIONS = ["https://www.googleapis.com/auth/gmail.readonly"]

_connexions = {}   # une connexion par compte, gardée en mémoire


def _connexion(compte):
    """Renvoie une connexion Gmail pour 'perso' ou 'sci'."""
    if compte not in COMPTES_GMAIL:
        raise ValueError(f"Compte inconnu : {compte}. Comptes possibles : {list(COMPTES_GMAIL)}")
    if compte in _connexions:
        return _connexions[compte]

    jeton = DOSSIER / f"token_{compte}.json"
    creds = None
    if jeton.exists():
        creds = Credentials.from_authorized_user_file(str(jeton), AUTORISATIONS)

    if creds and not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())          # renouvelle le jeton sans rien demander
        except Exception:
            creds = None                      # jeton périmé : on redemande l'autorisation

    if not creds or not creds.valid:
        if not IDENTIFIANTS.exists():
            raise FileNotFoundError("credentials.json introuvable dans le dossier du projet.")
        adresse = COMPTES_GMAIL[compte]
        print(f"\n🔐 Autorisation Gmail : choisis le compte {adresse} dans le navigateur.")
        flux = InstalledAppFlow.from_client_secrets_file(str(IDENTIFIANTS), AUTORISATIONS)
        creds = flux.run_local_server(port=0, login_hint=adresse)
        jeton.write_text(creds.to_json())

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    _connexions[compte] = service
    return service


def chercher(compte, requete, max_resultats=10):
    """Cherche des emails avec la syntaxe Gmail. Renvoie un résumé de chacun."""
    service = _connexion(compte)
    max_resultats = max(1, min(int(max_resultats), 25))
    liste = service.users().messages().list(
        userId="me", q=requete, maxResults=max_resultats
    ).execute()

    resultats = []
    for m in liste.get("messages", []):
        detail = service.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        entetes = {h["name"]: h["value"] for h in detail["payload"].get("headers", [])}
        resultats.append({
            "id": m["id"],
            "de": entetes.get("From", ""),
            "sujet": entetes.get("Subject", "(sans sujet)"),
            "date": entetes.get("Date", ""),
            "extrait": html.unescape(detail.get("snippet", "")),
            "non_lu": "UNREAD" in detail.get("labelIds", []),
        })
    return resultats


def compter_non_lus(compte):
    """Nombre approximatif d'emails non lus importants (hors pubs et réseaux sociaux)."""
    service = _connexion(compte)
    reponse = service.users().messages().list(
        userId="me", q="is:unread in:inbox -category:promotions -category:social", maxResults=1
    ).execute()
    return reponse.get("resultSizeEstimate", 0)


def _decoder(donnees):
    return base64.urlsafe_b64decode(donnees + "==").decode("utf-8", errors="replace")


def _texte_de(partie):
    """Va chercher le texte d'un email (qui peut contenir plusieurs morceaux)."""
    type_mime = partie.get("mimeType", "")
    donnees = partie.get("body", {}).get("data")
    if type_mime == "text/plain" and donnees:
        return _decoder(donnees)
    for sous_partie in partie.get("parts", []) or []:
        texte = _texte_de(sous_partie)
        if texte:
            return texte
    if type_mime == "text/html" and donnees:     # pas de version texte : on nettoie le HTML
        brut = _decoder(donnees)
        brut = re.sub(r"(?is)<(style|script).*?</\1>", " ", brut)
        brut = re.sub(r"<[^>]+>", " ", brut)
        return re.sub(r"\s+", " ", html.unescape(brut)).strip()
    return ""


def lire(compte, id_email, max_caracteres=6000):
    """Renvoie le contenu complet d'un email (raccourci s'il est très long)."""
    service = _connexion(compte)
    m = service.users().messages().get(userId="me", id=id_email, format="full").execute()
    entetes = {h["name"]: h["value"] for h in m["payload"].get("headers", [])}
    texte = _texte_de(m["payload"]).strip()
    if len(texte) > max_caracteres:
        texte = texte[:max_caracteres] + " […]"
    return {
        "de": entetes.get("From", ""),
        "a": entetes.get("To", ""),
        "sujet": entetes.get("Subject", ""),
        "date": entetes.get("Date", ""),
        "texte": texte,
    }
