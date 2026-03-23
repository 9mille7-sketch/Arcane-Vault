import os
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
import threading
import time
from dotenv import load_dotenv

# 1. SETUP & SECURITY
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    TOKEN = TOKEN.strip()

# --- PASTE THE LINK TO YOUR IMAGE BELOW ---
# Right-click the image you sent me and "Copy Link" to get this.
ARCANE_BANNER_URL = "PASTE_YOUR_LINK_HERE" 

# 2. FLASK WEB SERVER (The Full Marketplace Interface)
app = Flask(__name__)

@app.route('/')
def home():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ARCANE VAULT | DEVELOPED BY UNC</title>
        <style>
            :root {{
                --glow-color: #00ff41; 
                --bg-dark: #070707;
                --panel-bg: #121212;
                --sidebar-bg: #0d0d0d;
            }}
            body {{
                background-color: var(--bg-dark);
                color: #e0e0e0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                display: flex;
                height: 100vh;
                overflow: hidden;
            }}
            .sidebar {{
                width: 260px;
                background: var(--sidebar-bg);
                border-right: 1px solid #222;
                padding: 30px 20px;
                display: flex;
                flex-direction: column;
                box-shadow: 10px 0 20px rgba(0,0,0,0.5);
            }}
            .sidebar h2 {{ 
                color: var(--glow-color); 
                text-shadow: 0 0 15px var(--glow-color); 
                font-size: 22px;
                margin-bottom: 5px;
            }}
            .sidebar-status {{ font-size: 12px; color: #666; margin-bottom: 30px; letter-spacing: 1px; }}
            .nav-item {{ padding: 12px; color: #aaa; text-decoration: none; border-radius: 4px; transition: 0.3s; cursor: pointer; }}
            .nav-item:hover {{ background: #1a1a1a; color: var(--glow-color); }}
            .nav-active {{ color: var(--glow-color); border-left: 3px solid var(--glow-color); padding-left: 9px; }}
            
            .main-content {{ flex: 1; padding: 40px; overflow-y: auto; background: linear-gradient(135deg, #070707 0%, #0f0f0f 100%); }}
            .header-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; }}
            
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 25px;
            }}
            .slot {{
                background: var(--panel-bg);
                border: 1px solid #222;
                padding: 25px;
                border-radius: 8px;
                position: relative;
                transition: all 0.4s ease;
                animation: pulse 5s infinite ease-in-out;
            }}
            .slot:hover {{ 
                transform: translateY(-5px); 
                border-color: var(--glow-color); 
                box-shadow: 0 0 25px rgba(0, 255, 65, 0.2);
            }}
            
            @keyframes pulse {{
                0% {{ border-color: #222; }}
                50% {{ border-color: #333; }}
                100% {{ border-color: #222; }}
            }}

            .badge {{
                background: rgba(0, 255, 65, 0.1);
                color: var(--glow-color);
                padding: 4px 10px;
                font-size: 11px;
                border-radius: 20px;
                border: 1px solid var(--glow-color);
                text-transform: uppercase;
            }}
            .slot h3 {{ margin: 15px 0 10px 0; font-size: 18px; letter-spacing: 1px; }}
            .slot p {{ color: #888; font-size: 14px; line-height: 1.5; }}
            
            .btn-download {{
                margin-top: 20px;
                width: 100%;
                background: transparent;
                border: 1px solid var(--glow-color);
                color: var(--glow-color);
                padding: 10px;
                cursor: pointer;
                font-weight: bold;
                transition: 0.3s;
                text-transform: uppercase;
            }}
            .btn-download:hover {{ background: var(--glow-color); color: black; box-shadow: 0 0 15px var(--glow-color); }}
            
            .footer-credit {{ margin-top: auto; font-size: 10px; color: #444; border-top: 1px solid #222; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2>ARCANE VAULT</h2>
            <div class="sidebar-status">DEVELOPED BY UNC | ONLINE</div>
            
            <div class="nav-item nav-active">📊 DASHBOARD</div>
            <div class="nav-item">📁 ALL SCRIPTS</div>
            <div class="nav-item">🛡️ SECURITY LOGS</div>
            <div class="nav-item">⚙️ SETTINGS</div>
            
            <div class="footer-credit">
                <p>OWNER: BRIAN MILLER</p>
                <p>SYSTEM ARCHITECT: UNC</p>
            </div>
        </div>
        
        <div class="main-content">
            <div class="header-bar">
                <h1>MASTER MARKETPLACE</h1>
                <div style="color:var(--glow-color)">[ ENCRYPTION ACTIVE ]</div>
            </div>

            <div class="grid">
                <div class="slot">
                    <span class="badge">ZEN LABS</span>
                    <h3>RUST MASTER RECOIL</h3>
                    <p>Dynamic anti-recoil patterns for all 2026 meta weapons. Optimized by Unc.</p>
                    <button class="btn-download">DEPLOY SCRIPT</button>
                </div>
                <div class="slot">
                    <span class="badge">DYNASTY 2K</span>
                    <h3>NBA 2K26 TEMPO</h3>
                    <p>Perfect release synchronization engine. Mirrored timing for green bean consistency.</p>
                    <button class="btn-download">DEPLOY SCRIPT</button>
                </div>
                <div class="slot">
                    <span class="badge">SYNTAX</span>
                    <h3>SIEGE BEAMER</h3>
                    <p>Rainbow Six Siege operational script. No-recoil logic with rapid-fire modifiers.</p>
                    <button class="btn-download">DEPLOY SCRIPT</button>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def run_flask():
    try:
        app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask Error: {e}")

# 3. DISCORD BOT SETUP
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# 4. BOT EVENTS
@bot.event
async def on_ready():
    print(f'--- ARCANE VAULT: {bot.user} is Online ---')
    print('--- DEVELOPED BY UNC ---')
    try:
        synced = await bot.tree.sync()
        print(f"--- Marketplace Sync Complete ({len(synced)} commands) ---")
    except Exception as e:
        print(f"Sync Error: {e}")

# 5. SLASH COMMANDS
@bot.tree.command(name="status", description="Check the vault status")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡️ Arcane Vault Status",
        description="Systems are operational. Developed by Unc.",
        color=0x00ff41
    )
    embed.add_field(name="Gatekeeper", value="🟢 Active", inline=True)
    embed.add_field(name="Latency", value=f"⚡ {round(bot.latency * 1000)}ms", inline=True)
    
    # Add the Card Image
    if "http" in ARCANE_BANNER_URL:
        embed.set_image(url=ARCANE_BANNER_URL)
        
    embed.set_footer(text="Developed by Unc | Verified Owner: Brian Miller")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome", description="Welcome a user to the Publishers Family")
@app_commands.describe(member="The user you want to welcome")
async def welcome(interaction: discord.Interaction, member: discord.Member):
    welcome_embed = discord.Embed(
        title="⚔️ New Publisher Authorized",
        description=f"Welcome to the Publishers Family, {member.mention}!",
        color=0x00ff41
    )
    welcome_embed.add_field(name="Access Level", value="Master Vault / Upload Privileges", inline=False)
    
    # Add the Card Image
    if "http" in ARCANE_BANNER_URL:
        welcome_embed.set_image(url=ARCANE_BANNER_URL)
        
    welcome_embed.set_footer(text="Developed by Unc")
    await interaction.response.send_message(content=f"Attention {member.mention}!", embed=welcome_embed)

# 6. EXECUTION BLOCK
if __name__ == "__main__":
    if not TOKEN:
        print("CRITICAL ERROR: No DISCORD_TOKEN found!")
    else:
        # START WEB SERVER
        t = threading.Thread(target=run_flask)
        t.daemon = True
        t.start()
        
        # SAFETY DELAY
        time.sleep(2)
        
        # START BOT
        bot.run(TOKEN)
