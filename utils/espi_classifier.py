from enum import Enum

import requests
from bs4 import BeautifulSoup


class ESPIType(Enum):
    RESULTS = "📊 Wyniki finansowe"
    SHARES = "📈 Operacja na akcjach"
    GENERAL = "ℹ️ Informacja"

def classify_espi_type(title: str) -> ESPIType:
    if "raport okresowy" in title:
        return ESPIType.RESULTS

    if ("Zawiadomienia w trybie art. 19 ust. 1 rozporządzenia MAR".lower() in title) or ("Zbycie akcji".lower() in title):
        return ESPIType.SHARES

    return ESPIType.GENERAL

def handle_new_espi(espi:dict):
    espi_type = classify_espi_type(espi["title"])

    if espi_type == ESPIType.RESULTS:
        return handle_results_espi(f"https://biznes.pap.pl/{espi['url']}")

    if espi_type == ESPIType.SHARES:
        return f"https://biznes.pap.pl/{espi['url']}\n"+handle_general_espi(f"https://biznes.pap.pl/{espi['url']}")

    if espi_type == ESPIType.GENERAL:
        return handle_general_espi(f"https://biznes.pap.pl/{espi['url']}")





def handle_results_espi(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")

    results = []
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]

        results.append(cols)

    r = ""
    for t in results:
        r = r + str(t) + "\n"

    return r


def handle_shares_espi(url):
    raise NotImplementedError

def handle_general_espi(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    article = soup.find("article")
    paragraphs = article.find_all("p")[:-3]

    text = "\n\n".join(p.get_text(strip=True) for p in paragraphs)

    return text

if __name__ == "__main__":
    text = handle_general_espi("https://biznes.pap.pl/wiadomosci/firmy/11-bit-studios-sa-62020-zbycie-akcji-przez-osobe-zarzadzajaca")
    print(text)

    text = handle_results_espi(
        "https://biznes.pap.pl/wiadomosci/firmy/11-bit-studios-sa-raport-okresowy-roczny-rr-2")

    print(text)