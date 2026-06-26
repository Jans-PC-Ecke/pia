import ollama
from utils import sprich, logging

# ============== KONFIGURATION ==============
# Gute Modelle 2026 (schnell + gut auf Deutsch):
# "llama3.2:3b"     → sehr schnell, empfohlen für den Anfang
# "gemma2:9b"       → besser in Qualität
# "qwen2.5:7b"      → stark multilingual
OLLAMA_MODEL = "llama3.2:3b"

OLLAMA_HOST = "http://localhost:11434"
# ===========================================

def ollama_antwort(befehl: str, system_prompt: str = None) -> str:
    """Ruft Ollama auf und gibt die Antwort zurück"""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": befehl})

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={
                "temperature": 0.75,
                "num_ctx": 8192,
                "num_predict": 512,
            }
        )

        antwort = response['message']['content'].strip()

        # Kurze Sprachausgabe (nicht zu lang)
        if len(antwort) > 280:
            sprich(antwort[:280] + " …")
        else:
            sprich(antwort)

        return antwort

    except Exception as e:
        logging.error(f"Ollama Fehler: {e}", exc_info=True)
        sprich("Ollama antwortet gerade nicht.")
        return "Entschuldige Jan, Ollama ist momentan nicht erreichbar."


def tools_holen():
    return [
        ("ollama_antwort", ollama_antwort, "LLM / Ollama"),
    ]