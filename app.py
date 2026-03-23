# ==============================================================================
# ARCANE TEMPLE KERNEL - MASTER BUILD [RED ALTAR EDITION]
# DEVELOPED BY UNC | CREDITS: COCO & ROEY
# ==============================================================================

import os
import json
import logging
import threading
import datetime
import secrets
import time
import uuid
import sys
import base64
from flask import (
    Flask, 
    jsonify, 
    request, 
    render_template_string, 
    send_from_directory, 
    redirect, 
    url_for, 
    session, 
    abort
)
from werkzeug.utils import secure_filename
from discord.ext import commands, tasks
from discord import app_commands
import discord
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# [ 1. KERNEL SYSTEM CONFIGURATION ]
# ------------------------------------------------------------------------------
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
LOG_CHANNEL_ID = 1485513827222290572  # UNC's Private Logs
OWNER_ID = 638512345678901234         # Architect ID

# Path Hardening
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH = os.path.join(BASE_DIR, "temple_vault.json")
BINARY_DIR = os.path.join(BASE_DIR, "vault_binaries")
LOG_DIR = os.path.join(BASE_DIR, "kernel_logs")

# Directory Verification Logic
def verify_system_directories():
    """
    Checks for the existence of required system directories.
    If missing, the kernel attempts to self-repair by creating them.
    """
    directories = [BINARY_DIR, LOG_DIR]
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"[SYSTEM] Created Directory: {directory}")
            except Exception as e:
                print(f"[CRITICAL ERROR] Failed to create {directory}: {e}")

verify_system_directories()

# Advanced Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] UNC_KERNEL: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "kernel_main.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ArcaneTemple")

# ------------------------------------------------------------------------------
# [ 2. DATABASE ARCHITECTURE (VAULT ENGINE) ]
# ------------------------------------------------------------------------------
def initialize_vault():
    """Initializes the persistent JSON storage for the Temple."""
    if not os.path.exists(VAULT_PATH):
        logger.info("Generating new Temple Vault database...")
        schema = {
            "publishers": {},
            "users": {},
            "scripts": [],
            "blacklist": [],
            "audit_logs": [],
            "system_stats": {
                "total_flashes": 0,
                "active_bonds": 0,
                "last_update": str(datetime.datetime.now())
            }
        }
        with open(VAULT_PATH, "w") as vault_file:
            json.dump(schema, vault_file, indent=4)
        return schema
    
    try:
        with open(VAULT_PATH, "r") as vault_file:
            return json.load(vault_file)
    except Exception as e:
        logger.error(f"Vault Corruption Detected: {e}")
        return {}

def sync_vault(vault_data):
    """Writes the current state of the database to disk with timestamping."""
    try:
        vault_data["system_stats"]["last_update"] = str(datetime.datetime.now())
        with open(VAULT_PATH, "w") as vault_file:
            json.dump(vault_data, vault_file, indent=4)
    except Exception as e:
        logger.error(f"Failed to sync Vault to disk: {e}")

# ------------------------------------------------------------------------------
# [ 3. THE RED INDUSTRIAL UI (MASTER COMPONENT) ]
# ------------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = secrets.token_hex(64)

