# calendar_tools.py – Kalender, Erinnerungen, To-dos (einfache JSON-Version)

import os
from datetime import datetime, timedelta
from utils import BASE_DIR, sprich, telegram_senden, lade_json, speichere_json, logging

DATEI = os.path.join(BASE_DIR, "kalender.json")

def init():
    if not os.path.exists(DATEI):
        speichere_json("kalender.json", {"einträge": []})

def termin_hinzufügen(titel: str, datumzeit: str = None, typ: str = "termin"):
    # datumzeit format: "2026-02-15 14:30" oder nur "2026-02-15"
    init()
    daten = lade_json("kalender.json")
    
    eintrag = {
        "titel": titel.strip(),
        "typ": typ,               # termin / erinnerung / todo
        "erstellt": datetime.now().isoformat(),
        "status": "offen" if typ == "todo" else None
    }
    
    if datumzeit:
        try:
            if len(datumzeit.split()) == 1:
                datumzeit += " 08:00"
            dt = datetime.fromisoformat(datumzeit.replace(" ", "T"))
            eintrag["wann"] = dt.isoformat()
        except:
            return "Ungültiges Datumsformat (erwartet: YYYY-MM-DD HH:MM)"
    
    daten["einträge"].append(eintrag)
    speichere_json("kalender.json", daten)
    
    msg = f"→ {typ} hinzugefügt: {titel}"
    if "wann" in eintrag:
        msg += f"  ({eintrag['wann'][:16]})"
    sprich(msg)
    return msg

def termine_heute():
    init()
    daten = lade_json("kalender.json")
    heute = datetime.now().date().isoformat()
    
    treffer = [
        e for e in daten["einträge"]
        if "wann" in e and e["wann"].startswith(heute)
    ]
    
    if not treffer:
        return "Heute keine Termine / Erinnerungen."
    
    zeilen = []
    for e in sorted(treffer, key=lambda x: x.get("wann", "9999")):
        uhrzeit = e["wann"][11:16] if "wann" in e else "∞"
        status = f" [{e['status']}]" if e.get("status") else ""
        zeilen.append(f"{uhrzeit}  {e['titel']}{status}")
    
    return "\n".join(zeilen)

def tools_holen():
    return [
        ("termin_hinzufügen", termin_hinzufügen,   "Kalender"),
        ("termine_heute",     termine_heute,       "Kalender"),
    ]