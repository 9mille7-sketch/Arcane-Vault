# ==============================================================================
# ARCANE MARKETPLACE OMNI-KERNEL [V5.0]
# DEVELOPED BY: UNC | CREDITS: COCO & ROEY
# ==============================================================================
# [ SYSTEM ARCHITECTURE ]
# 1. SECTOR ISOLATION: Each Discord server operates as a private "Market Sector".
# 2. HARDWARE BINDING: Keys are bound to specific Serial Numbers (SN) and Guilds.
# 3. MULTI-LEVEL STAFF: 
#    - LEVEL 0: User (Browse Only)
#    - LEVEL 1: Creator (Can upload scripts to their own Sector)
#    - LEVEL 2: Manager (Can generate keys for their own Sector)
#    - LEVEL 3: Publisher (Can manage Staff and Sector Settings)
#    - OWNER: UNC (Global Control & Blacklisting)
# ==============================================================================

import os
import sys
import json
import sqlite3
import discord
import uuid
import secrets
import datetime
import logging
import asyncio
import aiohttp
import threading
import time
import re
import csv
import io
from flask import Flask, jsonify, request, render_template_string, make_response, send_file
from flask_cors import CORS
from discord.ext import commands, tasks
from discord import app_commands, ui
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# [ SECTION 1: SYSTEM INITIALIZATION & LOGGING ]
# ------------------------------------------------------------------------------
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
LOG_CHANNEL_ID = 1479634666691629208  
OWNER_ID = 638512345678901234  # UNC'S ID

# Initialize Global Logger
logger = logging.getLogger("ArcaneOmniV5")
logger.setLevel(logging.INFO)

# File Handler for permanent logs
log_file = "arcane_v5_master.log"
file_handler = logging.FileHandler(log_file)
file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
file_handler.setFormatter(file_formatter)

# Console Handler for real-time monitoring
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter('\033[91m%(asctime)s\033[0m | %(message)s')
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DIR = os.path.join(BASE_DIR, "secure_vault_v5")
DB_PATH = os.path.join(BASE_DIR, "arcane_v5_omni.db")

# Ensure environment is ready
if not os.path.exists(VAULT_DIR):
    os.makedirs(VAULT_DIR)
    logger.info(f"System: Created secure storage vault at {VAULT_DIR}")

# ------------------------------------------------------------------------------
# [ SECTION 2: RELATIONAL DATABASE SCHEMA ]
# ------------------------------------------------------------------------------

