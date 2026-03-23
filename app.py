# ==============================================================================
# ARCANE TEMPLE KERNEL - VERSION 5.0 (V5)
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
    """Writes the current state of the database to disk."""
    try:
        vault_data["system_stats"]["last_update"] = str(datetime.datetime.now())
        with open(VAULT_PATH, "w") as vault_file:
            json.dump(vault_data, vault_file, indent=4)
    except Exception as e:
        logger.error(f"Failed to sync Vault to disk: {e}")

# ------------------------------------------------------------------------------
# [ 3. THE GILDED AZTEC UI (KINETIC EDGE & COMPACT ENGINE) ]
# ------------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = secrets.token_hex(64)

MASTER_UI = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE TEMPLE | V5</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700;900&family=Montserrat:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --obsidian: #050705;
            --stone: #0a0c0a;
            --emerald: #00ff88;
            --mayan-gold: #c5a059;
            --bright-gold: #ffdf91;
            --deep-red: #8b0000;
            --jade-glow: 0 0 30px rgba(0, 255, 136, 0.3);
            --gold-glow: 0 0 25px rgba(197, 160, 89, 0.3);
            --interface-scale: 0.94;
        }

        /* --- KINETIC GOLD EDGE ANIMATION --- */
        @keyframes kinetic_glimmer {
            0% { border-color: var(--mayan-gold); box-shadow: inset 0 0 15px rgba(197, 160, 89, 0.2), 0 0 10px rgba(197, 160, 89, 0.1); }
            20% { border-color: var(--bright-gold); box-shadow: inset 0 0 45px rgba(255, 223, 145, 0.4), 0 0 30px rgba(255, 223, 145, 0.2); }
            40% { border-color: var(--mayan-gold); box-shadow: inset 0 0 25px rgba(197, 160, 89, 0.3), 0 0 15px rgba(197, 160, 89, 0.15); }
            60% { border-color: var(--bright-gold); box-shadow: inset 0 0 55px rgba(255, 223, 145, 0.5), 0 0 40px rgba(255, 223, 145, 0.3); }
            80% { border-color: var(--mayan-gold); box-shadow: inset 0 0 20px rgba(197, 160, 89, 0.25), 0 0 12px rgba(197, 160, 89, 0.12); }
            100% { border-color: var(--mayan-gold); box-shadow: inset 0 0 15px rgba(197, 160, 89, 0.2), 0 0 10px rgba(197, 160, 89, 0.1); }
        }

        @keyframes jade_pulse {
            0% { filter: drop-shadow(0 0 4px var(--emerald)); opacity: 0.6; transform: scale(1); }
            50% { filter: drop-shadow(0 0 20px var(--emerald)); opacity: 1; transform: scale(1.1); }
            100% { filter: drop-shadow(0 0 4px var(--emerald)); opacity: 0.6; transform: scale(1); }
        }

        @keyframes float_relic {
            0% { transform: translateY(0px) rotate(0deg); }
            33% { transform: translateY(-12px) rotate(0.5deg); }
            66% { transform: translateY(-5px) rotate(-0.5deg); }
            100% { transform: translateY(0px) rotate(0deg); }
        }

        @keyframes background_drift {
            from { background-position: 0% 0%; }
            to { background-position: 100% 100%; }
        }

        * { box-sizing: border-box; transition: all 0.6s cubic-bezier(0.15, 0.85, 0.35, 1); outline: none; }
        
        body {
            background: linear-gradient(rgba(5, 7, 5, 0.98), rgba(0, 0, 0, 0.99)), url('https://www.transparenttextures.com/patterns/dark-matter.png');
            background-color: var(--obsidian);
            color: #e0e0e0;
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            height: 100vh;
            display: flex;
            overflow: hidden;
            border: 10px solid var(--mayan-gold);
            animation: kinetic_glimmer 12s infinite linear, background_drift 200s infinite alternate;
        }

        /* COMPACT ALTAR WRAPPER */
        .altar-container {
            display: flex;
            width: 100%;
            height: 100%;
            max-width: 1750px;
            margin: auto;
            transform: scale(var(--interface-scale));
            transform-origin: center center;
            position: relative;
        }

        /* --- [ SIDEBAR ARCHITECTURE ] --- */
        .sidebar {
            width: 480px;
            background: var(--stone);
            border-right: 5px solid var(--mayan-gold);
            display: flex;
            flex-direction: column;
            z-index: 100;
            box-shadow: 40px 0 120px rgba(0,0,0,1);
            position: relative;
        }

        .sidebar-header {
            padding: 110px 60px;
            text-align: center;
            border-bottom: 1px solid rgba(197, 160, 89, 0.1);
        }

        .logo {
            font-family: 'Cinzel Decorative';
            font-size: 65px;
            font-weight: 900;
            letter-spacing: 18px;
            color: var(--mayan-gold);
            margin: 0;
            text-shadow: var(--gold-glow);
        }

        .dev-tag {
            font-size: 11px;
            color: var(--emerald);
            letter-spacing: 10px;
            font-weight: 900;
            margin-top: 35px;
            text-transform: uppercase;
            display: block;
        }

        .navigation {
            flex: 1;
            padding: 90px 60px;
        }

        .nav-label {
            font-size: 10px;
            color: #3a4a3a;
            font-weight: 900;
            letter-spacing: 6px;
            margin-bottom: 50px;
            display: block;
            text-transform: uppercase;
        }

        .nav-link {
            padding: 30px;
            color: #445544;
            font-weight: 900;
            font-size: 14px;
            letter-spacing: 5px;
            cursor: pointer;
            border-left: 0px solid var(--emerald);
            margin-bottom: 30px;
            text-transform: uppercase;
            background: rgba(0,0,0,0.1);
            display: block;
        }

        .nav-link:hover, .nav-link.active {
            color: #fff;
            background: rgba(0, 255, 136, 0.05);
            border-left: 5px solid var(--emerald);
            padding-left: 45px;
            box-shadow: -10px 0 30px rgba(0, 255, 136, 0.05);
        }

        .registration-portal {
            padding: 70px 60px;
            background: rgba(0,0,0,0.7);
            border-top: 4px solid var(--mayan-gold);
        }

        .temple-input {
            width: 100%;
            padding: 26px;
            background: #000;
            border: 2px solid #1a1a1a;
            color: var(--emerald);
            font-family: 'Cinzel Decorative';
            text-align: center;
            letter-spacing: 8px;
            font-size: 18px;
            margin-bottom: 35px;
            box-shadow: inset 0 0 30px rgba(0,0,0,1);
        }

        .btn-ritual {
            width: 100%;
            padding: 30px;
            background: none;
            border: 2px solid var(--mayan-gold);
            color: var(--mayan-gold);
            font-family: 'Cinzel Decorative';
            font-weight: 900;
            cursor: pointer;
            letter-spacing: 10px;
            font-size: 16px;
            text-transform: uppercase;
            position: relative;
            overflow: hidden;
        }

        .btn-ritual:hover {
            background: var(--mayan-gold);
            color: #000;
            box-shadow: 0 0 70px rgba(197, 160, 89, 0.4);
        }

        /* --- [ MAIN STAGE VIEWPORT ] --- */
        .stage {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .stage-header {
            height: 150px;
            padding: 0 110px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(0,0,0,0.85);
            border-bottom: 3px solid rgba(197, 160, 89, 0.15);
        }

        .kernel-pill {
            padding: 14px 35px;
            border: 2px solid var(--mayan-gold);
            font-size: 11px;
            font-weight: 900;
            letter-spacing: 6px;
            color: var(--mayan-gold);
            text-transform: uppercase;
        }

        .relic-grid {
            flex: 1;
            padding: 130px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
            gap: 100px;
            overflow-y: auto;
        }

        .relic-card {
            background: rgba(12, 18, 12, 0.98);
            border: 2px solid #1a221a;
            padding: 110px 80px;
            text-align: center;
            position: relative;
            clip-path: polygon(15% 0, 85% 0, 100% 15%, 100% 85%, 85% 100%, 15% 100%, 0 85%, 0 15%);
            animation: float_relic 8s ease-in-out infinite;
        }

        .relic-card:hover {
            border-color: var(--emerald);
            transform: scale(1.04);
            box-shadow: 0 0 80px rgba(0, 255, 136, 0.05);
        }

        .relic-title {
            font-family: 'Cinzel Decorative';
            font-size: 45px;
            color: #fff;
            margin-bottom: 70px;
            letter-spacing: 6px;
        }

        /* --- [ THE 8-SLOT HARDWARE ENGINE ] --- */
        .hardware-tray {
            height: 440px;
            background: #000;
            border-top: 6px solid var(--mayan-gold);
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            padding: 40px;
            gap: 35px;
        }

        .memory-slot {
            background: #080a08;
            border: 2px solid rgba(0, 255, 136, 0.04);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
        }

        .memory-id {
            font-family: 'Cinzel Decorative';
            font-size: 140px;
            color: var(--mayan-gold);
            opacity: 0.03;
            position: absolute;
            z-index: 1;
        }

        .memory-label {
            font-size: 11px;
            color: var(--emerald);
            font-weight: 900;
            letter-spacing: 6px;
            opacity: 0.6;
            z-index: 10;
        }

        .memory-data {
            font-size: 18px;
            color: #fff;
            font-weight: 700;
            margin-top: 25px;
            text-transform: uppercase;
            letter-spacing: 4px;
            z-index: 10;
        }

        .jade-led {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #1a1a1a;
            position: absolute;
            top: 35px;
            right: 35px;
            border: 2px solid #000;
        }

        .jade-led.active {
            background: var(--emerald);
            box-shadow: 0 0 30px var(--emerald);
            animation: jade_pulse 2.5s infinite;
        }

        .footer-credits {
            position: absolute;
            bottom: 45px;
            right: 70px;
            font-size: 12px;
            color: #2a352a;
            letter-spacing: 6px;
            font-weight: 900;
        }

        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: var(--mayan-gold); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--emerald); }
    </style>
