import os
import json
import logging
import threading
import datetime
import secrets
import time
import uuid
import requests
from flask import Flask, jsonify, request, render_template_string, send_from_directory, redirect, url_for, session
from werkzeug.utils import secure_filename
from discord.ext import commands
import discord
from dotenv import load_dotenv

# ==============================================================================
# [ 1. SYSTEM CORE & SECURITY CONFIG ]
# ==============================================================================
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
# Replace with your actual Discord ID for the 'Lead Architect' tag
OWNER_ID = "638512345678901234" 
VERSION = "V5.6.5-PREMIUM-MARBLE"

# Directory Architecture
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "arcane_vault_v5.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "scripts_vault")
LOG_FILE = os.path.join(BASE_DIR, "system_audit.log")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Professional Audit Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] ARCANE_CORE: %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("ArcaneCore")

# ==============================================================================
# [ 2. DATA ARCHIVE MANAGEMENT (JSON DATABASE) ]
# ==============================================================================
def load_vault():
    """Access the secure JSON vault for script metadata."""
    if not os.path.exists(DB_FILE):
        return {
            "scripts": [],
            "authorized_publishers": [OWNER_ID],
            "system_logs": [],
            "stats": {"total_flashes": 0, "active_sessions": 0},
            "config": {
                "version": VERSION,
                "lead_dev": "Unc",
                "theme": "Blue-Gold-Marble"
            }
        }
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Vault Read Error: {e}")
        return {"scripts": [], "authorized_publishers": [OWNER_ID]}

def save_vault(data):
    """Commit changes to the vault disk."""
    try:
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Vault Write Error: {e}")

# ==============================================================================
# [ 3. THE GILDED INTERFACE ENGINE (700+ LINE FRONTEND) ]
# ==============================================================================
app = Flask(__name__)
app.secret_key = secrets.token_hex(64)