def init_database():
    """Builds the heavy-duty relational schema for multi-publisher isolation."""
    logger.info("Database: Synchronizing Omni-Schema...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 2.1 Sectors Table: Defines the Discord Servers on the network
    c.execute('''CREATE TABLE IF NOT EXISTS sectors (
        guild_id TEXT PRIMARY KEY,
        publisher_id TEXT NOT NULL,
        staff_role_id TEXT NOT NULL,
        sector_name TEXT,
        sector_status TEXT DEFAULT 'ACTIVE',
        provisioned_by TEXT,
        provisioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 2.2 Staff Registry: Handles per-sector permissions
    c.execute('''CREATE TABLE IF NOT EXISTS staff_registry (
        user_id TEXT,
        guild_id TEXT,
        clearance_level INTEGER DEFAULT 1,
        added_by TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, guild_id),
        FOREIGN KEY (guild_id) REFERENCES sectors (guild_id) ON DELETE CASCADE
    )''')

    # 2.3 Product Catalog: The scripts, isolated by guild_id
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        guild_id TEXT NOT NULL,
        name TEXT NOT NULL,
        creator_id TEXT NOT NULL,
        category TEXT,
        file_name TEXT NOT NULL,
        description TEXT,
        version TEXT DEFAULT '1.0.0',
        download_count INTEGER DEFAULT 0,
        is_hidden INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (guild_id) REFERENCES sectors (guild_id) ON DELETE CASCADE
    )''')

    # 2.4 Ritual Keys: Access tokens for script redemption
    c.execute('''CREATE TABLE IF NOT EXISTS ritual_keys (
        key_string TEXT PRIMARY KEY,
        product_id TEXT NOT NULL,
        guild_id TEXT NOT NULL,
        creator_id TEXT NOT NULL,
        is_used INTEGER DEFAULT 0,
        redeemed_by_sn TEXT,
        redeemed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (product_id) ON DELETE CASCADE
    )''')

    # 2.5 Hardware Blacklist: Global device bans
    c.execute('''CREATE TABLE IF NOT EXISTS hardware_blacklist (
        serial_number TEXT PRIMARY KEY,
        reason TEXT,
        banned_by TEXT,
        banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # 2.6 Audit Telemetry: Detailed logs for every flash attempt
    c.execute('''CREATE TABLE IF NOT EXISTS flash_audit (
        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        serial TEXT,
        product_id TEXT,
        key_used TEXT,
        ip_address TEXT,
        status TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()
    logger.info("Database: Omni-Schema Sync Complete.")

init_database()

# ------------------------------------------------------------------------------
# [ SECTION 3: SYSTEM PERMISSION WRAPPERS ]
# ------------------------------------------------------------------------------

def check_unc(interaction: discord.Interaction) -> bool:
    """Checks if the user is the global system owner."""
    return interaction.user.id == OWNER_ID

def check_publisher(interaction: discord.Interaction) -> bool:
    """Checks if the user is the registered Lead Publisher for the current Sector."""
    if interaction.user.id == OWNER_ID:
        return True
    conn = sqlite3.connect(DB_PATH)
    res = conn.execute("SELECT 1 FROM sectors WHERE guild_id = ? AND publisher_id = ?", 
                       (str(interaction.guild.id), str(interaction.user.id))).fetchone()
    conn.close()
    return res is not None

def check_staff(level: int):
    """Decorator factory to check for specific staff clearance within a sector."""
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id == OWNER_ID:
            return True
        conn = sqlite3.connect(DB_PATH)
        res = conn.execute("SELECT clearance_level FROM staff_registry WHERE user_id = ? AND guild_id = ?", 
                           (str(interaction.user.id), str(interaction.guild.id))).fetchone()
        conn.close()
        return res and res[0] >= level
    return app_commands.check(predicate)

# ------------------------------------------------------------------------------
# [ SECTION 4: DISCORD KERNEL CORE ]
# ------------------------------------------------------------------------------

class ArcaneOmniBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.start_time = datetime.datetime.now()

    async def setup_hook(self):
        """Pre-launch synchronization."""
        self.heartbeat_monitor.start()
        await self.tree.sync()
        logger.info(f"Bot: Kernel v5.0 online. Latency: {round(self.latency * 1000)}ms")

    @tasks.loop(minutes=30)
    async def heartbeat_monitor(self):
        """Sends a detailed health report to the central log channel."""
        channel = self.get_channel(LOG_CHANNEL_ID)
        if channel:
            uptime = datetime.datetime.now() - self.start_time
            embed = discord.Embed(title="SYSTEM_HEALTH_REPORT", color=0x2ecc71, timestamp=datetime.datetime.now())
            embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=True)
            embed.add_field(name="Kernel Version", value="5.0_GOLD", inline=True)
            embed.set_footer(text="Developed by Unc | Arcane Omni-Network")
            await channel.send(embed=embed)

bot = ArcaneOmniBot()

# ------------------------------------------------------------------------------
# [ SECTION 5: OWNER COMMANDS (UNC ONLY) ]
# ------------------------------------------------------------------------------

@bot.tree.command(name="welcome", description="[UNC] Provision a new Market Sector for a server.")
@app_commands.check(check_unc)
async def welcome(interaction: discord.Interaction, publisher: discord.Member, staff_role: discord.Role):
    """Registers a server as an isolated sector and assigns a Lead Publisher."""
    await interaction.response.defer()
    
    conn = sqlite3.connect(DB_PATH)
    try:
        # Register the Sector
        conn.execute('''INSERT OR REPLACE INTO sectors 
                        (guild_id, publisher_id, staff_role_id, sector_name, provisioned_by) 
                        VALUES (?, ?, ?, ?, ?)''',
                     (str(interaction.guild.id), str(publisher.id), str(staff_role.id), 
                      interaction.guild.name, interaction.user.name))
        
        # Auto-Elevate the Publisher in their own Sector
        conn.execute('''INSERT OR REPLACE INTO staff_registry 
                        (user_id, guild_id, clearance_level, added_by) 
                        VALUES (?, ?, ?, ?)''',
                     (str(publisher.id), str(interaction.guild.id), 3, "UNC_SYSTEM"))
        
        conn.commit()
        
        embed = discord.Embed(title="SECTOR_PROVISION_SUCCESS", color=0xea4335)
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.add_field(name="Sector Name", value=interaction.guild.name, inline=True)
        embed.add_field(name="Lead Publisher", value=publisher.mention, inline=True)
        embed.add_field(name="Staff Permission", value=staff_role.mention, inline=False)
        embed.set_footer(text="Arcane Kernel V5.0 | Sector Isolation Active")
        
        await interaction.followup.send(embed=embed)
        logger.info(f"Owner: Provisioned Sector {interaction.guild.name} ({interaction.guild.id})")
        
    except Exception as e:
        logger.error(f"Error in welcome command: {e}")
        await interaction.followup.send("Critical failure in Sector Provisioning. Check logs.")
    finally:
        conn.close()

@bot.tree.command(name="remove_publisher", description="[UNC] Wipe a publisher and freeze their sector.")
@app_commands.check(check_unc)
async def remove_publisher(interaction: discord.Interaction, publisher: discord.Member):
    """Deletes all sector records and staff permissions for a publisher."""
    await interaction.response.defer()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM sectors WHERE guild_id = ? AND publisher_id = ?", 
                     (str(interaction.guild.id), str(publisher.id)))
        conn.execute("DELETE FROM staff_registry WHERE guild_id = ?", (str(interaction.guild.id),))
        conn.commit()
        
        await interaction.followup.send(f"💀 **REMOVAL COMPLETE:** Publisher **{publisher.name}** and all staff for this sector have been purged.")
        logger.info(f"Owner: Purged Sector {interaction.guild.name}")
    finally:
        conn.close()

