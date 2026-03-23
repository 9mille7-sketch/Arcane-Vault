# ==============================================================================
# ARCANE MARKETPLACE KERNEL - MASTER BUILD [V3.8]
# DEVELOPED BY: UNC | CREDITS: COCO & ROEY
# ==============================================================================
# VERSION: 3.8.0_GOLD
# DESCRIPTION: FULL-STACK DISCORD/WEB HARDWARE DISTRIBUTOR
# ==============================================================================

import os
import json
import sqlite3
import discord
import uuid
import secrets
import datetime
import logging
import sys
import asyncio
import aiohttp
import threading
import time
import re
from flask import Flask, jsonify, request, render_template_string, make_response
from flask_cors import CORS
from discord.ext import commands, tasks
from discord import app_commands, ui
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# [ 1. ADVANCED SYSTEM CONFIGURATION ]
# ------------------------------------------------------------------------------
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
LOG_CHANNEL_ID = 1479634666691629208  
OWNER_ID = 638512345678901234  # UNC'S ID

# Multi-Output Logging System
logger = logging.getLogger("ArcaneSystem")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

file_handler = logging.FileHandler("arcane_master.log")
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Directory Hardening
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DIR = os.path.join(BASE_DIR, "relic_vault")
DB_PATH = os.path.join(BASE_DIR, "arcane_engine_v3_8.db")

for path in [VAULT_DIR]:
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Initialized Directory: {path}")

# ------------------------------------------------------------------------------
# [ 2. DATABASE ARCHITECTURE - RELATIONAL SCHEMA ]
# ------------------------------------------------------------------------------
def run_migration():
    """Builds the multi-table architecture for secure script distribution."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # SECTORS: Server-specific configurations
    c.execute('''CREATE TABLE IF NOT EXISTS sectors (
        guild_id TEXT PRIMARY KEY, 
        publisher_id TEXT, 
        staff_role_id TEXT, 
        sector_name TEXT,
        provisioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # STAFF: Permissions registry
    c.execute('''CREATE TABLE IF NOT EXISTS staff_registry (
        user_id TEXT PRIMARY KEY, 
        username TEXT, 
        clearance_level INTEGER, 
        guild_id TEXT,
        added_by TEXT,
        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # PRODUCTS: The Marketplace Catalog
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY, 
        name TEXT, 
        creator_id TEXT, 
        category TEXT, 
        file_name TEXT, 
        description TEXT, 
        version TEXT DEFAULT '1.0',
        downloads INTEGER DEFAULT 0,
        is_hidden INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # KEYS: The Single-Use Handshake Tokens
    c.execute('''CREATE TABLE IF NOT EXISTS ritual_keys (
        key_string TEXT PRIMARY KEY, 
        product_id TEXT, 
        creator_id TEXT, 
        is_redeemed INTEGER DEFAULT 0, 
        redeemed_by_sn TEXT,
        redeemed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(product_id)
    )''')

    # BLACKLIST: Hardware Ban Registry
    c.execute('''CREATE TABLE IF NOT EXISTS hardware_blacklist (
        serial_number TEXT PRIMARY KEY, 
        reason TEXT, 
        banned_by TEXT, 
        banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # ANALYTICS: Telemetry for every flash attempt
    c.execute('''CREATE TABLE IF NOT EXISTS flash_telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        serial TEXT,
        product_id TEXT,
        key_used TEXT,
        ip_addr TEXT,
        status TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()
    logger.info("Database Schema V3.8 Migration Successful.")

run_migration()

# ------------------------------------------------------------------------------
# [ 3. DISCORD BOT ENGINE - CUSTOM CLASS ]
# ------------------------------------------------------------------------------
class ArcaneKernel(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.uptime = datetime.datetime.now()

    async def setup_hook(self):
        self.maintenance_loop.start()
        await self.tree.sync()
        logger.info("Command Tree Synced Across All Sectors.")

    @tasks.loop(minutes=30)
    async def maintenance_loop(self):
        """Auto-cleanup of expired sessions and system health check."""
        channel = self.get_channel(LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(title="SYSTEM_HEARTBEAT", color=0xea4335)
            embed.add_field(name="Kernel Uptime", value=str(datetime.datetime.now() - self.uptime).split('.')[0])
            embed.add_field(name="DB Connections", value="Active", inline=True)
            embed.set_footer(text="DEVELOPED BY UNC | V3.8")
            await channel.send(embed=embed)

bot = ArcaneKernel()

# --- PERMISSION SECURITY WRAPPERS ---

def is_unc():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == OWNER_ID
    return app_commands.check(predicate)

def has_staff_clearance():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == OWNER_ID: return True
        conn = sqlite3.connect(DB_PATH)
        user = conn.execute("SELECT 1 FROM staff_registry WHERE user_id = ?", (str(interaction.user.id),)).fetchone()
        conn.close()
        return user is not None
    return app_commands.check(predicate)

# ------------------------------------------------------------------------------
# [ 4. SLASH COMMANDS - THE MASTER SUITE ]
# ------------------------------------------------------------------------------

@bot.tree.command(name="welcome", description="Provision this server as an official Arcane Marketplace Sector.")
@is_unc()
async def welcome(interaction: discord.Interaction, publisher: discord.Member, staff_role: discord.Role):
    """Binds a guild to the marketplace engine and sets the Lead Publisher."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("INSERT OR REPLACE INTO sectors (guild_id, publisher_id, staff_role_id, sector_name) VALUES (?, ?, ?, ?)",
                     (str(interaction.guild.id), str(publisher.id), str(staff_role.id), interaction.guild.name))
        
        # Elevate Publisher to Clearance Level 3
        conn.execute("INSERT OR REPLACE INTO staff_registry (user_id, username, clearance_level, guild_id, added_by) VALUES (?, ?, ?, ?, ?)",
                     (str(publisher.id), publisher.name, 3, str(interaction.guild.id), "UNC_SYSTEM"))
        conn.commit()
        
        embed = discord.Embed(title="SECTOR_PROVISION_COMPLETE", color=0xea4335)
        embed.description = f"Guild `{interaction.guild.name}` is now linked to the Global Marketplace."
        embed.add_field(name="Lead Publisher", value=publisher.mention)
        embed.add_field(name="Authorized Role", value=staff_role.mention)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Kernel Error: {e}", ephemeral=True)
    finally:
        conn.close()

