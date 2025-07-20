import os
import json
import time
import logging
import subprocess
import threading
import asyncio
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
try:
    import discord
    from discord.ext import commands
    import discord.opus
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False

# Konfigurationspfade
BASE_DIR = os.path.join(os.path.expanduser("~"), "pia-aktuelles_script_pia")
os.makedirs(BASE_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(BASE_DIR, "pia_config.json")
NOTES_FILE = os.path.join(BASE_DIR, "notes.json")
REMINDERS_FILE = os.path.join(BASE_DIR, "reminders.json")
LOG_FILE = os.path.join(BASE_DIR, "pia3_termux.log")

# Logging einrichten
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a',
    encoding='utf-8'
)

# Globale Konfiguration
CONFIG = {}

def load_config():
    """Lädt die Konfigurationsdatei."""
    try:
        if not os.path.exists(CONFIG_FILE):
            logging.error("Konfigurationsdatei nicht gefunden: %s", CONFIG_FILE)
            raise FileNotFoundError(f"Konfigurationsdatei fehlt: {CONFIG_FILE}")
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            CONFIG.update(json.load(f))
        logging.info("Konfigurationsdatei geladen: %s", CONFIG_FILE)
        logging.debug("Konfiguration: %s", CONFIG)
        if CONFIG.get("llm_enabled") and not is_server_reachable(CONFIG.get("llm_server_port", 8081)):
            logging.warning("LLM-Server nicht erreichbar, KI-Anfragen werden fehlschlagen")
        if not CONFIG.get("discord_bot_token") or CONFIG.get("discord_bot_token") == "YOUR_VALID_DISCORD_TOKEN":
            logging.warning("Ungültiger oder fehlender Discord-Token")
        if not CONFIG.get("discord_channel_id"):
            logging.warning("Discord-Kanal-ID fehlt")
        if not CONFIG.get("discord_voice_channel_id") and CONFIG.get("voice_enabled", False):
            logging.warning("Discord-Voice-Channel-ID fehlt")
    except Exception as e:
        logging.error("Fehler beim Laden der Konfiguration: %s", e)
        raise

