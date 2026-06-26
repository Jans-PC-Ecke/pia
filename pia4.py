#!/usr/bin/env python3
# pia4.py – Haupteinstieg (CLI + Sprachmodus)
# Angepasst: Automatischer venv311-Start + Deactivate am Ende

import os
import sys
import subprocess
from utils import sprich

VENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pia4-venv311", "bin", "activate")

# Wenn wir nicht schon im venv sind → venv aktivieren und neu starten
if "pia4-venv311" not in sys.executable:
    print("→ Pia4 startet im venv311 ...")
    activate_cmd = f"source {VENV_PATH} && python3 {__file__} \"$@\""
    os.execvp("bash", ["bash", "-c", activate_cmd] + sys.argv[1:])
    sys.exit(0)

# Ab hier läuft alles im venv311
print("Pia4 läuft im venv311")

IS_TERMUX = "TERMUX_VERSION" in os.environ

def main():
    from module_loader import alle_tools_laden

    tools = alle_tools_laden()

    # Debug: Welche Tools wurden geladen?
    print("\n=== Geladene Tools (Debug) ===")
    for name, func, cat in tools:
        print(f"  • {name:25}  ({cat})")
    print("===============================\n")

    print("=== Pia4 – bereit ===")
    print("  1   Sprachmodus (Hey Pia)")
    print("  2   Terminal-Modus")
    if IS_TERMUX:
        print("  m1  Immer-hörend-Modus")
        print("  m2  Backup → Telegram")
    print("  q   Beenden\n")

    while True:
        choice = input("Auswahl → ").strip().lower()

        if choice in ("1", "sprache", "voice", "hey pia"):
            print("Versuche Sprachmodus zu starten ...")
            found = False
            for name, func, cat in tools:
                if name in ("sprachmodus", "immer_hoerend", "voice_mode", "hey_pia"):
                    try:
                        print(f"→ Starte Funktion: {name}")
                        func()
                        found = True
                    except Exception as e:
                        print(f"Fehler beim Starten des Sprachmodus ({name}): {e}")
                    break
            if not found:
                print("Kein passendes Sprachmodus-Tool gefunden.")
                print("Prüfe voice_tools.py und tools_holen()")

        elif choice in ("2", "terminal", "cli"):
            print("Terminal-Modus – :q oder exit zum Beenden")
            while True:
                cmd = input("Pia4> ").strip()
                if cmd.lower() in (":q", "exit", "quit"):
                    break
                if cmd:
                    from assistant_core import befehl_verarbeiten
                    print(befehl_verarbeiten(cmd))

        elif choice == "m1" and IS_TERMUX:
            print("Versuche Immer-hörend-Modus ...")
            for name, func, _ in tools:
                if name in ("immer_hoerend", "sprachmodus"):
                    func()
                    break

        elif choice == "m2" and IS_TERMUX:
            for name, func, _ in tools:
                if name == "daten_sichern":
                    print(func())
                    break

        elif choice in ("q", "quit", "exit"):
            sprich("Bis später!")
            print("Auf Wiedersehen.")
            break

        else:
            print("Ungültige Auswahl. Probiere 1, 2, q ...")

if __name__ == "__main__":
    try:
        main()
    finally:
        # venv deaktivieren (wenn wir im venv sind)
        if "VIRTUAL_ENV" in os.environ:
            print("→ venv311 wird deaktiviert")
            deactivate = os.path.join(os.environ["VIRTUAL_ENV"], "bin", "deactivate")
            if os.path.exists(deactivate):
                subprocess.run(["bash", "-c", f"source {deactivate}"], check=False)