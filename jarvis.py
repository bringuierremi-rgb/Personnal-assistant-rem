# ============================================================
#  ÉTAPE 6+7 — La boucle principale de Jarvis
#
#  Au démarrage :
#   musique + séquence de projection -> briefing flash (Bitcoin, emails)
#   -> « Que souhaitez-vous approfondir ? » -> Jarvis écoute ta réponse
#
#  Ensuite, MODE CONVERSATION :
#   double clap -> question -> réponse -> Jarvis reste à l'écoute
#   quelques secondes : tu enchaînes sans re-claquer. Silence -> veille.
#
#  Lancer :  python jarvis.py
# ============================================================
import os
import signal
import threading

from reveil import attendre_mot_reveil
from ecoute import enregistrer_phrase, transcrire, _charger_whisper
from cerveau import Cerveau
from voix import parler, bip
import interface
import briefing
import briefing_flash
import demarrage
import config_reveil

# Après une réponse, combien de secondes Jarvis attend ta question suivante
ATTENTE_SUITE = 6

CONSIGNE_REVEIL = {
    "clap": f"claque {config_reveil.NOMBRE_CLAPS} fois dans tes mains",
    "voix": 'dis "Hey Jarvis"',
    "les_deux": f'claque {config_reveil.NOMBRE_CLAPS} fois dans tes mains ou dis "Hey Jarvis"',
}.get(config_reveil.MODE, "")

# Phrases qui mettent Jarvis en veille : fenêtre fermée, musique coupée,
# le gardien attend le prochain double clap
MOTS_FIN = ["au revoir", "en veille", "mets-toi en veille", "mise en veille", "va dormir",
            "bonne nuit", "éteins-toi", "extinction", "à plus tard"]


def dire(texte):
    """Parle ET affiche la phrase à l'écran, orbe en mode 'parole'."""
    interface.etat("parole", reponse=texte)
    print(f"🤖 Jarvis : {texte}")
    parler(texte)


def en_reflexion(titre):
    interface.etat("reflexion", question=titre, reponse="")
    print(f"🧠 {titre}...")


def ecouter(attente=8):
    """Bip, puis enregistre et transcrit ta phrase (sans mot d'activation)."""
    bip()
    interface.etat("ecoute", question="", reponse="")
    print("👂 Je t'écoute...")
    return transcrire(enregistrer_phrase(attente_max=attente))


def traiter(question, cerveau):
    """Répond à une question. Renvoie False si tu as demandé d'éteindre Jarvis."""
    print(f"🗣️  Toi : {question}")
    texte = question.lower()

    if any(mot in texte for mot in MOTS_FIN):
        dire("Très bien Monsieur. Mise en veille.")
        terminer()
        return False

    if briefing.est_une_demande(question):
        if "complet" in texte:
            en_reflexion("Briefing complet")
            briefing.briefing_complet(cerveau, dire)
        else:
            lancer_flash(cerveau)
        return True

    en_reflexion(question)
    dire(cerveau.repondre(question))
    return True


def conversation(cerveau, question):
    """Enchaîne questions et réponses tant que tu parles. Renvoie False pour éteindre."""
    while question:
        if not traiter(question, cerveau):
            return False
        question = ecouter(attente=ATTENTE_SUITE)     # la suite, sans re-claquer
    return True


def lancer_flash(cerveau, texte=None, musique=None):
    """Briefing flash + question, puis approfondissement selon ta réponse."""
    if texte is None:
        en_reflexion("Briefing flash")
        texte = briefing_flash.texte_flash()
    question = briefing_flash.QUESTION
    corps = texte[:-len(question)].strip() if texte.endswith(question) else texte

    if musique is not None:
        demarrage.conclure(musique, dire, phrase=corps, question=question)
    else:
        dire(f"{corps} {question}")

    reponse = ecouter()
    if not reponse:
        dire("Très bien, Monsieur. Je reste en veille.")
        return
    print(f"🗣️  Toi : {reponse}")
    briefing_flash.approfondir(reponse, cerveau, dire, en_reflexion)


def terminer():
    """Coupe la musique et ferme la fenêtre de l'interface."""
    try:
        import musique_apple
        musique_apple.couper_tout()
    except Exception:
        pass
    interface.fermer_fenetre()


def main():
    # si tu fermes toi-même la fenêtre (Cmd + Q), Jarvis s'arrête aussi (et sa musique)
    interface.quand_fermee(lambda: os.kill(os.getpid(), signal.SIGINT))
    musique = demarrage.lancer()  # la musique démarre en même temps que la séquence
    interface.demarrer()          # ouvre la page de l'orbe en plein écran
    print("Démarrage de Jarvis...")
    interface.etat("reflexion", question="", reponse="Initialisation des systèmes…")

    # Le briefing flash se prépare pendant que Whisper se charge
    flash = {}
    preparation = threading.Thread(target=lambda: flash.update(texte=briefing_flash.texte_flash()),
                                   daemon=True)
    preparation.start()
    _charger_whisper()
    cerveau = Cerveau()
    preparation.join(timeout=25)

    lancer_flash(cerveau, flash.get("texte") or
                 "Jarvis en ligne, Monsieur. " + briefing_flash.QUESTION, musique)

    # après le briefing, on reste en conversation
    if not conversation(cerveau, ecouter(attente=ATTENTE_SUITE)):
        return

    while True:
        interface.etat("veille")
        print(f"\n💤 En veille... {CONSIGNE_REVEIL}")
        declencheur = attendre_mot_reveil()
        print(f"⚡ Réveil ({declencheur})")

        question = ecouter()
        if not question:
            dire("Je n'ai rien entendu, Monsieur.")
            continue
        if not conversation(cerveau, question):
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nArrêt de Jarvis.")
    finally:
        terminer()                 # musique coupée et fenêtre fermée, quoi qu'il arrive
