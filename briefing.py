# ============================================================
#  ÉTAPE 9 — Le briefing du matin
#  1. Python récupère la date, la météo et les cours (rapide, sans Claude)
#  2. On donne à Claude la consigne du briefing + ces infos
#  3. Claude cherche sur le web les causes des mouvements crypto,
#     fouille les deux boîtes mail avec ses outils, et rédige
#
#  Tester seul :  python briefing.py
# ============================================================
import time
from datetime import date, datetime
from pathlib import Path

from config_briefing import (CONSIGNES_BRIEFING, MOTS_DECLENCHEURS,
                             BRIEFING_AU_DEMARRAGE, HEURE_DEBUT, HEURE_FIN)
from meteo import meteo_du_jour
from marches import resume_marches

_JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
         "août", "septembre", "octobre", "novembre", "décembre"]
_TRACE = Path(__file__).with_name(".dernier_briefing")   # retient le jour du dernier briefing


def est_une_demande(phrase):
    """Vrai si ta phrase demande le briefing."""
    phrase = phrase.lower()
    return any(mot in phrase for mot in MOTS_DECLENCHEURS)


def consigne():
    """Construit la demande envoyée à Claude."""
    maintenant = datetime.now()
    # Le lundi, on remonte au vendredi pour inclure le week-end
    jours = 3 if maintenant.weekday() == 0 else 1
    requete = f"newer_than:{jours}d -category:promotions -category:social"

    try:
        meteo = meteo_du_jour()
    except Exception as e:
        print(f"   ⚠️  Météo indisponible : {e}")
        meteo = "météo indisponible pour le moment"

    try:
        marches = resume_marches()
    except Exception as e:
        print(f"   ⚠️  Marchés indisponibles : {e}")
        marches = "Cours des marchés indisponibles pour le moment."

    date_texte = (f"{_JOURS[maintenant.weekday()]} {maintenant.day} "
                  f"{_MOIS[maintenant.month - 1]} {maintenant.year}, {maintenant:%H:%M}")

    return (
        "BRIEFING DU MATIN.\n"
        f"Date et heure : {date_texte}\n"
        f"Météo : {meteo}\n\n"
        f"{marches}\n"
        + CONSIGNES_BRIEFING.format(requete=requete)
    )


def faire_briefing(cerveau):
    """Renvoie le texte du briefing (et le note comme fait aujourd'hui)."""
    texte = cerveau.repondre(consigne())
    _TRACE.write_text(date.today().isoformat())
    return texte


def briefing_complet(cerveau, dire, avant_preparation=None):
    """Musique + préparation + lecture, avec baisse de la musique sous la voix.
    'dire' est la fonction qui fait parler Jarvis."""
    import config_briefing as cfg
    musique = None
    if cfg.MUSIQUE_ACTIVE:
        if getattr(cfg, "SOURCE_MUSIQUE", "fichier") == "apple_music":
            try:
                from musique_apple import MusiqueAppleMusic
                musique = MusiqueAppleMusic(cfg.PLAYLIST_APPLE_MUSIC)
                musique.demarrer(cfg.VOLUME_PREPARATION)
            except Exception as e:
                print(f"   ⚠️  Apple Music indisponible ({e}), ambiance par défaut.")
                musique = None
        if musique is None:
            try:
                from musique import MusiqueDeFond
                musique = MusiqueDeFond(cfg.MUSIQUE_BRIEFING)
                musique.demarrer(cfg.VOLUME_PREPARATION)
            except Exception as e:
                print(f"   ⚠️  Musique indisponible : {e}")
                musique = None

    try:
        if avant_preparation:
            avant_preparation()
        texte = faire_briefing(cerveau)
        print(f"🤖 Jarvis : {texte}")
        if musique:
            musique.volume(cfg.VOLUME_SOUS_VOIX, fondu=1.5)
            time.sleep(1.5)                 # laisse la musique baisser avant de parler
        dire(texte)
    finally:
        if musique:
            try:
                musique.arreter(fondu=3.0)  # fondu de sortie, même en cas d'erreur
            except Exception as e:
                print(f"   ⚠️  Arrêt de la musique : {e}")
    return texte


def a_faire_au_demarrage():
    """Vrai si c'est le matin et que le briefing n'a pas encore été fait aujourd'hui."""
    if not BRIEFING_AU_DEMARRAGE:
        return False
    if not HEURE_DEBUT <= datetime.now().hour < HEURE_FIN:
        return False
    deja_fait = _TRACE.exists() and _TRACE.read_text().strip() == date.today().isoformat()
    return not deja_fait


if __name__ == "__main__":
    from cerveau import Cerveau
    from voix import parler

    print("Préparation du briefing...")
    briefing_complet(Cerveau(), parler)
