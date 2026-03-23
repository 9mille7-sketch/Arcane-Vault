# ==============================================================================
# ARCANE MARKETPLACE OMNI-KERNEL [V6.5] - INDUSTRIAL PRODUCTION BUILD
# OWNER/MASTER: Brian Miller (Unc) | ID: 1063556821517877258
# MASTER GUILD: 1483266011728838719 | LOG CHANNEL: 1485513827222290572
# ==============================================================================
# [ SYSTEM SUMMARY ]
# - SECTOR ISOLATION: Multi-tenant architecture for individual Publishers.
# - GLOBAL TELEMETRY: All flashes and uploads routed to Master Log Channel.
# - PERMISSION HIERARCHY:
#   - LEVEL 0: USER (Browse)
#   - LEVEL 1: CREATOR (Upload to specific Sector)
#   - LEVEL 2: MANAGER (Key Gen for specific Sector)
#   - LEVEL 3: PUBLISHER (Analytics for specific Sector)
#   - ARCHITECT: UNC (Global Control & Staff Authorization)
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
import shutil
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from discord.ext import commands, tasks
from discord import app_commands, ui
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# [ SECTION 1: SYSTEM CONFIGURATION ]
# ------------------------------------------------------------------------------
load_dotenv()

TOKEN = os.environ.get("DISCORD_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# HARD-LOCKED CREDENTIALS
MASTER_OWNER_ID = 1063556821517877258
MASTER_GUILD_ID = 1483266011728838719
MASTER_LOG_ID = 1485513827222290572

# BRANDING
EMBED_COLOR = 0xea4335  # CMIND Red
SUCCESS_COLOR = 0x2ecc71
WARN_COLOR = 0xf1c40f

# FILE SYSTEM
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DIR = os.path.join(BASE_DIR, "secure_vault_v6")
DB_PATH = os.path.join(BASE_DIR, "arcane_v6_production.db")
LOG_FILE = os.path.join(BASE_DIR, "system_runtime.log")

if not os.path.exists(VAULT_DIR):
    os.makedirs(VAULT_DIR)

# ------------------------------------------------------------------------------
# [ SECTION 2: ADVANCED LOGGING ENGINE ]
# ------------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ArcaneOmni")

# ------------------------------------------------------------------------------
# [ SECTION 3: RELATIONAL DATABASE & TELEMETRY ]
# ------------------------------------------------------------------------------
class DatabaseController:
    def __init__(self, path):
        self.path = path
        self.initialize_schema()

    def get_conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_schema(self):
        logger.info("Database: Running Schema Integrity Check...")
        conn = self.get_conn()
        c = conn.cursor()
        
        # 3.1 Sectors (Guild Authorization)
        c.execute('''CREATE TABLE IF NOT EXISTS sectors (
            guild_id TEXT PRIMARY KEY,
            publisher_id TEXT NOT NULL,
            sector_name TEXT,
            status TEXT DEFAULT 'ACTIVE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 3.2 Staff (Permission Registry - UNC CONTROLLED)
        c.execute('''CREATE TABLE IF NOT EXISTS staff_registry (
            user_id TEXT,
            guild_id TEXT,
            clearance_level INTEGER DEFAULT 1,
            added_by TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, guild_id)
        )''')

        # 3.3 Products (Market Inventory)
        c.execute('''CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            guild_id TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT,
            file_name TEXT NOT NULL,
            description TEXT,
            flash_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )''')

        # 3.4 Ritual Keys (Key-to-Sector Binding)
        c.execute('''CREATE TABLE IF NOT EXISTS ritual_keys (
            key_string TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            is_used INTEGER DEFAULT 0,
            bound_serial TEXT,
            redeemed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 3.5 Global Blacklist
        c.execute('''CREATE TABLE IF NOT EXISTS hardware_blacklist (
            serial TEXT PRIMARY KEY,
            reason TEXT,
            banned_by TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 3.6 Flash Audit (Telemetry)
        c.execute('''CREATE TABLE IF NOT EXISTS flash_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        logger.info("Database: Production Schema Synchronized.")

db = DatabaseController(DB_PATH)

# ------------------------------------------------------------------------------
# [ SECTION 4: PERMISSION MIDDLEWARE (UNC EXCLUSIVE) ]
# ------------------------------------------------------------------------------
def is_unc_architect():
    """STRICT: Only Brian Miller (ID 1063556821517877258) passes."""
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == MASTER_OWNER_ID:
            return True
        await interaction.response.send_message("❌ **CRITICAL ERROR:** Access restricted to UNC Architect credentials.", ephemeral=True)
        return False
    return app_commands.check(predicate)

def check_clearance(lvl: int):
    """Checks staff level within the specific Sector."""
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id == MASTER_OWNER_ID:
            return True
        conn = db.get_conn()
        res = conn.execute("SELECT clearance_level FROM staff_registry WHERE user_id = ? AND guild_id = ?",
                           (str(interaction.user.id), str(interaction.guild.id))).fetchone()
        conn.close()
        if res and res['clearance_level'] >= lvl:
            return True
        await interaction.response.send_message(f"❌ **ACCESS DENIED:** Level {lvl} clearance required in this Sector.", ephemeral=True)
        return False
    return app_commands.check(predicate)

# ------------------------------------------------------------------------------
# [ SECTION 5: DISCORD UI PAGINATOR ]
# ------------------------------------------------------------------------------
class MarketplaceView(ui.View):
    def __init__(self, items, guild_name, user_id):
        super().__init__(timeout=120)
        self.items = items
        self.guild_name = guild_name
        self.user_id = user_id
        self.page = 0
        self.per_page = 5
        self.max_pages = (len(items) - 1) // self.per_page

    def create_embed(self):
        start = self.page * self.per_page
        subset = self.items[start:start+self.per_page]
        embed = discord.Embed(title=f"MARKETPLACE: {self.guild_name}", color=EMBED_COLOR)
        for i in subset:
            embed.add_field(
                name=f"📦 {i['name']} (ID: {i['product_id']})",
                value=f"Flashes: {i['flash_count']} | Category: {i['category']}\n{i['description'][:80]}...",
                inline=False
            )
        embed.set_footer(text=f"Page {self.page+1} of {self.max_pages+1} | Arcane Omni-Kernel")
        return embed

    @ui.button(label="PREVIOUS", style=discord.ButtonStyle.gray)
    async def prev(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id: return
        if self.page > 0:
            self.page -= 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @ui.button(label="NEXT", style=discord.ButtonStyle.gray)
    async def next(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != self.user_id: return
        if self.page < self.max_pages:
            self.page += 1
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

# ------------------------------------------------------------------------------
# [ SECTION 6: THE DISCORD BOT KERNEL ]
# ------------------------------------------------------------------------------
class ArcaneKernel(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        self.uptime = datetime.datetime.now()

    async def setup_hook(self):
        await self.tree.sync()
        self.telemetry_loop.start()
        logger.info(f"Kernel: Slash Tree Synced to Global Network.")

    @tasks.loop(minutes=30)
    async def telemetry_loop(self):
        # Heartbeat to Master Log
        ch = self.get_channel(MASTER_LOG_ID)
        if ch and ch.guild.id == MASTER_GUILD_ID:
            e = discord.Embed(title="SYSTEM_HEARTBEAT", color=SUCCESS_COLOR, timestamp=datetime.datetime.now())
            e.add_field(name="Status", value="STABLE", inline=True)
            e.add_field(name="Kernel", value="V6.5_GOLD", inline=True)
            await ch.send(embed=e)

bot = ArcaneKernel()

# --- [ 6.1 MASTER ARCHITECT MODULE (UNC ONLY) ] ---

@bot.tree.command(name="welcome", description="[UNC ONLY] Provision a new Market Sector.")
@is_unc_architect()
async def welcome(interaction: discord.Interaction, publisher: discord.Member, staff_role: discord.Role):
    """Initializes a new server into the Marketplace network."""
    conn = db.get_conn()
    try:
        conn.execute("INSERT OR REPLACE INTO sectors (guild_id, publisher_id, sector_name) VALUES (?,?,?)",
                     (str(interaction.guild.id), str(publisher.id), interaction.guild.name))
        # Hard-lock Publisher as Lvl 3 in their server
        conn.execute("INSERT OR REPLACE INTO staff_registry (user_id, guild_id, clearance_level, added_by) VALUES (?,?,?,?)",
                     (str(publisher.id), str(interaction.guild.id), 3, "UNC_SYSTEM"))
        conn.commit()
        
        e = discord.Embed(title="SECTOR_INITIALIZED", color=SUCCESS_COLOR)
        e.add_field(name="Publisher", value=publisher.mention)
        e.add_field(name="Staff Role", value=staff_role.mention)
        await interaction.response.send_message(embed=e)
        
        # Log to Master
        log_ch = bot.get_channel(MASTER_LOG_ID)
        if log_ch:
            await log_ch.send(f"🏗️ **NEW SECTOR:** `{interaction.guild.name}` provisioned by Unc.")
    except Exception as e:
        logger.error(f"Welcome Command Failed: {e}")
        await interaction.response.send_message("❌ Database sync failure.", ephemeral=True)
    finally:
        conn.close()

@bot.tree.command(name="add_staff", description="[UNC ONLY] Authorize a staff member for a Sector.")
@is_unc_architect()
async def add_staff(interaction: discord.Interaction, member: discord.Member, level: int):
    """Only Unc can approve staff for any server."""
    conn = db.get_conn()
    conn.execute("INSERT OR REPLACE INTO staff_registry (user_id, guild_id, clearance_level, added_by) VALUES (?,?,?,?)",
                 (str(member.id), str(interaction.guild.id), level, interaction.user.name))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"✅ Authorized {member.name} (Lvl {level}) in this Sector.")

@bot.tree.command(name="blacklist", description="[UNC ONLY] Global Hardware Purge.")
@is_unc_architect()
async def blacklist(interaction: discord.Interaction, serial: str, reason: str):
    conn = db.get_conn()
    conn.execute("INSERT OR REPLACE INTO hardware_blacklist (serial, reason, banned_by) VALUES (?,?,?)",
                 (serial, reason, interaction.user.name))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"🚫 **BLACKLISTED:** `{serial}` banned globally.")

# --- [ 6.2 SECTOR OPERATIONS MODULE ] ---

@bot.tree.command(name="market_upload", description="[CREATOR] Upload script to your market.")
@check_clearance(1)
async def market_upload(interaction: discord.Interaction, name: str, category: str, description: str, file: discord.Attachment):
    if not file.filename.endswith(('.gpc', '.bin', '.txt')):
        return await interaction.response.send_message("❌ Unsupported file type.", ephemeral=True)

    pid = str(uuid.uuid4())[:8].upper()
    safe_name = secure_filename(f"{pid}_{file.filename}")
    await file.save(os.path.join(VAULT_DIR, safe_name))
    
    conn = db.get_conn()
    conn.execute("INSERT INTO products (product_id, guild_id, name, category, file_name, description) VALUES (?,?,?,?,?,?)",
                 (pid, str(interaction.guild.id), name, category, safe_name, description))
    conn.commit()
    conn.close()
    
    await interaction.response.send_message(f"📦 **RELIC COMMITTED:** ID `{pid}`")

@bot.tree.command(name="gen_key", description="[MANAGER] Mint an access key.")
@check_clearance(2)
async def gen_key(interaction: discord.Interaction, product_id: str):
    conn = db.get_conn()
    prod = conn.execute("SELECT name FROM products WHERE product_id = ? AND guild_id = ?", 
                        (product_id.upper(), str(interaction.guild.id))).fetchone()
    if not prod:
        conn.close()
        return await interaction.response.send_message("❌ Script not found in your sector.", ephemeral=True)

    key = f"ARC-{secrets.token_hex(4).upper()}"
    conn.execute("INSERT INTO ritual_keys (key_string, product_id, guild_id) VALUES (?,?,?)",
                 (key, product_id.upper(), str(interaction.guild.id)))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"🗝️ **KEY FOR {prod['name']}:** `{key}`", ephemeral=True)

@bot.tree.command(name="browse", description="View local market inventory.")
async def browse(interaction: discord.Interaction):
    conn = db.get_conn()
    items = conn.execute("SELECT * FROM products WHERE guild_id = ? AND is_active = 1", (str(interaction.guild.id),)).fetchall()
    conn.close()
    
    if not items: return await interaction.response.send_message("Market empty.")
    
    view = MarketplaceView([dict(r) for r in items], interaction.guild.name, interaction.user.id)
    await interaction.response.send_message(embed=view.create_embed(), view=view)

# ------------------------------------------------------------------------------
# [ SECTION 7: WEB ENGINE (API ISOLATION) ]
# ------------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

@app.route('/api/v6/redeem', methods=['POST'])
def api_redeem():
    payload = request.json
    sn, key, pid, gid = payload.get('serial'), payload.get('key'), payload.get('product_id'), payload.get('guild_id')
    ip = request.remote_addr
    
    conn = db.get_conn()
    
    # 1. Blacklist Check
    if conn.execute("SELECT 1 FROM hardware_blacklist WHERE serial = ?", (sn,)).fetchone():
        return jsonify({"success": False, "message": "HWID_BANNED"}), 403

    # 2. Key Handshake
    key_data = conn.execute("SELECT 1 FROM ritual_keys WHERE key_string = ? AND product_id = ? AND guild_id = ? AND is_used = 0", 
                            (key, pid, gid)).fetchone()
    
    if not key_data:
        conn.execute("INSERT INTO flash_audit (guild_id, serial, product_id, key_used, ip_address, status) VALUES (?,?,?,?,?,?)",
                     (gid, sn, pid, key, ip, "DENIED"))
        conn.commit()
        conn.close()
        return jsonify({"success": False, "message": "INVALID_HANDSHAKE"}), 400

    # 3. Process Success
    conn.execute("UPDATE ritual_keys SET is_used = 1, bound_serial = ?, redeemed_at = ? WHERE key_string = ?", 
                 (sn, datetime.datetime.now(), key))
    conn.execute("UPDATE products SET flash_count = flash_count + 1 WHERE product_id = ?", (pid,))
    conn.execute("INSERT INTO flash_audit (guild_id, serial, product_id, key_used, ip_address, status) VALUES (?,?,?,?,?,?)",
                 (gid, sn, pid, key, ip, "SUCCESS"))
    conn.commit()
    conn.close()

    # Route Telemetry to Master Channel
    asyncio.run_coroutine_threadsafe(
        bot.get_channel(MASTER_LOG_ID).send(f"⚡ **FLASH SUCCESS:** `{sn}` flashed `{pid}` (Sector: `{gid}`)"), 
        bot.loop
    )
    
    return jsonify({"success": True})

# ------------------------------------------------------------------------------
# [ SECTION 8: BOOTSTRAPPER ]
# ------------------------------------------------------------------------------
def run_flask():
    logger.info(f"Web: Launching Omni-API on Port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, use_reloader=False)

if __name__ == "__main__":
    if not TOKEN:
        logger.critical("FATAL: DISCORD_TOKEN missing.")
        sys.exit(1)

    threading.Thread(target=run_flask, daemon=True).start()
    
    try:
        logger.info("Bot: Initializing Core Lockdown...")
        bot.run(TOKEN)
    except Exception as e:
        logger.critical(f"Kernel Panic: {e}")
