import discord
import asyncio

from discord.ext import commands
from decouple import config

from cogs.espi_tracker import ESPITracker

# Bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is ready and logged in as: {bot.user}")

async def setup():
    # Load the ESPITracker cog
    print("setup")
    await bot.add_cog(ESPITracker(bot))

if __name__ == "__main__":
    TOKEN = config("DISCORD_TOKEN")

    asyncio.run(setup())
    bot.run(TOKEN)
