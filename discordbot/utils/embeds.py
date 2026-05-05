# discordbot/utils/embeds.py
import discord
from datetime import datetime
import pytz
from utils.status import STATUS_MAP, PARK_EMOJIS

paris_tz = pytz.timezone("Europe/Paris")

def build_dashboard_embed(df_live, status_map, all_pannes, heure_actuelle,
                           schedules, weather, parks_data,
                           anticipated_closings, dlp_closing, daw_closing,
                           emt_opening, park_opening, emt_early_open,
                           rides_daw, rehab_list):
    from utils.status import get_status

    now   = datetime.now(paris_tz).strftime("%H:%M:%S")
    embed = discord.Embed(
        title="🏰 Disney Live Board",
        description=f"Dernière mise à jour : **{now}**",
        color=0x6d28d9
    )

    # Météo
    if weather and weather.get("success"):
        embed.add_field(
            name="🌤️ Météo — Marne-la-Vallée",
            value=(
                f"{weather['emoji']} **{weather['desc']}** — "
                f"`{weather['temp']}°C` (Ressenti `{weather['feels_like']}°`)\n"
                f"💨 {weather['wind']} · 🚩 {weather['gusts']}"
            ),
            inline=False
        )

    # Horaires
    park_hours = [s for s in schedules if s.get("type") == "PARK"]
    if park_hours:
        hours_txt = ""
        for p in park_hours:
            name  = "DLP" if "Disneyland" in p["ride_name"] else "DAW"
            color = "🩷" if name == "DLP" else "🧡"
            hours_txt += f"{color} **{name}** : `{p['opening_time'][:5]}` → `{p['closing_time'][:5]}`\n"
        embed.add_field(name="🕒 Horaires", value=hours_txt.strip(), inline=False)

    # Attractions par parc
    for park_name, lands in parks_data.items():
        park_emoji = PARK_EMOJIS.get(park_name, "🎡")
        lines = []

        for land, attractions in lands.items():
            land_lines = []
            for attr_name in attractions:
                row = df_live[df_live["ride_name"] == attr_name]
                if row.empty:
                    continue
                ride_data = row.iloc[0].to_dict()
                status, detail = get_status(
                    ride_data, status_map, all_pannes, heure_actuelle,
                    anticipated_closings, dlp_closing, daw_closing,
                    emt_opening, park_opening, emt_early_open,
                    rides_daw, rehab_list
                )
                s        = STATUS_MAP.get(status, STATUS_MAP["INCONNU"])
                wait_str = f"`{detail}`" if status == "OUVERT" else f"_{detail}_"
                land_lines.append(f"{s['emoji']} **{attr_name}** — {wait_str}")

            if land_lines:
                lines.append(f"**{land.title()}**")
                lines.extend(land_lines)
                lines.append("")

        if lines:
            chunk = ""
            for line in lines:
                if len(chunk) + len(line) + 1 > 1020:
                    embed.add_field(name=f"{park_emoji} {park_name}", value=chunk.strip(), inline=False)
                    chunk = line + "\n"
                else:
                    chunk += line + "\n"
            if chunk.strip():
                embed.add_field(name=f"{park_emoji} {park_name}", value=chunk.strip(), inline=False)

    embed.set_footer(text="Disney Wait Time Bot · Données en temps réel")
    return embed


def build_notif_embed(ride_name, old_status, new_status, detail):
    s_new = STATUS_MAP.get(new_status, STATUS_MAP["INCONNU"])
    s_old = STATUS_MAP.get(old_status, STATUS_MAP["INCONNU"])
    now   = datetime.now(paris_tz).strftime("%H:%M")

    embed = discord.Embed(
        title=f"{s_new['emoji']} {ride_name}",
        description=f"{s_old['emoji']} ~~{s_old['label']}~~ → {s_new['emoji']} **{s_new['label']}**",
        color=s_new["color"],
        timestamp=datetime.now(paris_tz)
    )
    embed.add_field(name="Détail", value=detail,   inline=True)
    embed.add_field(name="Heure",  value=f"`{now}`", inline=True)
    embed.set_footer(text="Disney Wait Time Bot")
    return embed


def build_ride_embed(ride_name, status, detail, wait_time, pannes_30j):
    s     = STATUS_MAP.get(status, STATUS_MAP["INCONNU"])
    embed = discord.Embed(title=f"🎡 {ride_name}", color=s["color"])
    embed.add_field(name="Statut", value=f"{s['emoji']} {s['label']}", inline=True)
    embed.add_field(name="Détail", value=detail,                        inline=True)

    if pannes_30j:
        nb    = len(pannes_30j)
        total = sum(p["duree"] for p in pannes_30j if p.get("duree"))
        moy   = int(total / nb) if nb else 0
        embed.add_field(
            name="📊 Stats 30 jours",
            value=f"**{nb}** interruptions · **{total}** min total · moy. **{moy}** min",
            inline=False
        )
    return embed