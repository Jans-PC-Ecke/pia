# web_search_tools.py – sehr einfache Textsuche (DuckDuckGo oder Google via requests)

import requests
from bs4 import BeautifulSoup
from utils import logging, sprich

def web_suche(suchbegriff: str, anzahl: int = 5):
    suchbegriff = suchbegriff.strip()
    if not suchbegriff:
        return "Kein Suchbegriff angegeben."

    # DuckDuckGo HTML (einfacher, weniger JS)
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(suchbegriff)}"

    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; Pia4/1.0)"}
        r = requests.get(url, headers=headers, timeout=12)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        ergebnisse = []

        for result in soup.select(".result")[:anzahl]:
            titel = result.select_one(".result__title") or ""
            link = result.select_one(".result__url") or ""
            snippet = result.select_one(".result__snippet") or ""

            titel_text = titel.get_text(strip=True) if titel else "[kein Titel]"
            link_text = link.get("href", "") if link else ""
            snippet_text = snippet.get_text(strip=True) if snippet else ""

            ergebnisse.append(f"• {titel_text}\n  {link_text}\n  {snippet_text[:180]}…")

        if not ergebnisse:
            return "Keine brauchbaren Ergebnisse gefunden."

        text = f"Top {len(ergebnisse)} Ergebnisse für „{suchbegriff}“:\n\n"
        text += "\n\n".join(ergebnisse)

        sprich(f"Hier sind die wichtigsten Ergebnisse zu {suchbegriff}.")
        return text

    except Exception as e:
        logging.error(f"Web-Suche fehlgeschlagen: {e}")
        return "Internetsuche gerade nicht möglich."

def tools_holen():
    return [
        ("web_suche", web_suche, "Internet-Suche"),
    ]