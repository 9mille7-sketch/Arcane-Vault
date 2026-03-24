# ==============================================================================
# ARCANE MARKETPLACE OMNI-SYSTEM [V9.0] - THE GREAT ALTAR
# DEVELOPED BY: Unc 
# CREDITS: Coco, Roey
# MASTER ARCHITECT ID: 1063556821517877258
# ==============================================================================
# [ MIRROR SPECIFICATIONS: C-MIND API ]
# - DYNAMIC RELIC REGISTRY: Upload and manage scripts by Sector (Guild).
# - RITUAL HANDSHAKE: Bi-directional HWID + Key + Relic validation.
# - THEMED TELEMETRY: Real-time logging of all flashes to the Master Altar.
# - UI: Aztec/Mayan Obsidian & Jade Dashboard.
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
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from discord.ext import commands, tasks
from discord import app_commands, ui
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# [ SECTION 1: CORE SACRED CONFIG ]
# ------------------------------------------------------------------------------
load_dotenv()

TOKEN = os.environ.get("DISCORD_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# THE ARCHITECT'S SEAL (ID 1063556821517877258)
MASTER_OWNER_ID = 1063556821517877258
MASTER_GUILD_ID = 1483266011728838719
MASTER_LOG_ID = 1485513827222290572

# AZTEC PALETTE & BRANDING
JADE = 0x00a86b
MAYAN_GOLD = 0xd4af37
OBSIDIAN = 0x0a0a0a
BRANDING = "Developed By Unc | Credits: Coco, Roey"

# FILE SYSTEM
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH = os.path.join(BASE_DIR, "arcane_vault_v9")
DB_NAME = "arcane_altar_v9.db"

if not os.path.exists(VAULT_PATH):
    os.makedirs(VAULT_PATH)

# ------------------------------------------------------------------------------
# [ SECTION 2: THE RELIQUARY (DATABASE ENGINE) ]
# ------------------------------------------------------------------------------
class Reliquary:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_temple()

    def get_conn(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def init_temple(self):
        conn = self.get_conn()
        c = conn.cursor()
        # Kingdoms (Servers)
        c.execute('CREATE TABLE IF NOT EXISTS kingdoms (guild_id TEXT PRIMARY KEY, publisher_id TEXT, name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        # Hierarchy (Staff)
        c.execute('CREATE TABLE IF NOT EXISTS hierarchy (user_id TEXT, guild_id TEXT, rank INTEGER, appointed_by TEXT, PRIMARY KEY (user_id, guild_id))')
        # Relics (Scripts)
        c.execute('CREATE TABLE IF NOT EXISTS relics (relic_id TEXT PRIMARY KEY, guild_id TEXT, name TEXT, tier TEXT, file_ptr TEXT, rituals INTEGER DEFAULT 0)')
        # Ritual Keys (Keys)
        c.execute('CREATE TABLE IF NOT EXISTS ritual_keys (key_hex TEXT PRIMARY KEY, relic_id TEXT, guild_id TEXT, consumed INTEGER DEFAULT 0, hwid TEXT, timestamp TIMESTAMP)')
        # Forbidden Scrolls (Bans)
        c.execute('CREATE TABLE IF NOT EXISTS forbidden (hwid TEXT PRIMARY KEY, reason TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        conn.commit()
        conn.close()

db_manager = Reliquary(DB_NAME)

# ------------------------------------------------------------------------------
# [ SECTION 3: THE SACRED BOT INTERFACE (DISCORD) ]
# ------------------------------------------------------------------------------
class ArcaneBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all(), help_command=None)

    async def setup_hook(self):
        await self.tree.sync()
        self.heartbeat.start()

    @tasks.loop(minutes=20)
    async def heartbeat(self):
        ch = self.get_channel(MASTER_LOG_ID)
        if ch:
            e = discord.Embed(title="🌞 **Temple Heartbeat**", color=JADE, timestamp=datetime.datetime.now())
            e.set_footer(text=BRANDING)
            await ch.send(embed=e)

bot = ArcaneBot()

# --- [ PERMISSION DECORATORS ] ---
def is_unc():
    async def pred(itx: discord.Interaction):
        if itx.user.id == MASTER_OWNER_ID: return True
        await itx.response.send_message("🐍 **ACCESS DENIED.** Only the Architect can modify the Altar.", ephemeral=True)
        return False
    return app_commands.check(pred)

def has_rank(lvl):
    async def pred(itx: discord.Interaction):
        if itx.user.id == MASTER_OWNER_ID: return True
        conn = db_manager.get_conn()
        res = conn.execute("SELECT rank FROM hierarchy WHERE user_id = ? AND guild_id = ?", (str(itx.user.id), str(itx.guild.id))).fetchone()
        conn.close()
        if res and res['rank'] >= lvl: return True
        await itx.response.send_message(f"❌ **RANK {lvl} REQUIRED.**", ephemeral=True)
        return False
    return app_commands.check(pred)

# --- [ DISCORD SLASH COMMANDS ] ---

@bot.tree.command(name="welcome", description="[UNC ONLY] Provision a new Kingdom Sector.")
@is_unc()
async def welcome(itx: discord.Interaction, publisher: discord.Member):
    conn = db_manager.get_conn()
    conn.execute("INSERT OR REPLACE INTO kingdoms VALUES (?,?,?)", (str(itx.guild.id), str(publisher.id), itx.guild.name))
    conn.execute("INSERT OR REPLACE INTO hierarchy VALUES (?,?,?,?)", (str(publisher.id), str(itx.guild.id), 3, "UNC"))
    conn.commit()
    conn.close()
    await itx.response.send_message(f"🔱 **Kingdom Bound:** `{itx.guild.name}`\n**Lead Publisher:** {publisher.mention}")

@bot.tree.command(name="market_upload", description="[RANK 1+] Sacrifice a new relic to the vault.")
@has_rank(1)
async def market_upload(itx: discord.Interaction, name: str, tier: str, file: discord.Attachment):
    rid = f"RLC-{secrets.token_hex(3).upper()}"
    fn = secure_filename(f"{rid}_{file.filename}")
    await file.save(os.path.join(VAULT_PATH, fn))
    conn = db_manager.get_conn()
    conn.execute("INSERT INTO relics (relic_id, guild_id, name, tier, file_ptr) VALUES (?,?,?,?,?)", (rid, str(itx.guild.id), name, tier, fn))
    conn.commit()
    conn.close()
    await itx.response.send_message(f"🟢 **RELIC SECURED:** `{name}` (ID: `{rid}`)")

@bot.tree.command(name="mint_key", description="[RANK 2+] Create a Ritual Access Key.")
@has_rank(2)
async def mint_key(itx: discord.Interaction, relic_id: str):
    key = f"ARC-{secrets.token_hex(4).upper()}"
    conn = db_manager.get_conn()
    conn.execute("INSERT INTO ritual_keys (key_hex, relic_id, guild_id) VALUES (?,?,?,0,NULL,NULL)", (key, relic_id.upper(), str(itx.guild.id)))
    conn.commit()
    conn.close()
    await itx.response.send_message(f"🗝️ **RITUAL KEY:** `{key}`", ephemeral=True)

# ------------------------------------------------------------------------------
# [ SECTION 4: THE ARCANE DASHBOARD (WEB MIRROR) ]
# ------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

DASH_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ARCANE | DEVELOPED BY UNC</title>
    <style>
        body { background: #0a0a0a; color: #d4af37; font-family: 'Courier New', monospace; text-align: center; margin: 0; padding-top: 5vh; }
        .altar { border: 2px solid #00a86b; box-shadow: 0 0 30px #00a86b; border-radius: 20px; width: 85%; margin: auto; padding: 40px; }
        h1 { color: #00a86b; text-shadow: 0 0 15px #00a86b; font-size: 3em; letter-spacing: 10px; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 40px 0; }
        .card { border: 1px solid #d4af37; padding: 20px; background: rgba(0, 168, 107, 0.05); }
        .card h2 { font-size: 2.5em; margin: 10px 0; color: #fff; }
        .credits { margin-top: 50px; font-size: 0.9em; color: #555; }
        .highlight { color: #00a86b; font-weight: bold; }
    </style>
</head>
<body>
    <div class="altar">
        <h1>ARCANE VAULT</h1>
        <p class="highlight">CORE LOCKDOWN ACTIVE | SYSTEM: SECURE</p>
        <div class="grid">
            <div class="card"><h3>KINGDOMS</h3><h2>{{ k_count }}</h2></div>
            <div class="card"><h3>TOTAL RITUALS</h3><h2>{{ r_count }}</h2></div>
            <div class="card"><h3>SACRED RELICS</h3><h2>{{ re_count }}</h2></div>
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
def home():
    conn = db_manager.get_conn()
    k = conn.execute("SELECT COUNT(*) FROM kingdoms").fetchone()[0] or 0
    r = conn.execute("SELECT SUM(rituals) FROM relics").fetchone()[0] or 0
    re = conn.execute("SELECT COUNT(*) FROM relics").fetchone()[0] or 0
    conn.close()
    return render_template_string(DASH_HTML, k_count=k, r_count=r, re_count=re)

@app.route('/api/v8/ritual', methods=['POST'])
def perform_ritual():
    d = request.json
    conn = db_manager.get_conn()
    if conn.execute("SELECT 1 FROM forbidden WHERE hwid = ?", (d.get('hwid'),)).fetchone():
        return jsonify({"success": False, "msg": "HWID_CURSED"}), 403

    valid = conn.execute("SELECT 1 FROM ritual_keys WHERE key_hex = ? AND relic_id = ? AND guild_id = ? AND consumed = 0",
                         (d.get('key'), d.get('relic_id'), d.get('guild_id'))).fetchone()
    
    if not valid:
        conn.close()
        return jsonify({"success": False, "msg": "INVALID_OFFERING"}), 400

    conn.execute("UPDATE ritual_keys SET consumed = 1, hwid = ?, timestamp = ? WHERE key_hex = ?", (d.get('hwid'), datetime.datetime.now(), d.get('key')))
    conn.execute("UPDATE relics SET rituals = rituals + 1 WHERE relic_id = ?", (d.get('relic_id'),))
    conn.commit()
    conn.close()

    asyncio.run_coroutine_threadsafe(
        bot.get_channel(MASTER_LOG_ID).send(f"⚡ **SACRED RITUAL:** `{d.get('hwid')}` consumed key for Relic `{d.get('relic_id')}`"),
        bot.loop
    )
    return jsonify({"success": True, "token": secrets.token_hex(16)})

def run_web():
    app.run(host='0.0.0.0', port=PORT)

# ------------------------------------------------------------------------------
# [ SECTION 5: INVOCATION ]
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