@bot.tree.command(name="gen_key", description="Generate a single-use Ritual Key for a user.")
@has_staff_clearance()
@app_commands.describe(product_id="Find the ID in the Marketplace list")
async def gen_key(interaction: discord.Interaction, product_id: str):
    """Allows Publishers/Creators to mint keys for users."""
    conn = sqlite3.connect(DB_PATH)
    product = conn.execute("SELECT name FROM products WHERE product_id = ?", (product_id.upper(),)).fetchone()
    
    if not product:
        conn.close()
        return await interaction.response.send_message(f"Relic ID `{product_id}` not found in the vault.", ephemeral=True)

    # Key Construction
    ritual_key = f"ARCANE-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
    
    conn.execute("INSERT INTO ritual_keys (key_string, product_id, creator_id) VALUES (?, ?, ?)",
                 (ritual_key, product_id.upper(), str(interaction.user.id)))
    conn.commit()
    conn.close()

    embed = discord.Embed(title="RITUAL KEY GENERATED", color=0x2ecc71)
    embed.add_field(name="Relic", value=product[0], inline=True)
    embed.add_field(name="Key", value=f"||`{ritual_key}`||", inline=True)
    embed.set_footer(text="Deliver this key to the user. Valid for single flash only.")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="market_upload", description="Creator Tool: Upload a new script binary to the marketplace.")
@has_staff_clearance()
async def market_upload(interaction: discord.Interaction, name: str, category: str, description: str, file: discord.Attachment):
    """The bridge between Discord and the Web Storage."""
    if not file.filename.endswith(('.gpc', '.bin', '.txt')):
        return await interaction.response.send_message("Unsupported file format.", ephemeral=True)

    pid = str(uuid.uuid4())[:8].upper()
    safe_name = secure_filename(f"{pid}_{file.filename}")
    
    await file.save(os.path.join(VAULT_DIR, safe_name))
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO products (product_id, name, creator_id, category, file_name, description) VALUES (?, ?, ?, ?, ?, ?)",
                 (pid, name, str(interaction.user.id), category, safe_name, description))
    conn.commit()
    conn.close()
    
    await interaction.response.send_message(f"✅ Relic `{name}` committed to Marketplace. ID: `{pid}`")

