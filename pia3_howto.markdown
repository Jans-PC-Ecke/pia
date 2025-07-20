# Pia3-Projekt: Detailliertes How-To für Einrichtung, Installation und Nutzung

Dieses Dokument bietet eine umfassende Anleitung zur Einrichtung, Installation, Vorbereitung und Nutzung des **Pia3-Projekts**, eines Discord-Bots mit Spracherkennung (STT), Text-to-Speech (TTS), Wetterabfragen, Notizen und Erinnerungsfunktionen. Das Projekt besteht aus zwei Hauptkomponenten: dem **Bootloader** (`pia_bootloader.py`), der die Umgebung vorbereitet und Abhängigkeiten installiert, und dem **Haupt-Skript** (`pia3_termux.py`), das die Bot-Logik enthält. Die Anleitung ist für Termux (Android) und Arch-basierte Linux-Systeme (z. B. Manjaro, Arch Linux) optimiert.

## 1. Überblick
Das Pia3-Projekt ermöglicht einen Discord-Bot mit folgenden Funktionen:
- **Discord-Integration**: Befehle wie `!zeit`, `!wetter`, `!erinnerung` über Text oder Sprache.
- **Spracherkennung (STT)**: Unterstützt „Hey Pia“-Wake-Word-Befehle über Google Speech API oder Google Cloud Speech.
- **Text-to-Speech (TTS)**: Antworten werden über `gTTS` oder `termux-tts-speak` ausgesprochen.
- **Wetterabfragen**: Nutzt die OpenWeatherMap-API.
- **Notizen und Erinnerungen**: Speichert Notizen und zeitgesteuerte Erinnerungen in JSON-Dateien.
- **Systemspezifische Installation**: Automatische Installation von Abhängigkeiten über `pkg` (Termux), `pacman` (Arch Linux) oder `pip` (Fallback).

Der Bootloader prüft die Umgebung, sichert Berechtigungen, installiert Abhängigkeiten und startet das Haupt-Skript. Die Installation priorisiert systemeigene Paketmanager (`pkg`, `pacman`) und verwendet `pip` nur als letzte Option.

## 2. Voraussetzungen
Bevor du beginnst, stelle sicher, dass folgende Voraussetzungen erfüllt sind:
- **Umgebung**: Termux (Android) oder Arch-basiertes Linux-System (z. B. Manjaro, Arch Linux).
- **Python**: Version 3.8 oder höher.
  - Termux: `pkg install python`
  - Arch Linux: `sudo pacman -S python`
