import os
import sys
import subprocess
import json
import logging
from datetime import datetime

# Konfigurations- und Log-Pfade
CONFIG_DIR = os.path.join(os.path.expanduser("~"), "pia-aktuelles_script_pia")
BOOTLOADER_CONFIG = os.path.join(CONFIG_DIR, "pia_bootloader_config.json")
LOG_DIR = os.path.join(CONFIG_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, f"pia_boot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

def initialize_logging():
    """Initialisiert das Logging mit UTF-8 Kodierung."""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        logging.basicConfig(
            filename=LOG_FILE,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
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
    return "com.termux" in os.environ.get("PREFIX", "")

def check_command_exists(command):
    """Prüft, ob ein Befehl verfügbar ist."""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def ensure_termux_permissions():
    """Sichert Termux-Berechtigungen (Speicher und Mikrofon)."""
    if not is_termux():
        logging.info("Keine Termux-Umgebung erkannt, überspringe Berechtigungsprüfung")
        return True
    permissions = [
        ("termux-setup-storage", "Speicherberechtigungen"),
        ("termux-permission-microphone", "Mikrofonberechtigungen")
    ]
    for cmd, desc in permissions:
        if not check_command_exists(cmd):
            logging.error("%s nicht gefunden. Installiere Termux:API (`pkg install termux-api`)", cmd)
            print(f"[Pia3] Fehler: {cmd} nicht gefunden. Installiere Termux:API (`pkg install termux-api`)")
            return False
        try:
            result = subprocess.run([cmd], capture_output=True, text=True, check=True)
            logging.info("Termux %s gesichert: %s", desc, result.stdout)
        except subprocess.CalledProcessError as e:
            logging.error("Fehler beim Einrichten der Termux %s: %s", desc, e)
            print(f"[Pia3] Warnung: {desc} konnten nicht gesichert werden: {e}")
            return False
    return True

def install_system_package(pkg, installer="pkg"):
    """Installiert ein Systempaket mit dem angegebenen Installer."""
    try:
        if installer == "pkg":
            subprocess.run(["pkg", "install", pkg, "-y"], check=True)
        elif installer == "pacman":
            subprocess.run(["pacman", "-S", pkg, "--noconfirm"], check=True)
        logging.info("%s-Paket installiert: %s", installer, pkg)
        return True
    except subprocess.CalledProcessError as e:
        logging.error("Fehler beim Installieren des %s-Pakets %s: %s", installer, pkg, e)
        print(f"[Pia3] Warnung: Paket {pkg} konnte nicht installiert werden: {e}")
        return False
    except FileNotFoundError:
        logging.error("%s nicht gefunden. Stelle sicher, dass %s korrekt installiert ist.", installer, installer)
        print(f"[Pia3] Fehler: {installer} nicht gefunden. Stelle sicher, dass {installer} korrekt installiert ist.")
        return False

def install_python_package(dep):
    """Installiert eine Python-Abhängigkeit über pip als Fallback."""
    try:
        __import__(dep.lower().replace("speechrecognition", "speech_recognition").replace("google-cloud-speech", "google.cloud.speech"))
        logging.info("Abhängigkeit bereits installiert: %s", dep)
        return True
    except ImportError:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            logging.info("Abhängigkeit installiert: %s", dep)
            return True
        except subprocess.CalledProcessError as e:
            logging.error("Fehler beim Installieren der Abhängigkeit %s: %s", dep, e)
            print(f"[Pia3] Warnung: {dep} konnte nicht installiert werden. Einige Funktionen könnten nicht funktionieren: {e}")
            return False
        except FileNotFoundError:
            logging.error("pip nicht gefunden für die Installation von %s", dep)
            print(f"[Pia3] Fehler: pip nicht gefunden. Bitte installiere pip, um alle Funktionen zu nutzen.")
            return False

def install_dependencies():
    """Installiert erforderliche Abhängigkeiten für pia3_termux.py."""
    dependencies = {
        "system": {
            "termux": ["termux-api", "mpg123", "libportaudio2"],
            "linux": ["mpg123", "portaudio19-dev"]
        },
        "python": [
            "requests",
            "gTTS",
            "schedule",
            "speechrecognition",
            "PyAudio",
            "google-cloud-speech",
            "discord.py"
        ]
    }

    # Installiere Systempakete
    installer = "pkg" if is_termux() else "pacman"
    system_packages = dependencies["system"]["termux" if is_termux() else "linux"]
    for pkg in system_packages:
        if not check_command_exists(pkg.replace("libportaudio2", "portaudio") if is_termux() else pkg):
            if not install_system_package(pkg, installer):
                print(f"[Pia3] Hinweis: {pkg} nicht installiert. Einige Funktionen (z.B. Audio) könnten eingeschränkt sein.")

    # Installiere Python-Abhängigkeiten
    for dep in dependencies["python"]:
        if not install_python_package(dep):
            print(f"[Pia3] Hinweis: {dep} nicht installiert. Einige Funktionen könnten eingeschränkt sein.")

def create_default_bootloader_config():
    """Erstellt die Standard-Konfiguration für den Bootloader."""
    default_config = {
        "pia3_dir": os.path.join(os.path.expanduser("~"), "pia-aktuelles_script_pia"),
        "pia3_script": "pia3_termux.py",
        "language": "de-DE",
        "use_curses": True,
        "llm_enabled": False,
        "discord_intents": {
            "default": True,
            "message_content": True,
            "members": True,
            "presences": True
        },
        "google_speech_api_key": "YOUR_GOOGLE_API_KEY"
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

def verify_pia_script():
    """Prüft, ob pia3_termux.py existiert."""
    pia_script_path = os.path.join(CONFIG_DIR, "pia3_termux.py")
    if not os.path.exists(pia_script_path):
        logging.error("pia3_termux.py nicht gefunden in %s", pia_script_path)
        print(f"[Pia3] Fehler: pia3_termux.py nicht gefunden in {pia_script_path}")
        return False
    return True

def main():
    """Hauptfunktion des Bootloaders."""
    initialize_logging()
    print(f"[Pia3] Bootloader wird gestartet... (Umgebung: {'Termux' if is_termux() else 'Linux'})")
    create_default_bootloader_config()
    if not ensure_termux_permissions():
        print(f"[Pia3] Fatal: Termux-Berechtigungen konnten nicht gesichert werden. Beende...")
        sys.exit(1)
    install_dependencies()
    if not verify_directories():
        print(f"[Pia3] Fatal: Verzeichnis-Setup fehlgeschlagen. Beende...")
        sys.exit(1)
    if not verify_pia_script():
        print(f"[Pia3] Fatal: pia3_termux.py nicht gefunden. Beende...")
        sys.exit(1)

    # Starte pia3_termux.py
    try:
        os.chdir(CONFIG_DIR)
        print(f"[Pia3] Starte pia3_termux.py in {CONFIG_DIR}...")
        subprocess.run([sys.executable, "pia3_termux.py"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error("Fehler beim Starten von pia3_termux.py: %s", e)
        print(f"[Pia3] Fehler beim Starten von Pia3: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logging.error("pia3_termux.py nicht gefunden in %s", CONFIG_DIR)
        print(f"[Pia3] Fehler: pia3_termux.py nicht gefunden in {CONFIG_DIR}")
        sys.exit(1)

if __name__ == "__main__":
    main()