@bot.tree.command(name="blacklist", description="Globally ban a hardware serial from the network.")
@is_unc()
async def blacklist(interaction: discord.Interaction, serial: str, reason: str):
    """Total excommunication of a hardware ID."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO hardware_blacklist (serial_number, reason, banned_by) VALUES (?, ?, ?)",
                 (serial, reason, interaction.user.name))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"💀 Hardware `{serial}` has been purged from the network.")

# --- ADVANCED UI PAGINATION ---

class MarketplaceView(ui.View):
    def __init__(self, items, page=1):
        super().__init__(timeout=60)
        self.items = items
        self.page = page
        self.per_page = 5
        self.max_pages = (len(items) - 1) // self.per_page + 1

    @ui.button(label="PREV", style=discord.ButtonStyle.grey)
    async def prev(self, interaction: discord.Interaction, button: ui.Button):
        if self.page > 1:
            self.page -= 1
            await self.update(interaction)

    @ui.button(label="NEXT", style=discord.ButtonStyle.red)
    async def next(self, interaction: discord.Interaction, button: ui.Button):
        if self.page < self.max_pages:
            self.page += 1
            await self.update(interaction)

    async def update(self, interaction: discord.Interaction):
        start = (self.page - 1) * self.per_page
        end = start + self.per_page
        subset = self.items[start:end]
        
        embed = discord.Embed(title="ARCANE MARKETPLACE CATALOG", color=0xea4335)
        for p in subset:
            embed.add_field(name=f"{p[1]} [ID: {p[0]}]", value=f"*{p[5]}*", inline=False)
        embed.set_footer(text=f"Page {self.page} of {self.max_pages}")
        await interaction.response.edit_message(embed=embed, view=self)

@bot.tree.command(name="browse", description="View the global catalog of scripts.")
async def browse(interaction: discord.Interaction):
    conn = sqlite3.connect(DB_PATH)
    products = conn.execute("SELECT * FROM products WHERE is_hidden = 0").fetchall()
    conn.close()
    
    if not products: return await interaction.response.send_message("Vault is empty.")
    
    view = MarketplaceView(products)
    embed = discord.Embed(title="ARCANE MARKETPLACE CATALOG", color=0xea4335)
    for p in products[:5]:
        embed.add_field(name=f"{p[1]} [ID: {p[0]}]", value=f"*{p[5]}*", inline=False)
    
    await interaction.response.send_message(embed=embed, view=view)

# ------------------------------------------------------------------------------
# [ 5. WEB KERNEL - PRODUCTION FLASK API ]
# ------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)
app.secret_key = secrets.token_hex(64)

MASTER_MARKETPLACE_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARCANE MARKETPLACE</title>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@700&family=Montserrat:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #050505; --panel: #0d0d0d; --accent: #ea4335; --text: #d1bba4; }
        body { background: var(--bg); color: var(--text); font-family: 'Montserrat', sans-serif; margin: 0; }
        .nav { height: 70px; border-bottom: 2px solid var(--accent); display: flex; align-items: center; padding: 0 50px; background: var(--panel); }
        .hero { padding: 80px 50px; text-align: center; border-bottom: 1px solid #1a1a1a; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 30px; padding: 50px; }
        .card { background: var(--panel); border: 1px solid #222; padding: 25px; transition: 0.3s; }
        .card:hover { border-color: var(--accent); transform: translateY(-5px); }
        .btn { width: 100%; padding: 12px; background: transparent; border: 1px solid var(--accent); color: var(--accent); cursor: pointer; font-weight: 700; margin-top: 20px; text-transform: uppercase; }
        .btn:hover { background: var(--accent); color: black; }
        .modal { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: none; align-items: center; justify-content: center; z-index: 1000; }
        .modal-box { width: 450px; background: var(--panel); border: 2px solid var(--accent); padding: 40px; text-align: center; }
        .input-altar { width: 100%; padding: 15px; background: #000; border: 1px solid #333; color: var(--accent); margin: 10px 0; font-family: 'Oswald'; text-align: center; font-size: 18px; }
    </style>
</head>
<body>
    <div class="nav"><h1 style="font-family:'Oswald'; letter-spacing:4px; color:var(--accent);">ARCANE MARKETPLACE</h1></div>
    <div class="hero">
        <h2 style="font-family:'Oswald'; font-size:40px; margin:0;">GLOBAL RELIC ARCHIVE</h2>
        <p style="opacity:0.5; letter-spacing:2px;">DEVELOPED BY UNC | MIRROR V3.8</p>
    </div>
    <div class="grid" id="market_grid"></div>

    <div class="modal" id="flash_modal">
        <div class="modal-box">
            <h2 id="modal_title" style="font-family:'Oswald'; color:var(--accent);">AUTHORIZE FLASH</h2>
            <input type="text" id="sn_field" class="input-altar" placeholder="HARDWARE SERIAL">
            <input type="text" id="key_field" class="input-altar" placeholder="RITUAL KEY (ARCANE-XXXX)">
            <button class="btn" style="background:var(--accent); color:black;" onclick="submitFlash()">START SYNC</button>
            <button class="btn" style="border-color:#333; color:#333;" onclick="document.getElementById('flash_modal').style.display='none'">CANCEL</button>
        </div>
    </div>

    <script>
        let targetId = null;
        async function load() {
            const res = await fetch('/api/v1/list');
            const data = await res.json();
            document.getElementById('market_grid').innerHTML = data.map(p => `
                <div class="card">
                    <div style="font-size:10px; color:#555;">${p.category}</div>
                    <h3 style="font-family:'Oswald'; color:white; margin:10px 0;">${p.name}</h3>
                    <p style="font-size:12px; height:40px; overflow:hidden;">${p.description}</p>
                    <button class="btn" onclick="openFlash('${p.product_id}', '${p.name}')">DOWNLOAD SCRIPT</button>
                </div>
            `).join('');
        }
        function openFlash(id, name) {
            targetId = id;
            document.getElementById('modal_title').innerText = "FLASH: " + name;
            document.getElementById('flash_modal').style.display = 'flex';
        }
        async function submitFlash() {
            const sn = document.getElementById('sn_field').value;
            const key = document.getElementById('key_field').value;
            const res = await fetch('/api/v1/redeem', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ product_id: targetId, serial: sn, key: key })
            });
            const out = await res.json();
            alert(out.message);
            if(out.success) window.location.reload();
        }
        load();
    </script>
</body>
</html>
"""

