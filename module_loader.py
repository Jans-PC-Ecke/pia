import os
import importlib.util
import logging
import sys
import traceback

# Logging einrichten (sowohl Datei als auch Konsole)
logging.basicConfig(
    level=logging.DEBUG,  # ← mehr Details als INFO
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    handlers=[
        logging.FileHandler("module_loader_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# ANSI-Farben für bessere Lesbarkeit (optional)
class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL    = '\033[91m'
    ENDC    = '\033[0m'
    BOLD    = '\033[1m'

USE_COLOR = True  # ← auf False setzen, wenn du keine Farben willst

def cprint(color, text):
    if USE_COLOR:
        print(f"{color}{text}{bcolors.ENDC}")
    else:
        print(text)

def alle_tools_laden(debug=True):
    tools = []
    aktuelles_verzeichnis = os.path.dirname(os.path.abspath(__file__))

    cprint(bcolors.BOLD, f"\n[Module Loader] Suche in Verzeichnis: {aktuelles_verzeichnis}")
    logging.info(f"Suche in Verzeichnis: {aktuelles_verzeichnis}")

    gefundene_dateien = 0
    geladene_module   = 0
    fehlerhafte_module = 0

    for datei in sorted(os.listdir(aktuelles_verzeichnis)):
        if not datei.endswith("_tools.py") or datei == "__init__.py":
            continue

        gefundene_dateien += 1
        modul_name = datei[:-3]
        modul_pfad = os.path.join(aktuelles_verzeichnis, datei)

        cprint(bcolors.OKGREEN, f"  Gefunden: {datei}")
        logging.debug(f"Gefunden: {datei} → {modul_pfad}")

        try:
            spec = importlib.util.spec_from_file_location(modul_name, modul_pfad)
            if spec is None:
                cprint(bcolors.FAIL, f"  → Spec konnte nicht erstellt werden: {modul_name}")
                logging.error(f"Spec konnte nicht erstellt werden: {modul_name}")
                fehlerhafte_module += 1
                continue

            modul = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modul)

            if hasattr(modul, "tools_holen"):
                try:
                    modul_tools = modul.tools_holen()
                    if not isinstance(modul_tools, list):
                        cprint(bcolors.WARNING, f"  → tools_holen() liefert kein Liste zurück: {modul_name}")
                        logging.warning(f"tools_holen() von {modul_name} liefert kein Liste")
                        continue

                    tools.extend(modul_tools)
                    geladene_module += 1
                    anzahl = len(modul_tools)
                    cprint(bcolors.OKGREEN, f"  → Erfolgreich geladen: {modul_name}  ({anzahl} Tools)")
                    logging.info(f"Modul {modul_name} geladen – {anzahl} Tools")
                except Exception as e:
                    cprint(bcolors.FAIL, f"  → Fehler in tools_holen() von {modul_name}: {e}")
                    logging.error(f"Fehler in tools_holen() von {modul_name}", exc_info=True)
            else:
                cprint(bcolors.WARNING, f"  → Keine Funktion 'tools_holen()' in {modul_name}")
                logging.warning(f"Modul {modul_name} hat keine tools_holen()-Funktion")

        except Exception as e:
            fehlerhafte_module += 1
            cprint(bcolors.FAIL, f"  → Kritischer Fehler beim Laden von {modul_name}:")
            print(traceback.format_exc(limit=3))
            logging.exception(f"Kritischer Fehler beim Laden von {modul_name}")

    # Zusammenfassung
    print("\n" + "─" * 60)
    cprint(bcolors.BOLD, f"Zusammenfassung:")
    print(f"  Gefundene *_tools.py Dateien : {gefundene_dateien}")
    print(f"  Erfolgreich geladene Module   : {geladene_module}")
    print(f"  Module mit Fehlern            : {fehlerhafte_module}")
    print(f"  Gesamt Tools geladen          : {len(tools)}")
    print("─" * 60 + "\n")

    logging.info(f"Zusammenfassung: {gefundene_dateien} Dateien, {geladene_module} Module, {len(tools)} Tools")

    return tools


if __name__ == "__main__":
    print("Test-Lauf des Module Loaders (Debug-Modus)")
    alle_tools_laden(debug=True)