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
# [ 1. KERNEL & ENVIRONMENT ARCHITECTURE ]
# ==============================================================================
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
OWNER_ID = "638512345678901234" # Brian Miller / Lead Architect
VERSION = "V5.6.8-STABLE"

# File System Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH = os.path.join(BASE_DIR, "arcane_vault.json")
BINARY_DIR = os.path.join(BASE_DIR, "vault_binaries")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Ensure environment is primed
for path in [BINARY_DIR, LOG_DIR]:
    if not os.path.exists(path):
        os.makedirs(path)

# Advanced Logging System
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] ARCANE_CORE: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "kernel.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ArcaneCore")

# ==============================================================================
# [ 2. SECURE VAULT ENGINE ]
# ==============================================================================
def initialize_vault():
    if not os.path.exists(VAULT_PATH):
        initial_data = {
            "scripts": [],
            "authorized_publishers": [OWNER_ID],
            "system_stats": {"total_flashes": 0, "unique_visitors": 0},
            "registry": {"created_at": str(datetime.datetime.now()), "version": VERSION}
        }
        with open(VAULT_PATH, "w") as f:
            json.dump(initial_data, f, indent=4)
        return initial_data
    
    with open(VAULT_PATH, "r") as f:
        return json.load(f)

def update_vault(data):
    with open(VAULT_PATH, "w") as f:
        json.dump(data, f, indent=4)

# ==============================================================================
# [ 3. THE GILDED INTERFACE (FULL-SCALE CSS & HTML) ]
# ==============================================================================
app = Flask(__name__)
app.secret_key = secrets.token_hex(64)

