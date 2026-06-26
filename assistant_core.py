import requests
import logging
import subprocess
import os
from datetime import datetime
from utils import sprich, lade_json, speichere_json, telegram_senden

def kontext_laden():
    return lade_json("kontext.json", {"historie": []})

def kontext_speichern(d):
    speichere_json("kontext.json", d)

def zeige_hilfemenue() -> str:
    sprich("Hier ist das Hilfemenü.")

    hilfe_text = f"""
Pia4 – dein persönlicher Manjaro-Assistent

Direkt ausgeführte Befehle:

Zeit & Wetter
  • wie spät ist es? / uhrzeit / welches datum? / heute
  • wetter in Berlin / wetter Eschwege

Notizen & Kalender
  • notiz kauf Milch
  • termin arzt morgen 14 uhr
  • termine heute / was habe ich heute

Musik & Lautstärke
  • play / pause / next / weiter / vorheriger
  • lauter / leiser / stumm

Programme & Fenster
  • öffne firefox / starte brave / mach chrome auf
  • öffne thunderbird / mail / email
  • beende firefox / schließe vlc
  • welche fenster sind offen? / fensterliste
  • mach screenshot / bildschirmfoto
  • öffne datei ~/Downloads/report.pdf
  • neues terminal / öffne konsole

System
  • ausschalten / neustart / wlan aus / bluetooth ein
  • helligkeit hoch / dimm den Bildschirm

Suche & Internet
  • suche nach Python Tutorial

Backup
  • mach backup / backup machen / erstelle backup / daten sichern

E-Mail (Thunderbird)
  • mail an max / email an chef / schreibe email an anna

Hilfe
  • hilfe / was kannst du / ?

Sag einfach, was du willst – ich versuche es direkt zu machen!
Bei unbekannten Befehlen fragt Pia jetzt Ollama (llama3:8b).
"""

    print("\n" + "═" * 85)
    print(" " * 28 + "Pia4 – Hilfe & Befehlsübersicht")
    print("═" * 85)
    print(hilfe_text.strip())
    print("═" * 85 + "\n")

    return hilfe_text.strip()


