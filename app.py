import os
import json
import logging
import threading
import datetime
import secrets
import time
import uuid
import sys
from flask import Flask, jsonify, request, render_template_string, send_from_directory, redirect, url_for, session, abort
from werkzeug.utils import secure_filename
from discord.ext import commands, tasks
from discord import app_commands
import discord
from dotenv import load_dotenv

# ==============================================================================
# [ 1. KERNEL & IDENTITY CONFIGURATION ]
# ==============================================================================
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
LOG_CHANNEL_ID = 1485513827222290572  # UNC's Private Logs
OWNER_ID = 638512345678901234 # Set to your Discord ID

# Directory Hardening
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH = os.path.join(BASE_DIR, "temple_vault.json")
BINARY_DIR = os.path.join(BASE_DIR, "vault_binaries")
LOG_DIR = os.path.join(BASE_DIR, "kernel_logs")

if not os.path.exists(BINARY_DIR): os.makedirs(BINARY_DIR)
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

# System Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [UNC_KERNEL] %(message)s',
    handlers=[logging.FileHandler(os.path.join(LOG_DIR, "kernel.log")), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ArcaneTemple")

# ==============================================================================
# [ 2. DATABASE ENGINE (PERSISTENCE LAYER) ]
# ==============================================================================
def initialize_vault():
    if not os.path.exists(VAULT_PATH):
        schema = {
            "publishers": {}, # GuildID: {name, owner_id, role_id}
            "users": {},      # DiscordID: {serial, authorized, join_date}
            "scripts": [],    # {id, name, file, pub_guild, role_id}
            "blacklist": [],  # List of banned serial numbers
            "stats": {"total_flashes": 0, "active_bonds": 0}
        }
        with open(VAULT_PATH, "w") as f: json.dump(schema, f, indent=4)
        return schema
    with open(VAULT_PATH, "r") as f: return json.load(f)

def sync_vault(data):
    with open(VAULT_PATH, "w") as f: json.dump(data, f, indent=4)

# ==============================================================================
# [ 3. THE AZTEC ARCANE UI (FULL PRODUCTION STACK) ]
# ==============================================================================
app = Flask(__name__)
app.secret_key = secrets.token_hex(64)

MASTER_UI = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE TEMPLE</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700;900&family=Montserrat:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        :root {
            --obsidian: #050705;
            --stone: #111411;
            --emerald: #00ff88;
            --mayan-gold: #c5a059;
            --jade-glow: 0 0 30px rgba(0, 255, 136, 0.3);
            --gold-glow: 0 0 20px rgba(197, 160, 89, 0.2);
        }

        @keyframes jade_pulse {
            0% { filter: drop-shadow(0 0 2px var(--emerald)); opacity: 0.4; }
            50% { filter: drop-shadow(0 0 15px var(--emerald)); opacity: 1; }
            100% { filter: drop-shadow(0 0 2px var(--emerald)); opacity: 0.4; }
        }
        
        @keyframes float_anim {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
            100% { transform: translateY(0px); }
        }

        @keyframes bg_move {
            from { background-position: 0 0; }
            to { background-position: 100% 100%; }
        }

        * { box-sizing: border-box; transition: 0.5s cubic-bezier(0.1, 0.9, 0.2, 1); outline: none; }
        
        body {
            background: linear-gradient(rgba(5, 7, 5, 0.98), rgba(0, 0, 0, 0.99)), url('https://www.transparenttextures.com/patterns/dark-matter.png');
            background-color: var(--obsidian);
            color: #f0f0f0; font-family: 'Montserrat', sans-serif;
            margin: 0; height: 100vh; display: flex; overflow: hidden;
            border: 8px solid var(--mayan-gold);
            animation: bg_move 180s linear infinite;
        }

        /* --- SIDEBAR ARCHITECTURE --- */
        .sidebar {
            width: 480px; background: var(--stone);
            border-right: 4px solid var(--mayan-gold);
            display: flex; flex-direction: column; z-index: 100;
            box-shadow: 30px 0 100px #000;
            position: relative;
        }

        .sidebar-header { padding: 110px 60px; text-align: center; }
        .logo { 
            font-family: 'Cinzel Decorative'; font-size: 60px; font-weight: 900;
            letter-spacing: 15px; color: var(--mayan-gold); margin: 0;
            text-shadow: var(--gold-glow);
        }
        .signature { 
            font-size: 11px; color: var(--emerald); letter-spacing: 8px; 
            font-weight: 900; margin-top: 30px; text-transform: uppercase;
        }

        .nav { flex: 1; padding: 80px 60px; }
        .nav-label { font-size: 10px; color: #3a4a3a; font-weight: 900; letter-spacing: 6px; margin-bottom: 50px; display: block; }
        .nav-item {
            padding: 28px; color: #445544; font-weight: 900; font-size: 14px;
            letter-spacing: 4px; cursor: pointer; border-left: 0px solid var(--emerald);
            margin-bottom: 25px; text-transform: uppercase;
        }
        .nav-item:hover, .nav-item.active { 
            color: #fff; background: rgba(0,255,136,0.04); 
            border-left: 4px solid var(--emerald); padding-left: 40px;
        }

        .reg-box { padding: 60px; background: rgba(0,0,0,0.6); border-top: 3px solid var(--mayan-gold); }
        .aztec-input {
            width: 100%; padding: 25px; background: #000; border: 2px solid #1a1a1a;
            color: var(--emerald); font-family: 'Cinzel Decorative'; margin-bottom: 30px;
            text-align: center; letter-spacing: 6px; font-size: 18px;
            box-shadow: inset 0 0 20px #000;
        }

        /* --- STAGE VIEWPORT --- */
        .stage { flex: 1; display: flex; flex-direction: column; position: relative; }
        
        .top-bar {
            height: 140px; padding: 0 100px; display: flex; align-items: center; justify-content: space-between;
            background: rgba(0,0,0,0.8); border-bottom: 2px solid rgba(197, 160, 89, 0.1);
        }
        .pill { padding: 12px 30px; border: 1px solid var(--mayan-gold); font-size: 10px; font-weight: 900; letter-spacing: 4px; color: var(--mayan-gold); }

        .relic-vault {
            flex: 1; padding: 120px;
            display: grid; grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 80px; overflow-y: auto;
        }

        .relic-card {
            background: rgba(10, 16, 10, 0.98); border: 2px solid #1a221a;
            padding: 100px 70px; text-align: center; position: relative;
            clip-path: polygon(15% 0, 85% 0, 100% 15%, 100% 85%, 85% 100%, 15% 100%, 0 85%, 0 15%);
            animation: float_anim 6s ease-in-out infinite;
        }
        .relic-card:hover { border-color: var(--emerald); transform: scale(1.03); animation-play-state: paused; }
        .relic-title { font-family: 'Cinzel Decorative'; font-size: 42px; color: #fff; margin-bottom: 60px; letter-spacing: 5px; }

        /* --- THE 8-SLOT HARDWARE ENGINE --- */
        .tray {
            height: 420px; background: #000; border-top: 5px solid var(--mayan-gold);
            display: grid; grid-template-columns: repeat(4, 1fr); padding: 35px; gap: 30px;
        }
        .slot {
            background: #0a0d0a; border: 2px solid rgba(0, 255, 136, 0.05);
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            position: relative;
        }
        .slot-id { font-family: 'Cinzel Decorative'; font-size: 130px; color: var(--mayan-gold); opacity: 0.03; position: absolute; z-index: 1; }
        .slot-info { z-index: 10; text-align: center; }
        .slot-label { font-size: 10px; color: var(--emerald); font-weight: 900; letter-spacing: 5px; opacity: 0.6; }
        .slot-data { font-size: 16px; color: #fff; font-weight: 700; margin-top: 20px; text-transform: uppercase; letter-spacing: 3px; }

        .led {
            width: 14px; height: 14px; border-radius: 50%; background: #1a1a1a;
            position: absolute; top: 30px; right: 30px; border: 2px solid #000;
        }
        .led.active { background: var(--emerald); box-shadow: 0 0 25px var(--emerald); animation: jade_pulse 2s infinite; }

        .btn-aztec {
            width: 100%; padding: 28px; background: none; border: 2px solid var(--mayan-gold);
            color: var(--mayan-gold); font-family: 'Cinzel Decorative'; font-weight: 900;
            cursor: pointer; letter-spacing: 8px; font-size: 16px;
        }
        .btn-aztec:hover { background: var(--mayan-gold); color: #000; box-shadow: 0 0 60px rgba(197, 160, 89, 0.4); }

        .credits { position: absolute; bottom: 40px; right: 60px; font-size: 11px; color: #2a352a; letter-spacing: 5px; font-weight: 900; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: var(--emerald); }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <h1 class="logo">ARCANE</h1>
            <div class="signature">DEVELOPED BY UNC</div>
        </div>
        <div class="nav">
            <span class="nav-label">HIDDEN_ARCHIVES</span>
            <div class="nav-item active">Temple Vault</div>
            <div class="nav-item">System Pulse</div>
        </div>
        <div class="reg-box">
            <div style="font-size:10px; color:var(--mayan-gold); margin-bottom:20px; letter-spacing:4px; text-align:center;">HARDWARE_SERIAL</div>
            <input type="text" id="serial_num" class="aztec-input" placeholder="XXXX-XXXX-XXXX">
            <button class="btn-aztec" onclick="bondHardware()">BOND DEVICE</button>
            <div id="status_txt" style="text-align:center; font-size:10px; color:#1a1a1a; margin-top:25px; font-weight:900; letter-spacing:4px;">STATUS: OFFLINE</div>
        </div>
    </div>

    <div class="stage">
        <div class="top-bar">
            <div class="pill">UNC_KERNEL: ACTIVE</div>
            <div style="display:flex; gap:60px;">
                <div style="font-size:11px; color:var(--emerald); font-weight:900; letter-spacing:5px;">RELICS: <span id="count" style="color:#fff">0</span></div>
                <div style="font-size:11px; color:var(--mayan-gold); font-weight:900; letter-spacing:5px;">SESSION: <span style="color:#fff">AUTHORIZED</span></div>
            </div>
        </div>

        <div class="relic-vault" id="relic-mount"></div>

        <div class="tray">
            <script>
                for(let i=1; i<=8; i++) {
                    document.write(`
                        <div class="slot">
                            <div class="slot-id">${i}</div>
                            <div class="slot-info">
                                <div class="slot-label">MEMORY_BLOCK_0${i}</div>
                                <div class="slot-data" id="slot_txt_${i}">EMPTY</div>
                            </div>
                            <div class="led" id="led_${i}"></div>
                        </div>
                    `);
                }
            </script>
        </div>
        <div class="credits">CREDITS: COCO & ROEY</div>
    </div>

    <script>
        let bridge = null;

        async function bondHardware() {
            const sn = document.getElementById('serial_num').value;
            if(!sn) return alert("Enter Serial.");

            // Anti-Leak Check
            const check = await fetch(`/api/check_ban/${sn}`);
            const status = await check.json();
            if(status.banned) return alert("THIS DEVICE HAS BEEN EXCOMMUNICATED.");

            try {
                bridge = await navigator.usb.requestDevice({ filters: [{ vendorId: 0x2508 }] });
                await bridge.open();
                if (bridge.configuration === null) await bridge.selectConfiguration(1);
                await bridge.claimInterface(0);
                
                document.getElementById('status_txt').innerText = "LINKED: " + (bridge.productName || "ZEN_HW");
                document.getElementById('status_txt').style.color = "var(--emerald)";
                for(let i=1; i<=8; i++) document.getElementById('led_'+i).classList.add('active');
                
                alert("Hardware Bond established through Unc Kernel.");
            } catch (err) { alert("Detection Failed. Ensure you use the PROG port."); }
        }

        async function syncRelic(id, name) {
            if(!bridge) return alert("Bonding required.");
            const btn = event.target;
            btn.innerText = "SACRIFICING...";
            
            try {
                const res = await fetch(`/api/download/${id}`);
                const blob = await res.blob();
                const bytes = new Uint8Array(await blob.arrayBuffer());

                for (let i = 0; i < bytes.length; i += 64) {
                    await bridge.transferOut(1, bytes.slice(i, i + 64));
                }

                document.getElementById('slot_txt_1').innerText = name.toUpperCase();
                btn.innerText = "SYNC_SUCCESS";
                setTimeout(() => btn.innerText = "SYNC TO ZEN", 3000);
            } catch (err) { alert("Access Denied."); btn.innerText = "FAILED"; }
        }

        async function loadVault() {
            const res = await fetch('/api/scripts');
            const data = await res.json();
            document.getElementById('count').innerText = data.length;
            document.getElementById('relic-mount').innerHTML = data.map(s => `
                <div class="relic-card">
                    <span style="font-size:9px; color:var(--emerald); letter-spacing:4px;">RELIC_ID_${s.id}</span>
                    <h2 class="relic-title">${s.name}</h2>
                    <button class="btn-aztec" onclick="syncRelic('${s.id}', '${s.name}')">SYNC TO ZEN</button>
                </div>
            `).join('');
        }

        loadVault();
    </script>
</body>
</html>
"""

# ==============================================================================
# [ 4. DISCORD BOT: THE MANAGEMENT ENGINE ]
# ==============================================================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def dispatch_log(msg):
    ch = bot.get_channel(LOG_CHANNEL_ID)
    if ch:
        embed = discord.Embed(title="TEMPLE_KERNEL_UPDATE", description=f"```fix\n{msg}```", color=0x00ff88)
        embed.timestamp = datetime.datetime.now()
        await ch.send(embed=embed)

@bot.event
async def on_ready():
    await bot.tree.sync()
    await dispatch_log("High-Altar Online. Multi-Server Bot Ready.")

# --- OWNER (UNC) COMMANDS ---

@bot.tree.command(name="welcome_publisher", description="Welcome a user to the Publisher Family and grant powers.")
@app_commands.describe(user="The new publisher", role="The role they manage in their server")
async def welcome(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("Only the Architect can welcome publishers.", ephemeral=True)
    
    v = initialize_vault()
    v["publishers"][str(interaction.guild.id)] = {
        "name": interaction.guild.name,
        "owner_id": user.id,
        "role_id": role.id
    }
    sync_vault(v)
    
    embed = discord.Embed(title="NEW PUBLISHER BONDED", description=f"Welcome {user.mention}! You now manage relics for **{interaction.guild.name}**.", color=0xc5a059)
    embed.add_field(name="Role Requirement", value=role.mention)
    embed.set_footer(text="Developed by Unc")
    
    await interaction.response.send_message(embed=embed)
    await dispatch_log(f"NEW_PUBLISHER: {user.name} for {interaction.guild.name}")

@bot.tree.command(name="excommunicate", description="Instantly ban a Serial Number from the Temple.")
@app_commands.describe(serial="The Serial to ban", reason="Reason for purge")
async def excommunicate(interaction: discord.Interaction, serial: str, reason: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("Architect Access Only.", ephemeral=True)
    
    v = initialize_vault()
    if serial not in v["blacklist"]:
        v["blacklist"].append(serial)
    sync_vault(v)
    
    await dispatch_log(f"BAN_EXECUTED: Serial {serial} purged. Reason: {reason}")
    await interaction.response.send_message(f"💀 **{serial}** has been excommunicated from the temple.", ephemeral=True)

# --- PUBLISHER COMMANDS ---

@bot.tree.command(name="upload_relic", description="Publish a new script binary to the temple archives.")
@app_commands.describe(name="Display name", file="Attach the .bin or .gpc file")
async def upload(interaction: discord.Interaction, name: str, file: discord.Attachment):
    v = initialize_vault()
    gid = str(interaction.guild.id)
    
    if gid not in v["publishers"] or interaction.user.id != v["publishers"][gid]["owner_id"]:
        return await interaction.response.send_message("Access Denied: You are not the authorized Publisher for this server.", ephemeral=True)

    sid = str(uuid.uuid4())[:8]
    fname = secure_filename(f"{sid}_{file.filename}")
    await file.save(os.path.join(BINARY_DIR, fname))
    
    v["scripts"].append({
        "id": sid,
        "name": name,
        "file": fname,
        "pub_guild": gid,
        "role_id": v["publishers"][gid]["role_id"]
    })
    sync_vault(v)
    
    await interaction.response.send_message(f"✅ Relic **{name}** has been sacrificed to the archives.", ephemeral=True)
    await dispatch_log(f"NEW_RELIC: {name} uploaded by {interaction.user.name}")

@bot.tree.command(name="register_zen", description="Bond your Hardware Serial to your Account.")
async def register(interaction: discord.Interaction, serial: str):
    v = initialize_vault()
    if serial in v["blacklist"]:
        return await interaction.response.send_message("❌ This hardware has been excommunicated.", ephemeral=True)
        
    v["users"][str(interaction.user.id)] = {"serial": serial, "auth": True, "date": str(datetime.datetime.now())}
    sync_vault(v)
    await interaction.response.send_message(f"✅ Serial `{serial}` Bonded to your account.", ephemeral=True)

# ==============================================================================
# [ 5. FLASK KERNEL ]
# ==============================================================================

@app.route('/')
def home():
    return render_template_string(MASTER_UI)

@app.route('/api/check_ban/<sn>')
def check_ban(sn):
    v = initialize_vault()
    return jsonify({"banned": sn in v["blacklist"]})

@app.route('/api/scripts')
def api_scripts():
    v = initialize_vault()
    return jsonify(v["scripts"])

@app.route('/api/download/<sid>')
def api_download(sid):
    v = initialize_vault()
    script = next((s for s in v["scripts"] if s["id"] == sid), None)
    if not script: return abort(404)
    return send_from_directory(BINARY_DIR, script['file'])

# ==============================================================================
# [ 6. EXECUTION ]
# ==============================================================================
def start_web():
    app.run(host='0.0.0.0', port=10000, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=start_web, daemon=True).start()
    if TOKEN:
        bot.run(TOKEN)
