import os
import json
import logging
import threading
import datetime
import secrets
from flask import Flask, jsonify, request, render_template_string, send_from_directory, redirect, url_for, session
from werkzeug.utils import secure_filename
from discord.ext import commands
import discord
from dotenv import load_dotenv

# --- [ 1. SYSTEM CORE & INITIALIZATION ] ---
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
OWNER_ID = os.environ.get("OWNER_ID")  # Your Discord ID
SECRET_KEY = secrets.token_hex(24)

# Directory Architecture
DB_FILE = "arcane_vault_v5.json"
UPLOAD_FOLDER = "scripts_vault"
LOG_FILE = "system_audit.log"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Advanced Logging for the Secret Society
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [ARCANE_KERNEL] %(levelname)s: %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("ArcaneOS")

# --- [ 2. DATABASE REPOSITORY ] ---
def load_vault_data():
    if not os.path.exists(DB_FILE):
        return {
            "scripts": [],
            "authorized_publishers": [OWNER_ID],
            "audit_logs": [],
            "metadata": {
                "version": "V5.0.1",
                "lead_developer": "Unc",
                "contributing_architects": ["Coco", "Roey"],
                "build_date": str(datetime.date.today())
            }
        }
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Vault Corruption Detected: {e}")
        return {}

def save_vault_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- [ 3. THE GILDED MARBLE INTERFACE (HTML/CSS/JS) ] ---
app = Flask(__name__)
app.secret_key = SECRET_KEY

