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
from discord.ext import commands
import discord
from dotenv import load_dotenv

# ==============================================================================
# [ 1. KERNEL & IDENTITY CONFIGURATION ]
# ==============================================================================
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
# Identity: UNC (Lead Developer)
LEAD_DEV = "UNC"
OWNER_ID = "638512345678901234" 
VERSION = "V5.7.5-UNC-IMPERIAL"

# File System Integrity
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH = os.path.join(BASE_DIR, "unc_vault.json")
BINARY_DIR = os.path.join(BASE_DIR, "vault_binaries")
LOG_DIR = os.path.join(BASE_DIR, "system_logs")

for path in [BINARY_DIR, LOG_DIR]:
    if not os.path.exists(path):
        os.makedirs(path)

# Professional Kernel Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] UNC_CORE: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "kernel_main.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ArcaneImperial")

# ==============================================================================
# [ 2. DATABASE ENGINE ]
# ==============================================================================
def initialize_database():
    if not os.path.exists(VAULT_PATH):
        schema = {
            "scripts": [],
            "auth_ids": [OWNER_ID],
            "global_stats": {"flashes": 0, "uptime": str(datetime.datetime.now())}
        }
        with open(VAULT_PATH, "w") as f:
            json.dump(schema, f, indent=4)
        return schema
    with open(VAULT_PATH, "r") as f:
        return json.load(f)

def commit_to_db(data):
    with open(VAULT_PATH, "w") as f:
        json.dump(data, f, indent=4)

# ==============================================================================
# [ 3. THE IMPERIAL UI (BLUE/GOLD MARBLE | ZERO ORANGE) ]
# ==============================================================================
app = Flask(__name__)
app.secret_key = secrets.token_hex(64)

