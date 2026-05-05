# bot/bot.py
import discord
from discord.ext import commands, tasks
import os
from supabase_client import get_supabase

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
