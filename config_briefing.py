# ============================================================
#  RÉGLAGES DU BRIEFING DU MATIN
# ============================================================

# Ville pour la météo (coordonnées GPS)
VILLE = "Toulouse"
LATITUDE = 43.6047
LONGITUDE = 1.4442

# Phrases qui déclenchent le briefing (il suffit qu'une soit dans ta phrase)
MOTS_DECLENCHEURS = ["briefing", "point du jour", "point du matin", "quoi de neuf"]

# Briefing automatique au démarrage de Jarvis le matin (une seule fois par jour)
BRIEFING_AU_DEMARRAGE = True
HEURE_DEBUT = 5     # entre 5h...
HEURE_FIN = 12      # ...et midi

# --- Musique de fond pendant le briefing ---
MUSIQUE_ACTIVE = True

# D'où vient la musique :
#   "apple_music" -> une playlist de l'app Musique (nom exact ci-dessous)
#   "fichier"     -> un fichier audio dans le dossier du projet
# En cas de problème, Jarvis joue une ambiance qu'il génère lui-même.
SOURCE_MUSIQUE = "apple_music"
PLAYLIST_APPLE_MUSIC = "Briefing"           # nom exact de ta playlist
MUSIQUE_BRIEFING = "musique_briefing.mp3"   # utilisé si SOURCE_MUSIQUE = "fichier"

VOLUME_PREPARATION = 0.35    # pendant que Jarvis prépare le briefing (0 à 1)
VOLUME_SOUS_VOIX = 0.10      # pendant qu'il parle, pour ne pas couvrir sa voix

# --- Marchés : nom lu à voix haute -> code Yahoo Finance ---
# (pour trouver un code : chercher le nom sur finance.yahoo.com)
INDICES = {
    "CAC 40": "^FCHI",
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
}
CRYPTOS = {
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Solana": "SOL-USD",
    "XRP": "XRP-USD",
    "Bonk": "BONK-USD",
}

# Recherche web pour analyser les causes des mouvements crypto
# (payant à l'usage : environ 1 centime par recherche, plafonné ci-dessous)
RECHERCHES_WEB_MAX = 4

# Ce que contient le briefing (en français, modifiable librement)
CONSIGNES_BRIEFING = """
Prépare mon briefing du matin, qui sera LU À VOIX HAUTE : environ deux minutes, phrases naturelles,
aucune liste ni mise en forme. Arrondis les chiffres pour l'oral (« cent dix-huit mille dollars »).

1. OUVERTURE : salutation avec le jour et la date, puis la météo en une phrase.

2. BOURSE : en une ou deux phrases, le niveau et la variation du CAC 40, du S&P 500 et du Nasdaq
   (précise s'il s'agit de la clôture de la veille ou d'une séance en cours).

3. CRYPTOS : prix et variation sur 24 h du Bitcoin et de l'Ethereum, puis les autres en une phrase.
   Ensuite, ANALYSE DES CAUSES : utilise la recherche web (2 à 3 recherches, actualités des
   dernières 48 h) pour expliquer ce qui fait bouger le marché : macroéconomie (Fed, inflation,
   dollar, taux), flux des ETF bitcoin, régulation, actualités propres à une crypto, liquidations
   ou sentiment du marché, corrélation avec le Nasdaq. Si une crypto bouge nettement plus que
   les autres, explique pourquoi. 3 à 4 phrases, en distinguant les faits établis des hypothèses.
   Ne donne jamais de conseil d'achat ou de vente, et ne cite ni site ni lien.

4. EMAILS : cherche dans les DEUX comptes ("sci" puis "perso") avec la requête :
   {requete}
   Ouvre avec lire_email uniquement ceux qui semblent importants. Annonce le nombre d'emails utiles,
   puis le plus important en premier (SCI d'abord : locataires, loyers, factures, impôts, banque,
   notaire) : qui, quoi, action éventuelle. Regroupe le secondaire en une phrase.

5. CONCLUSION : les actions à faire aujourd'hui. S'il n'y a rien d'important, dis-le simplement.
"""
