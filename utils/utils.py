import requests
from bs4 import BeautifulSoup


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

                    announcements.append({
                        "date": date,
                        "time": time,
                        "company": company,
                        "title": title
                    })
    return announcements


def inform_new_espies(url, espi_history):
    """Checks for new ESPIs and informs only about new ones."""
    new_announcements = get_espi_announcements(url)

    if url not in espi_history:
        espi_history[url] = []  # Initialize storage for this company's ESPIs

    new_espies = []

    for announcement in new_announcements:
        if announcement["title"] not in espi_history[url]:  # Check if it's new
            new_espies.append(announcement)
            espi_history[url].append(announcement["title"])  # Store it as known

    return new_espies, espi_history  # Return only new ESPIs



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


