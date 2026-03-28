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
                if "projects" not in data: data = {"projects": {}}
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
        print(f"✅ Raytown Systems: Executive Suite Synced.")

bot = RaytownBot()

@bot.event
async def on_ready():
    print(f'🚀 Raytown Construction HQ: Online and Syncing.')

# --- THE HELP COMMAND ---

@bot.tree.command(name="help", description="List all available Raytown Construction commands")
async def help_command(interaction: discord.Interaction):
    embed = Embed(
        title="🏢 Raytown Construction Bot Help",
        description="Welcome to the digital HQ. Use the commands below to manage Upland projects.",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🛠️ Project Management",
        value=(
            "`/setrace`: Set project Spark hours and UPX rate.\n"
            "`/addcrew`: Add a worker and their stake to a project.\n"
            "`/editcrew`: Adjust a worker's stake (resets paid status).\n"
            "`/removecrew`: Delete a worker from a project."
        ),
        inline=False
    )
    
    embed.add_field(
        name="💰 Financial Tracking",
        value=(
            "`/payuser`: Mark a specific worker as PAID (✅).\n"
            "`/ledger`: View the live UPX breakdown for a project."
        ),
        inline=False
    )
    
    embed.add_field(
        name="📈 Analytics & Admin",
        value=(
            "`/summary`: Executive view of all UPX volume and debt.\n"
            "`/leaderboard`: Rank the top 10 all-time earners.\n"
            "`/ping`: Check bot latency."
        ),
        inline=False
    )
    
    embed.set_footer(text="Raytown Construction • Upland Metaverse Solutions")
    await interaction.response.send_message(embed=embed)

# --- PROJECT & CREW MANAGEMENT ---

@bot.tree.command(name="setrace", description="Initialize/Update project Spark/UPX metrics")
async def set_race(interaction: discord.Interaction, project_id: str, race_name: str, spark_hours: float, upx_rate: float):
    data = load_data()
    reward_pool = spark_hours * upx_rate
    if project_id not in data["projects"]: data["projects"][project_id] = {"crews": {}, "race": {}}
    data["projects"][project_id]["race"] = {
        "name": race_name, "spark_hours": spark_hours, "upx_rate": upx_rate, "reward_pool": reward_pool
    }
    save_data(data)
    await interaction.response.send_message(f"✅ **{project_id}** set: **{reward_pool:,.0f} UPX** pool.")

@bot.tree.command(name="addcrew", description="Add a new crew member's stake")
async def add_crew(interaction: discord.Interaction, project_id: str, user_name: str, stake: float):
    data = load_data()
    if project_id not in data["projects"]: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
    data["projects"][project_id]["crews"][user_name] = {"stake": stake, "paid": False}
    save_data(data)
    await interaction.response.send_message(f"👤 **{user_name}** added to **{project_id}** (Stake: {stake:,.1f})")

@bot.tree.command(name="editcrew", description="Update an existing crew member's stake")
async def edit_crew(interaction: discord.Interaction, project_id: str, user_name: str, new_stake: float):
    data = load_data()
    project = data["projects"].get(project_id)
    if not project: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
    crews = project.get("crews", {})
    found_user = next((name for name in crews if name.lower() == user_name.lower()), None)
    if found_user:
        crews[found_user]["stake"] = new_stake
        crews[found_user]["paid"] = False 
        save_data(data)
        await interaction.response.send_message(f"✏️ Updated **{found_user}** stake to **{new_stake:,.1f}**. Status reset to ❌.")
    else: await interaction.response.send_message(f"❓ User not found.", ephemeral=True)

@bot.tree.command(name="removecrew", description="Remove a member from a project")
async def remove_crew(interaction: discord.Interaction, project_id: str, user_name: str):
    data = load_data(); project = data["projects"].get(project_id)
    if not project: return await interaction.response.send_message("❌ Not found.", ephemeral=True)
    crews = project.get("crews", {})
    found_user = next((name for name in crews if name.lower() == user_name.lower()), None)
    if found_user:
        del project["crews"][found_user]; save_data(data)
        await interaction.response.send_message(f"🗑️ Removed **{found_user}** from **{project_id}**")
    else: await interaction.response.send_message("❓ User not found.", ephemeral=True)

