# ============================================================
#  CONFIG — tous les réglages de Jarvis au même endroit
#  (tu ne touches qu'à ce fichier pour personnaliser)
# ============================================================
from dotenv import load_dotenv

# Lit le fichier .env et charge ta clé API (ANTHROPIC_API_KEY)
load_dotenv()

# --- Audio ---
TAUX_ECHANTILLONNAGE = 16000   # 16 000 mesures/seconde : le format attendu par la détection et Whisper

# --- Mot d'activation ---
SEUIL_REVEIL = 0.3             # 0 à 1. Plus haut = moins de faux réveils, mais il faut parler plus clairement

# --- Détection de la fin de ta phrase ---
SEUIL_SILENCE = 179            # volume sous lequel on considère que c'est du silence (à calibrer avec test_micro.py)
DUREE_SILENCE = 1.2            # secondes de silence = "j'ai fini de parler"
DUREE_MAX = 15                 # durée max d'une question, en secondes

# --- Transcription (Whisper) ---
MODELE_WHISPER = "small"       # "base" = plus rapide, "small" = bon compromis, "medium" = plus précis mais lent

# --- Cerveau (Claude) ---
MODELE_CLAUDE = "claude-sonnet-5-5"

PERSONNALITE = """Tu es Jarvis, l'assistant personnel de Rémi, inspiré du majordome IA d'Iron Man.
Tu es poli, efficace, avec un humour britannique pince-sans-rire.
Tu appelles l'utilisateur "Monsieur".
Tes réponses sont LUES À VOIX HAUTE : sois bref (2-3 phrases max sauf si on te demande plus),
n'utilise jamais de listes, de titres, d'emojis ni de mise en forme markdown."""

# --- Voix ---
VOIX = "Thomas"                # voix française de macOS (liste : voir voix.py)

EFFET_VOIX = "discret"
EFFET_VOIX = "marque"
GRAVE_VOIX = "-12Hz"
VITESSE_VOIX = "-10%"
VITESSE_VOIX = "+5%"
DUREE_SILENCE = 0.9
