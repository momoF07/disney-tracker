# bot/bot.py
import discord
from discord.ext import commands
import os
import sys

# Ajoute le dossier parent au path pour trouver cogs/ et utils/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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