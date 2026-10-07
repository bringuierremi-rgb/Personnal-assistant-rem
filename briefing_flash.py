# ============================================================
#  BRIEFING FLASH — lancé automatiquement à chaque activation
#   1. Cours du Bitcoin et variation sur 24 h
#   2. Nombre d'emails non lus dans chaque boîte
#   3. « Que souhaitez-vous approfondir : marché, messagerie ou météo ? »
#  Préparé directement en Python (rapide, sans passer par Claude),
#  sauf les approfondissements marché et messagerie.
#
#  Tester :  python briefing_flash.py
# ============================================================
import re

QUESTION = "Que souhaitez-vous approfondir : le point marché, la messagerie, ou la météo du jour ?"

# Comment chaque boîte mail est annoncée à voix haute
NOMS_BOITES = {"sci": "la boîte de la SCI", "perso": "votre boîte personnelle"}

# Les mots qui désignent chaque thème dans ta réponse
THEMES = {
    "marche": ["marché", "marche", "bourse", "crypto", "bitcoin", "action", "indice"],
    "messagerie": ["messagerie", "mail", "e-mail", "courrier", "message"],
    "meteo": ["météo", "meteo", "temps", "pluie", "température"],
}
TOUT = ["tout", "les trois", "l'ensemble"]
REFUS = ["rien", "non", "merci", "c'est tout", "ça ira", "plus tard", "pas du tout"]

CONSIGNE_MARCHE = """POINT MARCHÉ, LU À VOIX HAUTE : environ une minute, phrases naturelles, aucune liste.
Voici les cours actuels :
{cours}
1. En une ou deux phrases : CAC 40, S&P 500 et Nasdaq (précise s'il s'agit de la clôture de la veille).
2. Cryptos : Bitcoin et Ethereum, puis les autres en une phrase.
3. Analyse des causes : utilise la recherche web (2 à 3 recherches, actualités des dernières 48 h)
   pour expliquer ce qui fait bouger le marché crypto (macro, Fed, dollar, flux des ETF, régulation,
   actualités propres à une crypto, liquidations). Distingue faits et hypothèses.
Ne donne jamais de conseil d'achat ou de vente, et ne cite ni site ni lien."""

CONSIGNE_MESSAGERIE = """POINT MESSAGERIE, LU À VOIX HAUTE : environ une minute, phrases naturelles, aucune liste.
Cherche les emails non lus dans les deux comptes ("sci" puis "perso") avec la requête :
is:unread in:inbox -category:promotions -category:social
Ouvre avec lire_email uniquement ceux qui semblent importants. Commence par les plus importants
(SCI d'abord : locataires, loyers, factures, impôts, banque, notaire) : qui, quoi, action à faire.
Regroupe le secondaire en une phrase. Termine par les actions à faire."""


# ---------- 1. Les données ----------
def bitcoin_24h():
    """Cours du Bitcoin et vraie variation sur les 24 dernières heures."""
    import pandas as pd
    import yfinance as yf
    from config_briefing import CRYPTOS
    ticker = CRYPTOS.get("Bitcoin", "BTC-USD")
    h = yf.Ticker(ticker).history(period="3d", interval="15m")["Close"].dropna()
    dernier = float(h.iloc[-1])
    avant = h[h.index <= h.index[-1] - pd.Timedelta(hours=24)]
    reference = float(avant.iloc[-1]) if len(avant) else float(h.iloc[0])
    return dernier, (dernier / reference - 1) * 100


def emails_non_lus():
    """{compte: nombre} pour chaque boîte déjà autorisée."""
    from pathlib import Path
    import gmail_outils
    from config_emails import COMPTES_GMAIL
    dossier = Path(__file__).parent
    return {c: gmail_outils.compter_non_lus(c) for c in COMPTES_GMAIL
            if (dossier / f"token_{c}.json").exists()}


# ---------- 2. Le texte du briefing ----------
def _pct(x):
    return f"{abs(x):.1f}".replace(".", ",") + " %"