# This block represents the core visual identity
MASTER_UI_CORE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE REPOSITORY | V5.6.8</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Montserrat:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        /* --- [ CSS MASTER ENGINE: BLUE, GOLD & NIGHTMARE ] --- */
        :root {
            --cobalt: #00d2ff;
            --gold: #ffd700;
            --arcane-orange: #ff6600;
            --deep-black: #020205;
            --panel-bg: rgba(5, 7, 12, 0.98);
            --marble-url: url('https://i.ibb.co/3c1baac1/marble.png'); /* User provided high-res texture */
        }

        * { box-sizing: border-box; outline: none; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
        
        body {
            background: linear-gradient(rgba(0, 0, 10, 0.85), rgba(0, 0, 0, 0.95)), var(--marble-url);
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            height: 100vh;
            display: flex;
            overflow: hidden;
            border: 2px solid #111;
        }

        /* --- [ SIDEBAR: CMIND DESIGN LANGUAGE ] --- */
        .sidebar {
            width: 400px;
            background: var(--panel-bg);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            flex-direction: column;
            z-index: 100;
            backdrop-filter: blur(30px);
            box-shadow: 15px 0 50px rgba(0,0,0,0.9);
        }

        .sidebar-header {
            padding: 70px 45px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }

        .logo-main {
            font-family: 'Cinzel', serif;
            font-size: 52px;
            font-weight: 900;
            letter-spacing: 8px;
            color: var(--arcane-orange);
            text-shadow: 0 0 25px rgba(255, 102, 0, 0.4);
            margin: 0;
        }

        .logo-sub {
            font-size: 9px;
            color: #444;
            letter-spacing: 4px;
            font-weight: 900;
            text-transform: uppercase;
            margin-top: 15px;
        }

        .nav-stack { flex: 1; padding: 50px 45px; }
        
        .nav-group-label {
            font-size: 10px;
            color: #222;
            font-weight: 900;
            letter-spacing: 2px;
            margin-bottom: 30px;
            display: block;
        }

        .nav-btn {
            display: flex;
            align-items: center;
            padding: 20px;
            color: #666;
            font-weight: 900;
            text-decoration: none;
            font-size: 12px;
            border-radius: 2px;
            margin-bottom: 12px;
            border: 1px solid transparent;
            cursor: pointer;
        }

        .nav-btn:hover, .nav-btn.active {
            color: var(--arcane-orange);
            background: rgba(255, 102, 0, 0.05);
            border-color: var(--arcane-orange);
        }

        /* --- [ MAIN STAGE INTERFACE ] --- */
        .stage {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .stage-top {
            height: 100px;
            padding: 0 60px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(0,0,0,0.4);
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }

        .search-field {
            width: 450px;
            background: #000;
            border: 1px solid #111;
            padding: 20px 25px;
            color: #fff;
            border-radius: 4px;
            font-size: 14px;
        }

        .grid-scroller {
            flex: 1;
            padding: 65px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 45px;
            overflow-y: auto;
        }

        /* --- [ REINFORCED 8-SLOT HARDWARE GRID ] --- */
        .hardware-tray {
            height: 350px;
            background: rgba(5, 6, 10, 0.98);
            border-top: 2px solid #111;
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-template-rows: repeat(2, 1fr);
            padding: 20px;
            gap: 15px;
        }

        .mem-slot {
            background: rgba(18, 22, 30, 0.85);
            border: 1px solid #1a1a1a;
            display: flex;
            align-items: center;
            padding: 30px;
            position: relative;
        }

        .mem-id-huge {
            font-family: 'Montserrat', sans-serif;
            font-size: 85px;
            font-weight: 900;
            color: var(--cobalt);
            opacity: 0.5;
            position: absolute;
            left: 20px;
            z-index: 1;
        }

        .mem-meta {
            margin-left: 95px;
            z-index: 5;
        }

        .mem-header { font-size: 9px; color: #333; font-weight: 900; letter-spacing: 3px; }
        .mem-name { font-size: 11px; color: #666; font-weight: 700; margin-top: 5px; text-transform: uppercase; }

        .mem-led {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #150000;
            position: absolute;
            top: 20px;
            right: 20px;
            border: 1px solid #200;
        }

        .mem-led.active {
            background: var(--cobalt);
            box-shadow: 0 0 20px var(--cobalt);
            border-color: #fff;
        }

        /* --- [ CARDS & BUTTONS ] --- */
        .script-card {
            background: rgba(0, 0, 0, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.04);
            padding: 55px 45px;
            text-align: center;
        }

        .script-card:hover {
            border-color: var(--arcane-orange);
            transform: translateY(-8px);
            box-shadow: 0 25px 50px rgba(0,0,0,0.8);
        }

        .architect-label {
            font-size: 10px;
            color: var(--arcane-orange);
            font-weight: 900;
            letter-spacing: 3px;
            margin-bottom: 25px;
            display: block;
        }

        .card-title {
            font-family: 'Cinzel', serif;
            font-size: 30px;
            margin: 0 0 35px 0;
            color: #eee;
        }

        .btn-sync {
            width: 100%;
            padding: 22px;
            background: var(--arcane-orange);
            border: none;
            color: #000;
            font-family: 'Cinzel', serif;
            font-weight: 900;
            cursor: pointer;
            letter-spacing: 3px;
            font-size: 13px;
        }

        .btn-sync:hover { background: #fff; }

        /* SCROLLBAR CUSTOMIZATION */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #1a1a1a; border-radius: 10px; }
    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <h1 class="logo-main">ARCANE</h1>
            <div class="logo-sub">Gilded Vault V5.6.8</div>
        </div>

        <div class="nav-stack">
            <span class="nav-group-label">SYSTEM_ACCESS</span>
            <div class="nav-btn active">Repository Marketplace</div>
            <div class="nav-btn">Device Input Monitor</div>
            <div class="nav-btn">GPC Compiler Console</div>
            <div class="nav-btn">Hardware Diagnostics</div>

            <span class="nav-group-label" style="margin-top:50px;">MANAGEMENT</span>
            <div class="nav-btn" onclick="toggleUploadPortal()">Push Binary to Vault</div>
        </div>

        <div style="padding:45px; border-top:1px solid rgba(255,255,255,0.03);">
            <button class="btn-sync" onclick="initHardwareHandshake()">INITIALIZE ZEN</button>
            <div id="kernel-status" style="text-align:center; font-size:10px; color:#222; margin-top:25px; font-weight:900; letter-spacing:2px;">STATUS: IDLE</div>
        </div>
    </div>

    <div class="stage">
        <div class="stage-top">
            <input type="text" class="search-field" placeholder="Search the Arcane Archives...">
            <div style="display:flex; gap:35px; align-items:center;">
                <div style="font-size:10px; color:var(--gold); font-weight:900; letter-spacing:2px;">AES-256_ACTIVE</div>
                <div style="font-size:10px; color:var(--cobalt); font-weight:900; letter-spacing:2px;">SERVER: ONLINE</div>
            </div>
        </div>

        <div class="grid-scroller" id="script-container">
            </div>

        <div class="hardware-tray">
            <script>
                for(let i=1; i<=8; i++) {
                    document.write(`
                        <div class="mem-slot">
                            <div class="mem-id-huge">${i}</div>
                            <div class="mem-meta">
                                <div class="mem-header">MEMORY_BANK_0${i}</div>
                                <div class="mem-name" id="label-slot-${i}">EMPTY_SLOT</div>
                            </div>
                            <div class="mem-led" id="led-slot-${i}"></div>
                        </div>
                    `);
                }
            </script>
        </div>
    </div>

    <div id="upload-portal" style="position:fixed; inset:0; background:rgba(0,0,0,0.98); z-index:1000; display:none; align-items:center; justify-content:center;">
        <div style="background:#050508; border:1px solid var(--arcane-orange); padding:80px; width:650px;">
            <h2 style="font-family:'Cinzel'; color:var(--arcane-orange); font-size:38px; text-align:center; margin-bottom:50px;">ARCHIVE COMMIT</h2>
            <form action="/api/upload" method="post" enctype="multipart/form-data">
                <input type="text" name="auth_key" style="width:100%; padding:20px; background:#000; border:1px solid #111; color:#fff; margin-bottom:20px;" placeholder="Verification Key" required>
                <input type="text" name="s_name" style="width:100%; padding:20px; background:#000; border:1px solid #111; color:#fff; margin-bottom:20px;" placeholder="Binary Name" required>
                <input type="file" name="file" style="margin-bottom:40px; color:#444;" required>
                <button type="submit" class="btn-sync">UPLOAD TO VAULT</button>
            </form>
            <button onclick="toggleUploadPortal()" style="background:none; border:none; color:#222; width:100%; margin-top:30px; cursor:pointer; font-weight:900;">ABORT_SESSION</button>
        </div>
    </div>

    <script>
        let hardware = null;

        // --- [ THE HARDWARE HANDSHAKE KERNEL ] ---
        async function initHardwareHandshake() {
            try {
                // Targeted filtering for Cronus Zen (Vendor ID 0x2508)
                hardware = await navigator.usb.requestDevice({ filters: [{ vendorId: 0x2508 }] });
                await hardware.open();
                
                if (hardware.configuration === null) await hardware.selectConfiguration(1);
                
                // IMPORTANT: Claiming Interface 0 specifically to bypass the "Aborted" error
                // caused by Windows/Mac trying to use the HID interface as a controller.
                await hardware.claimInterface(0);

                const statusEl = document.getElementById('kernel-status');
                statusEl.innerText = "LINKED: " + (hardware.productName || "CRONUS ZEN");
                statusEl.style.color = "var(--cobalt)";

                for(let i=1; i<=8; i++) {
                    document.getElementById('led-slot-'+i).classList.add('active');
                }
                
                alert("Hardware Handshake finalized successfully.");
            } catch (err) {
                console.error("Kernel Handshake Fault:", err);
                alert("HANDSHAKE ABORTED: Ensure Zen Studio is closed and PROG port is connected.");
            }
        }

        async function flashBinary(sid, sname) {
            if(!hardware) return alert("Hardware Link required to flash binaries.");
            
            const btn = event.target;
            btn.innerText = "TRANSFERRING...";
            
            try {
                const response = await fetch(`/api/download/${sid}`);
                const blob = await response.blob();
                const buffer = new Uint8Array(await blob.arrayBuffer());

                // Programming protocol: 64-byte bulk transfers
                for (let i = 0; i < buffer.length; i += 64) {
                    await hardware.transferOut(1, buffer.slice(i, i + 64));
                }

                // Update visual slot 1
                document.getElementById('label-slot-1').innerText = sname.toUpperCase();
                document.getElementById('label-slot-1').style.color = "var(--cobalt)";
                
                btn.innerText = "SYNC COMPLETE";
                setTimeout(() => { btn.innerText = "SYNC TO ZEN"; }, 3000);
            } catch (err) {
                alert("Binary Transfer Failed.");
                btn.innerText = "FAULT_RETRY";
            }
        }

        function toggleUploadPortal() {
            const p = document.getElementById('upload-portal');
            p.style.display = (p.style.display === 'flex') ? 'none' : 'flex';
        }

        async function loadVault() {
            const res = await fetch('/api/scripts');
            const data = await res.json();
            const container = document.getElementById('script-container');
            
            container.innerHTML = data.map(s => `
                <div class="script-card">
                    <span class="architect-label">ARCHITECT: LEAD</span>
                    <h2 class="card-title">${s.name}</h2>
                    <button class="btn-sync" onclick="flashBinary('${s.id}', '${s.name}')">SYNC TO ZEN</button>
                </div>
            `).join('');
        }

        loadVault();
    </script>
</body>
</html>
"""

# ==============================================================================
# [ 4. ARCHITECT API ENDPOINTS ]
# ==============================================================================

@app.route('/')
def route_home():
    return render_template_string(MASTER_UI_CORE)

@app.route('/api/scripts')
def route_get_scripts():
    v = initialize_vault()
    return jsonify(v["scripts"])

@app.route('/api/upload', methods=['POST'])
def route_upload():
    v = initialize_vault()
    auth_key = request.form.get('auth_key')
    
    # Secure permission check
    if auth_key not in v["authorized_publishers"]:
        logger.warning(f"Unauthorized upload attempt with key: {auth_key}")
        return abort(403)
    
    file = request.files['file']
    s_name = request.form.get('s_name')
    
    if file and s_name:
        filename = secure_filename(f"{s_name}_{int(time.time())}.bin")
        file.save(os.path.join(BINARY_DIR, filename))
        
        new_script = {
            "id": str(uuid.uuid4())[:8],
            "name": s_name,
            "path": filename,
            "publisher": "Lead Architect",
            "uploaded_at": str(datetime.datetime.now())
        }
        
        v["scripts"].append(new_script)
        update_vault(v)
        logger.info(f"New binary committed to vault: {s_name}")
        return redirect(url_for('route_home'))
    
    return "Invalid submission data.", 400

@app.route('/api/download/<string:script_id>')
def route_download(script_id):
    v = initialize_vault()
    script = next((s for s in v["scripts"] if s["id"] == script_id), None)
    
    if not script:
        return abort(404)
    
    v["system_stats"]["total_flashes"] += 1
    update_vault(v)
    
    return send_from_directory(BINARY_DIR, script["path"])

# ==============================================================================
# [ 5. DISCORD KERNEL (THE BOT) ]
# ==============================================================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Arcane Discord Kernel initialized: {bot.user}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Successfully synced {len(synced)} slash commands.")
    except Exception as e:
        logger.error(f"Failed to sync slash commands: {e}")

@bot.tree.command(name="vault_audit", description="Retrieve real-time marketplace analytics.")
async def vault_audit(interaction: discord.Interaction):
    v = initialize_vault()
    embed = discord.Embed(
        title="Arcane Vault Analytics",
        color=0xff6600,
        timestamp=datetime.datetime.now()
    )
    embed.add_field(name="Total Binaries", value=len(v["scripts"]), inline=True)
    embed.add_field(name="Total Syncs", value=v["system_stats"]["total_flashes"], inline=True)
    embed.add_field(name="Kernel Version", value=VERSION, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="authorize", description="Grant Architect status to a trusted user.")
async def authorize_user(interaction: discord.Interaction, user: discord.Member):
    if str(interaction.user.id) != OWNER_ID:
        return await interaction.response.send_message("Only the Lead Architect can grant permissions.", ephemeral=True)
    
    v = initialize_vault()
    user_id = str(user.id)
    if user_id not in v["authorized_publishers"]:
        v["authorized_publishers"].append(user_id)
        update_vault(v)
        await interaction.response.send_message(f"User {user.mention} has been authorized as an Architect.")
    else:
        await interaction.response.send_message("User is already authorized.")

# ==============================================================================
# [ 6. DUAL-BOOT EXECUTION SYSTEM ]
# ==============================================================================
def launch_web_interface():
    # Use port 10000 for standard Render/Cloud compatibility
    app.run(host='0.0.0.0', port=10000, use_reloader=False)

if __name__ == "__main__":
    # Launch Web Server in a dedicated thread
    web_thread = threading.Thread(target=launch_web_interface, daemon=True)
    web_thread.start()
    
    # Launch Discord Bot
    if TOKEN:
        bot.run(TOKEN)
    else:
        logger.critical("Discord Token missing. Bot kernel offline.")
