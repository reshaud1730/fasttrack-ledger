import discord
from discord import app_commands, Embed
from discord.ext import commands
import os
import json
from datetime import datetime

# --- DATA PERSISTENCE ---
DATA_FILE = 'race_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"projects": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- BOT INITIALIZATION ---
class RacingBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ Commands synced for {self.user}")

bot = RacingBot()

@bot.event
async def on_ready():
    print(f'🚀 Raytown Construction Bot Online | Logged in as {bot.user}')

# --- CORE COMMANDS ---

@bot.tree.command(name="setrace", description="Configure Spark hours and UPX rate for a project")
async def set_race(interaction: discord.Interaction, project_id: str, race_name: str, spark_hours: float, upx_rate: float):
    data = load_data()
    
    # Automatic calculation of the reward pool
    reward_pool = spark_hours * upx_rate
    
    data["projects"][project_id] = {
        "race": {
            "name": race_name,
            "spark_hours": spark_hours,
            "upx_rate": upx_rate,
            "reward_pool": reward_pool
        },
        "crews": data["projects"].get(project_id, {}).get("crews", {})
    }
    
    save_data(data)
    await interaction.response.send_message(
        f"✅ **{project_id}** configured!\n🏗️ {spark_hours:,.1f} Spark hrs @ {upx_rate} UPX/hr\n💰 Pool: **{reward_pool:,.0f} UPX**"
    )

@bot.tree.command(name="ledger", description="Display the UPX breakdown for a project")
async def ledger(interaction: discord.Interaction, project_id: str):
    data = load_data()
    project = data["projects"].get(project_id)

    if not project:
        return await interaction.response.send_message(f"❌ Project `{project_id}` not found.", ephemeral=True)

    crews = project.get("crews", {})
    race = project.get("race", {})
    total_stake = sum(crews.values())
    reward_pool = race.get("reward_pool", 0)

    embed = Embed(
        title=f"🏎️ Race Ledger: {project_id}",
        description=f"**Project:** {race.get('name')}\n**Rate:** {race.get('upx_rate')} UPX/hr",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    embed.add_field(name="Total Pool", value=f"{reward_pool:,.0f} UPX", inline=True)
    embed.add_field(name="Total Stake", value=f"{total_stake:,.1f}", inline=True)

    breakdown = ""
    for name, stake in crews.items():
        share = (stake / total_stake) * reward_pool if total_stake > 0 else 0
        breakdown += f"**{name}**: {stake:,.1f} → `{share:,.0f} UPX`\n"
    
    embed.add_field(name="Crew Payouts", value=breakdown or "No crew assigned.", inline=False)
    embed.set_footer(text="Raytown Construction • Upland Metaverse")

    await interaction.response.send_message(embed=embed)

# --- TOKEN EXECUTION ---
if __name__ == "__main__":
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("CRITICAL: DISCORD_TOKEN environment variable not set.")
