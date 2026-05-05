# discordbot/cogs/notifs.py
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz
import pandas as pd
from bot.supabase_client import get_supabase
from bot_config import CHANNEL_NOTIFS_ID, POLL_INTERVAL
from utils.status import get_status
from utils.embeds import build_notif_embed
from modules_bot import (
    PARKS_DATA, RIDES_DAW, ANTICIPATED_CLOSINGS,
    DLP_CLOSING, DAW_CLOSING, EMT_OPENING, PARK_OPENING,
    EMT_EARLY_OPEN, REHAB_LIST
)

paris_tz = pytz.timezone("Europe/Paris")

class Notifs(commands.Cog):
    def __init__(self, bot):
        self.bot         = bot
        self.supabase    = get_supabase()
        self.last_states = {}
        self.poll.start()

    def cog_unload(self):
        self.poll.cancel()

    @tasks.loop(seconds=POLL_INTERVAL)
    async def poll(self):
        channel = self.bot.get_channel(CHANNEL_NOTIFS_ID)
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

            all_pannes = []
            for row in resp_101.data:
                d_p = pd.to_datetime(row["start_time"]).astimezone(paris_tz)
                f_p = pd.to_datetime(row["end_time"]).astimezone(paris_tz) if row.get("end_time") else None
                all_pannes.append({
                    "ride":   row["ride_name"], "debut": d_p, "fin": f_p,
                    "statut": "EN_COURS" if f_p is None else "TERMINEE",
                    "duree":  int((f_p - d_p).total_seconds() / 60) if f_p else 0
                })

            important = {
                ("OUVERT", "INCIDENT"), ("OUVERT", "RETARDÉ"),
                ("INCIDENT", "OUVERT"), ("RETARDÉ", "OUVERT"),
                ("OUVERT", "TRAVAUX"),
            }

            for _, row in df_live.iterrows():
                ride_data  = row.to_dict()
                name       = ride_data["ride_name"]
                new_status, detail = get_status(
                    ride_data, status_map, all_pannes, heure_actuelle,
                    ANTICIPATED_CLOSINGS, DLP_CLOSING, DAW_CLOSING,
                    EMT_OPENING, PARK_OPENING, EMT_EARLY_OPEN,
                    RIDES_DAW, REHAB_LIST
                )
                old_status = self.last_states.get(name)

                if old_status and old_status != new_status:
                    if (old_status, new_status) in important:
                        embed = build_notif_embed(name, old_status, new_status, detail)
                        await channel.send(embed=embed)

                self.last_states[name] = new_status

        except Exception as e:
            print(f"❌ [NOTIFS] Erreur poll : {e}")

    @poll.before_loop
    async def before_poll(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Notifs(bot))