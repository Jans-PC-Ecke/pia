from utils import system_befehl, sprich, logging

def email_vorbereiten(an: str = "", betreff: str = "", text: str = ""):
    """
    Öffnet Thunderbird mit vorausgefülltem Composer
    """
    try:
        cmd_parts = []
        if an:
            cmd_parts.append(f"to={an}")
        if betreff:
            cmd_parts.append(f"subject={betreff}")
        if text:
            # Body escapen – einfache Variante
            body = text.replace('"', '\\"').replace("\n", "%0A")
            cmd_parts.append(f"body={body}")

        if cmd_parts:
            compose_str = ",".join(cmd_parts)
            cmd = f'thunderbird -compose "{compose_str}"'
        else:
            cmd = "thunderbird"

        system_befehl(cmd)
        sprich("E-Mail-Fenster in Thunderbird geöffnet.")
        return "Thunderbird Composer geöffnet"

    except Exception as e:
        logging.error(f"Thunderbird Fehler: {e}")
        sprich("Konnte Thunderbird nicht öffnen.")
        return "Fehler beim Öffnen von Thunderbird."


def tools_holen():
    return [
        ("email_vorbereiten", email_vorbereiten, "E-Mail / Thunderbird"),
    ]