MASTER_UI_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE | DEVELOPED BY UNC</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Montserrat:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        /* --- [ IMPERIAL COLOR SYSTEM ] --- */
        :root {
            --royal-blue: #002244;
            --electric-cyan: #00d2ff;
            --imperial-gold: #d4af37;
            --deep-void: #010103;
            --marble-bg: url('https://i.ibb.co/L9Y0Y5r/marble-texture.png');
            --glass: rgba(0, 10, 30, 0.96);
        }

        * { box-sizing: border-box; transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1); outline: none; }
        
        body {
            background: linear-gradient(rgba(0, 5, 20, 0.9), rgba(0, 0, 0, 0.98)), var(--marble-bg);
            background-size: cover; background-attachment: fixed;
            color: #ffffff; font-family: 'Montserrat', sans-serif;
            margin: 0; height: 100vh; display: flex; overflow: hidden;
            border: 2px solid var(--imperial-gold);
        }

        /* --- [ SIDEBAR: AUTHENTIC UNC BRANDING ] --- */
        .sidebar {
            width: 440px; background: var(--glass);
            border-right: 2px solid var(--imperial-gold);
            display: flex; flex-direction: column; z-index: 100;
            backdrop-filter: blur(45px);
            box-shadow: 25px 0 100px rgba(0,0,0,0.9);
        }

        .sidebar-brand { padding: 90px 60px; border-bottom: 1px solid rgba(212, 175, 55, 0.1); }
        .logo-main {
            font-family: 'Cinzel', serif; font-size: 52px; font-weight: 900;
            letter-spacing: 12px; color: var(--imperial-gold);
            text-shadow: 0 0 35px rgba(212, 175, 55, 0.4); margin: 0;
        }
        .dev-tag {
            font-size: 11px; color: var(--electric-cyan); letter-spacing: 6px;
            font-weight: 900; margin-top: 20px; text-transform: uppercase;
        }

        .nav-menu { flex: 1; padding: 70px 60px; }
        .nav-section-title { font-size: 12px; color: #1a2a3a; font-weight: 900; letter-spacing: 5px; margin-bottom: 45px; display: block; }
        
        .nav-item {
            display: flex; align-items: center; padding: 26px;
            color: #556677; font-weight: 900; text-decoration: none;
            font-size: 14px; border-radius: 4px; margin-bottom: 20px;
            border: 1px solid transparent; cursor: pointer;
        }
        .nav-item:hover, .nav-item.active {
            color: var(--electric-cyan); background: rgba(0, 210, 255, 0.04);
            border-color: var(--imperial-gold);
        }

        /* --- [ STAGE: CONTENT AREA ] --- */
        .stage { flex: 1; display: flex; flex-direction: column; position: relative; }
        .top-deck {
            height: 120px; padding: 0 80px; display: flex; align-items: center; justify-content: space-between;
            background: rgba(0,0,0,0.6); border-bottom: 1px solid rgba(212, 175, 55, 0.05);
        }
        .search-input {
            width: 550px; background: #000; border: 1px solid #111;
            padding: 24px 40px; color: #fff; border-radius: 6px; font-size: 16px;
        }

        .main-gallery {
            flex: 1; padding: 100px;
            display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
            gap: 70px; overflow-y: auto;
        }

        /* --- [ HARDWARE TRAY: 8-SLOT REFERENCE ] --- */
        .hardware-tray {
            height: 400px; background: #000;
            border-top: 3px solid var(--imperial-gold);
            display: grid; grid-template-columns: repeat(4, 1fr);
            grid-template-rows: repeat(2, 1fr);
            padding: 30px; gap: 25px;
        }

        .slot-box {
            background: rgba(5, 12, 25, 0.95);
            border: 1px solid rgba(212, 175, 55, 0.15);
            display: flex; align-items: center; padding: 40px;
            position: relative; overflow: hidden;
        }
        .slot-box:hover { border-color: var(--imperial-gold); background: rgba(0, 20, 50, 0.95); }

        .slot-giant-num {
            font-family: 'Montserrat', sans-serif; font-size: 110px; font-weight: 900;
            color: var(--imperial-gold); opacity: 0.1;
            position: absolute; left: 20px; z-index: 1;
        }

        .slot-data { margin-left: 120px; z-index: 5; }
        .slot-header { font-size: 11px; color: var(--electric-cyan); font-weight: 900; letter-spacing: 5px; }
        .slot-name { font-size: 14px; color: #fff; font-weight: 700; margin-top: 10px; text-transform: uppercase; }

        .led-status {
            width: 16px; height: 16px; border-radius: 50%;
            background: #100000; position: absolute; top: 30px; right: 30px;
            border: 2px solid #200;
        }
        .led-status.active {
            background: var(--electric-cyan);
            box-shadow: 0 0 30px var(--electric-cyan);
            border-color: #fff;
        }

        /* --- [ MARKET CARDS: LUXURY STYLE ] --- */
        .script-card {
            background: rgba(1, 2, 8, 0.95);
            border: 1px solid rgba(212, 175, 55, 0.2);
            padding: 85px 65px; text-align: center; border-radius: 2px;
        }
        .script-card:hover {
            border-color: var(--electric-cyan);
            transform: translateY(-15px);
            box-shadow: 0 50px 120px rgba(0,0,0,1);
        }

        .card-dev { font-size: 12px; color: var(--imperial-gold); font-weight: 900; letter-spacing: 5px; margin-bottom: 35px; display: block; }
        .card-title { font-family: 'Cinzel', serif; font-size: 38px; margin: 0 0 50px 0; color: #fff; letter-spacing: 3px; }

        .btn-action {
            width: 100%; padding: 26px; background: none;
            border: 2px solid var(--imperial-gold);
            color: var(--imperial-gold); font-family: 'Cinzel', serif;
            font-weight: 900; cursor: pointer; letter-spacing: 6px; font-size: 16px;
        }
        .btn-action:hover {
            background: var(--imperial-gold); color: #000;
            box-shadow: 0 0 60px rgba(212, 175, 55, 0.4);
        }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: var(--imperial-gold); }
    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-brand">
            <h1 class="logo-main">ARCANE</h1>
            <div class="dev-tag">DEVELOPED_BY_UNC</div>
        </div>

        <div class="nav-menu">
            <span class="nav-section-title">CORE_MODULES</span>
            <div class="nav-item active">Imperial Repository</div>
            <div class="nav-item">Device Bridge</div>
            <div class="nav-item">GPC Optimizer</div>
            <div class="nav-item">Security Audit</div>

            <span class="nav-section-title" style="margin-top:70px;">UNC_PRIVILEGE</span>
            <div class="nav-item" onclick="toggleUploadPortal()">Push Binary Update</div>
        </div>

        <div style="padding:70px 60px;">
            <button class="btn-action" style="border-color:var(--electric-cyan); color:var(--electric-cyan);" onclick="connectHardware()">INITIALIZE LINK</button>
            <div id="connection-status" style="text-align:center; font-size:12px; color:#1a2a3a; margin-top:35px; font-weight:900; letter-spacing:4px;">STATUS: OFFLINE</div>
        </div>
    </div>

    <div class="stage">
        <div class="top-deck">
            <input type="text" class="search-input" placeholder="Query UNC's Private Vault...">
            <div style="display:flex; gap:50px; align-items:center;">
                <div style="font-size:12px; color:var(--imperial-gold); font-weight:900; letter-spacing:4px;">OWNER: UNC</div>
                <div style="font-size:12px; color:var(--electric-cyan); font-weight:900; letter-spacing:4px;">TARGET: <span id="target-bank" style="color:#fff">NULL</span></div>
            </div>
        </div>

        <div class="main-gallery" id="script-list"></div>

        <div class="hardware-tray">
            <script>
                for(let i=1; i<=8; i++) {
                    document.write(`
                        <div class="slot-box">
                            <div class="slot-giant-num">${i}</div>
                            <div class="slot-data">
                                <div class="slot-header">MEMORY_BANK_0${i}</div>
                                <div class="slot-name" id="name-s${i}">EMPTY</div>
                            </div>
                            <div class="led-status" id="led-s${i}"></div>
                        </div>
                    `);
                }
            </script>
        </div>
    </div>

    <div id="upload-portal" style="position:fixed; inset:0; background:rgba(0,0,0,0.99); z-index:1000; display:none; align-items:center; justify-content:center; backdrop-filter:blur(30px);">
        <div style="background:#020205; border:2px solid var(--imperial-gold); padding:100px; width:750px; box-shadow: 0 0 200px rgba(212, 175, 55, 0.2);">
            <h2 style="font-family:'Cinzel'; color:var(--imperial-gold); font-size:55px; text-align:center; margin-bottom:70px; letter-spacing:10px;">COMMIT BINARY</h2>
            <form action="/api/upload" method="post" enctype="multipart/form-data">
                <input type="text" name="v_key" style="width:100%; padding:25px; background:#000; border:1px solid #111; color:#fff; margin-bottom:30px;" placeholder="UNC Security Key" required>
                <input type="text" name="b_name" style="width:100%; padding:25px; background:#000; border:1px solid #111; color:#fff; margin-bottom:30px;" placeholder="Script Name" required>
                <input type="file" name="file" style="margin-bottom:70px; color:#555;" required>
                <button type="submit" class="btn-action">EXECUTE PUSH</button>
            </form>
            <button onclick="toggleUploadPortal()" style="background:none; border:none; color:#222; width:100%; margin-top:50px; cursor:pointer; font-weight:900; letter-spacing:5px;">CANCEL_PUSH</button>
        </div>
    </div>

    <script>
        let hardware = null;

        // --- [ HARDWARE BRIDGE FIX ] ---
        async function connectHardware() {
            try {
                // Expanded filter to catch devices locked by other drivers
                hardware = await navigator.usb.requestDevice({ 
                    filters: [
                        { vendorId: 0x2508 }, // Cronus Global
                        { vendorId: 0x2508, productId: 0x0001 }, // Bootloader Mode
                        { vendorId: 0x2508, productId: 0x8001 }, // Interface Mode
                        { vendorId: 0x0483, productId: 0x5740 }  // Communication Bridge
                    ] 
                });

                await hardware.open();
                
                // FORCE RE-INITIALIZATION
                if (hardware.configuration === null) await hardware.selectConfiguration(1);
                
                // Claim Interface 0 with fallback
                try {
                    await hardware.claimInterface(0);
                } catch(e) {
                    console.warn("Interface 0 busy, attempting Interface 1...");
                    await hardware.claimInterface(1);
                }

                const status = document.getElementById('connection-status');
                status.innerText = "LINKED: " + (hardware.productName || "CRONUS_ZEN");
                status.style.color = "var(--electric-cyan)";
                document.getElementById('target-bank').innerText = "ZEN_PRIMARY";

                for(let i=1; i<=8; i++) document.getElementById('led-s'+i).classList.add('active');
                alert("Hardware Handshake Secure. UNC Bridge Active.");
            } catch (err) {
                console.error(err);
                alert("BRIDGE ERROR: \n1. Close Zen Studio. \n2. Check PROG Cable. \n3. Ensure Chrome/Edge has USB permissions.");
            }
        }

        async function flashBinary(id, name) {
            if(!hardware) return alert("Initialize hardware link first.");
            const btn = event.target;
            btn.innerText = "SYNCING...";
            
            try {
                const response = await fetch(`/api/download/${id}`);
                const blob = await response.blob();
                const buffer = new Uint8Array(await blob.arrayBuffer());

                // Sequential Packet Transfer (64-byte chunks)
                for (let i = 0; i < buffer.length; i += 64) {
                    await hardware.transferOut(1, buffer.slice(i, i + 64));
                }

                document.getElementById('name-s1').innerText = name.toUpperCase();
                document.getElementById('name-s1').style.color = "var(--electric-cyan)";
                btn.innerText = "SYNC_COMPLETE";
                setTimeout(() => { btn.innerText = "SYNC TO ZEN"; }, 3000);
            } catch (err) {
                alert("Sync Interrupted. Hardware connection reset required.");
                btn.innerText = "SYNC_FAILED";
            }
        }

        function toggleUploadPortal() {
            const p = document.getElementById('upload-portal');
            p.style.display = (p.style.display === 'flex') ? 'none' : 'flex';
        }

        async function loadMarket() {
            const res = await fetch('/api/scripts');
            const data = await res.json();
            const grid = document.getElementById('script-list');
            grid.innerHTML = data.map(s => `
                <div class="script-card">
                    <span class="card-dev">DEVELOPED BY: UNC</span>
                    <h2 class="card-title">${s.name}</h2>
                    <button class="btn-action" onclick="flashBinary('${s.id}', '${s.name}')">SYNC TO ZEN</button>
                </div>
            `).join('');
        }

        loadMarket();
    </script>
</body>
</html>
"""

# ==============================================================================
# [ 4. BACKEND KERNEL & DISCORD BOT ]
# ==============================================================================

@app.route('/')
def unc_home():
    return render_template_string(MASTER_UI_TEMPLATE)

@app.route('/api/scripts')
def api_scripts():
    db = initialize_database()
    return jsonify(db["scripts"])

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    db = initialize_database()
    v_key = request.form.get('v_key')
    
    # Secure push only for UNC
    if v_key not in db["auth_ids"] and v_key != "UNC_MASTER_ADMIN":
        logger.warning(f"Unauthorized Push Attempt: {v_key}")
        return abort(403)
    
    file = request.files['file']
    b_name = request.form.get('b_name')
    
    if file and b_name:
        fname = secure_filename(f"{b_name}_{int(time.time())}.bin")
        file.save(os.path.join(BINARY_DIR, fname))
        
        entry = {
            "id": str(uuid.uuid4())[:8],
            "name": b_name,
            "publisher": "UNC",
            "file": fname,
            "date": str(datetime.datetime.now())
        }
        
        db["scripts"].append(entry)
        commit_to_db(db)
        logger.info(f"UNC Committed Binary: {b_name}")
        return redirect(url_for('unc_home'))
    
    return "Invalid Data Packet", 400

@app.route('/api/download/<string:sid>')
def handle_download(sid):
    db = initialize_database()
    script = next((s for s in db["scripts"] if s["id"] == sid), None)
    if not script: return abort(404)
    
    db["global_stats"]["flashes"] += 1
    commit_to_db(db)
    return send_from_directory(BINARY_DIR, script["file"])

# --- [ DISCORD ARCHITECT BOT ] ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"UNC Management Bot Online: {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="unc_audit", description="Retrieve vault usage and statistics.")
async def unc_audit(interaction: discord.Interaction):
    db = initialize_database()
    embed = discord.Embed(title="UNC Vault Statistics", color=0x00d2ff)
    embed.add_field(name="Total Scripts", value=len(db["scripts"]))
    embed.add_field(name="Global Flash Syncs", value=db["global_stats"]["flashes"])
    embed.add_field(name="Kernel Version", value=VERSION)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="add_architect", description="Add a manager to the authorized roster.")
async def add_architect(interaction: discord.Interaction, user_id: str):
    if str(interaction.user.id) != OWNER_ID:
        return await interaction.response.send_message("Permission Denied: Master Architect required.", ephemeral=True)
    
    db = initialize_database()
    if user_id not in db["auth_ids"]:
        db["auth_ids"].append(user_id)
        commit_to_db(db)
        await interaction.response.send_message(f"ID {user_id} authorized.")

# ==============================================================================
# [ 5. EXECUTION BOOTLOADER ]
# ==============================================================================
def start_web():
    app.run(host='0.0.0.0', port=10000, use_reloader=False)

if __name__ == "__main__":
    # Launch Web Server
    threading.Thread(target=start_web, daemon=True).start()
    
    # Launch Bot
    if TOKEN:
        bot.run(TOKEN)
    else:
        logger.error("Discord Token Null. Bot Kernel offline.")
