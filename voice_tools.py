# voice_tools.py – Faster-Whisper + Wake-Word "hey pia"
import os
import time
import threading
import queue
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from utils import BASE_DIR, logging, sprich

WAKE_WORD = "hey pia"
MODEL_SIZE = "large-v3-turbo"           # Alternativen: "distil-large-v3", "base", "small"
DEVICE = "cuda" if os.path.exists("/dev/nvidia0") else "cpu"
COMPUTE_TYPE = "int8" if "cuda" in DEVICE else "default"

print(f"[STT] Lade Faster-Whisper {MODEL_SIZE}  device={DEVICE}  type={COMPUTE_TYPE}")

model = WhisperModel(
    MODEL_SIZE,
    device=DEVICE,
    compute_type=COMPUTE_TYPE,
    cpu_threads=8,                      # Ryzen 5600X → 8 Threads sinnvoll
    num_workers=4
)

audio_queue = queue.Queue(maxsize=30)

def audio_callback(indata, frames, time_info, status):
    if status:
        logging.warning(f"Audio-Status: {status}")
    audio_queue.put(indata.copy())

def sprachmodus():
    sprich("Hey-Pia-Modus ist jetzt aktiv. Sag einfach 'Hey Pia' und dann deinen Befehl.")
    print("[Sprachmodus] Mikrofon wird gestartet – sag 'Hey Pia ...'")

    def listener_loop():
        with sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype='float32',
            blocksize=8000,
            callback=audio_callback
        ) as stream:
            print("[STT] Mikrofon-Stream läuft")
            buffer = np.array([], dtype=np.float32)

            while True:
                try:
                    chunk = audio_queue.get(timeout=1.5)
                    buffer = np.concatenate((buffer, chunk.flatten()))

                    # Buffer nicht endlos wachsen lassen
                    if len(buffer) > 16000 * 10:
                        buffer = buffer[-16000*10:]

                    segments, info = model.transcribe(
                        buffer,
                        language="de",
                        vad_filter=True,
                        vad_parameters=dict(
                            min_silence_duration_ms=400,
                            max_speech_duration_s=12
                        )
                    )

                    text = " ".join(s.text.strip() for s in segments if s.text.strip()).lower().strip()

                    if text and WAKE_WORD in text:
                        kommando = text.split(WAKE_WORD, 1)[-1].strip()
                        if kommando:
                            print(f"[Wake] Erkannt: '{kommando}'")
                            from assistant_core import befehl_verarbeiten
                            antwort = befehl_verarbeiten(kommando)
                            sprich(antwort)
                        buffer = np.array([], dtype=np.float32)  # Buffer zurücksetzen

                except queue.Empty:
                    continue
                except Exception as e:
                    logging.error(f"STT Loop Fehler: {e}", exc_info=True)

    t = threading.Thread(target=listener_loop, daemon=True)
    t.start()
    print("[Sprachmodus] Hintergrund-Thread gestartet. Ctrl+C zum Beenden.")

def tools_holen():
    return [
        ("sprachmodus", sprachmodus, "Sprache / Wake-Word"),
    ]