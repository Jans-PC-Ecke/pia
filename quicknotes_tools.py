# quicknotes_tools.py – schnelle Sprach-/Text-Notizen + Telegram Echo

import os
from datetime import datetime
from utils import BASE_DIR, sprich, telegram_senden, lade_json, speichere_json

DATEI = os.path.join(BASE_DIR, "schnellnotizen.json")

def schnellnotiz(text: str):
    text = text.strip()
    if not text:
        return "Keine Notiz angegeben."

    daten = lade_json("schnellnotizen.json", {"notizen": []})

    eintrag = {
        "text": text,
        "zeit": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    daten["notizen"].append(eintrag)
    speichere_json("schnellnotizen.json", daten)

    msg = f"Notiz gespeichert: {text}"
    sprich(msg)

    telegram_senden(f"Schnellnotiz:\n{text}\n({eintrag['zeit']})")

    return msg

def tools_holen():
    return [
        ("schnellnotiz", schnellnotiz, "Schnellnotizen"),
    ]