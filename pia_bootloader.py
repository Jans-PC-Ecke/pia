import os
import sys
import subprocess
import json
import logging
from datetime import datetime

# Konfigurations- und Log-Pfade
CONFIG_DIR = os.path.join(os.path.expanduser("~"), "pia3")
BOOTLOADER_CONFIG = os.path.join(CONFIG_DIR, "pia_bootloader_config.json")
LOG_DIR = os.path.join(CONFIG_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, f"pia_boot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

def initialize_logging():
    """Initialisiert das Logging."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.info("Pia3 Bootloader gestartet")
    except Exception as e:
        print(f"[Pia3] Fehler beim Initialisieren des Loggings: {e}")
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.error("Fehler beim Erstellen des Log-Verzeichnisses %s: %s", LOG_DIR, e)

def is_termux():
    """Prüft, ob das Skript in Termux läuft."""
    return "com.termux" in os.getcwd()

def ensure_termux_permissions():
    """Sichert Termux-Berechtigungen, falls erforderlich."""
    if is_termux():
        try:
            result = subprocess.run(
                ["termux-setup-storage"],
                capture_output=True,
                text=True,
                check=True
            )
            logging.info("Termux-Speicherberechtigungen gesichert: %s", result.stdout)
        except subprocess.CalledProcessError as e:
            logging.error("Fehler beim Einrichten der Termux-Speicherberechtigungen: %s", e)
            print(f"[Pia3] Warnung: Speicherberechtigungen konnten nicht gesichert werden: {e}")
        except FileNotFoundError:
            logging.error("termux-setup-storage nicht gefunden. Installiere Termux:API (`pkg install termux-api`)")
            print(f"[Pia3] Fehler: termux-setup-storage nicht gefunden. Installiere Termux:API (`pkg install termux-api`)")

def install_dependencies():
    """Installiert erforderliche Abhängigkeiten für pia3_termux.py."""
    dependencies = [
        "requests",
        "gTTS",
        "schedule",
        "speechrecognition",  # speech_recognition als speechrecognition für pip
        "PyAudio"
    ]
    system_packages = {
        "termux": ["termux-api", "mpg123"],
        "linux": ["mpg123", "portaudio"]
    }

    # Installiere Systempakete basierend auf der Umgebung
    if is_termux():
        for pkg in system_packages["termux"]:
            try:
                subprocess.run(["pkg", "install", pkg, "-y"], check=True)
                logging.info("Termux-Systempaket installiert: %s", pkg)
            except subprocess.CalledProcessError as e:
                logging.error("Fehler beim Installieren des Termux-Pakets %s: %s", pkg, e)
                print(f"[Pia3] Warnung: Termux-Paket {pkg} konnte nicht installiert werden: {e}")
            except FileNotFoundError:
                logging.error("Termux pkg-Befehl nicht gefunden")
                print(f"[Pia3] Fehler: Termux-Paketmanager nicht gefunden")
    else:  # Standard Linux (z.B. Manjaro)
        for pkg in system_packages["linux"]:
            try:
                subprocess.run(["pacman", "-S", pkg, "--noconfirm"], check=True)
                logging.info("Linux-Systempaket installiert: %s", pkg)
            except subprocess.CalledProcessError as e:
                logging.error("Fehler beim Installieren des Linux-Pakets %s: %s", pkg, e)
                print(f"[Pia3] Warnung: Linux-Paket {pkg} konnte nicht installiert werden: {e}")
            except FileNotFoundError:
                logging.error("pacman nicht gefunden. Stelle sicher, dass du auf einem Arch-basierten System bist.")
                print(f"[Pia3] Fehler: pacman nicht gefunden. Stelle sicher, dass du auf einem Arch-basierten System bist.")

    # Installiere Python-Abhängigkeiten
    for dep in dependencies:
        try:
            __import__(dep.lower().replace("speechrecognition", "speech_recognition"))
            logging.info("Abhängigkeit bereits installiert: %s", dep)
        except ImportError:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
                logging.info("Abhängigkeit installiert: %s", dep)
            except subprocess.CalledProcessError as e:
                logging.error("Fehler beim Installieren der Abhängigkeit %s: %s", dep, e)
                print(f"[Pia3] Warnung: {dep} konnte nicht installiert werden. Einige Funktionen könnten nicht funktionieren: {e}")
            except FileNotFoundError:
                logging.error("pip nicht gefunden für die Installation von %s", dep)
                print(f"[Pia3] Fehler: pip nicht gefunden. Bitte installiere pip, um alle Funktionen zu nutzen.")

def create_default_bootloader_config():
    """Erstellt die Standard-Konfiguration für den Bootloader."""
    default_config = {
        "pia3_dir": os.path.join(os.path.expanduser("~"), "pia3"),
        "pia3_script": "pia3_termux.py",
        "language": "de-DE",
        "use_curses": True,
        "llm_enabled": False
    }
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if not os.path.exists(BOOTLOADER_CONFIG):
            with open(BOOTLOADER_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            logging.info("Standard-Bootloader-Konfiguration unter %s erstellt", BOOTLOADER_CONFIG)
    except Exception as e:
        logging.error("Fehler beim Erstellen der Bootloader-Konfiguration: %s", e)
        print(f"[Pia3] Fehler beim Erstellen der Bootloader-Konfiguration: {e}")

def verify_directories():
    """Prüft und erstellt erforderliche Verzeichnisse."""
    directories = [
        CONFIG_DIR,
        os.path.join(CONFIG_DIR, "logs"),
        os.path.join(CONFIG_DIR, "notes"),
        os.path.join(CONFIG_DIR, "reminders")
    ]
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            if not os.access(directory, os.R_OK | os.W_OK):
                logging.error("Kein Lese-/Schreibzugriff für %s", directory)
                print(f"[Pia3] Fehler: Kein Lese-/Schreibzugriff für {directory}")
                return False
        except Exception as e:
            logging.error("Fehler beim Erstellen des Verzeichnisses %s: %s", directory, e)
            print(f"[Pia3] Fehler beim Erstellen des Verzeichnisses {directory}: {e}")
            return False
    return True

def main():
    """Hauptfunktion des Bootloaders."""
    initialize_logging()
    print(f"[Pia3] Bootloader wird gestartet...")
    create_default_bootloader_config()
    ensure_termux_permissions()
    install_dependencies()
    if not verify_directories():
        print(f"[Pia3] Fatal: Verzeichnis-Setup fehlgeschlagen. Beende...")
        sys.exit(1)

    # Starte pia3_termux.py
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run([sys.executable, "pia3_termux.py"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error("Fehler beim Starten von pia3_termux.py: %s", e)
        print(f"[Pia3] Fehler beim Starten von Pia3: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logging.error("pia3_termux.py nicht gefunden in %s", os.getcwd())
        print(f"[Pia3] Fehler: pia3_termux.py nicht gefunden in {os.getcwd()}")
        sys.exit(1)

if __name__ == "__main__":
    main()