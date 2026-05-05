# discordbot/cogs/dashboard.py
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz
import pandas as pd
from supabase_client import get_supabase
from bot_config import CHANNEL_DASHBOARD_ID, MESSAGE_DASHBOARD_ID, POLL_INTERVAL
from utils.embeds import build_dashboard_embed
from modules_bot import (
    PARKS_DATA, RIDES_DAW, ANTICIPATED_CLOSINGS,
    DLP_CLOSING, DAW_CLOSING, EMT_OPENING, PARK_OPENING,
    EMT_EARLY_OPEN, REHAB_LIST
)
from modules.weather import get_disney_weather

paris_tz = pytz.timezone("Europe/Paris")

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot      = bot
        self.supabase = get_supabase()
        self.update.start()

    def cog_unload(self):
        self.update.cancel()

    @tasks.loop(seconds=POLL_INTERVAL)
    async def update(self):
        channel = self.bot.get_channel(CHANNEL_DASHBOARD_ID)
        if not channel:
            return

        try:
            now_paris      = datetime.now(paris_tz)
            heure_actuelle = now_paris.time()
            heure_reset    = now_paris.replace(hour=2, minute=30, second=0, microsecond=0)
            debut_journee  = heure_reset if now_paris >= heure_reset else heure_reset - timedelta(days=1)

            df_live    = pd.DataFrame(self.supabase.table("disney_live").select("*").execute().data)
            status_map = {i["ride_name"]: i for i in self.supabase.table("daily_status").select("*").execute().data}
            resp_101   = self.supabase.table("logs_101").select("*").gte("start_time", debut_journee.isoformat()).execute()
            schedules  = self.supabase.table("ride_schedules").select("*").execute().data or []
            weather    = get_disney_weather()

            all_pannes = []
            for row in resp_101.data:
                d_p = pd.to_datetime(row["start_time"]).astimezone(paris_tz)
                f_p = pd.to_datetime(row["end_time"]).astimezone(paris_tz) if row.get("end_time") else None
                all_pannes.append({
                    "ride":   row["ride_name"], "debut": d_p, "fin": f_p,
                    "statut": "EN_COURS" if f_p is None else "TERMINEE",
                    "duree":  int((f_p - d_p).total_seconds() / 60) if f_p else 0
                })

            embed = build_dashboard_embed(
                df_live, status_map, all_pannes, heure_actuelle,
                schedules, weather, PARKS_DATA,
                ANTICIPATED_CLOSINGS, DLP_CLOSING, DAW_CLOSING,
                EMT_OPENING, PARK_OPENING, EMT_EARLY_OPEN,
                RIDES_DAW, REHAB_LIST
            )

            try:
                msg = await channel.fetch_message(MESSAGE_DASHBOARD_ID)
                await msg.edit(embed=embed)
            except discord.NotFound:
                msg = await channel.send(embed=embed)
                print(f"📌 Nouveau dashboard créé : ID {msg.id} — à mettre dans MESSAGE_DASHBOARD_ID")

        except Exception as e:
            print(f"❌ [DASHBOARD] Erreur update : {e}")

    @update.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Dashboard(bot))