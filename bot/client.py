from discord.ext import commands
import discord
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

async def load_extensions():
    await bot.load_extension("bot.commands.chat_command")

# Run the bot
def run_discord_bot():
    asyncio.run(load_extensions())
    bot.run(os.getenv("DISCORD_TOKEN"))

if __name__ == "__main__":
    run_discord_bot()