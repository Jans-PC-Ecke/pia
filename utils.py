import os
import json
import logging
import subprocess
import threading
from datetime import datetime
from pathlib import Path
import socket

# ────────────────────────────────────────────────
# Basisverzeichnis
# ────────────────────────────────────────────────
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).resolve()
os.makedirs(BASE_DIR, exist_ok=True)

# Logging
logging.basicConfig(
    filename=BASE_DIR / "pia4.log",
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    encoding='utf-8',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s'))
logging.getLogger('').addHandler(console_handler)

# ANSI-Farben
class Colors:
    RESET = '\033[0m'
    RED   = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE  = '\033[94m'
    CYAN  = '\033[96m'
    BOLD  = '\033[1m'

USE_COLOR = True

def cprint(color: str, text: str, file=None):
    if USE_COLOR:
        print(f"{color}{text}{Colors.RESET}", file=file)
    else:
        print(text, file=file)

# ────────────────────────────────────────────────
# JSON Handling
# ────────────────────────────────────────────────
json_lock = threading.RLock()
_json_cache = {}

def lade_json(name: str, default=None, use_cache: bool = True):
    if default is None:
        default = {}

    path = BASE_DIR / name

    with json_lock:
        if use_cache:
            cached = _json_cache.get(name)
            if cached and path.exists() and cached[0] == path.stat().st_mtime:
                return cached[1]

        if not path.exists():
            speichere_json(name, default)
            return default

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if use_cache:
                _json_cache[name] = (path.stat().st_mtime, data)
            return data
        except Exception as e:
            logging.error(f"lade_json Fehler bei {name}: {e}")
            return default


def speichere_json(name: str, daten, indent=2):
    path = BASE_DIR / name
    backup_path = path.with_suffix(path.suffix + ".bak")

    with json_lock:
        try:
            if path.exists():
                path.rename(backup_path)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(daten, f, indent=indent, ensure_ascii=False)

            if backup_path.exists():
                backup_path.unlink()

            _json_cache.pop(name, None)

        except Exception as e:
            logging.error(f"speichere_json Fehler bei {name}: {e}", exc_info=True)
            if backup_path.exists():
                backup_path.rename(path)
            raise

# ────────────────────────────────────────────────
# KONFIG
# ────────────────────────────────────────────────
KONFIG = lade_json("pia4_konfig.json", {
    "openweather_api_key": "",
    "telegram_bot_token": "",
    "telegram_chat_id": ""
})

# ────────────────────────────────────────────────
# TTS: gTTS primär + Piper leise als Offline-Fallback
# ────────────────────────────────────────────────
piper_voice = None
try:
    from piper.voice import PiperVoice
    model_path = BASE_DIR / "de_DE-thorsten-medium.onnx"
    config_path = BASE_DIR / "de_DE-thorsten-medium.onnx.json"
    if model_path.exists() and config_path.exists():
        piper_voice = PiperVoice.load(str(model_path), str(config_path))
        logging.info("Piper offline TTS geladen")
    else:
        logging.debug("Piper-Modelldateien nicht gefunden → nur gTTS wird verwendet")
except Exception:
    logging.debug("Piper nicht verfügbar → nur gTTS wird verwendet")
    piper_voice = None

def sprich(text: str):
    """Sprachausgabe: gTTS bevorzugt, Piper als stille Offline-Alternative"""
    text = str(text).strip()
    if not text:
        return

    # 1. gTTS (gute Qualität)
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="de", slow=False)
        tmp_mp3 = BASE_DIR / "tmp_sprache.mp3"
        tts.save(tmp_mp3)
        subprocess.run(["mpg123", "-q", str(tmp_mp3)], check=False, timeout=15)
        tmp_mp3.unlink(missing_ok=True)
        return
    except Exception as e:
        logging.warning(f"gTTS-Fehler (kein Internet?): {e}")

    # 2. Piper als Offline-Fallback (kein Warning bei Fehlschlag)
    if piper_voice:
        try:
            wav_bytes = piper_voice.synthesize(text)
            tmp_wav = BASE_DIR / "tmp_pia.wav"
            with open(tmp_wav, "wb") as f:
                f.write(wav_bytes)
            subprocess.run(["mpg123", "-q", str(tmp_wav)], check=False, timeout=15)
            tmp_wav.unlink(missing_ok=True)
            return
        except:
            pass  # leise fehlschlagen

    # 3. Letzter Ausweg: Text auf Konsole ausgeben
    print(f"[Pia] {text}")


# ────────────────────────────────────────────────
# Telegram deaktiviert
# ────────────────────────────────────────────────
def telegram_senden(nachricht: str, anhang=None, parse_mode: str = "MarkdownV2"):
    logging.warning("Telegram ist deaktiviert – nutze Server-Backup")
    return False

# ────────────────────────────────────────────────
# System-Hilfsfunktionen
# ────────────────────────────────────────────────
def system_befehl(befehl, shell=True, check=False, timeout=None, capture_output=False):
    kwargs = {"shell": shell, "check": check, "timeout": timeout}
    if capture_output:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    else:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL

    try:
        result = subprocess.run(befehl, **kwargs)
        if capture_output:
            return result.stdout.strip() if result.returncode == 0 else ""
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Systembefehl fehlgeschlagen: {befehl} → {e}")
        return False

def is_process_running(process_name: str) -> bool:
    try:
        out = subprocess.check_output(["pgrep", "-f", process_name], text=True).strip()
        return bool(out)
    except:
        return False

# ────────────────────────────────────────────────
# Deutsche Zeit-Helfer
# ────────────────────────────────────────────────
DE_WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
DE_MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

def format_de_time(dt: datetime | None = None, fmt: str = "voll") -> str:
    if dt is None:
        dt = datetime.now()
    if fmt == "kurz":
        return dt.strftime("%H:%M")
    elif fmt == "datum":
        return f"{dt.day}. {DE_MONATE[dt.month-1]} {dt.year}"
    elif fmt == "wochentag":
        return DE_WOCHENTAGE[dt.weekday()]
    else:
        return f"{DE_WOCHENTAGE[dt.weekday()]}, {dt.day}. {DE_MONATE[dt.month-1]} {dt.year} – {dt.strftime('%H:%M')} Uhr"

# ────────────────────────────────────────────────
# Env Overrides
# ────────────────────────────────────────────────
def load_env_overrides():
    for key in list(KONFIG.keys()):
        env_key = f"PIA4_{key.upper()}"
        if val := os.getenv(env_key):
            KONFIG[key] = val
            logging.info(f"Konfig überschrieben via ENV: {env_key}")

load_env_overrides()

# ────────────────────────────────────────────────
if __name__ == "__main__":
    print("utils.py geladen – gTTS primär + Piper (leise)")