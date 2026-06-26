# system_tools.py – einfache Linux-Systembefehle

from utils import system_befehl, sprich, logging   # ← nur system_befehl

def system_aktion(aktion: str):
    aktion = aktion.lower().strip()
    
    if aktion in ("lauter", "lautstärke hoch"):
        system_befehl("pactl set-sink-volume @DEFAULT_SINK@ +5%")
        return "Lauter gemacht"
    
    elif aktion in ("leiser", "lautstärke runter"):
        system_befehl("pactl set-sink-volume @DEFAULT_SINK@ -5%")
        return "Leiser gemacht"
    
    elif aktion == "stumm":
        system_befehl("pactl set-sink-mute @DEFAULT_SINK@ toggle")
        return "Stummschaltung umgeschaltet"
    
    elif aktion in ("ausschalten", "herunterfahren", "shutdown"):
        sprich("Fahre in einer Minute herunter …")
        system_befehl("shutdown -h +1")
        return "Herunterfahren in 60 Sekunden initiiert"
    
    elif aktion in ("neustart", "reboot"):
        sprich("Starte neu …")
        system_befehl("reboot")
        return "Neustart wird durchgeführt"
    
    else:
        return "Unbekannte Systemaktion"

def tools_holen():
    return [
        ("system_aktion", system_aktion, "Systemsteuerung"),
    ]