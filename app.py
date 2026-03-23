import os
import json
import logging
import threading
import datetime
import secrets
import time
from flask import Flask, jsonify, request, render_template_string, send_from_directory, redirect, url_for, session, abort
from werkzeug.utils import secure_filename
from discord.ext import commands
import discord
from dotenv import load_dotenv

# --- [ 1. SYSTEM INITIALIZATION & SECURITY ] ---
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
OWNER_ID = os.environ.get("OWNER_ID")
SECRET_KEY = secrets.token_hex(32)

# Infrastructure Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "arcane_vault_v5.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "scripts_vault")
LOG_FILE = os.path.join(BASE_DIR, "system_audit.log")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Industrial Strength Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] ARCANE_KERNEL: %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("ArcaneCore")

# --- [ 2. VAULT DATA MANAGEMENT ] ---
def load_vault():
    if not os.path.exists(DB_FILE):
        return {
            "scripts": [],
            "authorized_publishers": [OWNER_ID],
            "system_logs": [],
            "config": {
                "version": "V5.0.3",
                "lead_dev": "Unc",
                "credits": ["Coco", "Roey"],
                "theme": "Cobalt_Marble_Silver"
            }
        }
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Vault Read Error: {e}")
        return {}

def save_vault(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- [ 3. THE GILDED INTERFACE ENGINE ] ---
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Using a massive multi-line string to contain the entire UI logic
MASTER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE V5 | Secret Society Vault</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Montserrat:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        /* --- [ CSS MASTER ENGINE ] --- */
        :root {
            --cobalt-bright: #0033aa;
            --cobalt-deep: #001133;
            --silver-trim: #c0c0c0;
            --silver-bright: #ffffff;
            --gold-vein: #ffd700;
            --electric-blue: #00d2ff;
            --danger-red: #ff4b2b;
            --black-glass: rgba(0, 5, 15, 0.9);
        }

        * { box-sizing: border-box; outline: none; }

        body {
            background-color: #000;
            /* BRIGHTER COBALT MARBLE WITH GOLD VEINS */
            background-image: 
                linear-gradient(135deg, rgba(255, 215, 0, 0.15) 0%, transparent 25%),
                linear-gradient(225deg, rgba(255, 215, 0, 0.05) 10%, transparent 40%),
                radial-gradient(circle at center, var(--cobalt-bright) 0%, var(--cobalt-deep) 100%);
            background-attachment: fixed;
            color: #eee;
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            height: 100vh;
            display: flex;
            overflow: hidden;
            border: 1px solid var(--silver-trim);
        }

        /* Marble Overlay Texture */
        body::before {
            content: ""; position: absolute; inset: 0;
            background: url('https://www.transparenttextures.com/patterns/marble.png');
            opacity: 0.35; pointer-events: none; z-index: 1;
        }

        /* --- [ SIDEBAR NAVIGATION ] --- */
        .sidebar {
            width: 420px;
            background: var(--black-glass);
            border-right: 2px solid var(--silver-trim); /* ORIGINAL SILVER LINE */
            display: flex;
            flex-direction: column;
            z-index: 100;
            backdrop-filter: blur(25px);
            box-shadow: 20px 0 80px rgba(0,0,0,0.8);
        }

        .sidebar-header {
            padding: 80px 40px;
            text-align: center;
            border-bottom: 1px solid rgba(192, 192, 192, 0.1);
        }

        .logo-text {
            font-family: 'Cinzel', serif;
            font-size: 64px;
            font-weight: 900;
            letter-spacing: 18px;
            margin: 0;
            background: linear-gradient(to bottom, #fff 0%, var(--silver-trim) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 15px rgba(255,255,255,0.2));
        }

        .dev-tag {
            font-size: 11px;
            color: var(--silver-trim);
            letter-spacing: 5px;
            text-transform: uppercase;
            margin-top: 30px;
            font-weight: 900;
        }

        .credits-tag {
            font-size: 8px;
            color: #555;
            margin-top: 10px;
            letter-spacing: 2px;
            font-weight: 700;
        }

        .nav-ledger {
            flex: 1;
            padding: 60px 40px;
            display: flex;
            flex-direction: column;
        }

        .nav-item {
            padding: 22px 30px;
            margin-bottom: 25px;
            color: #666;
            font-weight: 800;
            font-size: 11px;
            letter-spacing: 4px;
            text-transform: uppercase;
            cursor: pointer;
            border-left: 3px solid transparent;
            transition: all 0.4s ease;
        }

        .nav-item:hover {
            color: var(--electric-blue);
            background: rgba(0, 210, 255, 0.03);
            border-left-color: var(--electric-blue);
        }

        .nav-item.active {
            color: #fff;
            background: rgba(192, 192, 192, 0.05);
            border-left-color: var(--silver-trim);
            text-shadow: 0 0 10px rgba(255,255,255,0.3);
        }

        /* --- [ THE SYNC HUB ] --- */
        .sync-console {
            margin-top: auto;
            padding: 40px;
            border-top: 1px solid rgba(192, 192, 192, 0.1);
        }

        .btn-handshake {
            width: 100%;
            padding: 28px;
            background: transparent;
            border: 1px solid var(--silver-trim);
            color: var(--silver-trim);
            font-family: 'Cinzel', serif;
            font-weight: 900;
            font-size: 16px;
            letter-spacing: 6px;
            cursor: pointer;
            transition: 0.5s;
            position: relative;
            overflow: hidden;
        }

        .btn-handshake:hover {
            background: var(--silver-trim);
            color: #000;
            box-shadow: 0 0 50px rgba(192, 192, 192, 0.3);
        }

        .status-monitor {
            margin-top: 25px;
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 2px;
            text-align: center;
            color: var(--danger-red);
        }

        /* --- [ MAIN CANVAS AREA ] --- */
        .canvas {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
            z-index: 10;
        }

        .top-row {
            height: 120px;
            padding: 0 80px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(192, 192, 192, 0.05);
        }

        .search-box {
            width: 500px;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid #222;
            padding: 20px 40px;
            color: #fff;
            border-radius: 2px;
            font-family: 'Montserrat', sans-serif;
            font-size: 13px;
        }

        .vault-scroll {
            flex: 1;
            padding: 80px;
            overflow-y: auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 50px;
        }

        /* --- [ SCRIPT CARDS ] --- */
        .card {
            background: rgba(0, 10, 30, 0.6);
            border: 1px solid rgba(192, 192, 192, 0.1);
            padding: 50px;
            transition: 0.6s cubic-bezier(0.165, 0.84, 0.44, 1);
            position: relative;
            backdrop-filter: blur(5px);
        }

        .card:hover {
            transform: translateY(-15px);
            border-color: var(--electric-blue);
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
        }

        .card-header {
            font-size: 10px;
            color: var(--electric-blue);
            font-weight: 900;
            letter-spacing: 3px;
            margin-bottom: 20px;
        }

        .card h3 {
            font-family: 'Cinzel', serif;
            font-size: 28px;
            margin: 0 0 30px 0;
            font-weight: 900;
        }

        /* --- [ TALL REINFORCED MEMORY SLOTS ] --- */
        .memory-footer {
            height: 320px;
            background: rgba(0, 0, 0, 0.95);
            border-top: 3px solid var(--silver-trim); /* ORIGINAL SILVER LINE */
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            padding: 10px;
            gap: 15px;
        }

        .slot {
            background: linear-gradient(180deg, #0a0e1a 0%, #000 100%);
            border: 1px solid #1a1a1a;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
            transition: 0.3s;
        }

        .slot:hover {
            border-color: var(--electric-blue);
            background: #0d1526;
        }

        .slot-idx {
            font-family: 'Cinzel', serif;
            font-size: 70px;
            color: rgba(192, 192, 192, 0.03);
            position: absolute;
            top: 20px;
        }

        .slot-indicator {
            width: 15px;
            height: 15px;
            border-radius: 50%;
            background: #200;
            margin-bottom: 20px;
            border: 1px solid #400;
        }

        .slot-indicator.active {
            background: var(--electric-blue);
            box-shadow: 0 0 20px var(--electric-blue);
        }

        .slot-label {
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 3px;
            color: #333;
            text-transform: uppercase;
        }

        /* --- [ MODAL OVERLAY ] --- */
        #portal {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.98);
            z-index: 2000;
            display: none;
            align-items: center;
            justify-content: center;
        }

        .portal-box {
            background: #050505;
            border: 1px solid var(--silver-trim);
            padding: 80px;
            width: 600px;
            text-align: center;
            box-shadow: 0 0 100px rgba(0,0,0,1);
        }

        .watermark {
            position: fixed;
            bottom: 20px;
            right: 30px;
            font-size: 10px;
            font-weight: 900;
            color: #1a1a1a;
            letter-spacing: 2px;
        }

    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <h1 class="logo-text">ARCANE</h1>
            <div class="dev-tag">Developed By Unc</div>
            <div class="credits-tag">CREDITS: COCO & ROEY</div>
        </div>

        <div class="nav-ledger">
            <div class="nav-item active">ARCHIVE REPOSITORY</div>
            <div class="nav-item">ZEN DIAGNOSTICS</div>
            <div class="nav-item">SYSTEM LOGS</div>
            <div class="nav-item" onclick="togglePortal()">PUBLISH BINARY</div>

            <div class="sync-hub">
                <button class="btn-handshake" onclick="initZenLink()">INITIALIZE LINK</button>
                <div class="status-monitor" id="sync-status">HARDWARE_OFFLINE</div>
            </div>
        </div>
    </div>

    <div class="canvas">
        <div class="top-row">
            <div style="font-weight: 900; font-size: 12px; letter-spacing: 4px; color: var(--silver-trim);">VAULT_STATUS: SECURE</div>
            <input type="text" class="search-box" placeholder="Filter binaries...">
        </div>

        <div class="vault-scroll" id="vault-grid">
            </div>

        <div class="memory-footer">
            <script>
                for(let i=1; i<=8; i++) {
                    document.write(`
                        <div class="slot">
                            <div class="slot-idx">${i}</div>
                            <div class="slot-indicator" id="led-${i}"></div>
                            <div class="slot-label" id="label-${i}">SECTOR_EMPTY</div>
                        </div>
                    `);
                }
            </script>
        </div>
    </div>

    <div id="portal">
        <div class="portal-box">
            <h2 style="font-family:'Cinzel'; color:var(--silver-trim); font-size: 36px; margin-bottom: 40px;">Publish Binary</h2>
            <form action="/api/upload" method="post" enctype="multipart/form-data">
                <input type="text" name="pub_id" placeholder="Access Identifier" style="width:100%; padding:20px; background:#000; border:1px solid #222; color:#fff; margin-bottom:25px;" required>
                <input type="text" name="s_name" placeholder="Designation Name" style="width:100%; padding:20px; background:#000; border:1px solid #222; color:#fff; margin-bottom:25px;" required>
                <input type="file" name="file" style="margin-bottom:40px;" required>
                <button type="submit" class="btn-handshake">COMMIT TO VAULT</button>
            </form>
            <button onclick="togglePortal()" style="background:none; border:none; color:#333; margin-top:30px; cursor:pointer; font-weight:900;">ABORT_SESSION</button>
        </div>
    </div>

    <div class="watermark">ARCANE_V5 | STABLE_BUILD | DEV_UNC</div>

    <script>
        // --- [ HARDWARE LINK ENGINE ] ---
        let zen = null;

        // Expanded Filter Set for Cronus Zen (Standard, Bootloader, and Recovery modes)
        const ZEN_FILTERS = [
            { vendorId: 0x2508, productId: 0x0003 }, // Zen Standard
            { vendorId: 0x2508, productId: 0x8003 }, // Zen Bootloader
            { vendorId: 0x0C1C, productId: 0x1D01 }, // Alternate Interface
            { vendorId: 0x054C, productId: 0x05C4 }  // DualShock Bridge Mode
        ];

        async function initZenLink() {
            try {
                // Requesting access via the browser's WebUSB API
                zen = await navigator.usb.requestDevice({ filters: ZEN_FILTERS });
                
                await zen.open();
                if (zen.configuration === null) await zen.selectConfiguration(1);
                await zen.claimInterface(0);

                document.getElementById('sync-status').innerText = "HARDWARE_SYNCHRONIZED";
                document.getElementById('sync-status').style.color = "var(--electric-blue)";
                
                // Light up the first 3 sectors to show communication is active
                for(let i=1; i<=3; i++) {
                    document.getElementById('led-' + i).classList.add('active');
                    document.getElementById('label-' + i).innerText = "SECTOR_LINKED";
                    document.getElementById('label-' + i).style.color = "#888";
                }
                
                alert("ARCANE: Zen Protocol Handshake Successful.");
            } catch (err) {
                console.error(err);
                alert("ARCANE ERROR: Device not detected. Connect to PROG port and ensure 'WebUSB' is enabled in browser.");
            }
        }

        async function deployBinary(scriptId, name) {
            if(!zen) return alert("ARCANE: Initialize Handshake First.");
            
            const response = await fetch(`/api/download/${scriptId}`);
            if(!response.ok) {
                if(response.status === 403) alert("Access Denied: Permission ticket required.");
                return;
            }

            const data = new Uint8Array(await (await response.blob()).arrayBuffer());
            
            try {
                // Break data into 64-byte packets for Zen VM compatibility
                for (let i = 0; i < data.length; i += 64) {
                    const packet = data.slice(i, i + 64);
                    await zen.transferOut(1, packet);
                }
                alert("SUCCESS: Binary " + name + " written to device memory.");
            } catch (e) {
                alert("HARDWARE FAULT: Transfer Interrupted.");
            }
        }

        function togglePortal() {
            const p = document.getElementById('portal');
            p.style.display = (p.style.display === 'flex') ? 'none' : 'flex';
        }

        async function loadArchive() {
            const res = await fetch('/api/scripts');
            const data = await res.json();
            const grid = document.getElementById('vault-grid');
            grid.innerHTML = data.map(s => `
                <div class="card">
                    <div class="card-header">PUBLISHER: ${s.publisher}</div>
                    <h3>${s.name}</h3>
                    <button class="btn-handshake" style="padding:15px; font-size:11px;" onclick="deployBinary('${s.id}', '${s.name}')">FLASH BINARY</button>
                </div>
            `).join('');
        }

        loadArchive();
    </script>
</body>
</html>
"""

# --- [ 4. BACKEND ENDPOINTS ] ---

@app.route('/')
def home():
    return render_template_string(MASTER_HTML)

@app.route('/api/scripts')
def list_scripts():
    vault = load_vault()
    return jsonify(vault["scripts"])

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    vault = load_vault()
    pub_id = request.form.get('pub_id')
    
    # Permission logic
    if pub_id not in vault["authorized_publishers"]:
        logger.warning(f"UNAUTHORIZED UPLOAD ATTEMPT: {pub_id}")
        return "Unauthorized", 403
    
    file = request.files['file']
    s_name = request.form.get('s_name')
    
    if file and s_name:
        filename = secure_filename(f"{s_name}_{int(time.time())}.bin")
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        
        new_entry = {
            "id": len(vault["scripts"]) + 1,
            "name": s_name,
            "publisher": pub_id,
            "filename": filename,
            "timestamp": str(datetime.datetime.now())
        }
        vault["scripts"].append(new_entry)
        save_vault(vault)
        return redirect(url_for('home'))
    
    return "Invalid Request", 400

@app.route('/api/download/<int:script_id>')
def serve_binary(script_id):
    vault = load_vault()
    script = next((s for s in vault["scripts"] if s["id"] == script_id), None)
    if not script:
        return "Not Found", 404
    
    return send_from_directory(UPLOAD_FOLDER, script["filename"])

# --- [ 5. DISCORD INTERFACE ] ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Arcane Discord Controller Online: {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="authorize", description="Grant publisher access.")
async def authorize_user(interaction: discord.Interaction, member: discord.Member):
    if str(interaction.user.id) != OWNER_ID:
        return await interaction.response.send_message("Architect clearance required.", ephemeral=True)
    
    vault = load_vault()
    if str(member.id) not in vault["authorized_publishers"]:
        vault["authorized_publishers"].append(str(member.id))
        save_vault(vault)
        await interaction.response.send_message(f"Authorized {member.mention} to publish binaries.")
    else:
        await interaction.response.send_message("User already authorized.")

# --- [ 6. KERNEL EXECUTION ] ---
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

if __name__ == "__main__":
    # Start Web Thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start Discord Engine
    if TOKEN:
        bot.run(TOKEN)
    else:
        logger.critical("NO DISCORD_TOKEN FOUND.")
