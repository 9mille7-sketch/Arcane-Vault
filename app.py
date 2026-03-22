import os
import json
import discord
import threading
from flask import Flask, request, jsonify
from discord.ext import commands
from dotenv import load_dotenv

# 1. SETUP & SECURITY
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 1063556821517877258

app = Flask(__name__)

# 2. DISCORD BOT CONFIG
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Required for !commands
bot = commands.Bot(command_prefix="!", intents=intents)

# Helper function to read the registry
def get_registry():
    try:
        with open('registry.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading registry: {e}")
        return None

# 3. THE VERIFICATION API (For your Marketplace/Apps)
@app.route('/verify-access', methods=['POST'])
def verify():
    data = request.json
    user_id = int(data.get('discord_id'))
    
    # Check if Owner
    if user_id == OWNER_ID:
        return jsonify({"role": "OWNER", "access": "ALL", "folder": "scripts/admin"})

    # Check Publishers in Registry
    registry = get_registry()
    if registry:
        for g in registry.get('authorized_guilds', []):
            guild = bot.get_guild(int(g['guild_id']))
            if guild:
                member = guild.get_member(user_id)
                if member:
                    # Check if they have the specific publisher role
                    if any(str(role.id) == str(g['publisher_role_id']) for role in member.roles):
                        return jsonify({
                            "role": "PUBLISHER", 
                            "guild": g['guild_name'], 
                            "folder": g['folder']
                        })

    return jsonify({"role": "USER", "access": "DENIED"})

# 4. OWNER COMMANDS
@bot.event
async def on_ready():
    print(f"--- Arcane Gatekeeper V5.1 Live ---")
    print(f"Logged in as: {bot.user.name}")

@bot.command(name="status")
async def status(ctx):
    """Checks the health of the Registry and Bot"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Access Denied.")

    registry = get_registry()
    pub_count = len(registry.get('authorized_guilds', [])) if registry else 0
    
    embed = discord.Embed(title="🛡️ Arcane System Diagnostics", color=0x2f3136)
    embed.add_field(name="Gatekeeper Status", value="🟢 Online", inline=True)
    embed.add_field(name="Connected Guilds", value=f"📊 {pub_count}", inline=True)
    embed.add_field(name="Owner Verified", value="✅ Brian Miller", inline=False)
    embed.set_footer(text="Arcane Network v5.1 | Render Cloud")
    await ctx.send(embed=embed)

@bot.command(name="whois")
async def whois(ctx, member: discord.Member):
    """Checks if a specific user is authorized in the registry"""
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ Access Denied.")

    registry = get_registry()
    is_authorized = False
    
    for g in registry.get('authorized_guilds', []):
        if str(ctx.guild.id) == str(g['guild_id']):
            if any(str(role.id) == str(g['publisher_role_id']) for role in member.roles):
                is_authorized = True
                break

    status_msg = "✅ **AUTHORIZED PUBLISHER**" if is_authorized else "❌ **NOT AUTHORIZED**"
    await ctx.send(f"**Scanning {member.display_name}...**\nResult: {status_msg}")

# 5. STARTING THE ENGINE
def run_flask():
    # Render uses port 10000 by default
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    # Run Flask in a background thread so the Bot can run too
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
