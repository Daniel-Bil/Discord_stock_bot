
class ESPITracker:
    """Handles ESPI tracking for Polish stocks and generates company emojis using GPT."""

    def __init__(self):
        self.pinned_stocks = self.load_json(PINNED_STOCKS_FILE)  # {"url": {"name": "Company", "emoji": "🚀"}}
        self.espi_history = self.load_json(ESPI_HISTORY_FILE)  # {"url": ["Known ESPI Titles"]}

    def load_json(self, file):
        """Load JSON data from a file."""
        if os.path.exists(file):
            with open(file, "r") as f:
                return json.load(f)
        return {}

    def save_json(self, file, data):
        """Save JSON data to a file."""
        with open(file, "w") as f:
            json.dump(data, f, indent=4)

    def get_company_name(self, url):
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
                first_row = tbody.find("tr")
                if first_row:
                    cols = first_row.find_all("td")
                    if len(cols) >= 4:
                        return cols[2].text.strip()
        return None

    def get_latest_espi(self, url):
        """Fetches the latest ESPI announcement."""
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")

        if table:
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                if rows:
                    cols = rows[0].find_all("td")
                    if len(cols) >= 4:
                        return {
                            "date": cols[0].text.strip(),
                            "time": cols[1].text.strip(),
                            "company": cols[2].text.strip(),
                            "title": cols[3].text.strip()
                        }
        return None

    def get_company_emoji(self, company_name):
        """Generates a single emoji based on the company name using GPT."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI that provides a single emoji representing a company."},
                    {"role": "user", "content": f"Give me a single emoji that represents the company {company_name}."}
                ],
                max_tokens=10
            )
            emoji = response["choices"][0]["message"]["content"].strip()
            return emoji if emoji else "🏢"  # Default emoji if GPT fails
        except Exception as e:
            print(f"Error fetching emoji: {e}")
            return "🏢"  # Default emoji if API fails

    async def check_espi_updates(self):
        """Checks for new ESPI announcements and sends updates to Discord."""
        if not self.pinned_stocks:
            return  # No tracked companies

        channel = discord.utils.get(bot.get_all_channels(), name=PL_STOCKS_CHANNEL)
        if not channel:
            print(f"Channel {PL_STOCKS_CHANNEL} not found.")
            return

        for url, company_data in self.pinned_stocks.items():
            latest_espi = self.get_latest_espi(url)
            if not latest_espi:
                continue  # Skip if failed to fetch data

            last_known_espies = self.espi_history.get(url, [])

            if latest_espi["title"] not in last_known_espies:
                self.espi_history.setdefault(url, []).append(latest_espi["title"])
                self.save_json(ESPI_HISTORY_FILE, self.espi_history)

                await channel.send(
                    f"📢 **New ESPI Announcement for {company_data['name']} {company_data['emoji']}!**\n"
                    f"🕒 {latest_espi['date']} {latest_espi['time']}\n"
                    f"📌 **{latest_espi['title']}**\n🔗 [View on ESPI]({url})"
                )

    async def add_stock(self, ctx, url):
        """Adds a company to track ESPI announcements and generates an emoji."""
        if ctx.channel.name != PL_STOCKS_CHANNEL:
            await ctx.send(f"This command can only be used in {PL_STOCKS_CHANNEL}.")
            return

        company_name = self.get_company_name(url)
        if not company_name:
            await ctx.send("Invalid URL or failed to fetch company name.")
            return

        emoji = self.get_company_emoji(company_name)

        self.pinned_stocks[url] = {"name": company_name, "emoji": emoji}
        self.save_json(PINNED_STOCKS_FILE, self.pinned_stocks)

        await ctx.send(f"Now tracking ESPI announcements for **{company_name}** {emoji}.")

    async def remove_stock(self, ctx, url):
        """Stops tracking a company for ESPI updates."""
        if url in self.pinned_stocks:
            del self.pinned_stocks[url]
            self.save_json(PINNED_STOCKS_FILE, self.pinned_stocks)

            await ctx.send(f"Stopped tracking ESPI announcements for {url}.")
        else:
            await ctx.send("This company is not being tracked.")

    async def list_stocks(self, ctx):
        """Lists all currently tracked ESPI companies."""
        if not self.pinned_stocks:
            await ctx.send("No companies are currently being tracked.")
            return

        message = "**Currently tracked ESPI companies:**\n"
        for url, data in self.pinned_stocks.items():
            message += f"📌 {data['name']} {data['emoji']} - [ESPI Link]({url})\n"

        await ctx.send(message)