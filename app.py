import os
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
import threading
from dotenv import load_dotenv

# 1. SETUP & SECURITY
load_dotenv()
# This pulls the token safely from Render's secret settings
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    TOKEN = TOKEN.strip()

# 2. FLASK WEB SERVER (Keep-Alive for Render)
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Arcane API is LIVE. 🛡️</h1><p>System is guarding the vault.</p>"

def run_flask():
    # Render uses port 10000 by default
    app.run(host='0.0.0.0', port=10000)

# 3. DISCORD BOT SETUP
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 4. BOT EVENTS
@bot.event
async def on_ready():
    print(f'--- ARCANE V5: {bot.user} is Online ---')
    try:
        # This forces the commands to show up in your server immediately
        synced = await bot.tree.sync()
        print(f"--- ARCANE V5: Instant Sync of {len(synced)} Commands Complete ---")
    except Exception as e:
        print(f"Sync Error: {e}")

# 5. SLASH COMMANDS
@bot.tree.command(name="status", description="Check the vault status")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡️ Arcane Vault Status",
        description="Systems are operational. V5 is active.",
        color=discord.Color.green()
    )
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome", description="Send a test welcome message")
async def welcome(interaction: discord.Interaction):
    await interaction.response.send_message(f"Welcome to the Vault, {interaction.user.mention}! 🧪")

# 6. EXECUTION
if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: No DISCORD_TOKEN found in Environment Variables!")
    else:
        # Start the web server in a background thread
        t = threading.Thread(target=run_flask)
        t.daemon = True
        t.start()
        
        # Start the Bot
        bot.run(TOKEN)
