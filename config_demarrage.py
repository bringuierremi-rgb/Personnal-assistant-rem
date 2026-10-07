# ============================================================
#  RÉGLAGES DE LA MUSIQUE DE DÉMARRAGE
#  Elle accompagne la séquence de projection de l'interface,
#  baisse quand Jarvis dit « Jarvis en ligne, Monsieur »,
#  puis s'éteint en fondu.
# ============================================================

ACTIVE = True

# D'où vient la musique :
#   "fichier"     -> un fichier audio placé dans le dossier du projet
#   "apple_music" -> une playlist de l'app Musique (mets-y ton morceau)
SOURCE = "apple_music"
FICHIER = "musique_demarrage.mp3"     # mp3, m4a, wav...
PLAYLIST = "Jarvis"

VOLUME = 0.6                 # volume pendant la séquence (0 à 1)
VOLUME_SOUS_VOIX = 0.15      # pendant que Jarvis dit bonjour
DUREE_MINIMUM = 17
                             # (le temps que tous les panneaux soient projetés)
FONDU_SORTIE = 4             # durée du fondu final, en secondes
