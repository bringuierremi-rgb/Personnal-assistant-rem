# ============================================================
#  RÉGLAGES DU RÉVEIL DE JARVIS
# ============================================================

# Comment réveiller Jarvis :
#   "clap"     -> en claquant des mains
#   "voix"     -> en disant « Hey Jarvis »
#   "les_deux" -> l'un ou l'autre
MODE = "clap"

# Nombre de claquements à enchaîner (2 = double clap, recommandé)
NOMBRE_CLAPS = 2

# Écart autorisé entre deux claps, en secondes
ECART_MIN = 0.12
ECART_MAX = 0.8

# Sensibilité : de combien le clap doit dépasser le bruit de fond de la pièce.
#   plus BAS  = plus sensible (claps légers détectés, mais risque de faux réveils)
#   plus HAUT = moins sensible
SENSIBILITE = 8.0

# Volume minimum d'un clap (à calibrer avec : python reveil.py)
NIVEAU_MINIMUM = 0.02