def is_server_reachable(port):
    """Prüft, ob der LLM-Server erreichbar ist."""
    if not REQUESTS_AVAILABLE:
        return False
    try:
        response = requests.get(f"http://localhost:{port}/v1", timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False

def is_online():
    """Prüft, ob eine Internetverbindung besteht."""
    if not REQUESTS_AVAILABLE:
        logging.debug("is_online: requests-Modul nicht verfügbar")
        return False
    try:
        response = requests.get("https://api.openweathermap.org", timeout=3)
        logging.debug("is_online: Verbindung zu api.openweathermap.org erfolgreich, Status: %s", response.status_code)
        return True
    except requests.RequestException as e:
        logging.debug("is_online: Keine Internetverbindung - %s", e)
        return False

def query_llm(prompt):
    """Sendet eine Anfrage an den LLM-Server."""
    if not REQUESTS_AVAILABLE:
        return "KI nicht verfügbar (requests fehlt)"
    if not CONFIG.get("llm_enabled", False):
        return "KI deaktiviert (llm_enabled=False)"
    port = CONFIG.get("llm_server_port", 8081)
    if not is_server_reachable(port):
        return f"KI-Fehler: Server nicht erreichbar auf Port {port}"
    try:
        url = f"http://localhost:{port}/v1/completions"
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

def save_json(file_path, data):
    """Speichert Daten in eine JSON-Datei."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True, ""
    except Exception as e:
        logging.error("Fehler beim Speichern von %s: %s", file_path, e)
        return False, str(e)

def load_json(file_path, default_data):
    """Lädt Daten aus einer JSON-Datei."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default_data
    except Exception as e:
        logging.error("Fehler beim Laden von %s: %s", file_path, e)
        return default_data

async def send_discord_message(message, channel_id=None):
    """Sendet eine Nachricht an einen Discord-Kanal."""
    if not DISCORD_AVAILABLE:
        logging.warning("send_discord_message: Discord-Modul nicht verfügbar")
        return False, "Discord-Modul nicht verfügbar"
    if not CONFIG.get("discord_enabled", True):
        logging.warning("send_discord_message: Discord deaktiviert in Konfiguration")
        return False, "Discord deaktiviert"
    try:
        bot_token = CONFIG.get("discord_bot_token")
        channel_id = channel_id or CONFIG.get("discord_channel_id")
        if not bot_token or bot_token == "YOUR_VALID_DISCORD_TOKEN":
            logging.warning("send_discord_message: Ungültiger oder fehlender Discord-Token")
            return False, "Ungültiger Discord-Token"
        if not channel_id:
            logging.warning("send_discord_message: Discord-Kanal-ID fehlt")
            return False, "Discord-Kanal-ID fehlt"
        channel = client.get_channel(int(channel_id))
        if not channel:
            logging.warning("send_discord_message: Discord-Kanal mit ID %s nicht gefunden", channel_id)
            return False, "Discord-Kanal nicht gefunden"
        logging.debug("send_discord_message: Sende Nachricht '%s' an Kanal %s", message, channel_id)
        sent_message = await channel.send(message)
        logging.info("send_discord_message: Nachricht erfolgreich gesendet")
        # Automatisches Löschen, wenn konfiguriert
        delete_after = CONFIG.get("auto_delete_after", 0)
        if delete_after > 0:
            await asyncio.sleep(delete_after)
            try:
                await sent_message.delete()
                logging.info("send_discord_message: Nachricht nach %s Sekunden gelöscht", delete_after)
            except discord.errors.NotFound:
                logging.warning("send_discord_message: Nachricht bereits gelöscht")
            except discord.errors.Forbidden:
                logging.error("send_discord_message: Fehlende Berechtigung zum Löschen der Nachricht")
        return True, "Nachricht gesendet"
    except discord.errors.Forbidden as e:
        logging.error("send_discord_message: Fehlende Berechtigungen für Kanal %s: %s", channel_id, e)
        return False, f"Fehlende Berechtigungen: {str(e)}"
    except Exception as e:
        logging.error("send_discord_message: Fehler beim Senden an Discord: %s", e)
        return False, str(e)

def sync_send_discord_message(message, channel_id=None):
    """Synchroner Wrapper für send_discord_message."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logging.debug("sync_send_discord_message: Event-Loop läuft, verwende run_coroutine_threadsafe")
            future = asyncio.run_coroutine_threadsafe(send_discord_message(message, channel_id), loop)
            return future.result()
        logging.debug("sync_send_discord_message: Event-Loop läuft nicht, verwende asyncio.run")
        return asyncio.run(send_discord_message(message, channel_id))
    except Exception as e:
        logging.error("sync_send_discord_message: Fehler: %s", e)
        return False, str(e)

def speak_text(text):
    """Spricht Text lokal aus mit espeak, termux-tts-speak oder gTTS."""
    logging.debug("speak_text: Versuche lokale TTS für Text '%s'", text)
    try:
        if os.path.exists("/data/data/com.termux"):
            logging.debug("speak_text: Verwende termux-tts-speak")
            subprocess.run(["termux-tts-speak", text], check=True)
        else:
            logging.debug("speak_text: Verwende espeak")
            subprocess.run(["espeak", "-v", CONFIG.get("language", "de-DE").split('-')[0], text], check=True)
        logging.info("speak_text: Lokale TTS erfolgreich für Text '%s'", text)
        return True, ""
    except FileNotFoundError:
        logging.warning("speak_text: Keine lokale TTS-Engine verfügbar, versuche gTTS")
        if GTTS_AVAILABLE and is_online():
            try:
                logging.debug("speak_text: Verwende gTTS")
                tts = gTTS(text=text, lang=CONFIG.get("language", "de-DE").split('-')[0])
                output_file = os.path.join(BASE_DIR, "output.mp3")
                tts.save(output_file)
                subprocess.run(["mpg123", "-q", output_file], check=True)
                os.remove(output_file)
                logging.info("speak_text: gTTS erfolgreich für Text '%s'", text)
                return True, ""
            except Exception as e:
                logging.error("speak_text: Fehler beim gTTS-Sprechen: %s", e)
                return False, str(e)
        logging.error("speak_text: Keine TTS-Engine verfügbar (espeak oder termux-tts-speak fehlt)")
        return False, "Keine TTS-Engine verfügbar"

def get_weather(city):
    """Ruft Wetterdaten von OpenWeatherMap ab."""
    if not REQUESTS_AVAILABLE or not is_online():
        logging.warning("get_weather: Wetterabfrage nicht verfügbar (offline oder requests fehlt)")
        return "Wetterabfrage nicht verfügbar (offline oder requests fehlt)"
    try:
        api_key = CONFIG.get("openweather_api_key")
        if not api_key:
            logging.warning("get_weather: Wetter-API-Schlüssel fehlt")
            return "Wetter-API-Schlüssel fehlt"
        city = city.replace("in ", "").strip()
        if not city:
            logging.warning("get_weather: Keine Stadt angegeben")
            return "Keine Stadt angegeben"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=de"
        logging.debug("get_weather: Sende Anfrage an %s", url)
        response = requests.get(url, timeout=5)
        data = response.json()
        if response.status_code == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            logging.info("get_weather: Wetter erfolgreich abgerufen für %s: %s°C, %s", city, temp, desc)
            return f"Wetter in {city}: {temp}°C, {desc}"
        logging.error("get_weather: Fehler bei API-Antwort: %s", data.get('message', 'Unbekannter Fehler'))
        return f"Fehler: {data.get('message', 'Unbekannter Fehler')}"
    except Exception as e:
        logging.error("get_weather: Fehler bei Wetterabfrage: %s", e)
        return f"Fehler bei Wetterabfrage: {str(e)}"

def add_note(content):
    """Fügt eine Notiz hinzu und sendet sie optional an Discord."""
    notes = load_json(NOTES_FILE, {"notes": []}).get("notes", [])
    notes.append({"content": content, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    success, msg = save_json(NOTES_FILE, {"notes": notes})
    if not success:
        logging.error("add_note: Fehler beim Speichern der Notiz: %s", msg)
        return f"Fehler beim Speichern der Notiz: {msg}"
    if CONFIG.get("discord_enabled", True) and is_online():
        success, discord_msg = sync_send_discord_message(f"Neue Notiz: {content}")
        logging.info("add_note: Notiz hinzugefügt: %s, Discord: %s", content, discord_msg)
        return f"Notiz hinzugefügt{' und an Discord gesendet' if success else f' (Discord nicht gesendet: {discord_msg})'}: {content}"
    logging.info("add_note: Notiz hinzugefügt: %s (kein Discord)", content)
    return f"Notiz hinzugefügt: {content}"

def delete_note(index):
    """Löscht eine Notiz anhand des Indexes."""
    notes = load_json(NOTES_FILE, {"notes": []}).get("notes", [])
    try:
        if 0 <= index < len(notes):
            content = notes[index]["content"]
            notes.pop(index)
            save_json(NOTES_FILE, {"notes": notes})
            logging.info("delete_note: Notiz gelöscht: %s", content)
            return f"Notiz gelöscht: {content}"
        logging.warning("delete_note: Ungültiger Notiz-Index: %s", index)
        return "Ungültiger Notiz-Index"
    except Exception as e:
        logging.error("delete_note: Fehler beim Löschen der Notiz: %s", e)
        return f"Fehler beim Löschen: {str(e)}"

def list_notes():
    """Listet alle Notizen."""
    notes = load_json(NOTES_FILE, {"notes": []}).get("notes", [])
    if not notes:
        logging.info("list_notes: Keine Notizen vorhanden")
        return "Keine Notizen vorhanden"
    result = "\n".join(f"{i}. {note['content']} ({note['timestamp']})" for i, note in enumerate(notes, 1))
    logging.info("list_notes: Notizen gelistet: %s", result)
    return result

def add_reminder(content, date_time):
    """Fügt eine Erinnerung hinzu und sendet sie optional an Discord."""
    reminders = load_json(REMINDERS_FILE, {"reminders": []}).get("reminders", [])
    try:
        datetime.strptime(date_time, "%Y-%m-%d %H:%M")
        reminders.append({"content": content, "date_time": date_time})
        success, msg = save_json(REMINDERS_FILE, {"reminders": reminders})
        if not success:
            logging.error("add_reminder: Fehler beim Speichern der Erinnerung: %s", msg)
            return f"Fehler beim Speichern der Erinnerung: {msg}"
        if CONFIG.get("discord_enabled", True) and is_online():
            success, discord_msg = sync_send_discord_message(f"Neue Erinnerung: {content} am {date_time}")
            logging.info("add_reminder: Erinnerung hinzugefügt: %s am %s, Discord: %s", content, date_time, discord_msg)
            return f"Erinnerung hinzugefügt{' und an Discord gesendet' if success else f' (Discord nicht gesendet: {discord_msg})'}: {content}"
        logging.info("add_reminder: Erinnerung hinzugefügt: %s am %s (kein Discord)", content, date_time)
        return f"Erinnerung hinzugefügt: {content}"
    except ValueError:
        logging.warning("add_reminder: Ungültiges Datumsformat: %s", date_time)
        return "Ungültiges Datumsformat (YYYY-MM-DD HH:MM)"
    except Exception as e:
        logging.error("add_reminder: Fehler beim Hinzufügen der Erinnerung: %s", e)
        return f"Fehler beim Hinzufügen: {str(e)}"

def delete_reminder(index):
    """Löscht eine Erinnerung anhand des Indexes."""
    reminders = load_json(REMINDERS_FILE, {"reminders": []}).get("reminders", [])
    try:
        if 0 <= index < len(reminders):
            content = reminders[index]["content"]
            reminders.pop(index)
            save_json(REMINDERS_FILE, {"reminders": reminders})
            logging.info("delete_reminder: Erinnerung gelöscht: %s", content)
            return f"Erinnerung gelöscht: {content}"
        logging.warning("delete_reminder: Ungültiger Erinnerung-Index: %s", index)
        return "Ungültiger Erinnerung-Index"
    except Exception as e:
        logging.error("delete_reminder: Fehler beim Löschen der Erinnerung: %s", e)
        return f"Fehler beim Löschen: {str(e)}"

def list_reminders(date_str=None):
    """Listet Erinnerungen, optional gefiltert nach Datum."""
    reminders = load_json(REMINDERS_FILE, {"reminders": []}).get("reminders", [])
    if not reminders:
        logging.info("list_reminders: Keine Erinnerungen vorhanden")
        return "Keine Erinnerungen vorhanden"
    if date_str:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            filtered = [r for r in reminders if r["date_time"].startswith(date_str)]
            if not filtered:
                logging.info("list_reminders: Keine Erinnerungen für %s", date_str)
                return f"Keine Erinnerungen für {date_str}"
            result = "\n".join(f"{i}. {r['content']} ({r['date_time']})" for i, r in enumerate(filtered, 1))
            logging.info("list_reminders: Erinnerungen für %s: %s", date_str, result)
            return result
        except ValueError:
            logging.warning("list_reminders: Ungültiges Datumsformat: %s", date_str)
            return "Ungültiges Datumsformat (YYYY-MM-DD)"
    result = "\n".join(f"{i}. {r['content']} ({r['date_time']})" for i, r in enumerate(reminders, 1))
    logging.info("list_reminders: Alle Erinnerungen: %s", result)
    return result

def read_reminders():
    """Liest alle Erinnerungen vor."""
    reminders = load_json(REMINDERS_FILE, {"reminders": []}).get("reminders", [])
    if not reminders:
        logging.info("read_reminders: Keine Erinnerungen vorhanden")
        return "Keine Erinnerungen vorhanden"
    text = "Ihre Erinnerungen: " + "; ".join(f"{r['content']} am {r['date_time']}" for r in reminders)
    success, msg = speak_text(text)
    logging.info("read_reminders: Erinnerungen vorgelesen, Erfolg: %s, Nachricht: %s", success, msg)
    return "Erinnerungen vorgelesen" if success else f"Fehler beim Vorlesen: {msg}"

def set_volume(level=None, mute=False):
    """Setzt Lautstärke oder schaltet Audio stumm/aktiv."""
    try:
        if mute:
            cmd = ["termux-volume", "music", "0"] if os.path.exists("/data/data/com.termux") else ["amixer", "set", "Master", "mute"]
            subprocess.run(cmd, check=True)
            logging.info("set_volume: Audio stummgeschaltet")
            return "Audio stummgeschaltet"
        if level is not None:
            if not isinstance(level, int) or not 0 <= level <= 100:
                logging.warning("set_volume: Ungültiger Lautstärkepegel: %s", level)
                return "Ungültiger Lautstärkepegel (0-100)"
            cmd = ["termux-volume", "music", str(level)] if os.path.exists("/data/data/com.termux") else ["amixer", "set", "Master", f"{level}%"]
            subprocess.run(cmd, check=True)
            logging.info("set_volume: Lautstärke auf %s%% gesetzt", level)
            return f"Lautstärke auf {level}% gesetzt"
        logging.warning("set_volume: Kein Lautstärkepegel angegeben")
        return "Kein Lautstärkepegel angegeben"
    except Exception as e:
        logging.error("set_volume: Fehler beim Einstellen der Lautstärke: %s", e)
        return f"Fehler beim Einstellen der Lautstärke: {str(e)}"

async def delete_bot_messages(channel_id):
    """Löscht alle Nachrichten des Bots in einem bestimmten Kanal."""
    if not DISCORD_AVAILABLE:
        logging.warning("delete_bot_messages: Discord-Modul nicht verfügbar")
        return False, "Discord-Modul nicht verfügbar"
    try:
        channel = client.get_channel(int(channel_id))
        if not channel:
            logging.warning("delete_bot_messages: Discord-Kanal mit ID %s nicht gefunden", channel_id)
            return False, "Discord-Kanal nicht gefunden"
        deleted_count = 0
        async for message in channel.history(limit=100):
            if message.author == client.user:
                try:
                    await message.delete()
                    deleted_count += 1
                    logging.info("delete_bot_messages: Nachricht gelöscht (ID: %s)", message.id)
                except discord.errors.Forbidden:
                    logging.error("delete_bot_messages: Fehlende Berechtigung zum Löschen der Nachricht (ID: %s)", message.id)
                except discord.errors.NotFound:
                    logging.warning("delete_bot_messages: Nachricht bereits gelöscht (ID: %s)", message.id)
        logging.info("delete_bot_messages: %s Nachrichten gelöscht", deleted_count)
        return True, f"{deleted_count} Nachrichten gelöscht"
    except discord.errors.Forbidden as e:
        logging.error("delete_bot_messages: Fehlende Berechtigungen für Kanal %s: %s", channel_id, e)
        return False, f"Fehlende Berechtigungen: {str(e)}"
    except Exception as e:
        logging.error("delete_bot_messages: Fehler beim Löschen der Nachrichten: %s", e)
        return False, str(e)

def sync_delete_bot_messages(channel_id):
    """Synchroner Wrapper für delete_bot_messages."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            logging.debug("sync_delete_bot_messages: Event-Loop läuft, verwende run_coroutine_threadsafe")
            future = asyncio.run_coroutine_threadsafe(delete_bot_messages(channel_id), loop)
            return future.result()
        logging.debug("sync_delete_bot_messages: Event-Loop läuft nicht, verwende asyncio.run")
        return asyncio.run(delete_bot_messages(channel_id))
    except Exception as e:
        logging.error("sync_delete_bot_messages: Fehler: %s", e)
        return False, str(e)

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
                if CONFIG.get("discord_enabled", True) and is_online():
                    sync_send_discord_message(f"Erinnerung: {content} um {current_time}")
                logging.info("check_reminders: Erinnerung ausgelöst: %s", content)
            else:
                updated_reminders.append(reminder)
        if triggered:
            save_json(REMINDERS_FILE, {"reminders": updated_reminders})
        return triggered
    except Exception as e:
        logging.error("check_reminders: Fehler: %s", e)
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
                logging.warning("reminder_scheduler: schedule-Modul nicht verfügbar, verwende Fallback")
                while True:
                    check_reminders()
                    time.sleep(60)
        except Exception as e:
            logging.error("reminder_scheduler: Fehler im Scheduler-Thread: %s", e)
    threading.Thread(target=run_schedule, daemon=True).start()
    logging.info("reminder_scheduler: Erinnerungs-Scheduler gestartet")

# Discord-Client
client = None
if DISCORD_AVAILABLE:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    client = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

def process_command(command, stdscr=None, ctx=None):
    """Verarbeitet Textbefehle für Shell- und Discord-Modus."""
    command = command.lower().strip()
    logging.debug("process_command: Verarbeite Befehl: %s", command)
    if command.startswith("notiz hinzufügen"):
        content = command.replace("notiz hinzufügen", "").strip()
        if content:
            response = add_note(content)
            if ctx:
                asyncio.create_task(ctx.send(response))
            else:
                speak_text(response)
            return response
        response = "Kein Notizinhalt angegeben"
        if ctx:
            asyncio.create_task(ctx.send(response))
        return response
    elif command.startswith("notiz löschen"):
        try:
            index = int(command.replace("notiz löschen", "").strip()) - 1
            response = delete_note(index)
            if ctx:
                asyncio.create_task(ctx.send(response))
            else:
                speak_text(response)
            return response
        except ValueError:
            response = "Ungültiger Notiz-Index"
            if ctx:
                asyncio.create_task(ctx.send(response))
            return response
    elif command == "notizen auflisten":
        response = list_notes()
        if ctx:
            asyncio.create_task(ctx.send(response))
        else:
            speak_text(response)
        return response
    elif command.startswith("erinnerung hinzufügen"):
        parts = command.replace("erinnerung hinzufügen", "").strip().split(" am ")
        if len(parts) == 2:
            content, date_time = parts
            response = add_reminder(content.strip(), date_time.strip())
            if ctx:
                asyncio.create_task(ctx.send(response))
            else:
                speak_text(response)
            return response
        response = "Ungültiges Format (erwartet: erinnerung hinzufügen <Inhalt> am <YYYY-MM-DD HH:MM>)"
        if ctx:
            asyncio.create_task(ctx.send(response))
        return response
    elif command.startswith("erinnerung löschen"):
        try:
            index = int(command.replace("erinnerung löschen", "").strip()) - 1
            response = delete_reminder(index)
            if ctx:
                asyncio.create_task(ctx.send(response))
            else:
                speak_text(response)
            return response
        except ValueError:
            response = "Ungültiger Erinnerung-Index"
            if ctx:
                asyncio.create_task(ctx.send(response))
            return response
    elif command.startswith("erinnerungen auflisten"):
        date_str = command.replace("erinnerungen auflisten", "").strip()
        response = list_reminders(date_str if date_str else None)
        if ctx:
            asyncio.create_task(ctx.send(response))
        else:
            speak_text(response)
        return response
    elif command == "erinnerungen vorlesen":
        response = read_reminders()
        if ctx:
            asyncio.create_task(ctx.send(response))
        return response
    elif command.startswith("wetter"):
        city = command.replace("wetter", "").replace("in ", "").strip()
        if not city:
            response = "Keine Stadt angegeben (z.B. wetter Berlin)"
            if ctx:
                asyncio.create_task(ctx.send(response))
            return response
        response = get_weather(city)
        if ctx:
            asyncio.create_task(ctx.send(response))
        else:
            speak_text(response)
        return response
    elif command == "zeit":
        response = f"Die aktuelle Zeit ist {datetime.now().strftime('%H:%M')}"
        if ctx:
            asyncio.create_task(ctx.send(response))
        else:
            speak_text(response)
        return response
    elif command.startswith("lautstärke"):
        parts = command.replace("lautstärke", "").strip()
        if parts == "stumm":
            response = set_volume(mute=True)
            if ctx:
                asyncio.create_task(ctx.send(response))
            else:
                speak_text(response)
            return response
        try:
            level = int(parts)
            response = set_volume(level=level)
            if ctx:
                asyncio.create_task(ctx.send(response))
            else:
                speak_text(response)
            return response
        except ValueError:
            response = "Ungültiger Lautstärkepegel (0-100 oder 'stumm')"
            if ctx:
                asyncio.create_task(ctx.send(response))
            return response
    elif command == "nachrichten löschen":
        if ctx:
            success, response = sync_delete_bot_messages(ctx.channel.id)
            if ctx:
                asyncio.create_task(ctx.send(response))
            return response
        return "Nachrichten löschen nur über Discord verfügbar"
    elif command in ("hilfe", "help", "zeig mir die hilfe"):
        if ctx:
            help_items = [
                {"command": "!notiz <Inhalt>", "description": "Fügt eine neue Notiz hinzu.", "example": "!notiz Einkaufen gehen"},
                {"command": "!notiz_löschen <Index>", "description": "Löscht eine Notiz anhand der Nummer.", "example": "!notiz_löschen 1"},
                {"command": "!notizen", "description": "Listet alle gespeicherten Notizen.", "example": "!notizen"},
                {"command": "!erinnerung <Inhalt> am <YYYY-MM-DD HH:MM>", "description": "Fügt eine Erinnerung hinzu.", "example": "!erinnerung Arzttermin am 2025-07-15 17:00"},
                {"command": "!erinnerung_löschen <Index>", "description": "Löscht eine Erinnerung anhand der Nummer.", "example": "!erinnerung_löschen 1"},
                {"command": "!erinnerungen [YYYY-MM-DD]", "description": "Listet alle Erinnerungen oder für ein Datum.", "example": "!erinnerungen 2025-07-15"},
                {"command": "!erinnerungen_vorlesen", "description": "Liest alle Erinnerungen vor.", "example": "!erinnerungen_vorlesen"},
                {"command": "!wetter <Stadt>", "description": "Ruft die Wettervorhersage ab.", "example": "!wetter Berlin"},
                {"command": "!zeit", "description": "Zeigt die aktuelle Uhrzeit an.", "example": "!zeit"},
                {"command": "!lautstärke <Wert>|stumm", "description": "Setzt Lautstärke (0-100) oder schaltet stumm.", "example": "!lautstärke 50"},
                {"command": "!nachrichten_löschen", "description": "Löscht alle Bot-Nachrichten im Kanal.", "example": "!nachrichten_löschen"},
                {"command": "!hilfe", "description": "Zeigt dieses Hilfemenü.", "example": "!hilfe"},
                {"command": "!frage <Text>", "description": "Stellt eine Frage an die KI (falls aktiviert).", "example": "!frage Was ist die Hauptstadt von Deutschland?"}
            ]
            output = "\n[Pia3] Hilfemenü\n" + "\n".join(f"\nBefehl: {item['command']}\nBeschreibung: {item['description']}\nBeispiel: {item['example']}\n" for item in help_items)
            asyncio.create_task(ctx.send(output))
            return "Hilfemenü angezeigt"
        elif stdscr and CURSES_AVAILABLE:
            help_menu(stdscr)
        else:
            help_menu()
        return "Hilfemenü angezeigt"
    elif command.startswith("frage"):
        prompt = command.replace("frage", "").strip()
        if not prompt:
            response = "Keine Frage angegeben (z.B. frage Was ist die Hauptstadt von Deutschland?)"
            if ctx:
                asyncio.create_task(ctx.send(response))
            return response
        response = query_llm(prompt)
        if ctx:
            asyncio.create_task(ctx.send(response))
        else:
            speak_text(response)
        return response
    elif command in ("exit", ":q", "beenden"):
        return ":q"
    else:
        response = "Unbekannter Befehl. Verwende 'hilfe' für eine Liste der Befehle."
        if ctx:
            asyncio.create_task(ctx.send(response))
        return response

def start_discord_bot():
    """Startet den Discord-Bot mit Befehls- und Wake-Word-Unterstützung."""
    @client.event
    async def on_ready():
        logging.info(f"start_discord_bot: Discord-Bot verbunden als {client.user}")
        if CONFIG.get("voice_enabled", False) and CONFIG.get("discord_voice_channel_id"):
            try:
                voice_channel = client.get_channel(int(CONFIG.get("discord_voice_channel_id")))
                if voice_channel:
                    voice_client = await voice_channel.connect()
                    logging.info("start_discord_bot: Verbunden mit Voice Channel %s", voice_channel.id)
                    # Hinweis: Spracherkennung im Voice Channel ist aktuell deaktiviert.
                else:
                    logging.warning("start_discord_bot: Voice Channel %s nicht gefunden", CONFIG.get("discord_voice_channel_id"))
            except Exception as e:
                logging.error("start_discord_bot: Fehler beim Verbinden mit Voice Channel: %s", e)

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        if CONFIG.get("discord_enabled", True) and str(message.channel.id) == CONFIG.get("discord_channel_id"):
            content = message.content.lower()
            wake_word = CONFIG.get("wake_word", "Hey Pia").lower()
            if content.startswith(wake_word):
                logging.info("on_message: Wake-Word '%s' erkannt in Nachricht: %s", wake_word, content)
                command = content.replace(wake_word, "").strip()
                if command:
                    response = process_command(command, ctx=message)
                    logging.info("on_message: Wake-Word-Befehl verarbeitet: %s, Antwort: %s", command, response)
                else:
                    await message.channel.send("Ja, ich bin hier!")
                    logging.info("on_message: Wake-Word ohne Befehl erkannt")
            await client.process_commands(message)

    @client.command()
    async def notiz(ctx, *, content=None):
        response = process_command(f"notiz hinzufügen {content}" if content else "notiz hinzufügen", ctx=ctx)
        logging.info("notiz: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def notiz_löschen(ctx, index: int):
        response = process_command(f"notiz löschen {index}", ctx=ctx)
        logging.info("notiz_löschen: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def notizen(ctx):
        response = process_command("notizen auflisten", ctx=ctx)
        logging.info("notizen: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def erinnerung(ctx, *, args=None):
        response = process_command(f"erinnerung hinzufügen {args}" if args else "erinnerung hinzufügen", ctx=ctx)
        logging.info("erinnerung: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def erinnerung_löschen(ctx, index: int):
        response = process_command(f"erinnerung löschen {index}", ctx=ctx)
        logging.info("erinnerung_löschen: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def erinnerungen(ctx, date_str=None):
        response = process_command(f"erinnerungen auflisten {date_str}" if date_str else "erinnerungen auflisten", ctx=ctx)
        logging.info("erinnerungen: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def erinnerungen_vorlesen(ctx):
        response = process_command("erinnerungen vorlesen", ctx=ctx)
        logging.info("erinnerungen_vorlesen: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def wetter(ctx, *, city=None):
        response = process_command(f"wetter {city}" if city else "wetter", ctx=ctx)
        logging.info("wetter: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def zeit(ctx):
        response = process_command("zeit", ctx=ctx)
        logging.info("zeit: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def lautstärke(ctx, *, arg=None):
        response = process_command(f"lautstärke {arg}" if arg else "lautstärke", ctx=ctx)
        logging.info("lautstärke: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def nachrichten_löschen(ctx):
        response = process_command("nachrichten löschen", ctx=ctx)
        logging.info("nachrichten_löschen: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def hilfe(ctx):
        response = process_command("hilfe", ctx=ctx)
        logging.info("hilfe: Befehl ausgeführt, Antwort: %s", response)

    @client.command()
    async def frage(ctx, *, prompt=None):
        response = process_command(f"frage {prompt}" if prompt else "frage", ctx=ctx)
        logging.info("frage: Befehl ausgeführt, Antwort: %s", response)

    try:
        logging.info("start_discord_bot: Starte Bot mit Token %s", CONFIG.get("discord_bot_token", "Kein Token"))
        client.run(CONFIG.get("discord_bot_token"))
    except Exception as e:
        logging.error("start_discord_bot: Fehler beim Starten des Discord-Bots: %s", e)

def run_discord_bot():
    """Startet den Discord-Bot in einem separaten Thread."""
    if DISCORD_AVAILABLE and CONFIG.get("discord_enabled", True) and is_online():
        logging.info("run_discord_bot: Starte Discord-Bot-Thread")
        threading.Thread(target=start_discord_bot, daemon=True).start()
        logging.info("run_discord_bot: Discord-Bot-Thread gestartet")
    else:
        logging.warning("run_discord_bot: Discord-Bot nicht gestartet (DISCORD_AVAILABLE=%s, discord_enabled=%s, is_online=%s)",
                       DISCORD_AVAILABLE, CONFIG.get("discord_enabled", True), is_online())

def help_menu(stdscr=None):
    """Zeigt ein interaktives Hilfemenü mit curses oder als Text-Fallback."""
    help_items = [
        {"command": "notiz hinzufügen <Inhalt>", "description": "Fügt eine neue Notiz hinzu.", "example": "notiz hinzufügen Einkaufen gehen"},
        {"command": "notiz löschen <Index>", "description": "Löscht eine Notiz anhand der Nummer.", "example": "notiz löschen 1"},
        {"command": "notizen auflisten", "description": "Listet alle gespeicherten Notizen.", "example": "notizen auflisten"},
        {"command": "erinnerung hinzufügen <Inhalt> am <YYYY-MM-DD HH:MM>", "description": "Fügt eine Erinnerung hinzu.", "example": "erinnerung hinzufügen Arzttermin am 2025-07-15 17:00"},
        {"command": "erinnerung löschen <Index>", "description": "Löscht eine Erinnerung anhand der Nummer.", "example": "erinnerung löschen 1"},
        {"command": "erinnerungen auflisten [YYYY-MM-DD]", "description": "Listet alle Erinnerungen oder für ein Datum.", "example": "erinnerungen auflisten 2025-07-15"},
        {"command": "erinnerungen vorlesen", "description": "Liest alle Erinnerungen vor.", "example": "erinnerungen vorlesen"},
        {"command": "wetter <Stadt>", "description": "Ruft die Wettervorhersage ab.", "example": "wetter Berlin"},
        {"command": "zeit", "description": "Zeigt die aktuelle Uhrzeit an.", "example": "zeit"},
        {"command": "lautstärke <Wert>|stumm", "description": "Setzt die Lautstärke (0-100) oder schaltet Audio stumm.", "example": "lautstärke 50"},
        {"command": "nachrichten löschen", "description": "Löscht alle Bot-Nachrichten im Kanal.", "example": "nachrichten löschen"},
        {"command": "hilfe", "description": "Zeigt dieses Hilfemenü an.", "example": "hilfe"},
        {"command": "exit, :q, beenden", "description": "Beendet den Shell-Modus.", "example": "exit"}
    ]
    if CONFIG.get("use_curses", True) and stdscr and CURSES_AVAILABLE:
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
            elif key == 10:
                item = help_items[selected]
                message = f"Beispiel: {item['example']}"
                speak_text(f"Befehl: {item['command']}. {item['description']}. Beispiel: {item['example']}")
            elif key in (ord('q'), ord(':') + ord('q')):
                break
    else:
        output = "\n[Pia3] Hilfemenü\n" + "\n".join(f"\nBefehl: {item['command']}\nBeschreibung: {item['description']}\nBeispiel: {item['example']}\n" for item in help_items)
        print(output)
        if CONFIG.get("discord_enabled", True) and is_online():
            sync_send_discord_message(output)
        print("Drücke Enter, um zurückzukehren...")
        input()

def shell_mode():
    """Interaktiver Shell-Modus."""
    if CONFIG.get("use_curses", True) and CURSES_AVAILABLE:
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
            stdscr.addstr(max_y-2, 0, message[:max_x-2], curses.color_pair(1))
        stdscr.addstr(max_y-2, 0, f"> {input_string[:max_x-3]}", curses.color_pair(2))
        stdscr.refresh()
        key = stdscr.getch()
        if key == 10:
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
        logging.error("voice_mode: speech_recognition nicht installiert, Sprachmodus deaktiviert")
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
                text = recognizer.recognize_google(audio, language=CONFIG.get("language", "de-DE")).lower()
                logging.debug("voice_mode: Erkannter Text: %s", text)
                if CONFIG.get("wake_word", "Hey Pia").lower() in text:
                    speak_text("Ja, ich bin hier!")
                    subprocess.run(["mpg123", "-q", os.path.join(BASE_DIR, "wake_sound.mp3")], check=False)
                    with mic as source:
                        print("Befehl erwartet...")
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    try:
                        command = recognizer.recognize_google(audio, language=CONFIG.get("language", "de-DE")).lower()
                        logging.debug("voice_mode: Befehl erkannt: %s", command)
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
                        logging.error("voice_mode: %s", response)
                        speak_text(response)
                        print(response)
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                logging.error("voice_mode: Spracherkennungsfehler: %s", e)
                speak_text("Spracherkennungsfehler")
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error("voice_mode: Fehler im Sprachmodus: %s", e)
            speak_text("Ein Fehler ist aufgetreten")
            print(f"Fehler: {str(e)}")

def main():
    """Hauptfunktion."""
    try:
        load_config()
    except FileNotFoundError:
        print(f"Fehler: Konfigurationsdatei {CONFIG_FILE} nicht gefunden")
        return
    run_discord_bot()
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