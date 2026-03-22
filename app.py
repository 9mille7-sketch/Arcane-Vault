import os
import json
import discord
import threading
from flask import Flask, request, jsonify
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# 1. LOAD CONFIGURATION
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 1063556821517877258

app = Flask(__name__)

# 2. DISCORD BOT SETUP (SLASH COMMAND READY)
class ArcaneBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # This forces Discord to see your new /status and /welcome commands
        await self.tree.sync()
        print(f"--- ARCANE V5: Slash Commands Synced ---")

bot = ArcaneBot()

def get_registry():
    try:
        with open('registry.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Registry Error: {e}")
        return None

# 3. SLASH COMMANDS
@bot.tree.command(name="status", description="Check the health of the Arcane Vault")
async def status(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ **Access Denied.** You are not the Prime Architect.", ephemeral=True)
    
    registry = get_registry()
    pub_count = len(registry.get('authorized_guilds', [])) if registry else 0
    
    embed = discord.Embed(title="🛡️ Arcane V5 System Diagnostics", color=0x5865F2)
    embed.add_field(name="Gatekeeper Status", value="🟢 Online & Guarding", inline=True)
    embed.add_field(name="Authorized Publishers", value=f"📊 {pub_count}", inline=True)
    embed.add_field(name="Cloud Host", value="☁️ Render Web Service", inline=False)
    embed.set_footer(text="Verified Owner: Brian Miller")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome", description="Onboard a new partner to the network")
@app_commands.describe(member="The partner to welcome")
async def welcome(interaction: discord.Interaction, member: discord.Member):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ Only the Owner can run onboarding.", ephemeral=True)

    welcome_embed = discord.Embed(
        title="⚔️ Welcome to the Arcane Network",
        description=f"Greetings {member.mention}, your server is now linked to the Master Vault.",
        color=0x00ff00
    )
    welcome_embed.add_field(name="Next Step", value="Check your assigned GitHub folder for script uploads.", inline=False)
    welcome_embed.set_footer(text="Arcane V5 Security Protocol")
    
    await interaction.response.send_message(embed=welcome_embed)

# 4. FLASK API (The 'Not Found' Fix)
@app.route('/')
def home():
    return "<h1>Arcane API is LIVE. 🛡️</h1><p>System is guarding the vault.</p>"

@app.route('/verify-access', methods=['POST'])
def verify():
    data = request.json
    user_id = int(data.get('discord_id'))
    
    if user_id == OWNER_ID:
        return jsonify({"role": "OWNER", "access": "ALL"})

    registry = get_registry()
    if registry:
        for g in registry.get('authorized_guilds', []):
            guild = bot.get_guild(int(g['guild_id']))
            if guild:
                m = guild.get_member(user_id)
                if m and any(str(r.id) == str(g['publisher_role_id']) for r in m.roles):
                    return jsonify({"role": "PUBLISHER", "folder": g['folder']})

    return jsonify({"role": "USER", "access": "DENIED"})

# 5. EXECUTION
def run_flask():
    # Render binds to port 10000
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    # Start API in background, then start Bot
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
