import discord
from discord import app_commands, Embed
from discord.ext import commands
import os
import json
from datetime import datetime

# --- DATA MANAGEMENT ---
DATA_FILE = 'race_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                if "projects" not in data:
                    data = {"projects": {}}
                return data
            except json.JSONDecodeError:
                return {"projects": {}}
    return {"projects": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- BOT SETUP ---
class RaytownBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Raytown Systems: Commands Synced for {self.user}")

bot = RaytownBot()

# --- PROJECT & CREW MANAGEMENT ---

@bot.tree.command(name="setrace", description="Initialize a project's Spark/UPX metrics")
async def set_race(interaction: discord.Interaction, project_id: str, race_name: str, spark_hours: float, upx_rate: float):
    data = load_data()
    reward_pool = spark_hours * upx_rate
    
    if project_id not in data["projects"]:
        data["projects"][project_id] = {"crews": {}, "race": {}}

    data["projects"][project_id]["race"] = {
        "name": race_name,
        "spark_hours": spark_hours,
        "upx_rate": upx_rate,
        "reward_pool": reward_pool
    }
    
    save_data(data)
    await interaction.response.send_message(f"✅ **{project_id}** set: **{reward_pool:,.0f} UPX** pool.")

@bot.tree.command(name="addcrew", description="Add a crew member's stake")
async def add_crew(interaction: discord.Interaction, project_id: str, user_name: str, stake: float):
    data = load_data()
    if project_id not in data["projects"]:
        return await interaction.response.send_message("❌ Project not found.", ephemeral=True)

    data["projects"][project_id]["crews"][user_name] = {"stake": stake, "paid": False}
    save_data(data)
    await interaction.response.send_message(f"👤 **{user_name}** added to **{project_id}** (Stake: {stake:,.1f})")

@bot.tree.command(name="payuser", description="Mark a crew member as PAID")
async def pay_user(interaction: discord.Interaction, project_id: str, user_name: str):
    data = load_data()
    project = data["projects"].get(project_id)
    
    if project and user_name in project["crews"]:
        project["crews"][user_name]["paid"] = True
        save_data(data)
        await interaction.response.send_message(f"✅ **{user_name}** marked as **PAID** for **{project_id}**.")
    else:
        await interaction.response.send_message("❌ User or Project not found.", ephemeral=True)

# --- FINANCIAL REPORTS ---

@bot.tree.command(name="ledger", description="View project breakdown and payment status")
async def ledger(interaction: discord.Interaction, project_id: str):
    data = load_data()
    project = data["projects"].get(project_id)

    if not project:
        return await interaction.response.send_message("❌ Project not found.", ephemeral=True)

    crews = project.get("crews", {})
    race = project.get("race", {})
    total_stake = sum(c["stake"] for c in crews.values())
    reward_pool = race.get("reward_pool", 0)

    embed = Embed(title=f"🏎️ Ledger: {project_id}", color=discord.Color.blue(), timestamp=datetime.now())
    
    breakdown = ""
    for name, info in crews.items():
        status = "✅" if info.get("paid") else "❌"
        share = (info["stake"] / total_stake) * reward_pool if total_stake > 0 else 0
        breakdown += f"{status} **{name}**: `{share:,.0f} UPX`\n"
    
    embed.add_field(name="Payout Status", value=breakdown or "No crew members.", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="summary", description="Executive view of all Raytown Construction payouts")
async def summary(interaction: discord.Interaction):
    data = load_data()
    projects = data.get("projects", {})
    
    total_upx_handled = 0
    total_paid = 0
    total_unpaid = 0

    for p_id, p_data in projects.items():
        race = p_data.get("race", {})
        crews = p_data.get("crews", {})
        pool = race.get("reward_pool", 0)
        total_upx_handled += pool
        p_total_stake = sum(c["stake"] for c in crews.values())
        
        for name, info in crews.items():
            share = (info["stake"] / p_total_stake) * pool if p_total_stake > 0 else 0
            if info.get("paid"):
                total_paid += share
            else:
                total_unpaid += share

    embed = Embed(title="🏢 Raytown Construction Executive Summary", color=discord.Color.gold(), timestamp=datetime.now())
    embed.add_field(name="Total Volume", value=f"{total_upx_handled:,.0f} UPX", inline=True)
    embed.add_field(name="Total Paid", value=f"✅ {total_paid:,.0f} UPX", inline=True)
    embed.add_field(name="Total Owed", value=f"❌ {total_unpaid:,.0f} UPX", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="Rank crew members by total UPX earned")
async def leaderboard(interaction: discord.Interaction):
    data = load_data()
    projects = data.get("projects", {})
    rankings = {}

    for p_id, p_data in projects.items():
        race = p_data.get("race", {})
        crews = p_data.get("crews", {})
        pool = race.get("reward_pool", 0)
        p_total_stake = sum(c["stake"] for c in crews.values())

        for name, info in crews.items():
            share = (info["stake"] / p_total_stake) * pool if p_total_stake > 0 else 0
            rankings[name] = rankings.get(name, 0) + share

    # Sort users by total earnings (descending)
    sorted_rankings = sorted(rankings.items(), key=lambda item: item[1], reverse=True)

    embed = Embed(
        title="🏆 Raytown Heavy Hitters: All-Time Earnings",
        color=discord.Color.purple(),
        timestamp=datetime.now()
    )

    leaderboard_text = ""
    for index, (user, total) in enumerate(sorted_rankings[:10], start=1):
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else "🏎️"
        leaderboard_text += f"{medal} **#{index} {user}**: `{total:,.0f} UPX`\n"

    embed.description = leaderboard_text or "No data available yet."
    embed.set_footer(text="Rankings based on all project contributions")
    await interaction.response.send_message(embed=embed)

# --- RUN ---
token = os.environ.get('DISCORD_TOKEN')
if token:
    bot.run(token)
