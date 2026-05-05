# discordbot/bot/bot.py
import sys
import os

# Racine du repo → accès à config.py et modules/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# discordbot/ → accès à cogs/ et utils/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}")
    await bot.load_extension("cogs.notifs")
    await bot.load_extension("cogs.dashboard")
    await bot.load_extension("cogs.commands")
    await bot.tree.sync()
    print("✅ Commandes slash synchronisées")

if __name__ == "__main__":
    bot.run(os.environ.get("DISCORD_TOKEN"))