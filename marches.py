# ============================================================
#  MARCHÉS — indices boursiers et cryptomonnaies
#  Source : Yahoo Finance via la bibliothèque yfinance (gratuit, sans clé)
#  Tester :  python marches.py
# ============================================================
import math
import time
from datetime import date

import pandas as pd
import yfinance as yf

from config_briefing import INDICES, CRYPTOS


def _nombre(x):
    """Formate un nombre à la française (espaces pour les milliers)."""
    if x >= 100:
        return f"{x:,.0f}".replace(",", " ")
    if x >= 1:
        return f"{x:,.2f}".replace(",", " ").replace(".", ",")
    decimales = -int(math.floor(math.log10(x))) + 3      # ex : 0,00002345
    return f"{x:.{decimales}f}".replace(".", ",")


def _pct(x):
    return f"{x:+.1f} %".replace(".", ",")


def _cotation(ticker):
    """Dernier cours, variation sur 1 jour et sur 7 jours, date de la donnée."""
    h = yf.Ticker(ticker).history(period="15d", interval="1d")["Close"].dropna()
    if len(h) < 2:
        raise ValueError("pas assez de données")
    dernier, veille = h.iloc[-1], h.iloc[-2]
    il_y_a_7j = h[h.index <= h.index[-1] - pd.Timedelta(days=7)]
    var_7j = (dernier / il_y_a_7j.iloc[-1] - 1) * 100 if len(il_y_a_7j) else None
    return dernier, (dernier / veille - 1) * 100, var_7j, h.index[-1].strftime("%d/%m")


# ---------- Pour l'interface : historique 1 an + cours en direct ----------
_cache_historique = {}   # ticker -> (heure du téléchargement, dates, cours)
DUREE_CACHE = 3600       # l'historique d'un an n'est retéléchargé qu'une fois par heure


def _historique_1an(ticker):
    en_cache = _cache_historique.get(ticker)
    if en_cache and time.time() - en_cache[0] < DUREE_CACHE:
        return en_cache[1], en_cache[2]
    h = yf.Ticker(ticker).history(period="1y", interval="1d")["Close"].dropna()
    dates = [d.strftime("%Y-%m-%d") for d in h.index]
    cours = [float(v) for v in h]
    _cache_historique[ticker] = (time.time(), dates, cours)
    return dates, cours


def _cours_en_direct(ticker, cours):
    """Dernier cours et clôture de la veille. Si Yahoo ne répond pas, on prend l'historique."""
    try:
        info = yf.Ticker(ticker).fast_info
        dernier = float(getattr(info, "last_price", None) or info["lastPrice"])
        veille = float(getattr(info, "previous_close", None) or info["previousClose"])
        return dernier, veille
    except Exception:
        return cours[-1], cours[-2]


def cotations_temps_reel():
    """Pour chaque actif : cours en direct, variation du jour et sur 1 an, courbe d'un an."""
    aujourd_hui = date.today().isoformat()
    resultats = []
    for groupe, liste in (("indice", INDICES), ("crypto", CRYPTOS)):
        for nom, ticker in liste.items():
            try:
                dates, cours = _historique_1an(ticker)
                dernier, veille = _cours_en_direct(ticker, cours)
                dates, serie = list(dates), list(cours)
                if dates[-1] == aujourd_hui:
                    serie[-1] = dernier                  # la séance du jour suit le direct
                elif abs(dernier - serie[-1]) > 1e-12:
                    dates.append(aujourd_hui)            # nouveau point "en direct"
                    serie.append(dernier)
                resultats.append({
                    "nom": nom, "type": groupe,
                    "valeur": _nombre(dernier), "dernier": dernier,
                    "variation": round((dernier / veille - 1) * 100, 2),
                    "variation_1an": round((dernier / serie[0] - 1) * 100, 1),
                    "dates": dates,
                    "serie": [float(f"{v:.6g}") for v in serie],
                })
            except Exception:
                pass
    return resultats


def cotations():
    """Renvoie les cours sous forme de données (pour l'interface)."""
    resultats = []
    for groupe, liste in (("indice", INDICES), ("crypto", CRYPTOS)):
        for nom, ticker in liste.items():
            try:
                v, j1, _, _ = _cotation(ticker)
                resultats.append({"nom": nom, "type": groupe, "valeur": _nombre(v),
                                  "variation": round(float(j1), 2)})
            except Exception:
                pass
    return resultats


def resume_marches():
    """Renvoie un bloc de texte avec tous les cours, prêt à donner à Claude."""
    lignes = ["INDICES BOURSIERS (dernière valeur, variation sur la dernière séance, sur 7 jours) :"]
    for nom, ticker in INDICES.items():
        try:
            v, j1, j7, d = _cotation(ticker)
            sept = f", 7 jours : {_pct(j7)}" if j7 is not None else ""
            lignes.append(f"- {nom} : {_nombre(v)} points ({_pct(j1)}{sept}) — donnée du {d}")
        except Exception as e:
            lignes.append(f"- {nom} : indisponible ({e})")

    lignes.append("CRYPTOMONNAIES (en dollars, variation sur 24 h et sur 7 jours) :")
    for nom, ticker in CRYPTOS.items():
        try:
            v, j1, j7, _ = _cotation(ticker)
            sept = f", 7 jours : {_pct(j7)}" if j7 is not None else ""
            lignes.append(f"- {nom} : {_nombre(v)} $ (24 h : {_pct(j1)}{sept})")
        except Exception as e:
            lignes.append(f"- {nom} : indisponible ({e})")
    return "\n".join(lignes)


if __name__ == "__main__":
    print(resume_marches())
