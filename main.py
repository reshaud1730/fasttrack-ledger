import discord
from discord import app_commands, Embed
from discord.ext import commands
import os
import json
from datetime import datetime
# from keep_alive import keep_alive # Uncomment if using Replit

# --- CONFIGURATION & DATA LOGIC ---
DATA_FILE = 'race_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"projects": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- BOT SETUP ---
class RacingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Slash commands synced for {self.user}")

bot = RacingBot()

@bot.event
async def on_ready():
    print(f'🚀 Logged in as {bot.user} (ID: {bot.user.id})')
    print('------------------------------------------')

# --- SLASH COMMANDS ---

@bot.tree.command(name="calculate", description="Calculate a single share of a reward pool")
@app_commands.describe(stake="Your property/kart stake", total_stake="Total stake in race", reward_pool="Total UPX pool")
async def calculate(interaction: discord.Interaction, stake: float, total_stake: float, reward_pool: float):
    if total_stake <= 0:
        return await interaction.response.send_message("Total stake must be greater than zero.", ephemeral=True)
    
    share = (stake / total_stake) * reward_pool
    await interaction.response.send_message(f"Your calculated share is: **{share:,.0f} UPX** 🏎️")

@bot.tree.command(name="ledger", description="View the full breakdown for a project")
async def ledger(interaction: discord.Interaction, project_id: str):
    data = load_data()
    project = data["projects"].get(project_id)

    if not project:
        return await interaction.response.send_message(f"❌ Project `{project_id}` not found.", ephemeral=True)

    crews = project.get("crews", {})
    race = project.get("race", {})
    total_stake = sum(crews.values())
    reward_pool = race.get("reward_pool", 0)
    race_name = race.get("name", "Active Race")

    # Create a professional Embed
    embed = Embed(
        title=f"📋 Ledger: {project_id}",
        description=f"**Race:** {race_name}\n**Total Pool:** {reward_pool:,.0f} UPX",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(name="📈 Total Stake", value=f"{total_stake:,.0f}", inline=True)
    embed.add_field(name="👥 Participants", value=str(len(crews)), inline=True)

    breakdown = ""
    for name, stake in crews.items():
        share = (stake / total_stake) * reward_pool if total_stake > 0 else 0
        breakdown += f"**{name}**: {stake:,.0f} stake → `{share:,.0f} UPX`\n"
    
    embed.add_field(name="Detailed Breakdown", value=breakdown or "No crew members added.", inline=False)
    embed.set_footer(text="Upland Racing Ledger System")

    await interaction.response.send_message(embed=embed)

# --- PROJECT MANAGEMENT COMMANDS ---

@bot.tree.command(name="setrace", description="Set or update race details")
async def set_race(interaction: discord.Interaction, project_id: str, race_name: str, reward_pool: float):
    data = load_data()
    if project_id not in data["projects"]:
        data["projects"][project_id] = {"crews": {}, "race": {}}

    data["projects"][project_id]["race"] = {"name": race_name, "reward_pool": reward_pool}
    save_data(data)
    await interaction.response.send_message(f"✅ Project **{project_id}** updated: **{race_name}** with **{reward_pool:,.0f} UPX**.")

@bot.tree.command(name="addcrew", description="Add a member's stake to a project")
async def add_crew(interaction: discord.Interaction, project_id: str, user_name: str, stake: float):
    data = load_data()
    if project_id not in data["projects"]:
        return await interaction.response.send_message(f"❌ Project `{project_id}` not found. Use `/setrace` first.", ephemeral=True)

    data["projects"][project_id]["crews"][user_name] = stake
    save_data(data)
    await interaction.response.send_message(f"👤 Added **{user_name}** to **{project_id}** (Stake: {stake:,.0f})")

# --- RUN BOT ---
# keep_alive() # Uncomment if using Replit
token = os.environ.get('DISCORD_TOKEN')

if token:
    bot.run(token)
else:
    print("CRITICAL ERROR: DISCORD_TOKEN not found in environment variables.")
