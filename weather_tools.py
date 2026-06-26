# weather_tools.py – OpenWeatherMap Abfrage (einfach & robust)

import requests
from datetime import datetime
from utils import KONFIG, logging, sprich

def wetter_holen(stadt="Eschwege"):
    api_key = KONFIG.get("openweather_api_key")
    if not api_key:
        return "Kein OpenWeather API-Key eingetragen."

    stadt = stadt.strip()
    if not stadt:
        stadt = "Eschwege"

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={stadt}&appid={api_key}&units=metric&lang=de"
    )

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        if data.get("cod") != 200:
            return f"Stadt '{stadt}' nicht gefunden."

        wetter = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        gefuehlt = data["main"]["feels_like"]
        stadt_name = data["name"]

        jetzt = datetime.now().hour
        tageszeit = "Nacht" if jetzt < 6 or jetzt >= 21 else "Tag"

        antwort = (
            f"In {stadt_name} ({tageszeit}): {wetter.capitalize()}, "
            f"{temp:.1f} °C (gefühlt {gefuehlt:.1f} °C)."
        )

        sprich(antwort)
        return antwort

    except requests.RequestException as e:
        logging.error(f"Wetter-Abfrage fehlgeschlagen: {e}")
        return "Wetterdienst gerade nicht erreichbar."

def tools_holen():
    return [
        ("wetter_holen", wetter_holen, "Wetter"),
    ]