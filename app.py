import os
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask
import threading
import time
from dotenv import load_dotenv

# 1. SETUP & CONFIGURATION
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN: 
    TOKEN = TOKEN.strip()

# THE DIRECT IMAGE LINK YOU PROVIDED
ARCANE_BANNER_URL = "https://media.discordapp.net/attachments/1456130906401144904/1485391187195072723/ChatGPT_Image_Mar_22_2026_05_26_21_PM.png?ex=69c1b1d8&is=69c06058&hm=f8441f33fff5e9ad2cf6e70ffe3eb1470a877fdd3e2ce3edd1bb282eb1f6a8b5&=&format=webp&quality=lossless"

# 2. ARCANE WEB INTERFACE (The Dashboard)
app = Flask(__name__)

@app.route('/')
def home():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>ARCANE VAULT | UNC</title>
        <style>
            :root {{
                --arcane-orange: #ff5e00;
                --deep-rust: #2b140a;
                --bg: #0d0705;
            }}
            body {{ 
                background: var(--bg); 
                color: #d1c4bc; 
                font-family: 'Segoe UI', Tahoma, sans-serif; 
                margin: 0; 
                display: flex; 
                height: 100vh;
                overflow: hidden;
            }}
            /* Sidebar Styling */
            .sidebar {{ 
                width: 260px; 
                background: #000; 
                border-right: 2px solid var(--deep-rust); 
                padding: 30px 20px;
                display: flex;
                flex-direction: column;
                box-shadow: 10px 0 20px rgba(0,0,0,0.7);
            }}
            .sidebar h2 {{ 
                color: var(--arcane-orange); 
                letter-spacing: 5px; 
                text-shadow: 0 0 12px var(--arcane-orange);
                margin-bottom: 5px;
                text-transform: uppercase;
            }}
            .sidebar-status {{ font-size: 11px; color: #6b3e2a; font-weight: bold; letter-spacing: 1px; margin-bottom: 40px; }}
            .nav-item {{ padding: 12px; color: #888; border-radius: 4px; transition: 0.3s; cursor: pointer; border-bottom: 1px solid #1a1a1a; }}
            .nav-item:hover {{ background: #1f0d06; color: var(--arcane-orange); }}
            .nav-active {{ color: var(--arcane-orange); border-left: 4px solid var(--arcane-orange); padding-left: 8px; background: #140c0a; }}
            
            /* Main Content Area */
            .main {{ 
                flex: 1; 
                padding: 40px; 
                background: radial-gradient(circle at top right, #1f0d06, #0d0705);
                overflow-y: auto;
            }}
            .header-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; border-bottom: 1px solid var(--deep-rust); padding-bottom: 15px; }}
            
            /* The Grid Layout (Marketplace Cards) */
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }}
            .slot {{ 
                background: #140c0a; 
                border: 1px solid #3d1f16; 
                padding: 25px; 
                border-radius: 4px; 
                position: relative;
                transition: 0.4s ease;
                animation: emberGlow 6s infinite ease-in-out;
            }}
            .slot:hover {{ transform: scale(1.02); border-color: var(--arcane-orange); box-shadow: 0 0 25px rgba(255,94,0,0.15); }}
            
            @keyframes emberGlow {{
                0% {{ border-color: #3d1f16; }}
                50% {{ border-color: #5e2f1b; }}
                100% {{ border-color: #3d1f16; }}
            }}

            .badge {{ color: var(--arcane-orange); border: 1px solid var(--arcane-orange); padding: 3px 10px; font-size: 11px; text-transform: uppercase; font-weight: bold; }}
            .btn {{ 
                background: rgba(255,94,0,0.05); 
                border: 1px solid var(--arcane-orange); 
                color: var(--arcane-orange); 
                padding: 12px; 
                width: 100%; 
                cursor: pointer; 
                margin-top: 15px;
                font-weight: bold;
                letter-spacing: 2px;
                text-transform: uppercase;
                transition: 0.3s;
            }}
            .btn:hover {{ background: var(--arcane-orange); color: #000; box-shadow: 0 0 15px var(--arcane-orange); }}
            
            .footer-credit {{ margin-top: auto; font-size: 10px; color: #444; border-top: 1px solid #222; padding-top: 20px; letter-spacing: 1px; }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2>ARCANE</h2>
            <div class="sidebar-status">VAULT_SYSTEM_V5.4</div>
            <div class="nav-item nav-active">📊 DASHBOARD</div>
            <div class="nav-item">📁 ALL_SCRIPTS</div>
            <div class="nav-item">🛡️ SECURITY_LOGS</div>
            <div class="footer-credit">
                <p>SYSTEM ARCHITECT: UNC</p>
                <p>ACCESS: AUTHORIZED ONLY</p>
            </div>
        </div>
        <div class="main">
            <div class="header-bar">
                <h1 style="letter-spacing:10px; text-transform:uppercase; color:#fff; margin:0;">Master_Vault</h1>
                <div style="color:var(--arcane-orange); font-weight:bold;">[ ENCRYPTION_ACTIVE ]</div>
            </div>
            <div class="grid">
                <div class="slot">
                    <span class="badge">ZEN LABS</span>
                    <h3>RUST ELITE PROTOCOL</h3>
                    <p style="font-size:14px; color:#888;">Optimized recoil sync for 2026 meta. Industrial precision calibrated by Unc.</p>
                    <button class="btn">ACCESS DATA</button>
                </div>
                <div class="slot">
                    <span class="badge">DYNASTY</span>
                    <h3>NBA 2K26 MASTER</h3>
                    <p style="font-size:14px; color:#888;">Precision green-window timing engine. Server-side latency compensation active.</p>
                    <button class="btn">ACCESS DATA</button>
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
    print('--- ARCANE VAULT: ONLINE ---')
    print('--- ARCHITECT: UNC ---')
    try:
        await bot.tree.sync()
        print("--- Commands Synced ---")
    except Exception as e:
        print(f"Sync Error: {e}")

# 5. SLASH COMMANDS
@bot.tree.command(name="status", description="Check the vault status")
async def status(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ ARCANE VAULT STATUS",
        description="**SYSTEMS OPERATIONAL.**\nUnauthorized access attempts will be logged.",
        color=0xff5e00
    )
    embed.add_field(name="Authorized Architect", value="UNC", inline=True)
    embed.add_field(name="Vault Response", value=f"⚡ {round(bot.latency * 1000)}ms", inline=True)
    embed.set_image(url=ARCANE_BANNER_URL)
    embed.set_footer(text="Arcane Security | Developed by Unc")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="welcome", description="Authorize a new Publisher member")
@app_commands.describe(member="The user to welcome")
async def welcome(interaction: discord.Interaction, member: discord.Member):
    welcome_embed = discord.Embed(
        title="🔥 ACCESS AUTHORIZED",
        description=f"Subject {member.mention} has been integrated into the Publishers Family.",
        color=0xff5e00
    )
    welcome_embed.add_field(name="Clearance Level", value="MASTER PUBLISHER", inline=False)
    welcome_embed.set_image(url=ARCANE_BANNER_URL)
    welcome_embed.set_footer(text="Developed by Unc")
    await interaction.response.send_message(content=f"Attention {member.mention}!", embed=welcome_embed)

# 6. EXECUTION BLOCK
if __name__ == "__main__":
    if not TOKEN:
        print("CRITICAL ERROR: No DISCORD_TOKEN found!")
    else:
        # Start the Marketplace Web Server
        threading.Thread(target=run_flask, daemon=True).start()
        time.sleep(2)
        # Launch the Arcane Bot
        bot.run(TOKEN)
