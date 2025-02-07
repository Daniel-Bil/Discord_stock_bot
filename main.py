from decouple import config
import discord
from discord.ext import commands
import yfinance as yf
import matplotlib


if __name__ == "__main__":
	TOKEN = config('DISCORD_TOKEN')
	GUILD = config('DISCORD_GUILD')

	STOCK_CHANNEL_NAME = "stock"

	intents = discord.Intents.default()
	intents.messages = True
	intents.message_content = True  # Ensure this is enabled
	intents.guilds = True
	intents.presences = True
	intents.members = True  # Required for server members access

	bot = commands.Bot(command_prefix="!", intents=intents)


	@bot.event
	async def on_ready():
		print(f"Logged in as {bot.user}")
		for guild in bot.guilds:
			print(f"{guild.name}")
			if guild.name == GUILD:
				break


	@bot.command()
	async def hello(ctx):
		await ctx.send("Hello! I'm your Discord bot. 🤖")


	@bot.event
	async def on_message(message):
		print(message)
		if message.author == bot.user:  # Ignore bot's own messages
			return

		stock_symbol = message.content.upper()  # Convert message to uppercase (e.g., "aapl" -> "AAPL")

		try:
			stock = yf.Ticker(stock_symbol)
			price = stock.history(period="1d")['Close'].iloc[-1]
			volume = stock.history(period="1d")['Volume'].iloc[-1]
			await message.channel.send(f"📈 **{stock_symbol}**\n💰 Price: ${price:.2f}\n📊 Volume: {volume:,}")
		except Exception as e:
			await message.channel.send(
				f"❌ Error fetching data for `{stock_symbol}`. Make sure it's a valid stock ticker.")


		await bot.process_commands(message)

	bot.run(TOKEN)