def texte_flash():
    phrases = ["Bonjour Monsieur."]
    try:
        from marches import _nombre
        prix, var = bitcoin_24h()
        if abs(var) < 0.05:
            tendance = "stable sur 24 heures"
        else:
            tendance = f"en {'hausse' if var > 0 else 'baisse'} de {_pct(var)} sur 24 heures"
        phrases.append(f"Le Bitcoin s'échange à {_nombre(prix)} dollars, {tendance}.")
    except Exception as e:
        print(f"   ⚠️  Bitcoin indisponible : {e}")
        phrases.append("Le cours du Bitcoin est momentanément indisponible.")
    try:
        boites = emails_non_lus()
        if boites:
            morceaux = []
            for i, (compte, n) in enumerate(boites.items()):
                nom = NOMS_BOITES.get(compte, f"la boîte {compte}")
                if i == 0:
                    quantite = "aucun email non lu" if n == 0 else f"{n} email{'s' if n > 1 else ''} non lu{'s' if n > 1 else ''}"
                    morceaux.append(f"{quantite} sur {nom}")
                else:
                    morceaux.append(f"{n if n else 'aucun'} sur {nom}")
            phrases.append("Vous avez " + " et ".join(morceaux) + ".")
    except Exception as e:
        print(f"   ⚠️  Messagerie indisponible : {e}")
        phrases.append("La messagerie est momentanément indisponible.")
    phrases.append(QUESTION)
    return " ".join(phrases)


# ---------- 3. Comprendre la réponse ----------
def _contient(texte, mots):
    return [m for m in mots if re.search(r"(?<!\w)" + re.escape(m) + r"(?!\w)", texte)]


def themes_demandes(reponse):
    """Les thèmes cités, dans l'ordre où tu les as dits."""
    texte = reponse.lower()
    if "pas du tout" in texte or "c'est tout" in texte:
        texte = texte.replace("pas du tout", "").replace("c'est tout", "")
    if _contient(texte, TOUT):
        return ["marche", "messagerie", "meteo"]
    positions = []
    for theme, mots in THEMES.items():
        trouves = [texte.find(m) for m in mots if m in texte]
        if trouves:
            positions.append((min(trouves), theme))
    return [theme for _, theme in sorted(positions)]


def est_un_refus(reponse):
    return bool(_contient(reponse.lower(), REFUS)) and not themes_demandes(reponse)


# ---------- 4. Les approfondissements ----------
def point_meteo():
    from meteo import meteo_donnees
    m = meteo_donnees()
    return (f"À {m['ville']}, il fait actuellement {m['temperature']} degrés, {m['ciel']}. "
            f"Aujourd'hui, de {m['min']} à {m['max']} degrés, avec {m['pluie']} pour cent de risque de pluie.")


def point_marche(cerveau):
    from marches import resume_marches
    return cerveau.repondre(CONSIGNE_MARCHE.format(cours=resume_marches()))


def point_messagerie(cerveau):
    return cerveau.repondre(CONSIGNE_MESSAGERIE)


def approfondir(reponse, cerveau, dire, en_reflexion=lambda titre: None):
    """Traite ta réponse à la question du briefing flash."""
    themes = themes_demandes(reponse)
    if not themes:
        if est_un_refus(reponse):
            dire("Très bien, Monsieur. Je reste à votre disposition.")
        else:                                   # autre demande : question normale
            en_reflexion(reponse)
            dire(cerveau.repondre(reponse))
        return
    for theme in themes:
        try:
            if theme == "meteo":
                dire(point_meteo())
            elif theme == "marche":
                en_reflexion("Point marché")
                dire(point_marche(cerveau))
            elif theme == "messagerie":
                en_reflexion("Point messagerie")
                dire(point_messagerie(cerveau))
        except Exception as e:
            print(f"   ⚠️  {theme} : {e}")
            dire("Je n'arrive pas à obtenir ces informations pour le moment, Monsieur.")


if __name__ == "__main__":
    from voix import parler
    texte = texte_flash()
    print(f"\n🤖 {texte}\n")
    parler(texte)
