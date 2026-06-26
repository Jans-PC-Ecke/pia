import os
import subprocess
import zipfile
from datetime import datetime
from utils import BASE_DIR, sprich, logging

# ====================== SERVER KONFIGURATION ======================
SERVER_IP = "192.168.178.22"           
SERVER_USER = "dieter2"                
SERVER_PATH = "/media/dieter2/HappyDeath21/pia4/"   

# SSH-Einstellungen
USE_SSH_PASS = True                    # Auf True lassen, solange du noch kein SSH-Key hast
SSH_PASSWORD = "12041993"    

# Timeout-Einstellungen
SCP_TIMEOUT = 60                       
# ================================================================

def backup_erstellen():
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        zipname = os.path.join(BASE_DIR, f"pia4-config-backup-{ts}.zip")

        sprich("Erstelle lokales Backup...")

        added = 0
        skipped = 0

        # Nur Dateien direkt im Hauptordner
        files = [f for f in os.listdir(BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f))]

        include_extensions = ('.py', '.json', '.sh', '.ini', '.conf', '.toml', '.yaml', '.yml')

        with zipfile.ZipFile(zipname, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in files:
                # Nur gewünschte Dateitypen
                if not file.lower().endswith(include_extensions):
                    skipped += 1
                    continue

                # Ausschlüsse (Logs, große Dateien, etc.)
                if file.endswith(('.log', '.zip', '.mp3', '.gguf', '.pyc', '.pyo')):
                    skipped += 1
                    continue

                pfad = os.path.join(BASE_DIR, file)
                zf.write(pfad, file)          # Nur Dateiname, kein Pfad
                added += 1

        sprich(f"Backup erstellt ({added} Dateien). Übertrage auf Server...")

        # ========================== AUF SERVER KOPIEREN ==========================
        remote_dest = f"{SERVER_USER}@{SERVER_IP}:{SERVER_PATH}"

        if USE_SSH_PASS and SSH_PASSWORD and SSH_PASSWORD != "DEIN_PASSWORT_HIER":
            cmd = [
                "sshpass", "-p", SSH_PASSWORD,
                "scp", "-o", "ConnectTimeout=20",
                zipname, remote_dest
            ]
        else:
            # Versuch mit SSH-Key
            cmd = [
                "scp", "-o", "ConnectTimeout=20",
                "-o", "BatchMode=yes", zipname, remote_dest
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=SCP_TIMEOUT)

        if result.returncode == 0:
            msg = f"""Backup erfolgreich auf Server übertragen!
Datei: pia4-config-backup-{ts}.zip
Gesichert: {added} Dateien
Ziel: {SERVER_IP}:{SERVER_PATH}"""
            
            logging.info(msg)
            sprich("Backup wurde erfolgreich auf den Server kopiert.")
            return msg

        else:
            error_msg = f"scp-Fehler: {result.stderr.strip()}"
            logging.error(error_msg)
            sprich("Backup erstellt, aber Übertragung zum Server ist fehlgeschlagen.")
            return f"Fehler bei der Übertragung:\n{result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        logging.error("scp Timeout nach 60 Sekunden")
        sprich("Übertragung zum Server hat zu lange gedauert (Timeout).")
        return "scp-Übertragung timed out."

    except Exception as e:
        logging.error(f"Server-Backup Fehler: {e}", exc_info=True)
        sprich("Backup ist leider fehlgeschlagen.")
        return f"Fehler: {str(e)}"


def tools_holen():
    return [
        ("backup_erstellen", backup_erstellen, "Backup / Server"),
    ]