</head>
<body>
    <div class="altar-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <h1 class="logo">ARCANE</h1>
                <span class="dev-tag">DEVELOPED BY UNC</span>
            </div>
            
            <div class="navigation">
                <span class="nav-label">TEMPLE_REGISTRY</span>
                <div class="nav-link active">Relic Archives</div>
                <div class="nav-link">Bonded Totems</div>
                <div class="nav-link">System Metrics</div>
                
                <span class="nav-label" style="margin-top:70px;">COMMAND_CORE</span>
                <div class="nav-link" onclick="togglePublisherMode()">Publisher Access</div>
            </div>

            <div class="registration-portal">
                <div style="font-size:11px; color:var(--mayan-gold); margin-bottom:25px; letter-spacing:5px; text-align:center;">HARDWARE_SERIAL_LINK</div>
                <input type="text" id="serial_num" class="temple-input" placeholder="XXXX-XXXX-XXXX">
                <button class="btn-ritual" id="bond_btn" onclick="initiateBond()">BOND HARDWARE</button>
                <div id="status_log" style="text-align:center; font-size:11px; color:#1a1a1a; margin-top:35px; font-weight:900; letter-spacing:4px;">STATUS: DISCONNECTED</div>
            </div>
        </div>

        <div class="stage">
            <div class="stage-header">
                <div class="kernel-pill">UNC_KERNEL: ACTIVE_V5</div>
                <div style="display:flex; gap:80px;">
                    <div style="font-size:13px; color:var(--emerald); font-weight:900; letter-spacing:6px;">SESSION: <span style="color:#fff">AUTH_OK</span></div>
                    <div style="font-size:13px; color:var(--mayan-gold); font-weight:900; letter-spacing:6px;">RELICS: <span id="relic_count" style="color:#fff">0</span></div>
                </div>
            </div>

            <div class="relic-grid" id="relic_mount">
                </div>

            <div class="hardware-tray">
                <script>
                    for(let i=1; i<=8; i++) {
                        document.write(`
                            <div class="memory-slot">
                                <div class="memory-id">${i}</div>
                                <div class="memory-label">MEMORY_BLOCK_0${i}</div>
                                <div class="memory-data" id="slot_data_${i}">EMPTY</div>
                                <div class="jade-led" id="led_${i}"></div>
                            </div>
                        `);
                    }
                </script>
            </div>
            <div class="footer-credits">CREDITS: COCO & ROEY</div>
        </div>
    </div>

    <script>
        let device_bridge = null;

        /**
         * WebUSB Bridge Engine
         */
        async function initiateBond() {
            const sn = document.getElementById('serial_num').value;
            if (!sn) {
                alert("Serial Number Required for Ritual.");
                return;
            }

            // Excommunication Check (Backend)
            const banCheck = await fetch(`/api/security/check_ban/${sn}`);
            const result = await banCheck.json();
            
            if (result.banned) {
                document.body.style.borderColor = "#8b0000";
                alert("CRITICAL ERROR: THIS HARDWARE HAS BEEN EXCOMMUNICATED.");
                return;
            }

            try {
                // Connecting to Cronus Zen via VendorID 0x2508
                device_bridge = await navigator.usb.requestDevice({ filters: [{ vendorId: 0x2508 }] });
                await device_bridge.open();
                
                if (device_bridge.configuration === null) {
                    await device_bridge.selectConfiguration(1);
                }
                
                await device_bridge.claimInterface(0);
                
                // Visual Feedback
                document.getElementById('status_log').innerText = "LINKED: " + (device_bridge.productName || "ZEN_HW");
                document.getElementById('status_log').style.color = "var(--emerald)";
                document.getElementById('bond_btn').innerText = "BOND_ESTABLISHED";
                
                for(let i=1; i<=8; i++) {
                    document.getElementById('led_'+i).classList.add('active');
                }
                
                console.log("[BRIDGE] High-Speed Connection Active.");
            } catch (err) {
                console.error("[BRIDGE ERROR]", err);
                alert("Ritual Failed: No suitable hardware detected on PROG port.");
            }
        }

        /**
         * Binary Transfer Engine
         */
        async function syncRelic(relic_id, relic_name) {
            if (!device_bridge) {
                alert("Hardware Bond Required Before Sync.");
                return;
            }

            const syncBtn = event.target;
            const originalText = syncBtn.innerText;
            syncBtn.innerText = "TRANSFERRING...";
            syncBtn.style.borderColor = "var(--emerald)";

            try {
                const response = await fetch(`/api/vault/download/${relic_id}`);
                if (!response.ok) throw new Error("Vault Access Denied.");

                const blob = await response.blob();
                const buffer = await blob.arrayBuffer();
                const bytes = new Uint8Array(buffer);

                // Transfer Binary in 64-byte chunks (Standard HID/USB Buffer)
                for (let i = 0; i < bytes.length; i += 64) {
                    const chunk = bytes.slice(i, i + 64);
                    await device_bridge.transferOut(1, chunk);
                }

                // Update UI Tray
                document.getElementById('slot_data_1').innerText = relic_name.toUpperCase();
                syncBtn.innerText = "SYNC_COMPLETE";
                
                setTimeout(() => {
                    syncBtn.innerText = originalText;
                    syncBtn.style.borderColor = "var(--mayan-gold)";
                }, 3000);

            } catch (err) {
                console.error("[SYNC ERROR]", err);
                alert("Transfer Interrupted: Binary Corrupted or Denied.");
                syncBtn.innerText = "TRANSFER_FAILED";
            }
        }

        /**
         * Vault Loading Engine
         */
        async function fetchArchives() {
            try {
                const res = await fetch('/api/vault/scripts');
                const scripts = await res.json();
                
                document.getElementById('relic_count').innerText = scripts.length;
                const mount = document.getElementById('relic_mount');
                
                mount.innerHTML = scripts.map(s => `
                    <div class="relic-card">
                        <span style="font-size:10px; color:var(--emerald); letter-spacing:5px; opacity:0.5;">RELIC_HASH_${s.id}</span>
                        <h2 class="relic-title">${s.name}</h2>
                        <button class="btn-ritual" onclick="syncRelic('${s.id}', '${s.name}')">SYNC TO ZEN</button>
                    </div>
                `).join('');
            } catch (err) {
                console.error("[ARCHIVE ERROR]", err);
            }
        }

        // Initialize Archive on Load
        window.addEventListener('load', fetchArchives);
    </script>