MASTER_UI = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE | VAULT SYSTEM</title>
    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;700&family=Montserrat:wght@300;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --obsidian: #0a0807;
            --rust-panel: #14100e;
            --blood-red: #ea4335;
            --dim-red: #5d1c1a;
            --copper-stone: #d1bba4;
            --interface-scale: 0.94;
        }

        /* --- EXTENDED ANIMATION ENGINE --- */
        @keyframes red_glimmer {
            0% { border-color: var(--dim-red); box-shadow: 0 0 10px rgba(93, 28, 26, 0.4); }
            25% { border-color: var(--blood-red); box-shadow: 0 0 25px rgba(234, 67, 53, 0.2); }
            50% { border-color: #ff0000; box-shadow: 0 0 40px rgba(255, 0, 0, 0.4); }
            75% { border-color: var(--blood-red); box-shadow: 0 0 25px rgba(234, 67, 53, 0.2); }
            100% { border-color: var(--dim-red); box-shadow: 0 0 10px rgba(93, 28, 26, 0.4); }
        }

        @keyframes rotate_gear_clockwise {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes rotate_gear_counter {
            from { transform: rotate(360deg); }
            to { transform: rotate(0deg); }
        }

        @keyframes tube_pulse {
            0% { opacity: 0.4; filter: drop-shadow(0 0 2px var(--blood-red)); }
            50% { opacity: 1; filter: drop-shadow(0 0 15px var(--blood-red)); }
            100% { opacity: 0.4; filter: drop-shadow(0 0 2px var(--blood-red)); }
        }

        @keyframes scanning_line {
            0% { top: 0%; opacity: 0; }
            50% { opacity: 0.5; }
            100% { top: 100%; opacity: 0; }
        }

        @keyframes float_relic {
            0% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-20px) rotate(2deg); }
            100% { transform: translateY(0px) rotate(0deg); }
        }

        /* --- CORE STYLING --- */
        * { box-sizing: border-box; transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1); outline: none; }
        
        body {
            background-color: #000;
            color: var(--copper-stone);
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            height: 100vh;
            display: flex;
            overflow: hidden;
        }

        .altar-container {
            display: flex;
            width: 100%;
            height: 100%;
            max-width: 1800px;
            margin: auto;
            transform: scale(var(--interface-scale));
            border: 3px solid var(--dim-red);
            background: var(--obsidian);
            animation: red_glimmer 10s infinite linear;
            position: relative;
        }

        /* --- SIDEBAR ARCHITECTURE --- */
        .sidebar {
            width: 450px;
            background: var(--rust-panel);
            border-right: 2px solid var(--dim-red);
            display: flex;
            flex-direction: column;
            padding: 80px 50px;
            z-index: 10;
        }

        .logo-container {
            text-align: center;
            margin-bottom: 80px;
            position: relative;
        }

        .logo-text {
            font-family: 'Oswald';
            font-size: 70px;
            letter-spacing: 12px;
            color: var(--copper-stone);
            font-weight: 700;
            text-transform: uppercase;
        }

        .dev-tag {
            color: var(--blood-red);
            font-size: 14px;
            letter-spacing: 6px;
            font-weight: 900;
            margin-top: 15px;
            display: block;
            text-transform: uppercase;
        }

        .nav-group {
            margin-top: 60px;
            flex: 1;
        }

        .nav-header {
            font-family: 'Oswald';
            font-size: 16px;
            color: var(--dim-red);
            letter-spacing: 4px;
            margin-bottom: 35px;
            display: block;
            text-transform: uppercase;
        }
        
        .nav-item {
            padding: 25px;
            border: 2px solid var(--dim-red);
            color: var(--copper-stone);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 4px;
            margin-bottom: 25px;
            cursor: pointer;
            text-align: center;
            background: rgba(0,0,0,0.2);
        }

        .nav-item:hover, .nav-item.active {
            border-color: var(--blood-red);
            background: rgba(234, 67, 53, 0.08);
            color: var(--blood-red);
            box-shadow: 0 0 30px rgba(234, 67, 53, 0.2);
            padding-left: 35px;
        }

        .hardware-bond-zone {
            margin-top: auto;
            border-top: 2px solid var(--dim-red);
            padding-top: 50px;
        }

        .sn-input {
            width: 100%;
            padding: 25px;
            background: #000;
            border: 2px solid var(--dim-red);
            color: var(--blood-red);
            text-align: center;
            font-family: 'Oswald';
            font-size: 22px;
            letter-spacing: 5px;
            margin-bottom: 25px;
        }

        /* --- MAIN STAGE ENGINE --- */
        .main-stage {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        
        .stage-header {
            height: 120px;
            padding: 0 80px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 2px solid var(--dim-red);
            background: rgba(0,0,0,0.4);
        }

        .header-pill {
            padding: 12px 30px;
            border: 1px solid var(--dim-red);
            font-size: 13px;
            font-weight: 900;
            letter-spacing: 4px;
            text-transform: uppercase;
        }

        /* --- RELIC FIELD (ANIMATED ASSETS) --- */
        .relic-field {
            flex: 1;
            position: relative;
            background: radial-gradient(circle at center, #1a1412 0%, #0a0807 100%);
            overflow: hidden;
            border-bottom: 2px solid var(--dim-red);
        }

        .scanner {
            position: absolute;
            width: 100%;
            height: 2px;
            background: var(--blood-red);
            box-shadow: 0 0 20px var(--blood-red);
            animation: scanning_line 4s infinite linear;
            z-index: 5;
        }

        .gear-asset {
            position: absolute;
            border: 12px dashed var(--dim-red);
            border-radius: 50%;
            opacity: 0.1;
            z-index: 1;
        }

        .tube-asset {
            position: absolute;
            width: 35px;
            height: 90px;
            background: linear-gradient(to bottom, var(--blood-red), transparent);
            border-radius: 18px;
            box-shadow: 0 0 15px rgba(234, 67, 53, 0.5);
            animation: tube_pulse 4s infinite ease-in-out;
            z-index: 2;
        }

        /* --- MEMORY MATRIX --- */
        .memory-matrix {
            height: 450px;
            padding: 50px;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 35px;
            background: #000;
        }

        .memory-slot {
            background: var(--rust-panel);
            border: 2px solid var(--dim-red);
            padding: 40px;
            position: relative;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            clip-path: polygon(10% 0, 90% 0, 100% 10%, 100% 90%, 90% 100%, 10% 100%, 0 90%, 0 10%);
        }

        .memory-slot:hover {
            border-color: var(--blood-red);
            transform: translateY(-5px);
            background: rgba(234, 67, 53, 0.03);
        }

        .status-led {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #1a1a1a;
            position: absolute;
            top: 25px;
            right: 25px;
            border: 2px solid #000;
        }

        .status-led.active {
            background: var(--blood-red);
            box-shadow: 0 0 20px var(--blood-red);
            animation: tube_pulse 2s infinite;
        }

        .slot-label {
            font-size: 11px;
            color: var(--blood-red);
            font-weight: 900;
            letter-spacing: 4px;
            margin-bottom: 20px;
            text-transform: uppercase;
        }

        .slot-data {
            font-family: 'Oswald';
            font-size: 26px;
            color: var(--copper-stone);
            letter-spacing: 3px;
            text-transform: uppercase;
        }

        .footer-bar {
            height: 60px;
            padding: 0 50px;
            display: flex;
            justify-content: flex-end;
            align-items: center;
            font-size: 11px;
            letter-spacing: 5px;
            color: #2a2220;
            font-weight: 900;
        }

        /* --- SCROLLBAR CUSTOMIZATION --- */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: var(--dim-red); }
        ::-webkit-scrollbar-thumb:hover { background: var(--blood-red); }

    </style>
</head>
<body>
    <div class="altar-container">
        <aside class="sidebar">
            <div class="logo-container">
                <span class="logo-text">ARCANE</span>
                <span class="dev-tag">DEVELOPED BY UNC</span>
            </div>

            <nav class="nav-group">
                <span class="nav-header">HIDDEN ARCHIVES</span>
                <div class="nav-item active">TEMPLE VAULT</div>
                <div class="nav-item">SYSTEM PULSE</div>
                <div class="nav-item">SECURITY LOGS</div>
            </nav>

            <div class="hardware-bond-zone">
                <span class="nav-header">HARDWARE SERIAL</span>
                <input type="text" id="sn_input" class="sn-input" placeholder="XXXX-XXXX-XXXX">
                <div class="nav-item" onclick="initiateHardwareBond()" style="border-color: var(--blood-red); color: var(--blood-red); margin-top: 10px;">BOND DEVICE</div>
            </div>
        </aside>

        <main class="main-stage">
            <header class="stage-header">
                <div class="header-pill">UNC_KERNEL: ACTIVE</div>
                <div style="display: flex; gap: 60px;">
                    <div class="header-pill" style="border: none;">RELICS: <span id="relic_count" style="color: #fff;">0</span></div>
                    <div class="header-pill" style="color: var(--blood-red); border-color: var(--blood-red);">SESSION: AUTHORIZED</div>
                </div>
            </header>

            <section class="relic-field" id="relic_field">
                <div class="scanner"></div>
                </section>

            <section class="memory-matrix">
                <script>
                    for(let i=1; i<=8; i++) {
                        document.write(`
                            <div class="memory-slot">
                                <div class="status-led" id="led_${i}"></div>
                                <span class="slot-label">MEMORY_BLOCK_0${i}</span>
                                <div class="slot-data" id="data_${i}">EMPTY</div>
                            </div>
                        `);
                    }
                </script>
            </section>

            <footer class="footer-bar">
                <span>CREDITS: COCO & ROEY</span>
            </footer>
        </main>
    </div>

    <script>
        /**
         * KERNEL ANIMATION ENGINE
         * Responsible for generating the industrial background elements.
         */
        function initializeFieldAssets() {
            const field = document.getElementById('relic_field');
            
            // Generate Gears
            for(let i=0; i<8; i++) {
                const gear = document.createElement('div');
                const size = Math.floor(Math.random() * 150) + 100;
                gear.className = 'gear-asset';
                gear.style.width = size + 'px';
                gear.style.height = size + 'px';
                gear.style.left = Math.random() * 90 + '%';
                gear.style.top = Math.random() * 90 + '%';
                gear.style.animation = i % 2 === 0 ? 
                    `rotate_gear_clockwise ${Math.random() * 20 + 20}s linear infinite` : 
                    `rotate_gear_counter ${Math.random() * 20 + 20}s linear infinite`;
                field.appendChild(gear);
            }

            // Generate Vacuum Tubes
            for(let i=0; i<5; i++) {
                const tube = document.createElement('div');
                tube.className = 'tube-asset';
                tube.style.left = Math.random() * 90 + '%';
                tube.style.top = Math.random() * 90 + '%';
                tube.style.animationDelay = (Math.random() * 5) + 's';
                field.appendChild(tube);
            }
        }

        /**
         * WEB-USB BRIDGE ENGINE
         * Interfaces with hardware serial for device bonding.
         */
        async function initiateHardwareBond() {
            const sn = document.getElementById('sn_input').value;
            if(!sn) return alert("SERIAL REQUIRED FOR RITUAL.");

            // Security check against blacklist
            const response = await fetch(`/api/security/check/${sn}`);
            const security = await response.json();
            
            if(security.banned) {
                document.body.style.filter = "grayscale(1) contrast(2)";
                return alert("CRITICAL: HARDWARE HAS BEEN EXCOMMUNICATED.");
            }

            try {
                // Connection attempt (VendorID 0x2508 for Cronus Zen)
                const device = await navigator.usb.requestDevice({ filters: [{ vendorId: 0x2508 }] });
                await device.open();
                await device.selectConfiguration(1);
                await device.claimInterface(0);

                // UI feedback on successful bond
                for(let i=1; i<=8; i++) {
                    document.getElementById('led_'+i).classList.add('active');
                }
                document.querySelector('.sn-input').style.borderColor = "var(--blood-red)";
                alert("HARDWARE BOND ESTABLISHED.");
            } catch(err) {
                console.error("Bonding Error:", err);
                alert("CONNECTION FAILED: NO COMPATIBLE HARDWARE DETECTED.");
            }
        }

        /**
         * VAULT SYNCHRONIZATION
         * Fetches available relics from the Python backend.
         */
        async function syncVaultArchives() {
            try {
                const response = await fetch('/api/vault/list');
                const relics = await response.json();
                document.getElementById('relic_count').innerText = relics.length;
            } catch(err) {
                console.warn("Vault Sync Failed.");
            }
        }

        // Initialize on Load
        window.addEventListener('load', () => {
            initializeFieldAssets();
            syncVaultArchives();
        });
    </script>
</body>
</html>
"""

# ------------------------------------------------------------------------------
# [ 4. DISCORD MANAGEMENT ENGINE (FULL SUITE) ]
# ------------------------------------------------------------------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def dispatch_system_log(content, severity="INFO"):
    """Sends audit logs to the private architecture channel."""
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        color = 0xea4335 if severity == "WARNING" else 0xd1bba4
        embed = discord.Embed(
            title=f"KERNEL_{severity}", 
            description=f"```fix\n{content}\n```", 
            color=color
        )
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    """Triggered when the bot established connection to the Discord Altar."""
    await bot.tree.sync()
    logger.info(f"Bot authenticated as {bot.user.name}")
    await dispatch_system_log("Red Altar Interface Online. All systems green.")

# --- ARCHITECT LEVEL COMMANDS (OWNER ONLY) ---

@bot.tree.command(name="welcome_publisher", description="Authorize a new Publisher server.")
@app_commands.describe(user="The Publisher Account", role="The Access Role")
async def welcome_publisher(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("Architect Access Required.", ephemeral=True)
    
    vault = initialize_vault()
    guild_id = str(interaction.guild.id)
    
    vault["publishers"][guild_id] = {
        "publisher_name": user.name,
        "publisher_id": user.id,
        "required_role_id": role.id,
        "enrolled_at": str(datetime.datetime.now())
    }
    
    sync_vault(vault)
    await dispatch_system_log(f"NEW_PUBLISHER: {user.name} in {interaction.guild.name}")
    await interaction.response.send_message(f"✅ Publisher **{user.name}** authorized for this sector.")

@bot.tree.command(name="excommunicate", description="Permanently blacklist a hardware serial.")
async def excommunicate(interaction: discord.Interaction, serial: str, reason: str = "Unspecified"):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("Access Denied.", ephemeral=True)
    
    vault = initialize_vault()
    if serial not in vault["blacklist"]:
        vault["blacklist"].append(serial)
        sync_vault(vault)
        await dispatch_system_log(f"BAN_EXECUTED: Serial {serial} | Reason: {reason}", severity="WARNING")
        await interaction.response.send_message(f"💀 Hardware Serial `{serial}` purged from the archives.")
    else:
        await interaction.response.send_message("Serial already excommunicated.")

# --- PUBLISHER LEVEL COMMANDS ---

@bot.tree.command(name="upload_relic", description="Commit a new binary relic to the Temple Vault.")
@app_commands.describe(name="Display name", relic_file="The binary (.bin) file")
async def upload_relic(interaction: discord.Interaction, name: str, relic_file: discord.Attachment):
    vault = initialize_vault()
    guild_id = str(interaction.guild.id)
    
    # Permission verification
    if guild_id not in vault["publishers"]:
        return await interaction.response.send_message("This sector is not authorized for publishing.", ephemeral=True)
    
    if interaction.user.id != vault["publishers"][guild_id]["publisher_id"]:
        return await interaction.response.send_message("You are not the authorized Publisher for this sector.", ephemeral=True)

    # Secure File Processing
    relic_uuid = str(uuid.uuid4())[:12]
    safe_name = secure_filename(f"{relic_uuid}_{relic_file.filename}")
    save_path = os.path.join(BINARY_DIR, safe_name)
    
    await relic_file.save(save_path)
    
    # Registry update
    vault["scripts"].append({
        "id": relic_uuid,
        "name": name,
        "file": safe_name,
        "origin": interaction.guild.name,
        "timestamp": str(datetime.datetime.now())
    })
    
    sync_vault(vault)
    await dispatch_system_log(f"RELIC_COMMITTED: {name} (ID: {relic_uuid})")
    await interaction.response.send_message(f"✅ Relic **{name}** successfully archived.")

# ------------------------------------------------------------------------------
# [ 5. FLASK KERNEL (WEB API LAYER) ]
# ------------------------------------------------------------------------------

@app.route('/')
def altar_interface():
    """Main rendering point for the Red Altar Interface."""
    return render_template_string(MASTER_UI)

@app.route('/api/security/check/<serial>')
def check_security(serial):
    """Verifies serial status against the excommunication list."""
    vault = initialize_vault()
    banned = serial in vault["blacklist"]
    return jsonify({"banned": banned, "status": "DENIED" if banned else "OK"})

@app.route('/api/vault/list')
def get_vault_list():
    """Returns all available relics in the archive."""
    vault = initialize_vault()
    return jsonify(vault["scripts"])

@app.route('/api/vault/download/<relic_id>')
def download_relic(relic_id):
    """Serves the binary file if the ID is valid."""
    vault = initialize_vault()
    relic = next((s for s in vault["scripts"] if s["id"] == relic_id), None)
    
    if not relic:
        logger.warning(f"Unauthorized Access Attempt: {relic_id}")
        return abort(404)
        
    return send_from_directory(BINARY_DIR, relic["file"])

# ------------------------------------------------------------------------------
# [ 6. KERNEL INITIALIZATION ]
# ------------------------------------------------------------------------------

def launch_web_interface():
    """Executes the Flask kernel on a background thread."""
    logger.info("Initializing Flask Web Interface...")
    # Port 10000 is standard for Render/hosting deployments
    app.run(host='0.0.0.0', port=10000, use_reloader=False)

if __name__ == "__main__":
    # Start Web Thread
    threading.Thread(target=launch_web_interface, daemon=True).start()
    
    # Start Discord Bot
    if TOKEN:
        logger.info("Igniting Discord Altar connection...")
        bot.run(TOKEN)
    else:
        logger.critical("DISCORD_TOKEN MISSING FROM ENVIRONMENT.")
