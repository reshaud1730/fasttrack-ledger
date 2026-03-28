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
                # Ensure structure is consistent
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
        print(f"✅ Commands Synced for {self.user}")

bot = RaytownBot()

# --- PROJECT & CREW COMMANDS ---

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
    await interaction.response.send_message(f"✅ **{project_id}** set: {reward_pool:,.0f} UPX pool.")

@bot.tree.command(name="addcrew", description="Add a crew member's stake")
async def add_crew(interaction: discord.Interaction, project_id: str, user_name: str, stake: float):
    data = load_data()
    if project_id not in data["projects"]:
        return await interaction.response.send_message("❌ Project not found.", ephemeral=True)

    # Store as a dict to track payment status
    data["projects"][project_id]["crews"][user_name] = {"stake": stake, "paid": False}
    save_data(data)
    await interaction.response.send_message(f"👤 **{user_name}** added to **{project_id}** (Stake: {stake:,.1f})")

# --- PAYMENT TRACKING COMMANDS ---

@bot.tree.command(name="payuser", description="Mark a crew member as PAID")
async def pay_user(interaction: discord.Interaction, project_id: str, user_name: str):
    data = load_data()
    project = data["projects"].get(project_id)
    
    if project and user_name in project["crews"]:
        project["crews"][user_name]["paid"] = True
        save_data(data)
        await interaction.response.send_message(f"✅ **{user_name}** has been marked as **PAID** for project **{project_id}**.")
    else:
        await interaction.response.send_message("❌ User or Project not found.", ephemeral=True)

@bot.tree.command(name="unpayuser", description="Mark a crew member as UNPAID")
async def unpay_user(interaction: discord.Interaction, project_id: str, user_name: str):
    data = load_data()
    project = data["projects"].get(project_id)
    
    if project and user_name in project["crews"]:
        project["crews"][user_name]["paid"] = False
        save_data(data)
        await interaction.response.send_message(f"⚠️ **{user_name}** marked as **UNPAID**.")
    else:
        await interaction.response.send_message("❌ User or Project not found.", ephemeral=True)

# --- THE LEDGER ---

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

    embed = Embed(title=f"🏎️ Ledger: {project_id}", color=discord.Color.green(), timestamp=datetime.now())
    embed.add_field(name="Total Pool", value=f"{reward_pool:,.0f} UPX", inline=True)
    embed.add_field(name="Total Stake", value=f"{total_stake:,.1f}", inline=True)

    breakdown = ""
    for name, info in crews.items():
        stake = info["stake"]
        status = "✅" if info.get("paid") else "❌"
        share = (stake / total_stake) * reward_pool if total_stake > 0 else 0
        breakdown += f"{status} **{name}**: {stake:,.1f} → `{share:,.0f} UPX`\n"
    
    embed.add_field(name="Payout Status", value=breakdown or "No crew members.", inline=False)
    embed.set_footer(text="Raytown Construction Ledger System")

    await interaction.response.send_message(embed=embed)

# --- RUN ---
token = os.environ.get('DISCORD_TOKEN')
if token:
    bot.run(token)