</body>
</html>
"""

# ------------------------------------------------------------------------------
# [ 4. DISCORD MANAGEMENT ENGINE ]
# ------------------------------------------------------------------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def temple_log(message_text, severity="INFO"):
    """Dispatches encrypted-style logs to the private UNC channel."""
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        color = 0x00ff88 if severity == "INFO" else 0xff0000
        embed = discord.Embed(
            title=f"TEMPLE_KERNEL_{severity}", 
            description=f"```fix\n{message_text}\n```", 
            color=color
        )
        embed.set_footer(text=f"System Timestamp: {datetime.datetime.now()}")
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    """Triggered when the bot kernel establishes connection to Discord."""
    await bot.tree.sync()
    logger.info(f"Bot Logged in as {bot.user.name}")
    await temple_log("High-Altar Online. Kinetic Engine & Multi-Server Logic Ready.")

# --- ARCHITECT COMMANDS (OWNER ONLY) ---

@bot.tree.command(name="welcome_publisher", description="Welcome a new Publisher and grant them archive powers.")
@app_commands.describe(user="The Publisher to authorize", role="The Discord Role required to access their scripts")
async def welcome_publisher(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("Permission Denied: Only the Architect can welcome Publishers.", ephemeral=True)
    
    vault = initialize_vault()
    guild_id_str = str(interaction.guild.id)
    
    vault["publishers"][guild_id_str] = {
        "guild_name": interaction.guild.name,
        "publisher_id": user.id,
        "publisher_name": user.name,
        "authorized_role_id": role.id,
        "enrolled_date": str(datetime.datetime.now())
    }
    
    sync_vault(vault)
    
    embed = discord.Embed(
        title="NEW PUBLISHER AUTHORIZED", 
        description=f"**{user.name}** has been granted Publisher rights for **{interaction.guild.name}**.",
        color=0xc5a059
    )
    embed.add_field(name="Required Access Role", value=role.mention)
    embed.set_footer(text="Arcane Temple | V5 Publisher System")
    
    await interaction.response.send_message(embed=embed)
    await temple_log(f"NEW_PUBLISHER_BOND: {user.name} in {interaction.guild.name}")

@bot.tree.command(name="excommunicate", description="Purge a Hardware Serial from the Temple archives permanently.")
@app_commands.describe(serial="The Serial Number to ban", reason="Reason for the excommunication")
async def excommunicate(interaction: discord.Interaction, serial: str, reason: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("Permission Denied: Only Unc can perform excommunications.", ephemeral=True)
    
    vault = initialize_vault()
    if serial not in vault["blacklist"]:
        vault["blacklist"].append(serial)
        sync_vault(vault)
        
        await temple_log(f"BAN_EXECUTED: Serial {serial} banned. Reason: {reason}", severity="WARNING")
        await interaction.response.send_message(f"💀 Hardware Serial `{serial}` has been purged from the archives.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Serial `{serial}` is already blacklisted.", ephemeral=True)

# --- PUBLISHER COMMANDS ---

@bot.tree.command(name="upload_relic", description="Commit a new binary relic to the temple vault.")
@app_commands.describe(relic_name="The display name for the script", binary_file="The .bin or .gpc file to archive")
async def upload_relic(interaction: discord.Interaction, relic_name: str, binary_file: discord.Attachment):
    vault = initialize_vault()
    guild_id_str = str(interaction.guild.id)
    
    # Check if this server is authorized
    if guild_id_str not in vault["publishers"]:
        return await interaction.response.send_message("This server is not an authorized Publisher server.", ephemeral=True)
    
    # Check if the user is the authorized Publisher
    if interaction.user.id != vault["publishers"][guild_id_str]["publisher_id"]:
        return await interaction.response.send_message("Access Denied: You are not the authorized Publisher for this server.", ephemeral=True)

    # Secure File Processing
    relic_uuid = str(uuid.uuid4())[:12]
    sanitized_filename = secure_filename(f"{relic_uuid}_{binary_file.filename}")
    storage_path = os.path.join(BINARY_DIR, sanitized_filename)
    
    await binary_file.save(storage_path)
    
    # Update Vault Registry
    vault["scripts"].append({
        "id": relic_uuid,
        "name": relic_name,
        "filename": sanitized_filename,
        "origin_guild": guild_id_str,
        "required_role": vault["publishers"][guild_id_str]["authorized_role_id"],
        "timestamp": str(datetime.datetime.now())
    })
    
    sync_vault(vault)
    
    await interaction.response.send_message(f"✅ Relic **{relic_name}** successfully committed to the archives.", ephemeral=True)
    await temple_log(f"RELIC_UPLOADED: {relic_name} (ID: {relic_uuid}) by {interaction.user.name}")

@bot.tree.command(name="register_hardware", description="Bond your Zen Serial Number to your Temple Profile.")
async def register_hardware(interaction: discord.Interaction, serial: str):
    vault = initialize_vault()
    
    if serial in vault["blacklist"]:
        return await interaction.response.send_message("❌ Error: This hardware has been excommunicated.", ephemeral=True)
        
    vault["users"][str(interaction.user.id)] = {
        "serial": serial,
        "bonded_on": str(datetime.datetime.now()),
        "last_known_guild": interaction.guild.name
    }
    
    sync_vault(vault)
    await interaction.response.send_message(f"✅ Hardware Serial `{serial}` successfully bonded to your soul.", ephemeral=True)

# ------------------------------------------------------------------------------
# [ 5. FLASK KERNEL (WEB API LAYER) ]
# ------------------------------------------------------------------------------

@app.route('/')
def interface_home():
    """Main Landing for the Arcane Temple Interface."""
    return render_template_string(MASTER_UI)

@app.route('/api/security/check_ban/<serial_number>')
def security_check_ban(serial_number):
    """Endpoint to verify if a serial number is blacklisted."""
    vault = initialize_vault()
    is_banned = serial_number in vault["blacklist"]
    return jsonify({"banned": is_banned, "timestamp": str(datetime.datetime.now())})

@app.route('/api/vault/scripts')
def vault_get_scripts():
    """Retrieves all active relics in the registry."""
    vault = initialize_vault()
    return jsonify(vault["scripts"])

@app.route('/api/vault/download/<relic_id>')
def vault_download_relic(relic_id):
    """Securely fetches a binary file from the vault."""
    vault = initialize_vault()
    
    # Locate the relic entry
    relic_entry = next((script for script in vault["scripts"] if script["id"] == relic_id), None)
    
    if not relic_entry:
        logger.warning(f"Unauthorized Access Attempt for Relic ID: {relic_id}")
        return abort(404)
    
    return send_from_directory(BINARY_DIR, relic_entry['filename'])

# ------------------------------------------------------------------------------
# [ 6. KERNEL INITIALIZATION ]
# ------------------------------------------------------------------------------

def start_web_server():
    """Launches the Flask web kernel on a background thread."""
    logger.info("Initializing Flask Web Kernel...")
    app.run(host='0.0.0.0', port=10000, use_reloader=False)

if __name__ == "__main__":
    # Launch Web Server Thread
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # Launch Discord Bot (Blocking)
    if TOKEN:
        logger.info("Establishing connection to Discord Altar...")
        bot.run(TOKEN)
    else:
        logger.critical("DISCORD_TOKEN NOT FOUND IN ENVIRONMENT.")