MASTER_UI_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE REPOSITORY | V5.6.5 PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Montserrat:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        /* --- [ CSS MASTER ENGINE: BLUE, GOLD & MARBLE ] --- */
        :root {
            --cobalt: #00d2ff;
            --gold: #ffd700;
            --marble-texture: url('https://i.ibb.co/3c1baac1/marble.png');
            --deep-black: #020205;
            --panel-glass: rgba(0, 0, 0, 0.92);
            --arcane-orange: #ff6600;
        }

        * { box-sizing: border-box; outline: none; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        
        body {
            background: linear-gradient(rgba(0, 0, 20, 0.7), rgba(0, 0, 0, 0.9)), var(--marble-texture);
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            height: 100vh;
            display: flex;
            overflow: hidden;
            border: 4px solid #111;
        }

        /* --- [ SIDEBAR NAVIGATION ] --- */
        .sidebar {
            width: 420px;
            background: var(--panel-glass);
            border-right: 1px solid rgba(255, 215, 0, 0.1);
            display: flex;
            flex-direction: column;
            z-index: 100;
            backdrop-filter: blur(25px);
            box-shadow: 20px 0 60px rgba(0,0,0,0.8);
        }

        .sidebar-header {
            padding: 70px 45px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }

        .logo {
            font-family: 'Cinzel', serif;
            font-size: 55px;
            font-weight: 900;
            letter-spacing: 10px;
            color: var(--arcane-orange);
            text-shadow: 0 0 30px rgba(255, 102, 0, 0.3);
            margin: 0;
        }

        .tagline {
            font-size: 10px;
            color: #444;
            letter-spacing: 4px;
            margin-top: 15px;
            font-weight: 900;
            text-transform: uppercase;
        }

        .nav-content { flex: 1; padding: 50px 45px; }
        
        .nav-label {
            font-size: 10px;
            color: #222;
            font-weight: 900;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 35px;
            display: block;
        }

        .nav-item {
            display: flex;
            align-items: center;
            padding: 22px;
            color: #666;
            font-weight: 900;
            text-decoration: none;
            font-size: 13px;
            border-radius: 4px;
            margin-bottom: 15px;
            border: 1px solid transparent;
            cursor: pointer;
        }

        .nav-item:hover, .nav-item.active {
            color: var(--arcane-orange);
            background: rgba(255, 102, 0, 0.05);
            border-color: var(--arcane-orange);
            box-shadow: 0 0 20px rgba(255, 102, 0, 0.1);
        }

        .sidebar-footer {
            padding: 45px;
            border-top: 1px solid rgba(255, 255, 255, 0.03);
        }

        /* --- [ MAIN STAGE INTERFACE ] --- */
        .stage {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .stage-header {
            height: 120px;
            padding: 0 70px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(0,0,0,0.5);
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }

        .search-vault {
            width: 450px;
            background: #000;
            border: 1px solid #111;
            padding: 22px 30px;
            color: #fff;
            border-radius: 4px;
            font-size: 14px;
        }

        .grid-container {
            flex: 1;
            padding: 70px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 50px;
            overflow-y: auto;
        }

        /* --- [ REINFORCED 8-SLOT SYSTEM GRID ] --- */
        .footer-tray {
            height: 380px;
            background: rgba(0, 0, 0, 0.95);
            border-top: 2px solid var(--gold);
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            grid-template-rows: repeat(2, 1fr);
            padding: 20px;
            gap: 20px;
        }

        .memory-slot {
            background: rgba(15, 20, 30, 0.8);
            border: 1px solid #111;
            display: flex;
            align-items: center;
            padding: 30px;
            position: relative;
            overflow: hidden;
        }

        .slot-num-giant {
            font-family: 'Montserrat', sans-serif;
            font-size: 90px;
            font-weight: 900;
            color: #4a90e2;
            opacity: 0.7;
            position: absolute;
            left: 20px;
            z-index: 1;
        }

        .slot-details {
            margin-left: 100px;
            z-index: 5;
        }

        .slot-header { font-size: 10px; color: #333; font-weight: 900; letter-spacing: 3px; margin-bottom: 5px; }
        .slot-status { font-size: 13px; color: #555; font-weight: 700; text-transform: uppercase; }

        .led-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #150000;
            position: absolute;
            top: 20px;
            right: 20px;
            border: 1px solid #300;
        }

        .led-indicator.online {
            background: var(--cobalt);
            box-shadow: 0 0 20px var(--cobalt);
            border-color: #fff;
        }

        /* --- [ SCRIPT CARDS ] --- */
        .script-card {
            background: rgba(5, 5, 10, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 60px 45px;
            border-radius: 4px;
            text-align: center;
            position: relative;
        }

        .script-card:hover {
            transform: translateY(-10px);
            border-color: var(--arcane-orange);
            box-shadow: 0 30px 60px rgba(0,0,0,0.8);
        }

        .author-tag {
            font-size: 10px;
            color: var(--arcane-orange);
            font-weight: 900;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 25px;
        }

        .script-name {
            font-family: 'Cinzel', serif;
            font-size: 32px;
            margin: 0 0 35px 0;
            font-weight: 900;
            letter-spacing: 2px;
            color: #eee;
        }

        .btn-universal {
            width: 100%;
            padding: 22px;
            background: var(--arcane-orange);
            border: none;
            color: #000;
            font-family: 'Cinzel', serif;
            font-weight: 900;
            cursor: pointer;
            letter-spacing: 4px;
            font-size: 13px;
            border-radius: 2px;
        }

        .btn-universal:hover {
            background: #fff;
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.2);
        }

        /* --- [ MODAL OVERLAYS ] --- */
        #portal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.98);
            z-index: 1000;
            display: none;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(15px);
        }

        .portal-content {
            background: #040508;
            border: 1px solid var(--arcane-orange);
            padding: 100px;
            width: 750px;
            box-shadow: 0 0 100px rgba(255, 102, 0, 0.15);
        }

        .arcane-input {
            width: 100%;
            padding: 25px;
            background: #000;
            border: 1px solid #111;
            color: #fff;
            margin-bottom: 25px;
            font-family: 'Montserrat', sans-serif;
            font-size: 15px;
        }

        .arcane-input:focus { border-color: var(--gold); }

    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <h1 class="logo">ARCANE</h1>
            <div class="tagline">Gilded Repository V5.6.5</div>
        </div>

        <div class="nav-content">
            <span class="nav-label">ARCHIVE ACCESS</span>
            <div class="nav-item active">Repository Marketplace</div>
            <div class="nav-item">Device Input Monitor</div>
            <div class="nav-item">GPC Compiler Console</div>
            <div class="nav-item">System Diagnostics</div>

            <span class="nav-label" style="margin-top:60px;">ARCHITECT GATE</span>
            <div class="nav-item" onclick="togglePortal()">Commit New Binary</div>
        </div>

        <div class="sidebar-footer">
            <button class="btn-universal" onclick="connectHardware()">INITIALIZE HANDSHAKE</button>
            <div id="handshake-status" style="text-align:center; font-size:10px; color:#333; margin-top:30px; letter-spacing:3px; font-weight:900;">SYSTEM_OFFLINE</div>
        </div>
    </div>

    <div class="stage">
        <div class="stage-header">
            <input type="text" class="search-vault" placeholder="Query the secret archives...">
            <div style="display:flex; gap:40px;">
                <div style="font-size:10px; color:var(--gold); font-weight:900; letter-spacing:2px;">ENCRYPTION: ACTIVE</div>
                <div style="font-size:10px; color:var(--cobalt); font-weight:900; letter-spacing:2px;">DEST: <span id="dest-slot" style="color:#fff">SLOT_01</span></div>
            </div>
        </div>

        <div class="grid-container" id="vault-grid">
            </div>

        <div class="footer-tray">
            <script>
                for(let i=1; i<=8; i++) {
                    document.write(`
                        <div class="memory-slot">
                            <div class="slot-num-giant">${i}</div>
                            <div class="slot-details">
                                <div class="slot-header">MEMORY_BANK_0${i}</div>
                                <div class="slot-status" id="slot-name-${i}">EMPTY_SLOT</div>
                            </div>
                            <div class="led-indicator" id="led-${i}"></div>
                        </div>
                    `);
                }
            </script>
        </div>
    </div>

    <div id="portal-overlay">
        <div class="portal-content">
            <h2 style="font-family:'Cinzel'; color:var(--arcane-orange); font-size:45px; margin-bottom:60px; text-align:center; letter-spacing:5px;">ARCHIVE COMMIT</h2>
            <form action="/api/upload" method="post" enctype="multipart/form-data">
                <input type="text" name="pub_id" class="arcane-input" placeholder="Architect Verification Key" required>
                <input type="text" name="s_name" class="arcane-input" placeholder="Script Identification Name" required>
                <input type="file" name="file" style="margin-bottom:60px; color:#555;" required>
                <button type="submit" class="btn-universal">SECURE UPLOAD</button>
            </form>
            <button onclick="togglePortal()" style="background:none; border:none; color:#222; width:100%; margin-top:40px; cursor:pointer; font-weight:900; letter-spacing:3px;">ABORT_SESSION</button>
        </div>
    </div>

    <script>
        let zen = null;

        // --- [ KERNEL HARDWARE HANDSHAKE ] ---
        async function connectHardware() {
            try {
                zen = await navigator.usb.requestDevice({ filters: [] });
                await zen.open();
                if (zen.configuration === null) await zen.selectConfiguration(1);
                
                // NO-DRIVER FIX: Claiming only Interface 0 to avoid Windows conflicts
                await zen.claimInterface(0);

                const stat = document.getElementById('handshake-status');
                stat.innerText = "LINKED: " + (zen.productName || "ZEN_UNIT");
                stat.style.color = "var(--cobalt)";

                // Light up hardware slots
                for(let i=1; i<=8; i++) {
                    document.getElementById('led-'+i).classList.add('online');
                }
                
                alert("Handshake Complete. Arcane Repository is now synchronized with hardware.");
            } catch (err) {
                console.error(err);
                alert("Handshake Aborted. Verify PROG port and close Zen Studio.");
            }
        }

        async function flashToMemory(scriptId, scriptName) {
            if(!zen) return alert("Hardware Link Required.");
            
            const btn = event.target;
            const originalText = btn.innerText;
            btn.innerText = "PROGRAMMING...";
            
            try {
                const response = await fetch(`/api/download/${scriptId}`);
                const blob = await response.blob();
                const buffer = new Uint8Array(await blob.arrayBuffer());

                // PROGRAMMING PROTOCOL: 64-Byte Packet Stream
                for (let i = 0; i < buffer.length; i += 64) {
                    await zen.transferOut(1, buffer.slice(i, i + 64));
                }

                // Update Visual Slot 1 (Default)
                document.getElementById('slot-name-1').innerText = scriptName.toUpperCase();
                document.getElementById('slot-name-1').style.color = "var(--cobalt)";
                
                btn.innerText = "SYNC COMPLETE";
                setTimeout(() => { btn.innerText = originalText; }, 3000);
            } catch (err) {
                alert("Transfer Interrupted.");
                btn.innerText = "FAULT DETECTED";
            }
        }

        function togglePortal() {
            const p = document.getElementById('portal-overlay');
            p.style.display = (p.style.display === 'flex') ? 'none' : 'flex';
        }

        async function refreshArchives() {
            const r = await fetch('/api/scripts');
            const data = await r.json();
            const grid = document.getElementById('vault-grid');
            
            grid.innerHTML = data.map(s => `
                <div class="script-card">
                    <div class="author-tag">Architect: ${s.publisher}</div>
                    <h2 class="script-name">${s.name}</h2>
                    <button class="btn-universal" onclick="flashToMemory('${s.id}', '${s.name}')">SYNC TO ZEN</button>
                </div>
            `).join('');
        }

        refreshArchives();
    </script>
</body>
</html>
"""

# ==============================================================================
# [ 4. BACKEND API ENDPOINTS ]
# ==============================================================================

@app.route('/')
def main_view():
    return render_template_string(MASTER_UI_TEMPLATE)

@app.route('/api/scripts')
def api_scripts():
    v = load_vault()
    return jsonify(v["scripts"])

@app.route('/api/upload', methods=['POST'])
def api_upload():
    v = load_vault()
    pub_id = request.form.get('pub_id')
    
    # Architect Verification
    if pub_id not in v["authorized_publishers"]:
        logger.warning(f"Unauthorized Access: {pub_id}")
        return "Verification Failed: Access Denied.", 403
    
    file = request.files['file']
    s_name = request.form.get('s_name')
    
    if file and s_name:
        safe_name = secure_filename(f"{s_name}_{int(time.time())}.bin")
        file.save(os.path.join(UPLOAD_FOLDER, safe_name))
        
        entry = {
            "id": str(uuid.uuid4())[:8],
            "name": s_name,
            "publisher": "Lead Architect" if pub_id == OWNER_ID else "Architect",
            "filename": safe_name,
            "timestamp": str(datetime.datetime.now())
        }
        
        v["scripts"].append(entry)
        save_vault(v)
        return redirect(url_for('main_view'))
    
    return "Invalid Data Block", 400

@app.route('/api/download/<string:s_id>')
def api_download(s_id):
    v = load_vault()
    script = next((s for s in v["scripts"] if s["id"] == s_id), None)
    if not script:
        return "Binary not found in Vault", 404
    
    v["stats"]["total_flashes"] += 1
    save_vault(v)
    return send_from_directory(UPLOAD_FOLDER, script["filename"])

# ==============================================================================
# [ 5. DISCORD ARCHITECT BOT ]
# ==============================================================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Arcane Discord Kernel Online: {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="vault_audit", description="Audit the repository statistics.")
async def audit(interaction: discord.Interaction):
    v = load_vault()
    scripts_total = len(v["scripts"])
    flashes = v["stats"]["total_flashes"]
    
    embed = discord.Embed(title="Arcane Vault Audit", color=0xff6600)
    embed.add_field(name="Total Binaries", value=scripts_total)
    embed.add_field(name="Successful Syncs", value=flashes)
    embed.add_field(name="Version", value=VERSION)
    await interaction.response.send_message(embed=embed)

# ==============================================================================
# [ 6. EXECUTION ENGINE ]
# ==============================================================================
def run_web_server():
    # Running on Port 10000 for standard hosting compatibility
    app.run(host='0.0.0.0', port=10000, use_reloader=False)

if __name__ == "__main__":
    # Start Web Thread
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # Start Discord Bot
    if TOKEN:
        bot.run(TOKEN)
    else:
        logger.critical("CRITICAL ERROR: Discord Token missing from Environment.")