@app.route('/')
def web_index():
    return render_template_string(MASTER_MARKETPLACE_HTML)

@app.route('/api/v1/list')
def api_list():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    data = conn.execute("SELECT * FROM products WHERE is_hidden = 0").fetchall()
    conn.close()
    return jsonify([dict(row) for row in data])

@app.route('/api/v1/redeem', methods=['POST'])
def api_redeem():
    d = request.json
    sn, key, pid = d.get('serial'), d.get('key'), d.get('product_id')
    ip = request.remote_addr
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Global Blacklist Check
    if conn.execute("SELECT 1 FROM hardware_blacklist WHERE serial_number = ?", (sn,)).fetchone():
        return jsonify({"success": False, "message": "HARDWARE SERIAL BANNED."})

    # 2. Key Validation
    k_data = conn.execute("SELECT * FROM ritual_keys WHERE key_string = ? AND product_id = ? AND is_redeemed = 0", 
                          (key, pid)).fetchone()
    
    if not k_data:
        conn.execute("INSERT INTO flash_telemetry (serial, product_id, key_used, ip_addr, status) VALUES (?,?,?,?,?)",
                     (sn, pid, key, ip, "DENIED_INVALID_KEY"))
        conn.commit()
        conn.close()
        return jsonify({"success": False, "message": "INVALID KEY OR KEY ALREADY USED."})

    # 3. Commit Success
    conn.execute("UPDATE ritual_keys SET is_redeemed = 1, redeemed_by_sn = ?, redeemed_at = ? WHERE key_string = ?", 
                 (sn, datetime.datetime.now(), key))
    conn.execute("UPDATE products SET downloads = downloads + 1 WHERE product_id = ?", (pid,))
    conn.execute("INSERT INTO flash_telemetry (serial, product_id, key_used, ip_addr, status) VALUES (?,?,?,?,?)",
                 (sn, pid, key, ip, "SUCCESS"))
    
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "HANDSHAKE SUCCESSFUL. PREPARING DOWNLOAD..."})

# ------------------------------------------------------------------------------
# [ 6. EXECUTION LAYER ]
# ------------------------------------------------------------------------------

def run_web():
    logger.info("Initializing Arcane Marketplace API...")
    app.run(host='0.0.0.0', port=10000, use_reloader=False)

if __name__ == "__main__":
    # Start Web Interface
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    # Start Discord Kernel
    if TOKEN:
        logger.info("Connecting to Arcane Discord Kernel...")
        bot.run(TOKEN)
    else:
        logger.critical("NO DISCORD_TOKEN FOUND.")
