# uhr_tools.py – Uhrzeit, Datum, Wochentag

from datetime import datetime
from utils import sprich

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

def jetzt_sagen(was: str = "alles"):
    jetzt = datetime.now()
    if was.lower() in ("uhrzeit", "zeit", "jetzt"):
        text = jetzt.strftime("%H:%M Uhr")
    elif was.lower() in ("datum", "heute"):
        text = jetzt.strftime("%d. %B %Y")
    elif was.lower() in ("tag", "wochentag"):
        text = WOCHENTAGE[jetzt.weekday()]
    else:
        text = jetzt.strftime("%H:%M Uhr am %d. %B %Y – %A")
    
    sprich(text)
    return text

def tools_holen():
    return [
        ("jetzt_sagen", jetzt_sagen, "Uhr / Zeit"),
    ]