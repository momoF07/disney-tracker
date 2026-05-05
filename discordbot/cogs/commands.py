# discordbot/cogs/commands.py
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import pytz
import pandas as pd
from bot.supabase_client import get_supabase
from utils.status import get_status, STATUS_MAP
from utils.embeds import build_ride_embed
from modules_bot import (
    PARKS_DATA, RIDES_DAW, ANTICIPATED_CLOSINGS,
    DLP_CLOSING, DAW_CLOSING, EMT_OPENING, PARK_OPENING,
    EMT_EARLY_OPEN, REHAB_LIST
)
from modules.weather import get_disney_weather

paris_tz = pytz.timezone("Europe/Paris")

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot      = bot
        self.supabase = get_supabase()

    def _fetch_base(self):
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

        return df_live, status_map, all_pannes, heure_actuelle

    @app_commands.command(name="attente", description="Temps d'attente d'une attraction")
    @app_commands.describe(attraction="Nom de l'attraction")
    async def attente(self, interaction: discord.Interaction, attraction: str):
        await interaction.response.defer()
        df_live, status_map, all_pannes, heure_actuelle = self._fetch_base()

        matches = df_live[df_live["ride_name"].str.lower().str.contains(attraction.lower())]
        if matches.empty:
            await interaction.followup.send(f"❌ Attraction `{attraction}` introuvable.", ephemeral=True)
            return

        ride_data      = matches.iloc[0].to_dict()
        name           = ride_data["ride_name"]
        status, detail = get_status(
            ride_data, status_map, all_pannes, heure_actuelle,
            ANTICIPATED_CLOSINGS, DLP_CLOSING, DAW_CLOSING,
            EMT_OPENING, PARK_OPENING, EMT_EARLY_OPEN,
            RIDES_DAW, REHAB_LIST
        )

        date_30j   = (datetime.now(paris_tz) - timedelta(days=30)).isoformat()
        resp_30j   = self.supabase.table("logs_101").select("*").eq("ride_name", name).gte("start_time", date_30j).execute()
        pannes_30j = []
        for row in resp_30j.data:
            if row.get("end_time"):
                d = pd.to_datetime(row["start_time"]).astimezone(paris_tz)
                f = pd.to_datetime(row["end_time"]).astimezone(paris_tz)
                duree = int((f - d).total_seconds() / 60)
                if duree >= 2:
                    pannes_30j.append({"duree": duree})

        embed = build_ride_embed(name, status, detail, ride_data.get("wait_time", 0), pannes_30j)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="101", description="Attractions actuellement en panne ou en retard")
    async def incidents(self, interaction: discord.Interaction):
        await interaction.response.defer()
        df_live, status_map, all_pannes, heure_actuelle = self._fetch_base()

        incidents = []
        for _, row in df_live.iterrows():
            ride_data      = row.to_dict()
            status, detail = get_status(
                ride_data, status_map, all_pannes, heure_actuelle,
                ANTICIPATED_CLOSINGS, DLP_CLOSING, DAW_CLOSING,
                EMT_OPENING, PARK_OPENING, EMT_EARLY_OPEN,
                RIDES_DAW, REHAB_LIST
            )
            if status in ("INCIDENT", "RETARDÉ"):
                incidents.append((ride_data["ride_name"], status, detail))

        if not incidents:
            embed = discord.Embed(
                title="✅ Aucun incident en cours",
                description="Toutes les attractions sont opérationnelles.",
                color=0x10b981
            )
        else:
            embed = discord.Embed(title=f"⚠️ {len(incidents)} incident(s) en cours", color=0xf59e0b)
            for name, status, detail in incidents:
                s = STATUS_MAP[status]
                embed.add_field(name=f"{s['emoji']} {name}", value=detail, inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="horaires", description="Horaires des parcs aujourd'hui")
    async def horaires(self, interaction: discord.Interaction):
        await interaction.response.defer()
        schedules = self.supabase.table("ride_schedules").select("*").execute().data or []

        parks = [s for s in schedules if s.get("type") == "PARK"]
        emts  = {s["ride_name"].replace("EMT ", ""): s["opening_time"] for s in schedules if s.get("type") == "EMT"}

        embed = discord.Embed(title="🕒 Horaires des parcs", color=0x6d28d9)
        if not parks:
            embed.description = "Aucun horaire disponible pour aujourd'hui."
        else:
            for p in parks:
                is_dlp   = "Disneyland" in p["ride_name"]
                name     = "Disneyland Park" if is_dlp else "Disney Adventure World"
                opening  = p["opening_time"][:5]
                closing  = p["closing_time"][:5]
                emt_time = emts.get(p["ride_name"])
                emt_str  = f"\n✨ EMT : `{emt_time[:5]}` → `{opening}`" if emt_time else ""
                embed.add_field(
                    name=f"{'🩷' if is_dlp else '🧡'} {name}",
                    value=f"`{opening}` → `{closing}`{emt_str}",
                    inline=True
                )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="meteo", description="Météo actuelle à Marne-la-Vallée")
    async def meteo(self, interaction: discord.Interaction):
        await interaction.response.defer()
        weather = get_disney_weather()
        embed   = discord.Embed(title=f"{weather['emoji']} Météo — Marne-la-Vallée", color=0x7dd3fc)
        embed.add_field(name="🌡️ Température", value=f"`{weather['temp']}°C` (Ressenti `{weather['feels_like']}°`)", inline=True)
        embed.add_field(name="💨 Vent",         value=f"`{weather['wind']}`",  inline=True)
        embed.add_field(name="🚩 Rafales",      value=f"`{weather['gusts']}`", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="stats", description="Stats d'interruptions sur 30 jours")
    @app_commands.describe(attraction="Nom de l'attraction (optionnel)")
    async def stats(self, interaction: discord.Interaction, attraction: str = None):
        await interaction.response.defer()
        date_30j = (datetime.now(paris_tz) - timedelta(days=30)).isoformat()

        if attraction:
            resp = self.supabase.table("logs_101").select("*").ilike("ride_name", f"%{attraction}%").gte("start_time", date_30j).execute()
        else:
            resp = self.supabase.table("logs_101").select("*").gte("start_time", date_30j).execute()

        df = pd.DataFrame(resp.data)
        if df.empty:
            await interaction.followup.send("📭 Aucune donnée sur les 30 derniers jours.", ephemeral=True)
            return

        df = df[df["end_time"].notna()].copy()
        df["start_dt"] = pd.to_datetime(df["start_time"]).dt.tz_convert("Europe/Paris")
        df["end_dt"]   = pd.to_datetime(df["end_time"]).dt.tz_convert("Europe/Paris")
        df["duree"]    = (df["end_dt"] - df["start_dt"]).dt.total_seconds() / 60
        df = df[df["duree"] >= 2]

        if df.empty:
            await interaction.followup.send("📭 Aucune interruption significative.", ephemeral=True)
            return

        nb    = len(df)
        total = int(df["duree"].sum())
        moy   = int(df["duree"].mean())

        title = f"📊 Stats — {attraction}" if attraction else "📊 Stats globales — 30 jours"
        embed = discord.Embed(title=title, color=0xc4b5fd)
        embed.add_field(name="🔴 Interruptions", value=f"`{nb}`",        inline=True)
        embed.add_field(name="⏱️ Total",          value=f"`{total} min`", inline=True)
        embed.add_field(name="📈 Moyenne",         value=f"`{moy} min`",  inline=True)

        if not attraction:
            top     = df.groupby("ride_name")["duree"].count().sort_values(ascending=False).head(5)
            top_str = "\n".join([f"**{n}** — {c} interruption(s)" for n, c in top.items()])
            embed.add_field(name="🏆 Top 5", value=top_str, inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="rehab", description="Attractions en réhabilitation")
    async def rehab(self, interaction: discord.Interaction):
        await interaction.response.defer()
        today = datetime.now(paris_tz).date()
        embed = discord.Embed(title="🛠️ Réhabilitations en cours", color=0x64748b)
        found = False

        for name, info in REHAB_LIST.items():
            debut    = info.get("debut")
            fin      = info.get("fin")
            in_rehab = True if (not debut or not fin) else (debut <= today <= fin)
            if in_rehab:
                found     = True
                debut_str = debut.strftime("%d/%m/%Y") if debut else "—"
                fin_str   = fin.strftime("%d/%m/%Y")   if fin   else "Indéfini"
                embed.add_field(
                    name=f"⚫ {name}",
                    value=f"{info['msg']}\n`{debut_str}` → `{fin_str}`",
                    inline=False
                )

        if not found:
            embed.description = "Aucune attraction en réhabilitation actuellement."

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Commands(bot))