def befehl_verarbeiten(befehl: str) -> str:
    if not befehl:
        return ""

    orig = befehl.strip()
    clean = befehl.strip().lower()

    # ──────────────────────────────
    # Hilfemenü
    # ──────────────────────────────
    if clean in ("hilfe", "help", "was kannst du", "befehle", "kommando", "kommandos", "?"):
        return zeige_hilfemenue()

    # ──────────────────────────────
    # BACKUP
    # ──────────────────────────────
    backup_keywords = ["backup", "mach backup", "backup machen", "erstelle backup", "daten sichern", "sichere daten", "backup erstellen"]
    if any(kw in clean for kw in backup_keywords):
        try:
            from backup_tools import backup_erstellen
            sprich("Erstelle Backup – nur wichtige Dateien im Hauptordner …")
            return backup_erstellen()
        except Exception as e:
            logging.error(f"Backup-Tool Fehler: {e}")
            return "Backup-Tool gerade nicht verfügbar."

    # ──────────────────────────────
    # Programm öffnen / starten
    # ──────────────────────────────
    open_keywords = ["öffne", "starte", "mach auf", "start", "open", "aufrufen", "lade", "rufe auf"]
    if any(kw in clean for kw in open_keywords):
        used_kw = next((kw for kw in open_keywords if kw in clean), None)
        app_part = clean.split(used_kw, 1)[-1].strip() if used_kw else clean

        if not app_part:
            return "Was soll ich öffnen oder starten?"

        try:
            if any(p in app_part for p in ["firefox", "brave", "chrome", "browser"]):
                browser = "firefox" if "firefox" in app_part else "brave" if "brave" in app_part else "chromium"
                subprocess.Popen([browser])
                sprich(f"Öffne {browser.capitalize()} …")
                return f"{browser.capitalize()} wird gestartet."

            if any(t in app_part for t in ["terminal", "konsole", "shell", "cmd", "terminator", "kitty"]):
                terminal = "konsole" if "konsole" in app_part else "terminator" if "terminator" in app_part else "kitty" if "kitty" in app_part else "xterm"
                subprocess.Popen([terminal])
                sprich("Öffne Terminal …")
                return f"{terminal} wird gestartet."

            if "mousepad" in app_part:
                subprocess.Popen(["mousepad"])
                sprich("Öffne Mousepad …")
                return "Mousepad wird gestartet."

            path = app_part
            if os.path.exists(path) or path.startswith(("http", "file://")):
                subprocess.Popen(["xdg-open", path])
                sprich(f"Öffne {path} …")
                return f"Geöffnet: {path}"

            subprocess.Popen([app_part], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            sprich(f"Versuche {app_part} zu starten …")
            return f"{app_part} wird gestartet (falls installiert)."

        except Exception as e:
            logging.error(f"Öffnen-Fehler: {e}")
            return f"Konnte {app_part} nicht öffnen oder starten."

    # ──────────────────────────────
    # E-Mail mit Thunderbird (korrigiert)
    # ──────────────────────────────
    if any(kw in clean for kw in ["mail an", "email an", "schreibe email", "schreibe mail"]):
        try:
            from thunderbird_tools import email_vorbereiten
            if "mail an" in clean:
                person = clean.split("mail an", 1)[-1].strip()
            elif "email an" in clean:
                person = clean.split("email an", 1)[-1].strip()
            else:
                person = clean.split("an", 1)[-1].strip()

            sprich(f"Öffne E-Mail an {person} …")
            return email_vorbereiten(an=person)
        except Exception as e:
            logging.error(f"Thunderbird Tool Fehler: {e}")
            return "Thunderbird Tool nicht verfügbar."

    # ──────────────────────────────
    # Programm schließen / beenden
    # ──────────────────────────────
    close_keywords = ["schließe", "beende", "mach zu", "kill", "stopp", "ende", "beenden", "terminiere"]
    if any(kw in clean for kw in close_keywords):
        used_kw = next((kw for kw in close_keywords if kw in clean), None)
        app_part = clean.split(used_kw, 1)[-1].strip() if used_kw else ""

        if not app_part:
            return "Welches Programm soll ich schließen?"

        try:
            subprocess.run(["pkill", "-f", app_part], check=True)
            sprich(f"Beende {app_part} …")
            return f"{app_part} wird beendet."
        except:
            return f"Konnte {app_part} nicht finden oder beenden."

    # Fensterliste
    if any(kw in clean for kw in ["welche fenster", "fenster offen", "fensterliste", "offene fenster", "aktive fenster"]):
        try:
            result = subprocess.getoutput("wmctrl -l")
            sprich("Hier sind die aktuell offenen Fenster:")
            print(result)
            return result or "Keine Fenster gefunden."
        except Exception as e:
            logging.error(f"Fensterliste Fehler: {e}")
            return "Fensterliste nicht verfügbar – wmctrl installiert?"

    # Screenshot
    if any(kw in clean for kw in ["screenshot", "mach screenshot", "bildschirmfoto", "screen shot"]):
        try:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = os.path.join(os.path.expanduser("~/Bilder"), filename)
            subprocess.run(["scrot", path], check=True)
            sprich(f"Screenshot gespeichert unter ~/Bilder/{filename}")
            return f"Screenshot: {path}"
        except Exception as e:
            logging.error(f"Screenshot Fehler: {e}")
            return "Screenshot fehlgeschlagen – ist scrot installiert?"

    # Lautstärke & Audio
    if any(kw in clean for kw in ["lauter", "leiser", "stumm", "lautstärke hoch", "lautstärke runter", "mute"]):
        try:
            from system_tools import system_aktion
            sprich("Ändere Audio …")
            return system_aktion(clean)
        except:
            return "Audio-Steuerung gerade nicht möglich."

    # ──────────────────────────────
    # Restliche bekannte Tools
    # ──────────────────────────────
    if "wetter" in clean:
        stadt = clean.split("wetter", 1)[-1].strip() or "Eschwege"
        try:
            from weather_tools import wetter_holen
            return wetter_holen(stadt)
        except:
            return "Wetter gerade nicht verfügbar."

    if any(w in clean for w in ["wie spät", "uhrzeit", "zeit", "datum", "tag ist heute"]):
        try:
            from uhr_tools import jetzt_sagen
            if "datum" in clean or "tag" in clean:
                return jetzt_sagen("datum")
            return jetzt_sagen("uhrzeit")
        except:
            return "Uhrzeit gerade nicht verfügbar."

    if "notiz" in clean:
        text = clean.split("notiz", 1)[-1].strip()
        try:
            from quicknotes_tools import schnellnotiz
            return schnellnotiz(text)
        except:
            return "Notiz konnte nicht gespeichert werden."

    if any(w in clean for w in ["termin", "termine", "kalender", "was habe ich"]):
        try:
            from calendar_tools import termin_hinzufügen, termine_heute
            if "heute" in clean or "termine" in clean or "was habe ich" in clean:
                return termine_heute()
            titel = clean.split("termin", 1)[-1].strip()
            return termin_hinzufügen(titel)
        except:
            return "Kalender gerade nicht verfügbar."

    if "suche" in clean:
        suchbegriff = clean.split("suche", 1)[-1].strip()
        try:
            from web_search_tools import web_suche
            return web_suche(suchbegriff)
        except:
            return "Suche gerade nicht möglich."

    # ──────────────────────────────
    # Ollama
    # ──────────────────────────────

    ctx = kontext_laden()
    historie = "\n".join(ctx["historie"][-8:])

    system_prompt = f"""Du bist Pia – frech, direkt, hilfsbereit und ein bisschen frech.
Du sprichst Jan immer mit Vornamen an.
Du steuerst einen Manjaro-Linux-Rechner.
Antworte auf Deutsch, kurz, knackig und praxisnah. Maximal 2–3 Sätze.

Letzte Unterhaltung:
{historie}

Wenn es ein Systembefehl ist, den du nicht direkt ausführen kannst, schlage den genauen Linux-Befehl vor (z. B. `sudo pacman -Syu`)."""

    try:
        from ollama_tools import ollama_antwort
        antwort = ollama_antwort(befehl, system_prompt=system_prompt)

        ctx["historie"].append(f"Jan: {befehl}")
        ctx["historie"].append(f"Pia: {antwort[:180]}")
        if len(ctx["historie"]) > 30:
            ctx["historie"] = ctx["historie"][-20:]
        kontext_speichern(ctx)

        return antwort

    except Exception as e:
        logging.error(f"Ollama Fallback Fehler: {e}")
        fallback = "Entschuldige Jan – Ollama macht gerade Pause. Versuch's gleich nochmal."
        sprich(fallback)
        return fallback


def tools_holen():
    return [("befehl_verarbeiten", befehl_verarbeiten, "Kern / KI")]