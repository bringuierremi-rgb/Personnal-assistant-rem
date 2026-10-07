# ============================================================
#  LES OUTILS DE JARVIS
#  1) OUTILS : la "notice" envoyée à Claude. Il y lit ce que chaque
#     outil fait, et décide lui-même quand s'en servir.
#  2) executer() : quand Claude demande un outil, c'est NOTRE code
#     qui l'exécute ici, sur ton Mac, puis on lui renvoie le résultat.
#  Pour ajouter un outil plus tard : une notice + une ligne dans executer().
# ============================================================
import json
from datetime import datetime

import gmail_outils
from config_emails import COMPTES_GMAIL
from meteo import meteo_du_jour
from marches import resume_marches
from config_briefing import RECHERCHES_WEB_MAX

# Recherche web : un outil "serveur", exécuté directement chez Anthropic
# (notre code n'a rien à faire, Claude reçoit les résultats lui-même)
OUTIL_WEB = {
    "type": "web_search_20260318",
    "name": "web_search",
    "max_uses": RECHERCHES_WEB_MAX,
    "user_location": {"type": "approximate", "city": "Toulouse", "country": "FR",
                      "timezone": "Europe/Paris"},
    "response_inclusion": "excluded",   # n'encombre pas l'historique avec les pages lues
}

_COMPTES = list(COMPTES_GMAIL)

OUTILS = [
    {
        "name": "heure_actuelle",
        "description": "Donne la date et l'heure actuelles. À utiliser pour toute question sur "
                       "l'heure, la date, ou pour savoir ce que veut dire « aujourd'hui » ou « hier ».",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "meteo",
        "description": "Donne la météo actuelle et du jour (températures, ciel, risque de pluie).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "cours_marches",
        "description": "Donne les derniers cours du CAC 40, du S&P 500, du Nasdaq et des principales "
                       "cryptomonnaies, avec leurs variations sur 1 jour et 7 jours.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "chercher_emails",
        "description": "Cherche des emails dans un compte Gmail avec la syntaxe de recherche Gmail. "
                       "Renvoie pour chaque email : id, expéditeur, sujet, date, extrait, non lu ou non.",
        "input_schema": {
            "type": "object",
            "properties": {
                "compte": {"type": "string", "enum": _COMPTES,
                           "description": "Quel compte Gmail consulter."},
                "requete": {"type": "string",
                            "description": "Recherche Gmail, ex : 'is:unread newer_than:1d', "
                                           "'label:Locataires newer_than:30d', 'from:impots.gouv.fr'."},
                "max_resultats": {"type": "integer", "description": "Entre 1 et 25. Par défaut 10."},
            },
            "required": ["compte", "requete"],
        },
    },
    {
        "name": "lire_email",
        "description": "Lit le contenu complet d'un email, à partir de l'id donné par chercher_emails.",
        "input_schema": {
            "type": "object",
            "properties": {
                "compte": {"type": "string", "enum": _COMPTES},
                "id_email": {"type": "string"},
            },
            "required": ["compte", "id_email"],
        },
    },
]

_JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def executer(nom, parametres):
    """Exécute l'outil demandé par Claude et renvoie le résultat sous forme de texte."""
    if nom == "heure_actuelle":
        maintenant = datetime.now()
        return f"{_JOURS[maintenant.weekday()]} {maintenant:%d/%m/%Y, %H:%M}"

    if nom == "meteo":
        return meteo_du_jour()

    if nom == "cours_marches":
        return resume_marches()

    if nom == "chercher_emails":
        resultats = gmail_outils.chercher(
            parametres["compte"], parametres["requete"], parametres.get("max_resultats", 10)
        )
        return json.dumps(resultats, ensure_ascii=False) if resultats else "Aucun email trouvé."

    if nom == "lire_email":
        return json.dumps(
            gmail_outils.lire(parametres["compte"], parametres["id_email"]), ensure_ascii=False
        )

    raise ValueError(f"Outil inconnu : {nom}")
