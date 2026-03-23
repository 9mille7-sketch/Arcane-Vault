# ==============================================================================
# ARCANE MARKETPLACE OMNI-SYSTEM [V8.0] - THE SACRED ALTAR
# DEVELOPED BY: Unc 
# CREDITS: Coco, Roey
# MASTER ARCHITECT ID: 1063556821517877258
# MASTER GUILD ID: 1483266011728838719
# MASTER LOG CHANNEL: 1485513827222290572
# ==============================================================================
# [ SYSTEM PROTOCOLS ]
# 1. NO REAL NAMES: Branding is strictly 'Developed By Unc'.
# 2. MASTER LOCK: Only ID 1063556821517877258 can authorize Kingdoms.
# 3. SECTOR ISOLATION: Multi-tenant database logic for script security.
# 4. AZTEC THEME: Jade, Obsidian, and Mayan Gold UI aesthetics.
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
import threading
import traceback
import platform
import time
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from discord.ext import commands, tasks
from discord import app_commands, ui
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# [ SECTION 1: SACRED CONSTANTS ]
# ------------------------------------------------------------------------------
load_dotenv()

TOKEN = os.environ.get("DISCORD_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# THE ARCHITECT'S SEAL
MASTER_OWNER_ID = 1063556821517877258
MASTER_GUILD_ID = 1483266011728838719
MASTER_LOG_ID = 1485513827222290572

# AZTEC PALETTE
OBSIDIAN_CODE = 0x0a0a0a
JADE_GLOW = 0x00a86b
MAYAN_GOLD = 0xd4af37
BLOOD_SACRIFICE = 0x8b0000

# FILE SYSTEM
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH = os.path.join(BASE_DIR, "arcane_vault_relics")
DB_NAME = "arcane_altar_v8.db"

if not os.path.exists(VAULT_PATH):
    os.makedirs(VAULT_PATH)

# ------------------------------------------------------------------------------
# [ SECTION 2: THE RELIQUARY (DATABASE) ]
# ------------------------------------------------------------------------------
class Reliquary:
    def __init__(self, db_file):
        self.db_file = db_file
        self.initialize_temple()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_temple(self):
        conn = self.get_connection()
        c = conn.cursor()
        
        # Kingdoms: The Mayan Territories (Servers)
        c.execute('''CREATE TABLE IF NOT EXISTS kingdoms (
            guild_id TEXT PRIMARY KEY,
            publisher_id TEXT NOT NULL,
            name TEXT,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # Hierarchy: The Priests and Nobles (Staff)
        c.execute('''CREATE TABLE IF NOT EXISTS hierarchy (
            user_id TEXT,
            guild_id TEXT,
            rank INTEGER DEFAULT 1, -- 1: Warrior, 2: High Priest, 3: Ruler
            appointed_by TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )''')

        # Relics: The Sacred Scripts
        c.execute('''CREATE TABLE IF NOT EXISTS relics (
            relic_id TEXT PRIMARY KEY,
            guild_id TEXT NOT NULL,
            relic_name TEXT NOT NULL,
            relic_tier TEXT,
            file_pointer TEXT NOT NULL,
            rituals_performed INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )''')

        # Ritual Keys: Access tokens
        c.execute('''CREATE TABLE IF NOT EXISTS ritual_keys (
            key_string TEXT PRIMARY KEY,
            relic_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            is_consumed INTEGER DEFAULT 0,
            hardware_bound TEXT,
            consumed_at TIMESTAMP
        )''')

        # Forbidden Scrolls: Global HWID Blacklist
        c.execute('''CREATE TABLE IF NOT EXISTS forbidden_scrolls (
            hwid TEXT PRIMARY KEY,
            curse_reason TEXT,
            banished_by TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # Telemetry: Flash Logs
        c.execute('''CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hwid TEXT,
            action TEXT,
            guild_id TEXT,
            relic_id TEXT,
            status TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.commit()
        conn.close()

db_manager = Reliquary(DB_NAME)

# ------------------------------------------------------------------------------
# [ SECTION 3: PERMISSION FIREWALL ]
# ------------------------------------------------------------------------------
def is_unc_architect():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == MASTER_OWNER_ID:
            return True
        await interaction.response.send_message("🐍 **CURSE OF KUKULKAN:** Unauthorized access to the Architect's chamber.", ephemeral=True)
        return False
    return app_commands.check(predicate)

def has_temple_rank(required_rank: int):
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == MASTER_OWNER_ID:
            return True
        conn = db_manager.get_connection()
        user_data = conn.execute("SELECT rank FROM hierarchy WHERE user_id = ? AND guild_id = ?", 
                                (str(interaction.user.id), str(interaction.guild.id))).fetchone()
        conn.close()
        if user_data and user_data['rank'] >= required_rank:
            return True
        await interaction.response.send_message(f"❌ **RANK INSUFFICIENT.** Rank {required_rank} required in this Kingdom.", ephemeral=True)
        return False
    return app_commands.check(predicate)

# ------------------------------------------------------------------------------
# [ SECTION 4: THE SACRED BOT INTERFACE ]
# ------------------------------------------------------------------------------
class ArcaneTemple(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all(), help_command=None)

    async def setup_hook(self):
        await self.tree.sync()
        self.temple_heartbeat.start()

    @tasks.loop(minutes=20)
    async def temple_heartbeat(self):
        log_ch = self.get_channel(MASTER_LOG_ID)
        if log_ch:
            embed = discord.Embed(title="🌞 **Temple Pulse**", color=JADE_GLOW, timestamp=datetime.datetime.now())
            embed.set_footer(text="Developed By Unc | Credits: Coco, Roey")
            await log_ch.send(embed=embed)

bot = ArcaneTemple()

# --- [ ARCHITECT (UNC) COMMANDS ] ---

@bot.tree.command(name="welcome", description="[UNC ONLY] Provision a new Kingdom Sector.")
@is_unc_architect()
async def welcome(interaction: discord.Interaction, publisher: discord.Member):
    conn = db_manager.get_connection()
    conn.execute("INSERT OR REPLACE INTO kingdoms (guild_id, publisher_id, name) VALUES (?,?,?)",
                 (str(interaction.guild.id), str(publisher.id), interaction.guild.name))
    conn.execute("INSERT OR REPLACE INTO hierarchy (user_id, guild_id, rank, appointed_by) VALUES (?,?,?,?)",
                 (str(publisher.id), str(interaction.guild.id), 3, "UNC"))
    conn.commit()
    conn.close()
    
    e = discord.Embed(title="🔱 **New Kingdom Established**", color=MAYAN_GOLD)
    e.add_field(name="Kingdom", value=interaction.guild.name)
    e.add_field(name="Ruler (Publisher)", value=publisher.mention)
    e.set_footer(text="Developed By Unc")
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="appoint_staff", description="[UNC ONLY] Grant a rank to a member.")
@is_unc_architect()
async def appoint_staff(interaction: discord.Interaction, member: discord.Member, rank: int):
    conn = db_manager.get_connection()
    conn.execute("INSERT OR REPLACE INTO hierarchy (user_id, guild_id, rank, appointed_by) VALUES (?,?,?,?)",
                 (str(member.id), str(interaction.guild.id), rank, "UNC"))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"🏺 {member.mention} has been appointed to **Rank {rank}** by the Architect.")

@bot.tree.command(name="banish", description="[UNC ONLY] Add HWID to Forbidden Scrolls.")
@is_unc_architect()
async def banish(interaction: discord.Interaction, hwid: str, reason: str):
    conn = db_manager.get_connection()
    conn.execute("INSERT OR REPLACE INTO forbidden_scrolls (hwid, curse_reason, banished_by) VALUES (?,?,?)",
                 (hwid, reason, "UNC"))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"💀 **BANISHMENT COMPLETE:** `{hwid}` is now cursed.")

# --- [ KINGDOM STAFF COMMANDS ] ---

@bot.tree.command(name="market_upload", description="[RANK 1+] Sacrifice a new relic.")
@has_temple_rank(1)
async def market_upload(interaction: discord.Interaction, name: str, tier: str, file: discord.Attachment):
    relic_id = f"RLC-{secrets.token_hex(3).upper()}"
    safe_name = secure_filename(f"{relic_id}_{file.filename}")
    await file.save(os.path.join(VAULT_PATH, safe_name))
    
    conn = db_manager.get_connection()
    conn.execute("INSERT INTO relics (relic_id, guild_id, relic_name, relic_tier, file_pointer) VALUES (?,?,?,?,?)",
                 (relic_id, str(interaction.guild.id), name, tier, safe_name))
    conn.commit()
    conn.close()
    
    await interaction.response.send_message(f"🟢 **RELIC BOUND:** `{name}` (ID: `{relic_id}`)")

@bot.tree.command(name="mint_key", description="[RANK 2+] Create a Ritual Access Key.")
@has_temple_rank(2)
async def mint_key(interaction: discord.Interaction, relic_id: str):
    new_key = f"ARC-{secrets.token_hex(4).upper()}"
    conn = db_manager.get_connection()
    conn.execute("INSERT INTO ritual_keys (key_string, relic_id, guild_id) VALUES (?,?,?)",
                 (new_key, relic_id.upper(), str(interaction.guild.id)))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"🗝️ **RITUAL KEY MINTED:** `{new_key}`", ephemeral=True)

# ------------------------------------------------------------------------------
# [ SECTION 5: THE ARCANE WEB INTERFACE ]
# ------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

ALTAR_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ARCANE ALTAR | DEVELOPED BY UNC</title>
    <style>
        body { background-color: #0a0a0a; color: #d4af37; font-family: 'Courier New', monospace; margin: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; }
        .temple-container { border: 2px solid #00a86b; padding: 40px; box-shadow: 0 0 30px #00a86b; border-radius: 20px; text-align: center; max-width: 800px; }
        h1 { font-size: 3em; color: #00a86b; text-shadow: 0 0 10px #00a86b; margin-bottom: 10px; }
        .divider { height: 2px; background: linear-gradient(to right, transparent, #d4af37, transparent); margin: 20px 0; }
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px; }
        .stat-card { border: 1px solid #d4af37; padding: 20px; background: rgba(0, 168, 107, 0.05); }
        .stat-value { font-size: 2em; color: #ffffff; }
        .credits { margin-top: 40px; color: #555; font-size: 0.9em; }
        .highlight { color: #00a86b; }
    </style>
</head>
<body>
    <div class="temple-container">
        <h1>ARCANE VAULT</h1>
        <p class="highlight">CORE LOCKDOWN ACTIVE | SYSTEM SECURE</p>
        <div class="divider"></div>
        <div class="stats-grid">
            <div class="stat-card"><h3>TOTAL RITUALS</h3><div class="stat-value">{{ rituals }}</div></div>
            <div class="stat-card"><h3>ACTIVE KINGDOMS</h3><div class="stat-value">{{ kingdoms }}</div></div>
        </div>
        <div class="credits">
            DEVELOPED BY <span class="highlight">UNC</span><br>
            CREDITS TO <span class="highlight">COCO & ROEY</span>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def altar_home():
    conn = db_manager.get_connection()
    rituals = conn.execute("SELECT SUM(rituals_performed) FROM relics").fetchone()[0] or 0
    kingdoms = conn.execute("SELECT COUNT(*) FROM kingdoms").fetchone()[0] or 0
    conn.close()
    return render_template_string(ALTAR_HTML, rituals=rituals, kingdoms=kingdoms)

@app.route('/api/v8/ritual', methods=['POST'])
def perform_ritual():
    data = request.json
    hwid = data.get('hwid')
    key = data.get('key')
    relic_id = data.get('relic_id')
    guild_id = data.get('guild_id')

    conn = db_manager.get_connection()
    
    # 1. Blacklist Check
    if conn.execute("SELECT 1 FROM forbidden_scrolls WHERE hwid = ?", (hwid,)).fetchone():
        return jsonify({"success": False, "msg": "HWID_CURSED"}), 403

    # 2. Ritual Handshake
    key_check = conn.execute("SELECT 1 FROM ritual_keys WHERE key_string = ? AND relic_id = ? AND guild_id = ? AND is_consumed = 0",
                            (key, relic_id, guild_id)).fetchone()
    
    if not key_check:
        conn.execute("INSERT INTO telemetry (hwid, action, guild_id, relic_id, status) VALUES (?,?,?,?,?)",
                     (hwid, "RITUAL_ATTEMPT", guild_id, relic_id, "FAILED"))
        conn.commit()
        conn.close()
        return jsonify({"success": False, "msg": "INVALID_OFFERING"}), 400

    # 3. Consumption Logic
    conn.execute("UPDATE ritual_keys SET is_consumed = 1, hardware_bound = ?, consumed_at = ? WHERE key_string = ?",
                 (hwid, datetime.datetime.now(), key))
    conn.execute("UPDATE relics SET rituals_performed = rituals_performed + 1 WHERE relic_id = ?", (relic_id,))
    conn.execute("INSERT INTO telemetry (hwid, action, guild_id, relic_id, status) VALUES (?,?,?,?,?)",
                 (hwid, "RITUAL_COMPLETE", guild_id, relic_id, "SUCCESS"))
    conn.commit()
    conn.close()

    # Master Telemetry Notification
    asyncio.run_coroutine_threadsafe(
        bot.get_channel(MASTER_LOG_ID).send(f"⚡ **SACRED RITUAL:** `{hwid}` consumed key for Relic `{relic_id}` (Kingdom: `{guild_id}`)"), 
        bot.loop
    )
    
    return jsonify({"success": True, "token": secrets.token_hex(16)})

def run_flask_altar():
    app.run(host='0.0.0.0', port=PORT, use_reloader=False)

# ------------------------------------------------------------------------------
# [ SECTION 6: INVOCATION ]
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    if not TOKEN:
        print("CRITICAL: DISCORD_TOKEN NOT FOUND IN ENVIRONMENT.")
        sys.exit(1)

    # Launch Web Engine
    threading.Thread(target=run_flask_altar, daemon=True).start()
    
    # Launch Discord Kernel
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"KERNEL PANIC: {e}")
