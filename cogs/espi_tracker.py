from discord.ext import commands, tasks
import discord
import json
from pathlib import Path
from utils.utils import get_company_name, inform_new_espies, decode_to_number, get_espi_announcements
from openai import OpenAI
from colorama import Fore
from decouple import config
from datetime import datetime

CHECK_INTERVAL = 60
PL_STOCKS_CHANNEL = "⌊🌍⌉-czat-polska"
ESPI_HISTORY_FILE = "espi_history.json"
PINNED_STOCKS_FILE = "pinned_stocks.json"

STOCK_ID_FILE = Path("decoders") / "stock_id.json"
SYMBOL_TO_ID_FILE = Path("decoders") / "symbol_to_id.json"
TICKER_TO_ID_FILE = Path("decoders") / "ticker_to_id.json"

class ESPITracker(commands.Cog):
    """Handles ESPI tracking for Polish stocks and generates company emojis using GPT."""

    def __init__(self, bot):
        self.bot = bot
        self.client = OpenAI(api_key=config("OPENAI_API_KEY"))
        self.pinned_stocks = self.load_json(PINNED_STOCKS_FILE)
        self.espi_history = self.load_json(ESPI_HISTORY_FILE)

        self.stock_id = self.load_json(STOCK_ID_FILE)
        self.symbol_to_id = self.load_json(SYMBOL_TO_ID_FILE)
        self.ticker_to_id = self.load_json(TICKER_TO_ID_FILE)

        self.check_espi.start()
        print("check_espi loop started")

    def load_json(self, file):
        """Load JSON data from a file."""
        if Path(file).exists():
            with open(file, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: {file} is corrupted or empty. Resetting data.")
                    return {}  # Return an empty dictionary if JSON is invalid
        return {}

    def save_json(self, file, data):
        """Save JSON data to a file."""
        with open(file, "w") as f:
            json.dump(data, f, indent=4)


    def get_company_emoji(self, company_name):
        """Generates a single emoji based on the company name using GPT."""
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                store=True,
                messages=[
                    {"role": "user", "content": f"Give me a single emoji that represents the company {company_name}. If you don't know return random emoji"}
                ]
            )
            return completion.choices[0].message.content or "🏢"
        except Exception as e:
            return "🏢"  # Default emoji if API fails

    async def _remove_stock(self, ctx, number: str):
        """Stops tracking a company for ESPI updates and unpins any pinned messages."""
        if number not in self.pinned_stocks:
            await ctx.send("This company is not being tracked.")
            return

        company_data = self.pinned_stocks[number]
        company_name = company_data["name"]
        channel = discord.utils.get(ctx.guild.channels, name=PL_STOCKS_CHANNEL)

        # Unpin any pinned messages
        for msg in company_data.get("messages", []):
            if msg.get("pinned") and "id" in msg:
                try:
                    message = await channel.fetch_message(msg["id"])
                    await message.unpin()
                except discord.NotFound:
                    print(f"Message ID {msg['id']} not found in Discord.")
                except discord.Forbidden:
                    print("Bot does not have permission to unpin messages.")
                except discord.HTTPException as e:
                    print(f"Error unpinning message: {e}")

        # Remove company from memory and persist
        del self.pinned_stocks[number]
        self.espi_history.pop(number, None)

        self.save_json(PINNED_STOCKS_FILE, self.pinned_stocks)
        self.save_json(ESPI_HISTORY_FILE, self.espi_history)

        await ctx.send(f"Stopped tracking ESPI announcements for **{company_name}**.")

    async def _add_company_to_dict(self, ctx, number: str) -> None:
        """Adds a company to track ESPI announcements and generates an emoji."""
        if ctx.channel.name != PL_STOCKS_CHANNEL:
            await ctx.send(f"This command can only be used in {PL_STOCKS_CHANNEL}.")
            return

        url = f"https://biznes.pap.pl/espi/espi/{datetime.now().year}?company={number}&selectCompany={number}"  # build the actual URL

        company_name = get_company_name(url)
        if not company_name:
            await ctx.send("Invalid URL or failed to fetch company name.")
            return

        emoji = self.get_company_emoji(company_name)

        self.pinned_stocks[number] = {"name": company_name, "emoji": emoji, "url": url, "messages": []}
        self.espi_history[number] = get_espi_announcements(url)

        await ctx.send(f"Now tracking ESPI announcements for **{company_name}** {emoji}.")
        message = await ctx.send(f"{company_name} {emoji}")
        await message.pin()

        self.pinned_stocks[number]["messages"].append({"content": message.content, "id": message.id, "pinned": True})

        self.save_json(PINNED_STOCKS_FILE, self.pinned_stocks)
        self.save_json(ESPI_HISTORY_FILE, self.espi_history)

    @commands.command()
    async def add(self, ctx, input_str):
        try:
            number = decode_to_number(input_str, self.ticker_to_id, self.symbol_to_id, self.stock_id)
            await self._add_company_to_dict(ctx, number)
        except ValueError as e:
            await ctx.send(str(e))

    @commands.command()
    async def remove(self, ctx, input_str):
        try:
            number = decode_to_number(
                input_str,
                self.ticker_to_id,
                self.symbol_to_id,
                self.stock_id
            )
            await self._remove_stock(ctx, number)
        except ValueError as e:
            await ctx.send(str(e))

    @tasks.loop(seconds=CHECK_INTERVAL)
    async def check_espi(self):
        """Checks for new ESPI announcements and sends updates to Discord."""
        print(f"{Fore.LIGHTBLUE_EX}Checking ESPI updates... {datetime.now().strftime('%c')}{Fore.RESET}")

        if not self.pinned_stocks:
            print("No tracked companies")
            return

        channel = discord.utils.get(self.bot.get_all_channels(), name=PL_STOCKS_CHANNEL)
        if not channel:
            print(f"Channel {PL_STOCKS_CHANNEL} not found.")
            return

        for number, company_data in list(self.pinned_stocks.items()):
            try:
                url = company_data["url"]
                new_espies = inform_new_espies(url, company_espi_history=self.espi_history[number])

                if not new_espies:
                    print(f"No new ESPI reports for {company_data['name']}")
                    continue




                for espi in new_espies:
                    self.espi_history[number].append(espi)
                    message = await channel.send(
                        f"📢 **{company_data['name']} {company_data['emoji']}**\n"
                        f"🕒 {espi['date']} {espi['time']}\n"
                        f"📌 **{espi['title']}**\n🔗 [View on ESPI]({url})"
                    )
                    self.pinned_stocks[number]["messages"].append({"content": message.content, "id": message.id, "pinned": False})
                print(f"{Fore.GREEN}New ESPIs sent for {company_data['name']}{Fore.RESET}")
                self.save_json(PINNED_STOCKS_FILE, self.pinned_stocks)
                self.save_json(ESPI_HISTORY_FILE, self.espi_history)
            except Exception as e:
                print(f"Error while checking {company_data['name']}: {e}")

    @check_espi.before_loop
    async def before_check_espi(self):
        print("⏳ Waiting for bot to be ready before starting check_espi...")
        await self.bot.wait_until_ready()