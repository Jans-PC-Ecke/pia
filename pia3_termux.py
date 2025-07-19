import os
import json
import time
import logging
import subprocess
import threading
import socket
from datetime import datetime
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
try:
    import curses
    CURSES_AVAILABLE = True
except ImportError:
    CURSES_AVAILABLE = False

# Konfigurationspfade
BASE_DIR = os.path.join(os.path.expanduser("~"), "pia3")
os.makedirs(BASE_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(BASE_DIR, "pia_config.json")
NOTES_FILE = os.path.join(BASE_DIR, "notes.json")
REMINDERS_FILE = os.path.join(BASE_DIR, "reminders.json")
LOG_FILE = os.path.join(BASE_DIR, "pia3_termux.log")

# Logging einrichten
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Standard-Konfiguration
DEFAULT_CONFIG = {
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "openweather_api_key": "",
    "wake_word": "Hey Pia",
    "language": "de-DE",
    "use_curses": True,
    "llm_model_path": "/run/media/gustavtux/6D7F-FAE4/models/TinyLlama-1.1B-Chat-v1.0.Q4_0.llamafile",
    "llm_enabled": False,
    "llm_server_port": 8081
}

# Globale Variablen
CONFIG = DEFAULT_CONFIG.copy()

def is_server_reachable(port):
    """Prüft, ob der LLM-Server erreichbar ist."""
    try:
        response = requests.get(f"http://localhost:{port}/v1", timeout=3)
        return response.status_code == 200
    except requests.RequestException as e:
        logging.error("LLM-Server nicht erreichbar auf Port %s: %s", port, e)
        return False

def query_llm(prompt):
    """Sendet eine Anfrage an den LLM-Server."""
    if not REQUESTS_AVAILABLE:
        logging.warning("requests nicht installiert, KI deaktiviert")
        return "KI nicht verfügbar (requests fehlt)"
    if not CONFIG["llm_enabled"]:
        logging.warning("KI deaktiviert in Konfiguration (llm_enabled=False)")
        return "KI deaktiviert (llm_enabled=False in Konfiguration)"
    if not is_server_reachable(CONFIG["llm_server_port"]):
        logging.error("LLM-Server nicht erreichbar auf Port %s", CONFIG["llm_server_port"])
        return f"KI-Fehler: Server nicht erreichbar auf Port {CONFIG['llm_server_port']}"
    try:
        url = f"http://localhost:{CONFIG['llm_server_port']}/v1/completions"
        payload = {
            "prompt": f"Antworte auf Deutsch: {prompt}",
            "max_tokens": 50,
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.95
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()["choices"][0]["text"].strip()
        logging.error("LLM-Fehler: %s (Status: %s)", response.text, response.status_code)
        return f"KI-Fehler: {response.text}"
    except Exception as e:
        logging.error("Fehler bei KI-Anfrage: %s", e)
        return f"Fehler bei KI: {str(e)}"

def load_config():
    """Lädt die Konfigurationsdatei."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                CONFIG.update(json.load(f))
            logging.info("Konfigurationsdatei geladen: %s", CONFIG_FILE)
        else:
            logging.warning("Konfigurationsdatei nicht gefunden, erstelle Standard-Konfiguration: %s", CONFIG_FILE)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
        logging.debug("Konfiguration: %s", CONFIG)
        # Prüfe, ob der LLM-Server erreichbar ist, wenn llm_enabled=True
        if CONFIG["llm_enabled"]:
            if not is_server_reachable(CONFIG["llm_server_port"]):
                logging.warning("LLM-Server nicht erreichbar, KI-Anfragen werden fehlschlagen")
    except Exception as e:
        logging.error("Fehler beim Laden der Konfiguration: %s", e)

def save_json(file_path, data):
    """Speichert Daten in eine JSON-Datei."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True, ""
    except Exception as e:
        logging.error("Fehler beim Speichern von %s: %s", file_path, e)
        return False, str(e)

def load_json(file_path, default_data):
    """Lädt Daten aus einer JSON-Datei."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return default_data
    except Exception as e:
        logging.error("Fehler beim Laden von %s: %s", file_path, e)
        return default_data

def speak_text(text):
    """Spricht Text aus, falls gTTS verfügbar ist."""
    if not GTTS_AVAILABLE:
        logging.warning("gTTS nicht installiert, Sprachausgabe deaktiviert")
        return False, "gTTS nicht installiert"
    try:
        tts = gTTS(text=text, lang=CONFIG["language"].split('-')[0])
        output_file = os.path.join(BASE_DIR, "output.mp3")
        tts.save(output_file)
        # Plattformabhängige Wiedergabe
        if os.path.exists("/data/data/com.termux"):
            subprocess.run(["termux-media-player", "play", output_file], check=True)
        else:
            subprocess.run(["mpg123", "-q", output_file], check=True)
        time.sleep(0.5)
        os.remove(output_file)
        return True, ""
    except Exception as e:
        logging.error("Fehler beim Sprechen von Text: %s", e)
        return False, str(e)

def send_telegram_message(message):
    """Sendet eine Nachricht über Telegram."""
    if not REQUESTS_AVAILABLE:
        logging.warning("requests nicht installiert, Telegram deaktiviert")
        return False, "requests nicht installiert"
    try:
        bot_token = CONFIG.get("telegram_bot_token")
        chat_id = CONFIG.get("telegram_chat_id")
        if not bot_token or not chat_id:
            logging.warning("Telegram nicht konfiguriert (Token oder Chat-ID fehlt)")
            return False, "Telegram nicht konfiguriert"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            return True, "Nachricht gesendet"
        logging.error("Telegram-Fehler: %s", response.text)
        return False, f"Telegram-Fehler: {response.text}"
    except Exception as e:
        logging.error("Fehler beim Senden an Telegram: %s", e)
        return False, str(e)

def get_weather(city):
    """Ruft Wetterdaten von OpenWeatherMap ab."""
    if not REQUESTS_AVAILABLE:
        logging.warning("requests nicht installiert, Wetterabfrage deaktiviert")
        return "Wetterabfrage nicht verfügbar (requests fehlt)"
    try:
        api_key = CONFIG.get("openweather_api_key")
        if not api_key:
            logging.warning("OpenWeatherMap API-Schlüssel fehlt")
            return "Wetter-API nicht konfiguriert"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=de"
        response = requests.get(url, timeout=5)
        data = response.json()
        if response.status_code == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"Wetter in {city}: {temp}°C, {desc}"
        logging.error("Wetterabfrage-Fehler: %s", data.get("message", "Unbekannter Fehler"))
        return f"Fehler: {data.get('message', 'Unbekannter Fehler')}"
    except Exception as e:
        logging.error("Fehler bei Wetterabfrage: %s", e)
        return f"Fehler bei Wetterabfrage: {str(e)}"

def add_note(content):
    """Fügt eine Notiz hinzu und sendet sie optional an Telegram."""
    notes = load_json(NOTES_FILE, {"notes": []}).get("notes", [])
    notes.append({"content": content, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    success, msg = save_json(NOTES_FILE, {"notes": notes})
    if not success:
        return f"Fehler beim Speichern der Notiz: {msg}"
    success, telegram_msg = send_telegram_message(f"Neue Notiz: {content}")
    if success:
        return f"Notiz hinzugefügt und an Telegram gesendet: {content}"
    return f"Notiz hinzugefügt: {content} (Telegram nicht gesendet: {telegram_msg})"

def delete_note(index):
    """Löscht eine Notiz anhand des Indexes."""
    notes = load_json(NOTES_FILE, {"notes": []}).get("notes", [])
    try:
        if 0 <= index < len(notes):
            content = notes[index]["content"]
            notes.pop(index)
            save_json(NOTES_FILE, {"notes": notes})
            return f"Notiz gelöscht: {content}"
        return "Ungültiger Notiz-Index"
    except Exception as e:
        logging.error("Fehler beim Löschen der Notiz: %s", e)
        return f"Fehler beim Löschen: {str(e)}"

def list_notes():
    """Listet alle Notizen."""
    notes = load_json(NOTES_FILE, {"notes": []}).get("notes", [])
    if not notes:
        return "Keine Notizen vorhanden"
    result = ["Notizen:"]
    for i, note in enumerate(notes, 1):
        result.append(f"{i}. {note['content']} ({note['timestamp']})")
    return "\n".join(result)

def add_reminder(content, date_time):
    """Fügt eine Erinnerung hinzu und sendet sie optional an Telegram."""
    reminders = load_json(REMINDERS_FILE, {"reminders": []}).get("reminders", [])
    try:
        datetime.strptime(date_time, "%Y-%m-%d %H:%M")  # Validierung
        reminders.append({"content": content, "date_time": date_time})
        success, msg = save_json(REMINDERS_FILE, {"reminders": reminders})
        if not success:
            return f"Fehler beim Speichern der Erinnerung: {msg}"
        success, telegram_msg = send_telegram_message(f"Neue Erinnerung: {content} am {date_time}")
        if success:
            return f"Erinnerung hinzugefügt und an Telegram gesendet: {content}"
        return f"Erinnerung hinzugefügt: {content} (Telegram nicht gesendet: {telegram_msg})"
    except ValueError:
        return "Ungültiges Datumsformat (YYYY-MM-DD HH:MM)"
    except Exception as e:
        logging.error("Fehler beim Hinzufügen der Erinnerung: %s", e)
        return f"Fehler beim Hinzufügen: {str(e)}"

def delete_reminder(index):
    """Löscht eine Erinnerung anhand des Indexes."""
    reminders = load_json(REMINDERS_FILE, {"reminders": []}).get("reminders", [])
    try:
        if 0 <= index < len(reminders):
            content = reminders[index]["content"]
            reminders.pop(index)
            save_json(REMINDERS_FILE, {"reminders": reminders})
            return f"Erinnerung gelöscht: {content}"
        return "Ungültiger Erinnerung-Index"
    except Exception as e:
        logging.error("Fehler beim Löschen der Erinnerung: %s", e)
        return f"Fehler beim Löschen: {str(e)}"

def list_reminders(date_str=None):
    """Listet Erinnerungen, optional gefiltert nach Datum."""
    reminders = load_json(REMINDERS_FILE, {"reminders": []}).get("reminders", [])
    if not reminders:
        return "Keine Erinnerungen vorhanden"
    if date_str:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            filtered = [r for r in reminders if r["date_time"].startswith(date_str)]
            if not filtered:
                return f"Keine Erinnerungen für {date_str}"
            result = [f"Erinnerungen für {date_str}:"]
            for i, reminder in enumerate(filtered, 1):
                result.append(f"{i}. {reminder['content']} ({reminder['date_time']})")
            return "\n".join(result)
        except ValueError:
            return "Ungültiges Datumsformat (YYYY-MM-DD)"
    result = ["Erinnerungen:"]
    for i, reminder in enumerate(reminders, 1):
        result.append(f"{i}. {reminder['content']} ({reminder['date_time']})")
    return "\n".join(result)

def read_reminders():
    """Liest alle Erinnerungen vor."""
    reminders = load_json(REMINDERS_FILE, {"reminders": []}).get("reminders", [])
    if not reminders:
        return "Keine Erinnerungen vorhanden"
    text = "Ihre Erinnerungen: " + "; ".join(f"{r['content']} am {r['date_time']}" for r in reminders)
    success, msg = speak_text(text)
    if success:
        return "Erinnerungen vorgelesen"
    return f"Fehler beim Vorlesen: {msg}"

def set_volume(level=None, mute=False):
    """Setzt Lautstärke oder schaltet Audio stumm/aktiv."""
    try:
        if mute:
            if os.path.exists("/data/data/com.termux"):
                subprocess.run(["termux-volume", "music", "0"], check=True)
            else:
                subprocess.run(["amixer", "set", "Master", "mute"], check=True)
            return "Audio stummgeschaltet"
        if level is not None:
            if not isinstance(level, int) or not 0 <= level <= 100:
                return "Ungültiger Lautstärkepegel (0-100)"
            if os.path.exists("/data/data/com.termux"):
                subprocess.run(["termux-volume", "music", str(level)], check=True)
            else:
                subprocess.run(["amixer", "set", "Master", f"{level}%"], check=True)
            return f"Lautstärke auf {level}% gesetzt"
        return "Kein Lautstärkepegel angegeben"
    except Exception as e:
        logging.error("Fehler beim Einstellen der Lautstärke: %s", e)
        return f"Fehler beim Einstellen der Lautstärke: {str(e)}"

def check_reminders():
    """Überprüft Erinnerungen und löst Benachrichtigungen aus."""
    try:
        reminders = load_json(REMINDERS_FILE, {"reminders": []}).get("reminders", [])
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        updated_reminders = []
        triggered = False
        for reminder in reminders:
            if reminder["date_time"] == current_time:
                triggered = True
                content = reminder["content"]
                speak_text(f"Erinnerung: {content}")
                send_telegram_message(f"Erinnerung: {content} um {current_time}")
                logging.info("Erinnerung ausgelöst: %s", content)
            else:
                updated_reminders.append(reminder)
        if triggered:
            save_json(REMINDERS_FILE, {"reminders": updated_reminders})
        return triggered
    except Exception as e:
        logging.error("Fehler in check_reminders: %s", e)
        return False

def reminder_scheduler():
    """Hintergrundprozess für automatische Erinnerungen."""
    def run_schedule():
        try:
            if SCHEDULE_AVAILABLE:
                schedule.every(1).minutes.do(check_reminders)
                while True:
                    schedule.run_pending()
                    time.sleep(60)
            else:
                logging.warning("schedule-Modul nicht verfügbar, verwende Fallback")
                while True:
                    check_reminders()
                    time.sleep(60)
        except Exception as e:
            logging.error("Fehler im Scheduler-Thread: %s", e)

    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()
    logging.info("Erinnerungs-Scheduler gestartet")

def help_menu(stdscr=None):
    """Zeigt ein interaktives Hilfemenü mit curses oder als Text-Fallback."""
    help_items = [
        {
            "command": "notiz hinzufügen <Inhalt>",
            "description": "Fügt eine neue Notiz hinzu.",
            "example": "notiz hinzufügen Einkaufen gehen"
        },
        {
            "command": "notiz löschen <Index>",
            "description": "Löscht eine Notiz anhand der Nummer.",
            "example": "notiz löschen 1"
        },
        {
            "command": "notizen auflisten",
            "description": "Listet alle gespeicherten Notizen.",
            "example": "notizen auflisten"
        },
        {
            "command": "erinnerung hinzufügen <Inhalt> am <YYYY-MM-DD HH:MM>",
            "description": "Fügt eine Erinnerung hinzu, die zu einem bestimmten Zeitpunkt ausgelöst wird.",
            "example": "erinnerung hinzufügen Arzttermin am 2025-07-15 17:00"
        },
        {
            "command": "erinnerung löschen <Index>",
            "description": "Löscht eine Erinnerung anhand der Nummer.",
            "example": "erinnerung löschen 1"
        },
        {
            "command": "erinnerungen auflisten [YYYY-MM-DD]",
            "description": "Listet alle Erinnerungen oder nur für ein bestimmtes Datum.",
            "example": "erinnerungen auflisten 2025-07-15"
        },
        {
            "command": "erinnerungen vorlesen",
            "description": "Liest alle Erinnerungen vor (Sprachausgabe).",
            "example": "erinnerungen vorlesen"
        },
        {
            "command": "wetter in <Stadt>",
            "description": "Ruft die aktuelle Wettervorhersage für eine Stadt ab.",
            "example": "wetter in Berlin"
        },
        {
            "command": "zeit",
            "description": "Zeigt die aktuelle Uhrzeit an.",
            "example": "zeit"
        },
        {
            "command": "lautstärke <Wert>|stumm",
            "description": "Setzt die Lautstärke (0-100) oder schaltet Audio stumm.",
            "example": "lautstärke 50 oder lautstärke stumm"
        },
        {
            "command": "hilfe",
            "description": "Zeigt dieses Hilfemenü an.",
            "example": "hilfe"
        },
        {
            "command": "exit, :q, beenden",
            "description": "Beendet den Shell-Modus.",
            "example": "exit"
        },
        {
            "command": "(beliebige Frage oder Coding-Aufgabe)",
            "description": "Stellt eine Frage oder Coding-Aufgabe an die KI (falls Server läuft und llm_enabled=True).",
            "example": "Was ist die Hauptstadt von Deutschland?"
        }
    ]

    if CONFIG.get("use_curses") and stdscr and CURSES_AVAILABLE:
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        selected = 0
        message = ""
        while True:
            stdscr.clear()
            max_y, max_x = stdscr.getmaxyx()
            stdscr.addstr(0, 0, "[Pia3] Hilfemenü (Pfeiltasten, Enter, q)", curses.color_pair(1))
            stdscr.addstr(max_y-1, 0, f"[Pia3] Drücke q zum Verlassen {datetime.now().strftime('%H:%M:%S')}"[:max_x-1], curses.color_pair(1))
            for i, item in enumerate(help_items[:max_y-5]):
                line = f"{item['command']}: {item['description']}"
                if i == selected:
                    stdscr.addstr(2 + i, 0, f"> {line[:max_x-2]}", curses.color_pair(2))
                else:
                    stdscr.addstr(2 + i, 0, f"  {line[:max_x-2]}", curses.color_pair(1))
            if message:
                stdscr.addstr(max_y-2, 0, message[:max_x-10], curses.color_pair(3))
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP and selected > 0:
                selected -= 1
            elif key == curses.KEY_DOWN and selected < len(help_items) - 1:
                selected += 1
            elif key == 10:  # Enter
                item = help_items[selected]
                message = f"Beispiel: {item['example']}"
                speak_text(f"Befehl: {item['command']}. {item['description']}. Beispiel: {item['example']}")
            elif key in (ord('q'), ord(':') + ord('q')):
                break
    else:
        print("\n[Pia3] Hilfemenü")
        for item in help_items:
            print(f"\nBefehl: {item['command']}")
            print(f"Beschreibung: {item['description']}")
            print(f"Beispiel: {item['example']}")
        print("\nDrücke Enter, um zurückzukehren...")
        input()

def process_command(command, stdscr=None):
    """Verarbeitet Textbefehle und verwendet die KI für allgemeine Fragen."""
    command = command.lower().strip()
    if command.startswith("notiz hinzufügen"):
        content = command.replace("notiz hinzufügen", "").strip()
        if content:
            response = add_note(content)
            speak_text(response)
            return response
        return "Kein Notizinhalt angegeben"
    elif command.startswith("notiz löschen"):
        try:
            index = int(command.replace("notiz löschen", "").strip()) - 1
            response = delete_note(index)
            speak_text(response)
            return response
        except ValueError:
            return "Ungültiger Notiz-Index"
    elif command == "notizen auflisten":
        response = list_notes()
        speak_text(response)
        return response
    elif command.startswith("erinnerung hinzufügen"):
        parts = command.replace("erinnerung hinzufügen", "").strip().split(" am ")
        if len(parts) == 2:
            content, date_time = parts
            response = add_reminder(content.strip(), date_time.strip())
            speak_text(response)
            return response
        return "Ungültiges Format (erwartet: erinnerung hinzufügen <Inhalt> am <YYYY-MM-DD HH:MM>)"
    elif command.startswith("erinnerung löschen"):
        try:
            index = int(command.replace("erinnerung löschen", "").strip()) - 1
            response = delete_reminder(index)
            speak_text(response)
            return response
        except ValueError:
            return "Ungültiger Erinnerung-Index"
    elif command.startswith("erinnerungen auflisten"):
        date_str = command.replace("erinnerungen auflisten", "").strip()
        response = list_reminders(date_str if date_str else None)
        speak_text(response)
        return response
    elif command == "erinnerungen vorlesen":
        response = read_reminders()
        return response
    elif command.startswith("wetter in"):
        city = command.replace("wetter in", "").strip()
        response = get_weather(city)
        speak_text(response)
        return response
    elif command == "zeit":
        response = f"Die aktuelle Zeit ist {datetime.now().strftime('%H:%M')}"
        speak_text(response)
        return response
    elif command.startswith("lautstärke"):
        parts = command.replace("lautstärke", "").strip()
        if parts == "stumm":
            response = set_volume(mute=True)
            speak_text(response)
            return response
        try:
            level = int(parts)
            response = set_volume(level=level)
            speak_text(response)
            return response
        except ValueError:
            return "Ungültiger Lautstärkepegel (0-100 oder 'stumm')"
    elif command in ("hilfe", "help", "zeig mir die hilfe"):
        if stdscr and CURSES_AVAILABLE:
            help_menu(stdscr)
        else:
            help_menu()
        return "Hilfemenü angezeigt"
    elif command in ("exit", ":q", "beenden"):
        return ":q"
    else:
        response = query_llm(command)
        speak_text(response)
        return response

def shell_mode():
    """Interaktiver Shell-Modus."""
    if CONFIG.get("use_curses") and CURSES_AVAILABLE:
        curses.wrapper(shell_mode_curses)
    else:
        print("Pia3 Shell-Modus (:q zum Beenden)")
        while True:
            command = input("> ").strip()
            if command in (":q", "exit", "beenden"):
                break
            response = process_command(command)
            print(response)

def shell_mode_curses(stdscr):
    """Curses-basierter Shell-Modus."""
    curses.curs_set(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    input_string = ""
    message = ""
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        stdscr.addstr(0, 0, "[Pia3] Shell-Modus (:q zum Beenden)", curses.color_pair(1))
        stdscr.addstr(max_y-1, 0, f"[Pia3] {datetime.now().strftime('%H:%M:%S')}"[:max_x-1], curses.color_pair(1))
        if message:
            stdscr.addstr(2, 0, message[:max_x-2], curses.color_pair(1))
        stdscr.addstr(max_y-2, 0, f"> {input_string[:max_x-3]}", curses.color_pair(2))
        stdscr.refresh()
        key = stdscr.getch()
        if key == 10:  # Enter
            if input_string in (":q", "exit", "beenden"):
                break
            message = process_command(input_string, stdscr)
            input_string = ""
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            input_string = input_string[:-1]
        elif 32 <= key <= 126:
            input_string += chr(key)

def voice_mode():
    """Sprachmodus mit Wake-Word-Erkennung."""
    if not SPEECH_AVAILABLE:
        logging.error("speech_recognition nicht installiert, Sprachmodus deaktiviert")
        print("Sprachmodus nicht verfügbar (speech_recognition fehlt)")
        return
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
    print("Lausche auf Wake-Word: 'Hey Pia'")
    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
            try:
                text = recognizer.recognize_google(audio, language=CONFIG["language"]).lower()
                logging.debug("Erkannter Text: %s", text)
                if CONFIG["wake_word"].lower() in text:
                    speak_text("Ja, ich bin hier!")
                    subprocess.run(["mpg123", "-q", os.path.join(BASE_DIR, "wake_sound.mp3")], check=False)
                    with mic as source:
                        print("Befehl erwartet...")
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    try:
                        command = recognizer.recognize_google(audio, language=CONFIG["language"]).lower()
                        logging.debug("Befehl erkannt: %s", command)
                        response = process_command(command)
                        print(response)
                        if response == ":q":
                            break
                    except sr.UnknownValueError:
                        response = "Befehl nicht verstanden"
                        speak_text(response)
                        print(response)
                    except sr.RequestError as e:
                        response = f"Spracherkennungsfehler: {str(e)}"
                        logging.error(response)
                        speak_text(response)
                        print(response)
            except sr.UnknownValueError:
                pass  # Kein Wake-Word erkannt
            except sr.RequestError as e:
                logging.error("Spracherkennungsfehler: %s", e)
                speak_text("Spracherkennungsfehler")
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error("Fehler im Sprachmodus: %s", e)
            speak_text("Ein Fehler ist aufgetreten")
            print(f"Fehler: {str(e)}")

def main():
    """Hauptfunktion."""
    load_config()
    reminder_scheduler()
    print("Pia3 Termux Assistent")
    print("Modi: 1. Sprachmodus, 2. Shell-Modus, 3. Beenden")
    choice = input("Wähle einen Modus (1-3): ").strip()
    if choice == "1":
        voice_mode()
    elif choice == "2":
        shell_mode()
    elif choice == "3":
        print("Beende Pia3...")
    else:
        print("Ungültige Auswahl")

if __name__ == "__main__":
    main()