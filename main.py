from pathlib import Path
import discord
from colorama import Fore
from discord.ext import commands, tasks
import json
from decouple import config

from openai import OpenAI

from utils.utils import get_company_name, inform_new_espies

TOKEN = config('DISCORD_TOKEN')
GUILD = config('DISCORD_GUILD')
OPENAI_API_KEY = config("OPENAI_API_KEY")

PL_STOCKS_CHANNEL = "⌊🌍⌉-czat-polska"
# PL_STOCKS_CHANNEL = "stock"
CHECK_INTERVAL = 60  # Every 10 s
ESPI_HISTORY_FILE = "espi_history.json"
PINNED_STOCKS_FILE = "pinned_stocks.json"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

client = OpenAI(
  api_key=OPENAI_API_KEY
)

class ESPITracker:
    """Handles ESPI tracking for Polish stocks and generates company emojis using GPT."""

    def __init__(self):
        self.pinned_stocks = self.load_json(PINNED_STOCKS_FILE)  # {"url": {"name": "Company", "emoji": "🚀"}}
        self.espi_history = self.load_json(ESPI_HISTORY_FILE)  # {"url": ["Known ESPI Titles"]}

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
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                store=True,
                messages=[
                    {"role": "user", "content": f"Give me a single emoji that represents the company {company_name}."}
                ]
            )
            emoji = completion.choices[0].message.content
            return emoji if emoji else "🏢"  # Default emoji if GPT fails
        except Exception as e:
            print(f"Error fetching emoji: {e}")
            return "🏢"  # Default emoji if API fails

    async def check_espi_updates(self):
        """Checks for new ESPI announcements and sends updates to Discord."""
        print(f"{Fore.LIGHTBLUE_EX}Checking ESPI updates...{Fore.RESET}")

        if not self.pinned_stocks:
            print("No tracked companies")
            return  # No tracked companies

        channel = discord.utils.get(bot.get_all_channels(), name=PL_STOCKS_CHANNEL)
        if not channel:
            print(f"Channel {PL_STOCKS_CHANNEL} not found.")
            return

        for url, company_data in self.pinned_stocks.items():
            new_espies, history = inform_new_espies(url, espi_history=self.espi_history)  # Get only new ESPIs
            self.save_json(ESPI_HISTORY_FILE, history)

            if not new_espies:
                print(f"No new ESPI reports for {company_data['name']}")
                continue  # No new announcements

            for espi in new_espies:
                await channel.send(
                    f"📢 **New ESPI Announcement for {company_data['name']} {company_data['emoji']}!**\n"
                    f"🕒 {espi['date']} {espi['time']}\n"
                    f"📌 **{espi['title']}**\n🔗 [View on ESPI]({url})"
                )

            print(f"{Fore.GREEN}New ESPIs sent for {company_data['name']}{Fore.RESET}")

    async def add_stock(self, ctx, url):
        """Adds a company to track ESPI announcements and generates an emoji."""
        if ctx.channel.name != PL_STOCKS_CHANNEL:
            await ctx.send(f"This command can only be used in {PL_STOCKS_CHANNEL}.")
            return

        company_name = get_company_name(url)
        if not company_name:
            await ctx.send("Invalid URL or failed to fetch company name.")
            return

        emoji = self.get_company_emoji(company_name)

        self.pinned_stocks[url] = {"name": company_name, "emoji": emoji}
        self.save_json(PINNED_STOCKS_FILE, self.pinned_stocks)

        await ctx.send(f"Now tracking ESPI announcements for **{company_name}** {emoji}.")
        message = await ctx.send(f"{company_name} {emoji}\n")
        self.pinned_stocks[url]["message"] = {"content": message.content, "id": message.id}
        await message.pin()

    async def remove_stock(self, ctx, url):
        """Stops tracking a company for ESPI updates."""
        if url in self.pinned_stocks:
            company = self.pinned_stocks[url]["name"]
            channel = discord.utils.get(ctx.guild.channels, name=PL_STOCKS_CHANNEL)

            # Check if the pinned message exists before trying to unpin
            if "message" in self.pinned_stocks[url]:
                try:
                    message_id = self.pinned_stocks[url]["message"]["id"]
                    message = await channel.fetch_message(message_id)
                    await message.unpin()
                except discord.NotFound:
                    print(f"Message ID {message_id} not found in Discord. It may have been deleted manually.")
                except discord.Forbidden:
                    print("Bot does not have permission to unpin messages.")
                except discord.HTTPException as e:
                    print(f"Error fetching/unpinning message: {e}")

            # Remove the stock from tracking
            del self.pinned_stocks[url]
            self.save_json(PINNED_STOCKS_FILE, self.pinned_stocks)

            await ctx.send(f"Stopped tracking ESPI announcements for {company}\n{url}.")
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





@bot.command()
async def add(ctx, url):
    await espi_tracker.add_stock(ctx, url)

@bot.command()
async def remove(ctx, url):
    await espi_tracker.remove_stock(ctx, url)

@bot.command()
async def list(ctx):
    await espi_tracker.list_stocks(ctx)

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_espi():
    await espi_tracker.check_espi_updates()

@bot.event
async def on_ready():
    """Starts the ESPI checking loop when the bot is ready."""
    print(f"Logged in as {bot.user}")
    check_espi.start()

if __name__ == "__main__":
    # Initialize ESPI tracker
    espi_tracker = ESPITracker()

    bot.run(TOKEN)