- **Internetverbindung**: Für die Installation von Abhängigkeiten und API-Zugriffe (OpenWeatherMap, Google Speech).
- **Discord-Bot-Token**: Erstelle einen Bot im [Discord Developer Portal](https://discord.com/developers/applications) und aktiviere alle Intents:
  - Presence Intent
  - Server Members Intent
  - Message Content Intent
- **OpenWeatherMap API-Schlüssel**: Registriere dich bei [OpenWeatherMap](https://openweathermap.org) und hole einen API-Schlüssel.
- **Google Cloud Speech API-Schlüssel (optional)**: Für präzisere STT, erstelle einen Schlüssel in der [Google Cloud Console](https://console.cloud.google.com).
- **Mikrofon (für STT)**: Stelle sicher, dass ein Mikrofon verfügbar ist und Berechtigungen erteilt wurden.
- **Lautsprecher (für TTS)**: Für Sprachausgabe, z. B. via `mpg123`.

## 3. Verzeichnisstruktur einrichten
Das Projekt verwendet `~/pia-aktuelles_script_pia` als Basisverzeichnis. Der Bootloader erstellt die Struktur automatisch, aber du kannst sie auch manuell einrichten.

**Manuelle Einrichtung**:
```bash
mkdir -p ~/pia-aktuelles_script_pia/{logs,notes,reminders}
touch ~/pia-aktuelles_script_pia/pia_config.json
touch ~/pia-aktuelles_script_pia/reminders.json
touch ~/pia-aktuelles_script_pia/notes.json
```

**Automatische Einrichtung**: Der Bootloader (`pia_bootloader.py`) erstellt die Verzeichnisse `/logs`, `/notes` und `/reminders` sowie die Konfigurationsdatei `pia_bootloader_config.json`, falls sie fehlen.

## 4. Bootloader einrichten
Der Bootloader (`pia_bootloader.py`) ist der Einstiegspunkt, der:
- Die Umgebung (Termux oder Linux) erkennt.
- Berechtigungen (Speicher, Mikrofon) sichert.
- Abhängigkeiten über `pkg` (Termux), `pacman` (Arch Linux) oder `pip` (Fallback) installiert.
- Verzeichnisse prüft und erstellt.
- Das Haupt-Skript `pia3_termux.py` startet.

**Schritte**:
1. **Speichere den Bootloader**:
   - Kopiere den Code aus [pia_bootloader.py](#pia-bootloader-code) und speichere ihn in `~/pia-aktuelles_script_pia/pia_bootloader.py`.
   - Alternativ, lade die Datei direkt herunter und verschiebe sie:
     ```bash
     mv ~/Downloads/pia_bootloader.py ~/pia-aktuelles_script_pia/
     chmod +x ~/pia-aktuelles_script_pia/pia_bootloader.py
     ```

2. **Überprüfe die Konfiguration**:
   - Der Bootloader erstellt automatisch `pia_bootloader_config.json` mit Standardwerten, falls sie fehlt:
     ```json
     {
       "pia3_dir": "/home/user/pia-aktuelles_script_pia",
       "pia3_script": "pia3_termux.py",
       "language": "de-DE",
       "use_curses": true,
       "llm_enabled": false,
       "discord_intents": {
         "default": true,
         "message_content": true,
         "members": true,
         "presences": true
       },
       "google_speech_api_key": "YOUR_GOOGLE_API_KEY"
     }
     ```
   - Bearbeite die Datei, falls notwendig:
     ```bash
     nano ~/pia-aktuelles_script_pia/pia_bootloader_config.json
     ```

## 5. Haupt-Skript einrichten
Das Haupt-Skript `pia3_termux.py` enthält die Logik für den Discord-Bot, STT, TTS, Wetterabfragen, Notizen und Erinnerungen. Es wurde bereits korrigiert, um Fehler wie `'list' object has no attribute 'get'` zu beheben und STT mit Google Cloud Speech zu unterstützen.

**Schritte**:
1. **Speichere das Haupt-Skript**:
   - Kopiere den Code aus [pia3_termux.py](#pia3-termux-code) und speichere ihn in `~/pia-aktuelles_script_pia/pia3_termux.py`.
   - Alternativ, lade die Datei herunter und verschiebe sie:
     ```bash
     mv ~/Downloads/pia3_termux.py ~/pia-aktuelles_script_pia/
     chmod +x ~/pia-aktuelles_script_pia/pia3_termux.py
     ```

2. **STT-Integration**:
   - Das Skript unterstützt STT über `speech_recognition` (Google Speech API) oder `google-cloud-speech` (fortgeschritten).
   - Für Google Cloud Speech, füge den API-Schlüssel in `pia_config.json` hinzu (siehe unten).

## 6. Konfigurationsdateien erstellen
Erstelle oder aktualisiere die Konfigurationsdateien in `~/pia-aktuelles_script_pia`.

**`pia_config.json`**:
```json
{
  "discord_bot_token": "YOUR_DISCORD_BOT_TOKEN",
  "discord_channel_id": "YOUR_CHANNEL_ID",
  "discord_voice_channel_id": "YOUR_VOICE_CHANNEL_ID",
  "wake_word": "Hey Pia",
  "language": "de-DE",
  "use_curses": true,
  "discord_enabled": true,
  "voice_enabled": true,
  "openweather_api_key": "YOUR_OPENWEATHER_API_KEY",
  "llm_enabled": false,
  "auto_delete_after": 300,
  "google_speech_api_key": "YOUR_GOOGLE_API_KEY"
}
```
- Ersetze:
  - `YOUR_DISCORD_BOT_TOKEN` mit deinem Bot-Token aus dem Discord Developer Portal.
  - `YOUR_CHANNEL_ID` mit der Textkanal-ID (z. B. `1396263394926923846`).
  - `YOUR_VOICE_CHANNEL_ID` mit der Sprachkanal-ID (z. B. `1396264734478565420`).
  - `YOUR_OPENWEATHER_API_KEY` mit deinem OpenWeatherMap API-Schlüssel.
  - `YOUR_GOOGLE_API_KEY` mit deinem Google Cloud Speech API-Schlüssel (optional).

**Befehl zum Bearbeiten**:
```bash
nano ~/pia-aktuelles_script_pia/pia_config.json
```

**Initialisiere JSON-Dateien**:
```bash
echo '[]' > ~/pia-aktuelles_script_pia/reminders.json
echo '{"notes": []}' > ~/pia-aktuelles_script_pia/notes.json
```

## 7. Abhängigkeiten installieren
Der Bootloader installiert automatisch alle Abhängigkeiten, priorisiert `pkg` (Termux) oder `pacman` (Arch Linux) und verwendet `pip` als Fallback. Hier ist der Installationsprozess im Detail:

### Systempakete
- **Termux**:
  - `termux-api`: Für Termux-spezifische Funktionen (z. B. Mikrofonzugriff).
  - `mpg123`: Für TTS-Audioausgabe.
  - `libportaudio2`: Für `PyAudio` (Mikrofon-Eingabe).
- **Arch Linux**:
  - `mpg123`: Für TTS-Audioausgabe.
  - `portaudio19-dev`: Für `PyAudio`.

**Manuelle Installation (falls notwendig)**:
- Termux:
  ```bash
  pkg update && pkg upgrade
  pkg install python termux-api mpg123 libportaudio2
  ```
- Arch Linux:
  ```bash
  sudo pacman -Syu
  sudo pacman -S python mpg123 portaudio19-dev
  ```

### Python-Pakete
- `requests`: Für API-Anfragen (z. B. OpenWeatherMap).
- `gTTS`: Für Text-to-Speech.
- `schedule`: Für Erinnerungsplanung.
- `speechrecognition`: Für einfache STT (Google Speech API).
- `PyAudio`: Für Mikrofonzugriff.
- `google-cloud-speech`: Für fortgeschrittene STT (optional).
- `discord.py`: Für Discord-Integration.

**Manuelle Installation (falls notwendig)**:
```bash
pip install requests gTTS schedule speechrecognition PyAudio google-cloud-speech discord.py
```

**Automatische Installation durch Bootloader**:
- Der Bootloader prüft, ob Pakete installiert sind (`check_command_exists` für Systempakete, `__import__` für Python-Pakete).
- Installiert Systempakete zuerst über `pkg` oder `pacman`.
- Fällt auf `pip` zurück, wenn ein Python-Paket fehlt.
- Protokolliert alle Installationsschritte in `~/pia-aktuelles_script_pia/logs/pia_boot_*.log`.

## 8. Discord-Bot vorbereiten
1. **Bot erstellen**:
   - Gehe zum [Discord Developer Portal](https://discord.com/developers/applications).
   - Erstelle eine neue Anwendung, füge einen Bot hinzu und kopiere den **Bot-Token**.
   - Aktiviere alle Intents unter **Bot > Privileged Gateway Intents**:
     - Presence Intent
     - Server Members Intent
     - Message Content Intent
   - Lade den Bot zu deinem Server ein:
     - Gehe zu **OAuth2 > URL Generator**, wähle `bot` und die Berechtigungen:
       - `Read Messages/View Channels`
       - `Send Messages`
       - `Manage Messages`
       - `Connect`
       - `Speak`
       - `Use Voice Activity`
     - Kopiere die generierte URL und öffne sie in einem Browser, um den Bot hinzuzufügen.

2. **Kanal-IDs holen**:
   - Aktiviere den Entwicklermodus in Discord (**Einstellungen > Darstellung > Entwicklermodus**).
   - Rechtsklicke auf den Textkanal und Sprachkanal, wähle **ID kopieren** und füge sie in `pia_config.json` ein.

3. **Berechtigungen prüfen**:
   - Stelle sicher, dass der Bot (`pia#7929`) im Textkanal (`1396263394926923846`) und Sprachkanal (`1396264734478565420`) die oben genannten Berechtigungen hat.

## 9. Projekt starten
1. **Beende laufende Instanzen**:
   ```bash
   pkill -f "python.*pia3_termux.py"
   pkill -f "python.*pia_bootloader.py"
   ```

2. **Starte den Bootloader**:
   ```bash
   cd ~/pia-aktuelles_script_pia
   python ./pia_bootloader.py
   ```

3. **Überprüfe die Logs**:
   - Bootloader-Logs:
     ```bash
     tail -f ~/pia-aktuelles_script_pia/logs/pia_boot_*.log
     ```
     Erwartete Ausgabe:
     ```
     2025-07-20 04:52:21 - INFO - Pia3 Bootloader gestartet
     2025-07-20 04:52:21 - INFO - Standard-Bootloader-Konfiguration unter ... erstellt
     2025-07-20 04:52:22 - INFO - Termux-Speicherberechtigungen gesichert
     2025-07-20 04:52:22 - INFO - Termux-Mikrofonberechtigungen gesichert
     2025-07-20 04:52:23 - INFO - Termux-Systempaket installiert: termux-api
     ...
     ```
   - Bot-Logs:
     ```bash
     tail -f ~/pia-aktuelles_script_pia/pia3_termux.log
     ```
     Erwartete Ausgabe:
     ```
     2025-07-20 04:52:25 - INFO - start_discord_bot: Discord-Bot verbunden als pia#7929
     2025-07-20 04:52:25 - INFO - Verbunden mit Voice Channel 1396264734478565420
     ```

## 10. Projekt nutzen
Sobald der Bot online ist, kannst du ihn in Discord testen.

### Textbefehle
- **Zeit anzeigen**:
  ```text
  !zeit
  ```
  Erwartete Antwort: „Die aktuelle Zeit ist 04:52“
- **Wetter abfragen**:
  ```text
  Hey Pia, wetter in Berlin
  ```
  Erwartete Antwort: „Wetter in Berlin: 20°C, klar“
- **Erinnerung hinzufügen**:
  ```text
  Hey Pia, erinnerung Arzttermin am 2025-07-20 10:00
  ```
  Erwartete Antwort: „Erinnerung hinzugefügt: Arzttermin“
- **Erinnerungen auflisten**:
  ```text
  Hey Pia, erinnerungen
  ```
  Erwartete Antwort: „1. Arzttermin (2025-07-20 10:00)“

### Sprachbefehle
- Verbinde dich mit dem Sprachkanal (`1396264734478565420`).
- Sprich: „Hey Pia, zeit“.
- Erwartete Antwort (gesprochen): „Die aktuelle Zeit ist 04:52“.
- Überprüfe die Logs auf STT-Erkennung:
  ```
  INFO - listen: Sprachbefehl erkannt: Hey Pia, zeit
  INFO - on_message: Wake-Word-Befehl verarbeitet: zeit, Antwort: Die aktuelle Zeit ist 04:52
  ```

## 11. Fehlerbehebung
### Bootloader startet nicht
- **Prüfe Python**:
  ```bash
  python --version
  ```
  Stelle sicher, dass Python 3.8+ installiert ist.
- **Überprüfe Logs**:
  ```bash
  cat ~/pia-aktuelles_script_pia/logs/pia_boot_*.log
  ```
  Suche nach Fehlern wie „FileNotFoundError“ oder „Permission denied“.

### Abhängigkeiten fehlen
- **Systempakete**:
  - Termux:
    ```bash
    pkg install libportaudio2
    ```
  - Arch Linux:
    ```bash
    sudo pacman -S portaudio19-dev
    ```
- **Python-Pakete**:
  ```bash
  pip install requests gTTS schedule speechrecognition PyAudio google-cloud-speech discord.py
  ```
- **Pip aktualisieren**:
  ```bash
  python -m pip install --upgrade pip
  ```

### Bot reagiert nicht
- **Berechtigungen**:
  - Überprüfe im Discord-Server, ob der Bot die Berechtigungen „Nachrichten lesen/senden“, „Verbinden“, „Sprechen“ hat.
- **Token und Intents**:
  - Verifiziere den Bot-Token in `pia_config.json`.
  - Stelle sicher, dass alle Intents im Discord Developer Portal aktiviert sind.
- **Debugging-Logs**:
  - Füge zusätzliche Logs in `pia3_termux.py` hinzu:
    ```python
    logging.debug("on_message: Empfangene Nachricht von %s in Kanal %s: %s", message.author, message.channel.id, message.content)
    ```
  - Überprüfe:
    ```bash
    tail -f ~/pia-aktuelles_script_pia/pia3_termux.log
    ```

### STT funktioniert nicht
- **Teste Mikrofon**:
  ```bash
  termux-microphone-record -l 10 -f test.wav
  termux-media-player play test.wav
  ```
- **Prüfe Abhängigkeiten**:
  ```bash
  python -c "import speech_recognition; print('speech_recognition OK')"
  python -c "import pyaudio; print('PyAudio OK')"
  ```
- **Google Cloud Speech**:
  - Stelle sicher, dass der API-Schlüssel in `pia_config.json` korrekt ist.
  - Teste mit:
    ```bash
    termux-microphone-record -l 10 -f test.wav
    python -c "from pia3_termux import test_google_speech; test_google_speech()"
    ```

## 12. Erweiterte STT-Integration
Für präzisere Spracherkennung kannst du Google Cloud Speech verwenden:
1. **API-Schlüssel erstellen**:
   - Gehe zur [Google Cloud Console](https://console.cloud.google.com).
   - Erstelle ein Projekt, aktiviere die Speech-to-Text API und generiere einen API-Schlüssel.
   - Speichere den Schlüssel in `pia_config.json` und `pia_bootloader_config.json`.
2. **Teste STT**:
   ```python
   def test_google_speech():
       from google.cloud import speech
       client = speech.SpeechClient.from_service_account_json(CONFIG.get("google_speech_api_key"))
       with open("test.wav", "rb") as audio_file:
           content = audio_file.read()
       audio = speech.RecognitionAudio(content=content)
       config = speech.RecognitionConfig(
           encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
           sample_rate_hertz=16000,
           language_code="de-DE"
       )
       response = client.recognize(config=config, audio=audio)
       for result in response.results:
           print(f"Erkannt: {result.alternatives[0].transcript}")
   ```
   ```bash
   termux-microphone-record -l 10 -f test.wav
   python -c "from pia3_termux import test_google_speech; test_google_speech()"
   ```

## 13. Wartung und Updates
- **Logs überwachen**:
  ```bash
  tail -f ~/pia-aktuelles_script_pia/pia3_termux.log
  tail -f ~/pia-aktuelles_script_pia/logs/pia_boot_*.log
  ```
- **Abhängigkeiten aktualisieren**:
  ```bash
  pkg update && pkg upgrade  # Termux
  sudo pacman -Syu  # Arch Linux
  pip install --upgrade requests gTTS schedule speechrecognition PyAudio google-cloud-speech discord.py
  ```
- **Bot neustarten**:
  ```bash
  pkill -f "python.*pia3_termux.py"
  pkill -f "python.*pia_bootloader.py"
  python ~/pia-aktuelles_script_pia/pia_bootloader.py
  ```

## 14. Zusammenfassung
Das Pia3-Projekt bietet einen vielseitigen Discord-Bot mit STT/TTS, Wetterabfragen und Erinnerungsfunktionen. Der Bootloader automatisiert die Einrichtung und Installation, während das Haupt-Skript die Bot-Logik bereitstellt. Mit dieser Anleitung solltest du in der Lage sein, das Projekt in Termux oder Arch Linux einzurichten, zu konfigurieren und zu nutzen. Für weitere Fragen oder Anpassungen, kontaktiere den Support oder überprüfe die Logs für detaillierte Fehlerinformationen.