# --- PAYMENTS & REPORTS ---

@bot.tree.command(name="payuser", description="Mark a crew member as PAID")
async def pay_user(interaction: discord.Interaction, project_id: str, user_name: str):
    data = load_data(); project = data["projects"].get(project_id)
    if project:
        found_user = next((n for n in project["crews"] if n.lower() == user_name.lower()), None)
        if found_user:
            project["crews"][found_user]["paid"] = True; save_data(data)
            return await interaction.response.send_message(f"✅ **{found_user}** marked as **PAID** for **{project_id}**.")
    await interaction.response.send_message("❌ Not found.", ephemeral=True)

@bot.tree.command(name="ledger", description="View project breakdown and status")
async def ledger(interaction: discord.Interaction, project_id: str):
    data = load_data(); project = data["projects"].get(project_id)
    if not project: return await interaction.response.send_message("❌ Not found.", ephemeral=True)
    crews = project.get("crews", {}); race = project.get("race", {})
    total_stake = sum(c["stake"] for c in crews.values()); pool = race.get("reward_pool", 0)
    embed = Embed(title=f"🏎️ Ledger: {project_id}", color=discord.Color.green(), timestamp=datetime.now())
    breakdown = ""
    for name, info in crews.items():
        status = "✅" if info.get("paid") else "❌"
        share = (info["stake"] / total_stake) * pool if total_stake > 0 else 0
        breakdown += f"{status} **{name}**: `{share:,.0f} UPX`\n"
    embed.add_field(name="Payout Status", value=breakdown or "No crew.", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="summary", description="Executive view of all Raytown payouts")
async def summary(interaction: discord.Interaction):
    data = load_data(); projects = data.get("projects", {})
    total_vol = 0; paid = 0; unpaid = 0
    for p_id, p_data in projects.items():
        race = p_data.get("race", {}); crews = p_data.get("crews", {}); pool = race.get("reward_pool", 0)
        total_vol += pool; p_stake = sum(c["stake"] for c in crews.values())
        for n, i in crews.items():
            share = (i["stake"] / p_stake) * pool if p_stake > 0 else 0
            if i.get("paid"): paid += share
            else: unpaid += share
    embed = Embed(title="🏢 Raytown Executive Summary", color=discord.Color.gold(), timestamp=datetime.now())
    embed.add_field(name="Total Volume", value=f"{total_vol:,.0f} UPX", inline=True)
    embed.add_field(name="Total Paid", value=f"✅ {paid:,.0f} UPX", inline=True)
    embed.add_field(name="Total Owed", value=f"❌ {unpaid:,.0f} UPX", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="Rank crew members by total UPX")
async def leaderboard(interaction: discord.Interaction):
    data = load_data(); projects = data.get("projects", {}); rankings = {}
    for p_id, p_data in projects.items():
        race = p_data.get("race", {}); crews = p_data.get("crews", {}); pool = race.get("reward_pool", 0)
        p_stake = sum(c["stake"] for c in crews.values())
        for n, i in crews.items():
            share = (i["stake"] / p_stake) * pool if p_stake > 0 else 0
            rankings[n] = rankings.get(n, 0) + share
    sorted_r = sorted(rankings.items(), key=lambda x: x[1], reverse=True)
    embed = Embed(title="🏆 Raytown Heavy Hitters", color=discord.Color.purple())
    text = ""
    for idx, (u, t) in enumerate(sorted_r[:10], 1):
        m = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🏎️"
        text += f"{m} **#{idx} {u}**: `{t:,.0f} UPX`\n"
    embed.description = text or "No data."
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Check latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏎️ Latency: `{round(bot.latency * 1000)}ms`")

# --- RUN ---
token = os.environ.get('DISCORD_TOKEN')
if token: bot.run(token)