ARCANE_MASTER_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE V5 | Gilded Secret Society Vault</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Montserrat:wght@200;400;900&display=swap" rel="stylesheet">
    <style>
        /* --- [ CSS ENGINE: GOLD MARBLE & COBALT SHIMMER ] --- */
        :root {
            --gold: #d4af37;
            --gold-bright: #f9e29d;
            --cobalt: #002366;
            --electric-blue: #00d2ff;
            --deep-black: #020205;
            --marble-texture: url('https://www.transparenttextures.com/patterns/marble.png');
            --shimmer-anim: shimmer-metallic 4s infinite alternate;
        }

        @keyframes shimmer-metallic {
            0% { border-color: #1a1a1a; box-shadow: 0 0 5px rgba(0, 210, 255, 0.1); }
            100% { border-color: var(--gold); box-shadow: 0 0 25px rgba(212, 175, 55, 0.4); }
        }

        @keyframes gold-vein-pulse {
            0% { background-position: 0% 50%; }
            100% { background-position: 100% 50%; }
        }

        body {
            background-color: var(--deep-black);
            background-image: var(--marble-texture), radial-gradient(circle at center, #0a0f1e 0%, #000 100%);
            color: #e0e0e0;
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            height: 100vh;
            display: flex;
            overflow: hidden;
            border: 2px solid var(--gold);
            box-sizing: border-box;
        }

        /* --- [ SIDEBAR: ARCHITECT'S WING ] --- */
        .sidebar {
            width: 400px;
            background: rgba(5, 5, 10, 0.98);
            border-right: 2px solid var(--gold);
            display: flex;
            flex-direction: column;
            z-index: 100;
            backdrop-filter: blur(15px);
            box-shadow: 10px 0 60px rgba(0,0,0,1);
        }

        .sidebar-header {
            padding: 60px 40px;
            text-align: center;
            border-bottom: 1px solid rgba(212, 175, 55, 0.1);
            background: linear-gradient(180deg, rgba(212, 175, 55, 0.05) 0%, transparent 100%);
        }

        .logo-main {
            font-family: 'Cinzel', serif;
            font-size: 58px;
            font-weight: 900;
            letter-spacing: 15px;
            background: linear-gradient(90deg, #fff, var(--gold), #fff);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gold-vein-pulse 5s linear infinite;
        }

        .dev-badge {
            font-size: 10px;
            color: var(--gold);
            letter-spacing: 5px;
            text-transform: uppercase;
            margin-top: 25px;
            font-weight: 900;
            opacity: 0.8;
        }

        .credits-sub {
            font-size: 8px;
            color: #444;
            margin-top: 10px;
            letter-spacing: 2px;
        }

        .nav-container {
            flex: 1;
            padding: 40px;
            overflow-y: auto;
        }

        .nav-btn {
            padding: 22px;
            margin-bottom: 20px;
            border: 1px solid transparent;
            cursor: pointer;
            transition: 0.4s;
            font-weight: 800;
            letter-spacing: 3px;
            font-size: 11px;
            color: #666;
            text-transform: uppercase;
        }

        .nav-btn:hover {
            color: var(--electric-blue);
            border-color: var(--electric-blue);
            background: rgba(0, 210, 255, 0.03);
        }

        .nav-btn.active {
            color: #fff;
            border-color: var(--gold);
            background: rgba(212, 175, 55, 0.05);
            text-shadow: 0 0 10px var(--gold);
        }

        /* --- [ BUTTON ARCHITECTURE ] --- */
        .btn-handshake {
            width: 100%;
            padding: 25px;
            background: #000;
            border: 1px solid var(--gold);
            color: var(--gold);
            font-family: 'Cinzel', serif;
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 6px;
            cursor: pointer;
            transition: 0.5s;
            position: relative;
            overflow: hidden;
        }

        .btn-handshake:hover {
            background: var(--gold);
            color: #000;
            box-shadow: 0 0 40px var(--gold);
        }

        /* --- [ THE MAIN VAULT INTERFACE ] --- */
        .main-stage {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .top-status-bar {
            height: 120px;
            padding: 0 60px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(212, 175, 55, 0.1);
        }

        .search-vault {
            width: 500px;
            background: rgba(0,0,0,0.5);
            border: 1px solid #1a1a1a;
            padding: 18px 30px;
            color: #fff;
            font-family: 'Montserrat', sans-serif;
            border-radius: 4px;
        }

        .hardware-light-group {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .led-indicator {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #200;
            box-shadow: 0 0 5px #f00;
            transition: 0.5s;
        }

        .led-indicator.active {
            background: var(--electric-blue);
            box-shadow: 0 0 25px var(--electric-blue);
        }

        .grid-container {
            flex: 1;
            padding: 60px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
            gap: 40px;
            overflow-y: auto;
        }

        .script-card {
            background: rgba(5, 5, 15, 0.8);
            border: 1px solid rgba(212, 175, 55, 0.15);
            padding: 45px;
            transition: 0.6s cubic-bezier(0.23, 1, 0.32, 1);
            position: relative;
            overflow: hidden;
            animation: var(--shimmer-anim);
        }

        .script-card:hover {
            transform: translateY(-15px) scale(1.02);
            border-color: var(--electric-blue);
        }

        /* --- [ REINFORCED MEMORY SLOTS ] --- */
        .memory-footer {
            height: 320px;
            background: #000;
            border-top: 3px solid var(--gold);
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            gap: 5px;
            padding: 5px;
        }

        .memory-slot {
            background: linear-gradient(180deg, #08080c 0%, #000 100%);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 1px solid #111;
            transition: 0.3s;
            position: relative;
        }

        .memory-slot:hover {
            background: #0d0d15;
            border-color: var(--electric-blue);
        }

        .slot-id {
            font-family: 'Cinzel', serif;
            font-size: 52px;
            color: rgba(212, 175, 55, 0.03);
            position: absolute;
            top: 20px;
        }

        .slot-name {
            font-size: 10px;
            letter-spacing: 3px;
            color: #444;
            font-weight: 900;
            text-transform: uppercase;
        }

        /* MODAL OVERLAYS */
        #gate-modal {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.98);
            z-index: 1000;
            display: none;
            align-items: center;
            justify-content: center;
        }

        .modal-vault-box {
            background: #050505;
            border: 1px solid var(--gold);
            padding: 80px;
            width: 600px;
            box-shadow: 0 0 100px rgba(212, 175, 55, 0.2);
            text-align: center;
        }

        .watermark-dev {
            position: fixed;
            bottom: 20px;
            right: 30px;
            font-size: 10px;
            font-weight: 900;
            color: #222;
            letter-spacing: 2px;
        }

    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <h1 class="logo-main">ARCANE</h1>
            <div class="dev-badge">Developed By Unc</div>
            <div class="credits-sub">CREDITS TO COCO & ROEY</div>
        </div>

        <div class="nav-container">
            <div class="nav-btn active">VAULT ACCESS</div>
            <div class="nav-btn">HARDWARE STATUS</div>
            <div class="nav-btn">TRANSACTION LOGS</div>
            <div class="nav-btn" onclick="openGate()">COMMIT NEW BINARY</div>

            <div style="margin-top: 120px;">
                <button class="btn-handshake" onclick="runZenHandshake()">INITIALIZE LINK</button>
            </div>
        </div>
    </div>

    <div class="main-stage">
        <div class="top-status-bar">
            <input type="text" class="search-vault" placeholder="Query the secret archives...">
            <div class="hardware-light-group">
                <div class="led-indicator" id="zen-led"></div>
                <div style="font-size: 12px; font-weight: 900; letter-spacing: 3px; color: var(--gold);">
                    LINK: <span id="sync-text">OFFLINE</span>
                </div>
            </div>
        </div>

        <div class="grid-container" id="script-injection-point">
            </div>

        <div class="memory-footer">
            <script>
                for(let i=1; i<=8; i++) {
                    document.write(`
                        <div class="memory-slot">
                            <div class="slot-id">${i}</div>
                            <div class="slot-name" id="slot-tag-${i}">SECTOR_EMPTY</div>
                        </div>
                    `);
                }
            </script>
        </div>
    </div>

    <div id="gate-modal">
        <div class="modal-vault-box">
            <h2 style="font-family:'Cinzel'; color:var(--gold); font-size:32px;">Authorized Upload</h2>
            <form action="/api/upload" method="post" enctype="multipart/form-data">
                <input type="text" name="pub_id" placeholder="DISCORD_IDENTIFIER" style="width:100%; padding:20px; background:#000; border:1px solid #333; color:#fff; margin-bottom:20px;">
                <input type="text" name="s_name" placeholder="SCRIPT_DESIGNATION" style="width:100%; padding:20px; background:#000; border:1px solid #333; color:#fff; margin-bottom:20px;">
                <input type="file" name="file" style="margin-bottom:30px; color:#444;">
                <button type="submit" class="btn-handshake">PUSH TO VAULT</button>
            </form>
            <button onclick="openGate()" style="background:none; border:none; color:#444; margin-top:30px; cursor:pointer; font-weight:900;">ABORT SESSION</button>
        </div>
    </div>

    <div class="watermark-dev">ARCANE_V5.0 | SYSTEM_STABLE | BY_UNC</div>

    <script>
        // --- [ ADVANCED HARDWARE HANDSHAKE ENGINE ] ---
        let device = null;
        
        // Multi-State Scan (Ensures it finds Zen even in recovery or prog mode)
        const FILTERS = [
            { vendorId: 0x0C1C, productId: 0x1D01 }, // Standard
            { vendorId: 0x0C1C, productId: 0xF001 }, // Bootloader
            { vendorId: 0x0C1C } // Vendor Sweep
        ];

        async function runZenHandshake() {
            try {
                device = await navigator.usb.requestDevice({ filters: FILTERS });
                await device.open();
                
                if (device.configuration === null) {
                    await device.selectConfiguration(1);
                }
                
                await device.claimInterface(0);
                
                document.getElementById('zen-led').classList.add('active');
                document.getElementById('sync-text').innerText = "SYNCHRONIZED";
                document.getElementById('sync-text').style.color = "var(--electric-blue)";
                
                alert("ARCANE CORE: Secure Handshake Established.");
            } catch (err) {
                console.error("Hardware Error:", err);
                alert("ARCANE ERROR: Handshake Denied. Verify Zen PROG connection.");
            }
        }

        async function writeToSector(id, name) {
            if(!device) return alert("Error: No Active Handshake.");
            
            const res = await fetch(`/api/download/${id}`);
            if(!res.ok) {
                if(res.status === 403) alert("Nice try, Make a ticket in the discord to get perms for this file");
                return;
            }

            const binaryData = new Uint8Array(await (await res.blob()).arrayBuffer());
            
            // WebUSB transfer packet logic
            try {
                await device.transferOut(1, binaryData);
                alert("SUCCESS: Sector Synced with " + name);
            } catch (e) {
                alert("HARDWARE FAULT: Transfer Interrupted.");
            }
        }

        function openGate() {
            const m = document.getElementById('gate-modal');
            m.style.display = (m.style.display === 'flex') ? 'none' : 'flex';
        }

        async function fetchRegistry() {
            const res = await fetch('/api/scripts');
            const data = await res.json();
            const grid = document.getElementById('script-injection-point');
            
            grid.innerHTML = data.map(s => `
                <div class="script-card">
                    <div style="font-size:9px; color:var(--gold); font-weight:900; letter-spacing:2px;">PUBLISHER: ${s.publisher}</div>
                    <h3 style="font-family:'Cinzel'; margin:20px 0; font-size:24px;">${s.name}</h3>
                    <button class="btn-handshake" style="padding:15px; font-size:12px; width:100%;" onclick="writeToSector('${s.id}', '${s.name}')">DEPLOY BINARY</button>
                </div>
            `).join('');
        }

        fetchRegistry();
    </script>
</body>
</html>
"""

# --- [ 4. BACKEND INFRASTRUCTURE ] ---

@app.route('/')
def home():
    return render_template_string(ARCANE_MASTER_UI)

@app.route('/api/scripts')
def get_vault_scripts():
    data = load_vault_data()
    return jsonify(data["scripts"])

@app.route('/api/upload', methods=['POST'])
def handle_vault_upload():
    db = load_vault_data()
    pub_id = request.form.get('pub_id')
    
    # Permission Gate
    if pub_id not in db["authorized_publishers"]:
        logger.warning(f"UNAUTHORIZED ACCESS ATTEMPT BY: {pub_id}")
        return "Access Denied", 403
    
    file = request.files['file']
    s_name = request.form.get('s_name')
    
    if file and s_name:
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        safe_name = secure_filename(f"{s_name}_{ts}.bin")
        file.save(os.path.join(UPLOAD_FOLDER, safe_name))
        
        new_script = {
            "id": len(db["scripts"]) + 1,
            "name": s_name,
            "publisher": pub_id,
            "file_path": safe_name,
            "date": str(datetime.date.today())
        }
        db["scripts"].append(new_script)
        save_vault_data(db)
        return redirect(url_for('home'))
    
    return "Missing Parameters", 400

@app.route('/api/download/<int:s_id>')
def serve_binary(s_id):
    db = load_vault_data()
    script = next((s for s in db["scripts"] if s["id"] == s_id), None)
    if not script: return "Not Found", 404
    
    # Add your logic here if you want to check specific Discord roles via an API
    return send_from_directory(UPLOAD_FOLDER, script["file_path"])

# --- [ 5. DISCORD BOT COMMANDS ] ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Arcane Discord Bot Online: {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="grant_access", description="Authorize a member to publish to the vault.")
async def authorize(interaction: discord.Interaction, member: discord.Member):
    if str(interaction.user.id) != OWNER_ID:
        return await interaction.response.send_message("Only Unc can authorize publishers.")
    
    db = load_vault_data()
    if str(member.id) not in db["authorized_publishers"]:
        db["authorized_publishers"].append(str(member.id))
        save_vault_data(db)
        await interaction.response.send_message(f"Access granted to {member.mention}.")
    else:
        await interaction.response.send_message("User is already authorized.")

# --- [ 6. MULTI-THREADED KERNEL ] ---
def launch_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

if __name__ == "__main__":
    # Start Web Server
    threading.Thread(target=launch_web, daemon=True).start()
    # Start Discord Engine
    if TOKEN:
        bot.run(TOKEN)
    else:
        logger.critical("NO DISCORD_TOKEN DETECTED.")
