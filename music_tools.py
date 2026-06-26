# music_tools.py – Steuerung über playerctl (MPRIS)

from utils import system_befehl, sprich, logging   # ← nur system_befehl

def musik_befehl(befehl: str):
    befehl = befehl.lower().strip()

    actions = {
        "play":           "play",
        "abspielen":      "play",
        "pause":          "pause",
        "play-pause":     "play-pause",
        "weiter":         "next",
        "nächster":       "next",
        "zurück":         "previous",
        "vorheriger":     "previous",
        "stop":           "stop",
        "stoppen":        "stop",
    }

    if befehl in actions:
        cmd = f"playerctl {actions[befehl]}"
        system_befehl(cmd)   # ← geändert
        sprich(f"Musik: {befehl}")
        return f"playerctl → {befehl}"

    elif befehl.startswith("lauter"):
        system_befehl("playerctl volume 0.07+")
        return "Lauter gemacht"

    elif befehl.startswith("leiser"):
        system_befehl("playerctl volume 0.07-")
        return "Leiser gemacht"

    elif befehl.startswith("lautstärke"):
        try:
            wert = float(befehl.split()[-1]) / 100
            if 0 <= wert <= 1.5:
                system_befehl(f"playerctl volume {wert:.2f}")
                sprich(f"Lautstärke auf {int(wert*100)}%")
                return f"Lautstärke → {int(wert*100)}%"
        except:
            pass

    return "Unbekannter Musikbefehl. Versuche: play, pause, next, previous, lauter, leiser, lautstärke 70"

def tools_holen():
    return [
        ("musik_befehl", musik_befehl, "Musiksteuerung"),
    ]