@bot.tree.command(name="blacklist", description="[UNC] Globally ban a hardware serial from the network.")
@app_commands.check(check_unc)
async def blacklist(interaction: discord.Interaction, serial: str, reason: str):
    """Prevents a specific Zen/Matrix serial from using any keys in any sector."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO hardware_blacklist (serial_number, reason, banned_by) VALUES (?, ?, ?)",
                 (serial, reason, interaction.user.name))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(title="HARDWARE_EXCOMMUNICATED", color=0x000000)
    embed.add_field(name="Serial", value=f"`{serial}`", inline=True)
    embed.add_field(name="Reason", value=reason, inline=True)
    embed.set_footer(text="Global Blacklist Sync Complete")
    await interaction.response.send_message(embed=embed)

# ------------------------------------------------------------------------------
# [ SECTION 6: PUBLISHER COMMANDS (LVL 3) ]
# ------------------------------------------------------------------------------

@bot.tree.command(name="add_staff", description="[PUBLISHER] Add a Creator to your specific sector.")
@app_commands.check(check_publisher)
async def add_staff(interaction: discord.Interaction, member: discord.Member, level: int = 1):
    """Assigns staff roles within the specific publisher's sector."""
    if level > 3: level = 3
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''INSERT OR REPLACE INTO staff_registry 
                    (user_id, guild_id, clearance_level, added_by) 
                    VALUES (?, ?, ?, ?)''',
                 (str(member.id), str(interaction.guild.id), level, interaction.user.name))
    conn.commit()
    conn.close()
    
    await interaction.response.send_message(f"✅ User **{member.name}** authorized for **{interaction.guild.name}** at Level {level}.")

@bot.tree.command(name="sector_stats", description="[PUBLISHER] View analytics for your sector.")
@app_commands.check(check_publisher)
async def sector_stats(interaction: discord.Interaction):
    """Provides a data dump of total downloads and active products for the publisher."""
    conn = sqlite3.connect(DB_PATH)
    stats = conn.execute('''SELECT COUNT(product_id), SUM(download_count) 
                            FROM products WHERE guild_id = ?''', 
                         (str(interaction.guild.id),)).fetchone()
    conn.close()
    
    embed = discord.Embed(title=f"ANALYTICS: {interaction.guild.name}", color=0x3498db)
    embed.add_field(name="Total Products", value=stats[0] or 0, inline=True)
    embed.add_field(name="Total Flashes", value=stats[1] or 0, inline=True)
    await interaction.response.send_message(embed=embed)

# ------------------------------------------------------------------------------
# [ SECTION 7: CREATOR & MANAGER COMMANDS (LVL 1-2) ]
# ------------------------------------------------------------------------------

@bot.tree.command(name="market_upload", description="[CREATOR] Upload a script to YOUR sector's market.")
@check_staff(level=1)
async def market_upload(interaction: discord.Interaction, name: str, category: str, description: str, file: discord.Attachment):
    """Securely uploads a file and binds it to the current Sector ID."""
    await interaction.response.defer()
    
    # Validation
    if not file.filename.endswith(('.gpc', '.bin', '.txt', '.xmc')):
        return await interaction.followup.send("❌ Error: Unsupported file format.", ephemeral=True)

    pid = str(uuid.uuid4())[:8].upper()
    safe_name = secure_filename(f"{pid}_{file.filename}")
    storage_path = os.path.join(VAULT_DIR, safe_name)
    
    await file.save(storage_path)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''INSERT INTO products (product_id, guild_id, name, creator_id, category, file_name, description) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (pid, str(interaction.guild.id), name, str(interaction.user.id), category, safe_name, description))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(title="RELIC_COMMITTED", color=0x2ecc71)
    embed.add_field(name="Name", value=name, inline=True)
    embed.add_field(name="Relic ID", value=f"`{pid}`", inline=True)
    embed.add_field(name="Sector", value=interaction.guild.name, inline=False)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="gen_key", description="[MANAGER] Generate a Ritual Key for a script in your sector.")
@check_staff(level=2)
async def gen_key(interaction: discord.Interaction, product_id: str):
    """Mints a unique access key that is isolated to the current server's catalog."""
    conn = sqlite3.connect(DB_PATH)
    
    # Verification of Sector Isolation
    product = conn.execute("SELECT name FROM products WHERE product_id = ? AND guild_id = ?", 
                           (product_id.upper(), str(interaction.guild.id))).fetchone()
    
    if not product:
        conn.close()
        return await interaction.response.send_message("❌ Access Denied: This script is locked to another Sector or does not exist.", ephemeral=True)

    # Key Minting
    new_key = f"ARCANE-{secrets.token_hex(4).upper()}"
    conn.execute('''INSERT INTO ritual_keys (key_string, product_id, guild_id, creator_id) 
                    VALUES (?, ?, ?, ?)''',
                 (new_key, product_id.upper(), str(interaction.guild.id), str(interaction.user.id)))
    conn.commit()
    conn.close()
    
    embed = discord.Embed(title="RITUAL_KEY_MINTED", color=0x9b59b6)
    embed.add_field(name="Target Script", value=product[0], inline=True)
    embed.add_field(name="Key", value=f"||`{new_key}`||", inline=True)
    embed.set_footer(text="Valid for single use only | Sector Bound")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ------------------------------------------------------------------------------
# [ SECTION 8: UTILITY & HELP SYSTEM ]
# ------------------------------------------------------------------------------

@bot.tree.command(name="help", description="View authorized commands for your clearance level.")
async def help_command(interaction: discord.Interaction):
    """Dynamically builds a help menu based on database clearance and owner status."""
    is_owner = interaction.user.id == OWNER_ID
    conn = sqlite3.connect(DB_PATH)
    staff = conn.execute("SELECT clearance_level FROM staff_registry WHERE user_id = ? AND guild_id = ?", 
                         (str(interaction.user.id), str(interaction.guild.id))).fetchone()
    conn.close()
    
    lvl = staff[0] if staff else 0
    embed = discord.Embed(title="ARCANE_OMNI_INTERFACE", color=0xea4335)
    embed.description = "System credentials verified. Listing available modules..."
    
    # Layer 0: Public
    embed.add_field(name="🌐 SYSTEM", value="`/help` - Show this menu\n`/browse` - Browse Sector scripts", inline=False)
    
    # Layer 1: Creator
    if lvl >= 1 or is_owner:
        embed.add_field(name="🛠️ CREATOR_MODULE", value="`/market_upload` - Upload new scripts", inline=False)
    
    # Layer 2: Manager
    if lvl >= 2 or is_owner:
        embed.add_field(name="🗝️ MANAGER_MODULE", value="`/gen_key` - Mint access keys", inline=False)
        
    # Layer 3: Publisher
    if lvl >= 3 or is_owner:
        embed.add_field(name="🛡️ PUBLISHER_MODULE", value="`/add_staff` - Authorize Creators\n`/sector_stats` - View analytics", inline=False)
        
    # Layer 4: Unc/Owner
    if is_owner:
        embed.add_field(name="💀 ARCHITECT_CORE (UNC)", value="`/welcome` - Provision Sector\n`/remove_publisher` - Revoke Sector\n`/blacklist` - Global Ban\n`/export_logs` - Download Audit CSV", inline=False)
    
    embed.set_footer(text=f"User: {interaction.user.name} | Clearance: {'OWNER' if is_owner else f'LEVEL {lvl}'}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ------------------------------------------------------------------------------
# [ SECTION 9: WEB MARKETPLACE ENGINE (FLASK) ]
# ------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# --- REUSABLE UI COMPONENTS ---
HTML_HEAD = """
<head>
    <meta charset="UTF-8"><title>ARCANE MARKETPLACE</title>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@700&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #050505; --panel: #0d0d0d; --accent: #ea4335; --text: #d1bba4; }
        body { background: var(--bg); color: var(--text); font-family: 'Montserrat', sans-serif; margin: 0; overflow-x: hidden; }
        .nav { height: 70px; border-bottom: 2px solid var(--accent); display: flex; align-items: center; padding: 0 50px; background: var(--panel); position: sticky; top: 0; z-index: 100; }
        .container { padding: 50px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 30px; }
        .card { background: var(--panel); border: 1px solid #1a1a1a; padding: 30px; transition: 0.4s; position: relative; }
        .card:hover { border-color: var(--accent); transform: translateY(-5px); box-shadow: 0 10px 30px rgba(234, 67, 53, 0.1); }
        .card-title { font-family: 'Oswald'; font-size: 24px; color: white; margin: 10px 0; letter-spacing: 2px; }
        .badge { font-size: 10px; background: #222; padding: 4px 8px; border-radius: 3px; color: #888; text-transform: uppercase; }
        .btn { width: 100%; padding: 15px; background: transparent; border: 1px solid var(--accent); color: var(--accent); cursor: pointer; font-weight: 700; margin-top: 25px; text-transform: uppercase; letter-spacing: 2px; transition: 0.3s; }
        .btn:hover { background: var(--accent); color: black; }
        .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); display: none; align-items: center; justify-content: center; z-index: 1000; }
        .modal-box { width: 450px; background: var(--panel); border: 2px solid var(--accent); padding: 50px; text-align: center; }
        .input-altar { width: 100%; padding: 18px; background: #000; border: 1px solid #333; color: var(--accent); margin: 12px 0; font-family: 'Oswald'; text-align: center; font-size: 18px; letter-spacing: 2px; }
    </style>
</head>
"""

@app.route('/sector/<guild_id>')
def render_sector(guild_id):
    """Main landing page for a specific Sector."""
    conn = sqlite3.connect(DB_PATH)
    sector = conn.execute("SELECT sector_name FROM sectors WHERE guild_id = ?", (guild_id,)).fetchone()
    conn.close()
    
    if not sector:
        return "<h1>INVALID SECTOR ID</h1>", 404

    return render_template_string(f"""
        <!DOCTYPE html><html>{HTML_HEAD}
        <body>
            <div class="nav"><h1 style="font-family:'Oswald'; letter-spacing:5px; color:var(--accent);">ARCANE: {sector[0]}</h1></div>
            <div class="container">
                <div class="grid" id="market_grid"></div>
            </div>
            <div class="modal" id="flash_modal"><div class="modal-box">
                <h2 id="modal_title" style="font-family:'Oswald'; color:var(--accent);">SYSTEM_HANDSHAKE</h2>
                <input type="text" id="sn_field" class="input-altar" placeholder="ZEN SERIAL">
                <input type="text" id="key_field" class="input-altar" placeholder="RITUAL KEY">
                <button class="btn" style="background:var(--accent); color:black;" onclick="executeFlash()">AUTHORIZE SYNC</button>
                <button class="btn" style="border-color:#333; color:#333;" onclick="document.getElementById('flash_modal').style.display='none'">ABORT</button>
            </div></div>
            <script>
                let currentId = null;
                async function loadMarket() {{
                    const r = await fetch('/api/v5/list/{guild_id}');
                    const data = await r.json();
                    document.getElementById('market_grid').innerHTML = data.map(p => `
                        <div class="card">
                            <span class="badge">${{p.category}}</span>
                            <div class="card-title">${{p.name}}</div>
                            <p style="font-size:12px; opacity:0.6;">${{p.description}}</p>
                            <button class="btn" onclick="openFlash('${{p.product_id}}', '${{p.name}}')">GET SCRIPT</button>
                        </div>
                    `).join('');
                }}
                function openFlash(id, name) {{ 
                    currentId = id; 
                    document.getElementById('modal_title').innerText = "FLASH: " + name;
                    document.getElementById('flash_modal').style.display = 'flex'; 
                }}
                async function executeFlash() {{
                    const sn = document.getElementById('sn_field').value;
                    const key = document.getElementById('key_field').value;
                    const res = await fetch('/api/v5/redeem', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{ product_id: currentId, serial: sn, key: key, guild_id: '{guild_id}' }})
                    }});
                    const out = await res.json();
                    alert(out.message);
                    if(out.success) window.location.reload();
                }}
                loadMarket();
            </script>
        </body></html>
    """)

@app.route('/api/v5/list/<guild_id>')
def api_list(guild_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    data = conn.execute("SELECT * FROM products WHERE guild_id = ? AND is_hidden = 0", (guild_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in data])

@app.route('/api/v5/redeem', methods=['POST'])
def api_redeem():
    d = request.json
    sn, key, pid, gid = d.get('serial'), d.get('key'), d.get('product_id'), d.get('guild_id')
    ip = request.remote_addr
    
    conn = sqlite3.connect(DB_PATH)
    
    # Check Blacklist
    if conn.execute("SELECT 1 FROM hardware_blacklist WHERE serial_number = ?", (sn,)).fetchone():
        return jsonify({"success": False, "message": "HARDWARE BANNED"})

    # Check Key Integrity and Sector Isolation
    key_check = conn.execute('''SELECT 1 FROM ritual_keys 
                                WHERE key_string = ? AND product_id = ? AND guild_id = ? AND is_used = 0''', 
                             (key, pid, gid)).fetchone()
    
    if not key_check:
        conn.execute("INSERT INTO flash_audit (guild_id, serial, product_id, key_used, status, ip_address) VALUES (?,?,?,?,?,?)",
                     (gid, sn, pid, key, "DENIED_INVALID", ip))
        conn.commit()
        conn.close()
        return jsonify({"success": False, "message": "INVALID KEY FOR THIS SECTOR"})

    # Process Redemption
    conn.execute("UPDATE ritual_keys SET is_used = 1, redeemed_by_sn = ?, redeemed_at = ? WHERE key_string = ?", 
                 (sn, datetime.datetime.now(), key))
    conn.execute("UPDATE products SET download_count = download_count + 1 WHERE product_id = ?", (pid,))
    conn.execute("INSERT INTO flash_audit (guild_id, serial, product_id, key_used, status, ip_address) VALUES (?,?,?,?,?,?)",
                 (gid, sn, pid, key, "SUCCESS", ip))
    
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "HANDSHAKE SUCCESSFUL. PREPARING DOWNLOAD..."})

# ------------------------------------------------------------------------------
# [ SECTION 10: EXECUTION ENGINE ]
# ------------------------------------------------------------------------------

def start_web():
    logger.info("Web: Initializing Omni-Marketplace API...")
    app.run(host='0.0.0.0', port=10000, use_reloader=False)

if __name__ == "__main__":
    # Launch Web Server as a Daemon Thread
    threading.Thread(target=start_web, daemon=True).start()
    
    # Launch Discord Kernel
    if TOKEN:
        logger.info("Bot: Establishing connection to Arcane Network...")
        bot.run(TOKEN)
    else:
        logger.critical("FATAL: Discord Token missing from .env")
