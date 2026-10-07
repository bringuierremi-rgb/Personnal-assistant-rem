# Jarvis — assistant vocal pour Mac

## Installation (une seule fois)

```bash
brew install python@3.11            # si Homebrew : https://brew.sh
cd ~/Desktop/jarvis                 # le dossier du projet
python3.11 -m venv .venv            # crée un environnement isolé
source .venv/bin/activate           # l'active (à refaire à chaque nouveau Terminal)
pip install -r requirements.txt     # installe les briques
cp .env.exemple .env                # puis colle ta clé API dans .env
```

## Tests, dans l'ordre

| Étape | Commande | Ce que ça vérifie |
|---|---|---|
| 1 | `python test_micro.py` | Le micro marche, calibre SEUIL_SILENCE |
| 2 | `python reveil.py` | "Hey Jarvis" est détecté |
| 3 | `python ecoute.py` | Ta voix devient du texte |
| 4 | `python cerveau.py` | Claude répond (au clavier) |
| 5 | `python voix.py` | Le Mac parle |
| 6 | `python jarvis.py` | Tout assemblé 🎉 |

Si une étape échoue, ne passe pas à la suivante : corrige d'abord.
