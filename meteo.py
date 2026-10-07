# ============================================================
#  MÉTÉO — via Open-Meteo (gratuit, sans compte ni clé)
#  Tester :  python meteo.py
# ============================================================
import requests   # gère les certificats HTTPS lui-même (contrairement à urllib)

from config_briefing import VILLE, LATITUDE, LONGITUDE

# Les codes météo internationaux (WMO) traduits en français
_CODES = {
    0: "ciel dégagé", 1: "plutôt ensoleillé", 2: "partiellement nuageux", 3: "couvert",
    45: "brouillard", 48: "brouillard givrant",
    51: "bruine légère", 53: "bruine", 55: "bruine forte",
    61: "pluie faible", 63: "pluie", 65: "forte pluie", 66: "pluie verglaçante", 67: "pluie verglaçante",
    71: "neige faible", 73: "neige", 75: "forte neige", 77: "grains de neige",
    80: "quelques averses", 81: "averses", 82: "fortes averses", 85: "averses de neige", 86: "averses de neige",
    95: "orages", 96: "orages avec grêle", 99: "orages avec grêle",
}


def meteo_donnees():
    """Renvoie la météo sous forme de données (pour l'interface)."""
    actuel, jour = _interroger()
    return {
        "ville": VILLE,
        "temperature": round(actuel["temperature_2m"]),
        "ciel": _CODES.get(actuel["weather_code"], "temps variable"),
        "min": round(jour["temperature_2m_min"][0]),
        "max": round(jour["temperature_2m_max"][0]),
        "pluie": jour["precipitation_probability_max"][0],
    }


def _interroger():
    reponse = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": "temperature_2m,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "Europe/Paris",
            "forecast_days": 1,
        },
        timeout=8,
    )
    reponse.raise_for_status()      # stoppe avec un message clair si le service répond une erreur
    d = reponse.json()
    return d["current"], d["daily"]


def meteo_du_jour():
    """Renvoie la météo actuelle et du jour en une phrase."""
    actuel, jour = _interroger()
    return (
        f"{VILLE} : actuellement {round(actuel['temperature_2m'])}°C, "
        f"{_CODES.get(actuel['weather_code'], 'temps variable')}. "
        f"Aujourd'hui : {_CODES.get(jour['weather_code'][0], 'temps variable')}, "
        f"de {round(jour['temperature_2m_min'][0])} à {round(jour['temperature_2m_max'][0])}°C, "
        f"risque de pluie {jour['precipitation_probability_max'][0]}%."
    )


if __name__ == "__main__":
    print(meteo_du_jour())
