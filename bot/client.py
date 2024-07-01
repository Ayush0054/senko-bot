from discord.ext import commands
import discord
import os
from dotenv import load_dotenv
import asyncio
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"{bot.user} has connected to Discord!")

async def load_extensions():
    logging.info("Loading extensions...")
    await bot.load_extension("bot.commands.chat_command")
    logging.info("Extensions loaded")

# Modified run_discord_bot function
async def run_discord_bot():
    await load_extensions()
    await bot.start(os.getenv("DISCORD_TOKEN"))

# This part is only needed if you want to run the bot standalone
if __name__ == "__main__":
    asyncio.run(run_discord_bot())
