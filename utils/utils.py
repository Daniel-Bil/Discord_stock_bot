import numpy as np
import requests
from bs4 import BeautifulSoup

import camelot.io as camelot
from rapidfuzz import fuzz, process


def get_espi_announcements(url):
    """Fetches all ESPI announcements for a company from Biznes PAP."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error during request")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    announcements = []

    if table:
        tbody = table.find("tbody")
        if tbody:
            rows = tbody.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    date = cols[0].text.strip()
                    time = cols[1].text.strip()
                    company = cols[2].text.strip()
                    title = cols[3].text.strip()

                    next_url = cols[3].find('a')["href"]
                    announcements.append({
                        "date": date,
                        "time": time,
                        "company": company,
                        "title": title,
                        "url": next_url
                    })
    return announcements


def inform_new_espies(url, company_espi_history):
    """Checks for new ESPIs and informs only about new ones."""
    new_announcements = get_espi_announcements(url)

    new_espies = []

    for announcement in new_announcements:
        if announcement not in company_espi_history:  # Check if it's new
            new_espies.append(announcement)

    return new_espies



def get_company_name(url):
    """Extracts the company name from the ESPI page."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if table:
        tbody = table.find("tbody")
        if tbody:
            second_row = tbody.find_all("tr")[1]
            if second_row:
                cols = second_row.find_all("td")
                if len(cols) >= 4:
                    company_name_col = cols[2]
                    a_tag = company_name_col.find("a")
                    return a_tag.text.strip()  # Extract company name
    return None

def get_espi_article(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    article = soup.find("article")
    title = article.find_all("p", class_="field--name-field-lead")[0].text.strip()
    print(title)
    data = None

    if "Raport okresowy roczny RR" in title:
        print("Raport okresowy roczny RR")
        data = get_periodic_results_data(article)
    elif "Raport okresowy roczny skonsolidowany SRR" in title:
        print("Raport okresowy roczny skonsolidowany SRR")
        print("jeszcze nie obslugiwany")
    elif "Raport okresowy kwartalny" in title:
        print("Raport okresowy kwartalny")
        print("jeszcze nie obslugiwany")
        get_periodic_results_data(article)
    elif "Raport bieżący" in title:
        if "z plikiem" in title:
            print("Raport bieżący z plikiem")
            data = get_current_report_with_file(article)
        else:
            print("Raport bieżący")
            data = get_current_report(article)
    else:
        print(f"inny typ tytułu {title}")

    print(data)

def get_periodic_results_data(article):
    table = article.find("table")

    message = ""
    if table:
        tbody = table.find("tbody")
        if tbody is None:
            rows = table.find_all("tr")
        else:
            rows = tbody.find_all("tr")

        for row in rows:
            section = row.find_all("td")
            message_row = ""
            for idx, element in enumerate(section):
                if idx == 0:
                    message_row += f"{element.text.strip():<20}"
                else:
                    message_row += f"{element.text.strip():^20}"

            message += message_row + "\n"
    print(message)

def get_current_report(article):
    pass

def get_current_report_with_file(article):
    pass


def espi_message(company_data,espi,url,data):
    message = f"📢 **{company_data['name']} {company_data['emoji']}**\n"+\
              f"🕒 {espi['date']} {espi['time']}\n"+\
              f"📌 **{espi['title']}**\n🔗 [View on ESPI]({url})"

    return message


def parse_transaction_info2(pdf):
    row_keys = ["Stanowisko/status", "Rodzaj transakcji"]
    raw_data = pdf._tables[0].data
    data = {"position": np.nan, "incentive": np.nan, "transaction_mode": np.nan}
    if len(raw_data)<13:
        print("shorter file")
        return {"position": "shorter", "incentive": "shorter", "transaction_mode": "shorter"}
    for key in row_keys:
        print(key)
        for idx, row in enumerate(raw_data):
            print(row)
            if key == "Stanowisko/status":
                if np.any(np.array([key in e for e in row])):
                    if np.any(np.array(["Członek Zarządu" in e for e in row])):
                        data["position"] = "Członek Zarządu"
                    elif np.any(np.array(["Prezes" in e for e in row])):
                        data["position"] = "Prezes"
                    elif np.any(np.array(["Wiceprezes" in e for e in row])):
                        data["position"] = "Wiceprezes"
                    else:
                        data["position"] = "Unknown"

            if key == "Rodzaj transakcji":
                incentive = None
                if np.any(np.array([key in e for e in row])):
                    if np.any(np.array(["Nabycie" in e for e in row])) or np.any(np.array(["purchase" in e for e in row])) or np.any(np.array(["Kupno" in e for e in row])) or np.any(np.array(["objęcie" in e for e in row])):
                        transaction_mode = "purchase"
                        if np.any(np.array(["motywacyjnego" in e for e in row])):
                            print("Nabycie w ramach programu motywacyjnego")
                            incentive = True
                        else:
                            print("Nabycie")
                            incentive = False
                    else:
                        transaction_mode = "disposal"
                        print("zbycie")

                    data["incentive"] = incentive
                    data["transaction_mode"] = transaction_mode
    return data

def read_pdf_and_parse(pdf_file):
    abc = camelot.read_pdf(pdf_file, pages="all", flavor='lattice')  # address of pdf file
    if len(abc) == 0:
        return {"position": np.nan, "incentive": np.nan, "transaction_mode": np.nan}
    data = parse_transaction_info2(abc)
    return data

def get_article_and_return_pdf(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    data = []

    for link in soup.find_all("a", href=True):
        if ".pdf" in link["href"]:
            print("Found PDF:", link["href"])
            print(link.text.strip())
            data.append([link["href"],link.text.strip()])
    return data

def decode_to_number(input_str: str, ticker_to_number: dict, symbol_to_number: dict, stock_id: dict) -> str:
    # 1. Direct number
    if input_str.isdigit() and input_str in stock_id:
        return input_str

    # 2. Ticker
    if input_str.upper() in ticker_to_number:
        return ticker_to_number[input_str.upper()]

    # 3. Short name
    if input_str.upper() in symbol_to_number:
        return symbol_to_number[input_str.upper()]

    # 4. Full name fuzzy match
    reversed_map = {v: k for k, v in stock_id.items()}

    for name in reversed_map:
        if input_str.lower() == name.lower():
            return reversed_map[name]

    matches = process.extract(
        input_str.lower(),
        [name.lower() for name in reversed_map.keys()],
        scorer=fuzz.ratio,
        score_cutoff=90
    )

    if len(matches) == 1:
        match_name = matches[0][0]
        print(match_name)
        for key in reversed_map:
            if key.lower() == match_name:
                return reversed_map[key]


    elif len(matches) > 1:
        options = [match[0] for match in matches]
        print(options)
        raise ValueError(f"Ambiguous company name. Did you mean: {', '.join(options)}?")

    else:
        raise ValueError("Unrecognized company identifier.")
