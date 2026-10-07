# ============================================================
#  ÉTAPE 4 (v3) — Le cerveau : Claude + ses outils + recherche web
#
#  Le principe du "tool use" :
#   1. On envoie ta question à Claude, avec la notice des outils.
#   2. S'il a besoin d'un de NOS outils (emails, météo...), il le demande,
#      notre code l'exécute (outils.py) et on lui renvoie le résultat.
#   3. La recherche web, elle, est exécutée directement chez Anthropic :
#      on n'a rien à faire, sauf relancer si Claude fait une pause.
#   4. On recommence jusqu'à ce qu'il donne sa réponse finale.
#
#  Lancer :  python cerveau.py   (discussion au clavier)
# ============================================================
import anthropic

from config import MODELE_CLAUDE, PERSONNALITE
from config_emails import CONSIGNES_EMAILS
from outils import OUTILS, OUTIL_WEB, executer

MAX_TOURS_OUTILS = 10   # garde-fou : nombre max d'allers-retours par question


class Cerveau:
    def __init__(self):
        self.client = anthropic.Anthropic()   # lit ANTHROPIC_API_KEY depuis .env
        self.historique = []
        self.consignes = PERSONNALITE + "\n\n" + CONSIGNES_EMAILS
        self.web_actif = True

    def _appeler(self):
        """Un appel à Claude. Si la recherche web est refusée, on continue sans."""
        outils = OUTILS + ([OUTIL_WEB] if self.web_actif else [])
        try:
            return self.client.messages.create(
                model=MODELE_CLAUDE, max_tokens=2048, system=self.consignes,
                tools=outils, messages=self.historique,
            )
        except anthropic.BadRequestError as e:
            if not self.web_actif:
                raise
            print(f"   ⚠️  Recherche web indisponible ({e}). Je continue sans.")
            self.web_actif = False
            return self._appeler()

    def repondre(self, texte):
        self.historique.append({"role": "user", "content": texte})

        for _ in range(MAX_TOURS_OUTILS):
            reponse = self._appeler()
            self.historique.append({"role": "assistant", "content": reponse.content})

            for bloc in reponse.content:          # on affiche les recherches web
                if bloc.type == "server_tool_use":
                    print(f"   🌐 recherche : {bloc.input.get('query', '')}")

            if reponse.stop_reason == "pause_turn":
                continue      # recherche web longue : on relance tel quel

            if reponse.stop_reason != "tool_use":
                break         # réponse finale

            # Claude a demandé un ou plusieurs de NOS outils : on les exécute
            resultats = []
            for bloc in reponse.content:
                if bloc.type != "tool_use":
                    continue
                print(f"   🔧 {bloc.name} {bloc.input}")
                try:
                    contenu, erreur = executer(bloc.name, bloc.input), False
                except Exception as e:
                    contenu, erreur = f"Erreur : {e}", True
                    print(f"   ⚠️  {contenu}")
                resultats.append({
                    "type": "tool_result",
                    "tool_use_id": bloc.id,
                    "content": contenu,
                    "is_error": erreur,
                })
            self.historique.append({"role": "user", "content": resultats})

        texte_reponse = "".join(b.text for b in reponse.content if b.type == "text").strip()
        self._raccourcir()
        return texte_reponse or "Je n'ai pas réussi à finir cette recherche, Monsieur."

    def _raccourcir(self, max_messages=30):
        """Garde la fin de la conversation, en commençant toujours par une vraie question."""
        h = self.historique[-max_messages:]
        while h and not (h[0]["role"] == "user" and isinstance(h[0]["content"], str)):
            h = h[1:]
        self.historique = h


if __name__ == "__main__":
    cerveau = Cerveau()
    print("Discute avec Jarvis au clavier (Ctrl+C pour quitter)")
    while True:
        question = input("\nToi : ")
        print(f"Jarvis : {cerveau.repondre(question)}")
