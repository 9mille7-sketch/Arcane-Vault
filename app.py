import os
import json
import logging
import threading
import datetime
import secrets
import time
import uuid
from flask import Flask, jsonify, request, render_template_string, send_from_directory, redirect, url_for, session, abort
from werkzeug.utils import secure_filename
from discord.ext import commands
import discord
from dotenv import load_dotenv

# --- [ 1. SYSTEM CORE & INITIALIZATION ] ---
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
OWNER_ID = os.environ.get("OWNER_ID")  # Your Discord ID
SECRET_KEY = os.environ.get("FLASK_SECRET", secrets.token_hex(64))

# Directory Architecture for the Secret Society
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "arcane_vault_v5.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "scripts_vault")
LOG_FILE = os.path.join(BASE_DIR, "system_audit.log")
STATIC_FOLDER = os.path.join(BASE_DIR, "static")

for folder in [UPLOAD_FOLDER, STATIC_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Industrial Strength Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] ARCANE_KERNEL: %(message)s',
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)
logger = logging.getLogger("ArcaneCore")

# --- [ 2. VAULT DATA REPOSITORY ] ---
def load_vault():
    if not os.path.exists(DB_FILE):
        return {
            "scripts": [],
            "authorized_publishers": [OWNER_ID, "854041234567890123"], # IDs for Coco/Roey
            "system_logs": [],
            "stats": {"total_flashes": 0, "active_sessions": 0},
            "config": {
                "version": "V5.5.0",
                "lead_dev": "Unc",
                "architects": ["Coco", "Roey"],
                "branding": "Arcane Vault"
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

# MASSIVE UI BLOCK (CSS & HTML to match cmindapi exactly)
MASTER_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE V5 | Gilded Repository</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Montserrat:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        /* --- [ MASTER STYLING: BRIGHT COBALT & SILVER ] --- */
        :root {
            --cobalt-bright: #00d2ff;
            --cobalt-deep: #001f4d;
            --silver-trim: #c0c0c0;
            --gold-vein: #ffd700;
            --deep-black: #020205;
            --glass: rgba(0, 0, 0, 0.85);
            --marble-url: url('https://i.imgur.com/3c1baac1.png'); /* Fallback to your uploaded texture */
        }

        * { box-sizing: border-box; outline: none; transition: all 0.3s ease; }
        
        body {
            background-color: var(--deep-black);
            background-image: linear-gradient(135deg, rgba(0,210,255,0.05) 0%, transparent 100%), var(--marble-url);
            background-size: cover;
            background-attachment: fixed;
            color: #fff;
            font-family: 'Montserrat', sans-serif;
            margin: 0;
            height: 100vh;
            display: flex;
            overflow: hidden;
            border: 2px solid var(--silver-trim);
        }

        /* --- [ SIDEBAR: MARKETPLACE STYLE ] --- */
        .sidebar {
            width: 420px;
            background: var(--glass);
            border-right: 2px solid var(--silver-trim);
            display: flex;
            flex-direction: column;
            z-index: 100;
            backdrop-filter: blur(20px);
            box-shadow: 15px 0 50px rgba(0,0,0,0.9);
        }

        .sidebar-header {
            padding: 70px 40px;
            text-align: center;
            border-bottom: 1px solid rgba(192, 192, 192, 0.1);
        }

        .logo-main {
            font-family: 'Cinzel', serif;
            font-size: 52px;
            font-weight: 900;
            letter-spacing: 12px;
            color: var(--cobalt-bright);
            text-shadow: 0 0 25px rgba(0, 210, 255, 0.5);
            margin: 0;
        }

        .dev-badge {
            font-size: 10px;
            color: var(--gold-vein);
            letter-spacing: 4px;
            margin-top: 20px;
            font-weight: 900;
            text-transform: uppercase;
        }

        .nav-section {
            flex: 1;
            padding: 40px;
            overflow-y: auto;
        }

        .nav-label {
            font-size: 10px;
            color: #444;
            font-weight: 900;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 20px;
            display: block;
        }

        .nav-link {
            display: block;
            padding: 18px 25px;
            color: #888;
            font-weight: 700;
            text-decoration: none;
            font-size: 13px;
            border-radius: 4px;
            margin-bottom: 10px;
            border: 1px solid transparent;
        }

        .nav-link:hover, .nav-link.active {
            color: #fff;
            background: rgba(0, 210, 255, 0.05);
            border-color: var(--cobalt-bright);
            box-shadow: 0 0 15px rgba(0, 210, 255, 0.1);
        }

        /* --- [ HARDWARE CONSOLE ] --- */
        .hw-console {
            padding: 30px;
            background: rgba(0,0,0,0.5);
            border-top: 1px solid rgba(192, 192, 192, 0.1);
        }

        .btn-handshake {
            width: 100%;
            padding: 22px;
            background: transparent;
            border: 1px solid var(--cobalt-bright);
            color: var(--cobalt-bright);
            font-family: 'Cinzel', serif;
            font-weight: 900;
            letter-spacing: 5px;
            cursor: pointer;
            border-radius: 4px;
        }

        .btn-handshake:hover {
            background: var(--cobalt-bright);
            color: #000;
            box-shadow: 0 0 40px var(--cobalt-bright);
        }

        /* --- [ MAIN STAGE ] --- */
        .stage {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .top-bar {
            height: 100px;
            padding: 0 60px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(0,0,0,0.3);
            border-bottom: 1px solid rgba(192, 192, 192, 0.05);
        }

        .search-vault {
            width: 500px;
            background: rgba(0,0,0,0.6);
            border: 1px solid #1a1a1a;
            padding: 18px 30px;
            color: #fff;
            border-radius: 5px;
        }

        .grid-view {
            flex: 1;
            padding: 60px;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 40px;
            overflow-y: auto;
        }

        /* --- [ REINFORCED MEMORY SLOTS (TALL) ] --- */
        .footer-slots {
            height: 320px;
            background: #010206;
            border-top: 3px solid var(--silver-trim); /* SILVER DIVIDER */
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            padding: 10px;
            gap: 15px;
        }

        .memory-slot {
            background: linear-gradient(180deg, #0a1122 0%, #000 100%);
            border: 1px solid #111;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .memory-slot:hover { border-color: var(--cobalt-bright); }

        .slot-id-bg {
            font-family: 'Cinzel', serif;
            font-size: 70px;
            color: rgba(0, 210, 255, 0.03); /* Faint Blue Num */
            position: absolute;
            top: 20px;
        }

        .slot-indicator {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #100;
            margin-bottom: 25px;
            border: 1px solid #300;
        }

        .slot-indicator.active {
            background: var(--cobalt-bright);
            box-shadow: 0 0 20px var(--cobalt-bright);
            border-color: #fff;
        }

        .slot-tag {
            font-size: 10px;
            font-weight: 900;
            color: #333;
            letter-spacing: 3px;
            text-transform: uppercase;
        }

        /* --- [ SCRIPT CARDS ] --- */
        .card {
            background: rgba(5, 10, 20, 0.8);
            border: 1px solid rgba(192, 192, 192, 0.1);
            padding: 45px;
            border-radius: 5px;
            position: relative;
            overflow: hidden;
        }

        .card:hover {
            transform: translateY(-10px);
            border-color: var(--cobalt-bright);
        }

        .card-publisher {
            font-size: 9px;
            color: var(--cobalt-bright);
            font-weight: 900;
            letter-spacing: 2px;
            margin-bottom: 15px;
        }

        .card-name {
            font-family: 'Cinzel', serif;
            font-size: 28px;
            margin: 0 0 25px 0;
            font-weight: 900;
        }

        .btn-load {
            width: 100%;
            padding: 18px;
            background: transparent;
            border: 1px solid #333;
            color: #666;
            font-family: 'Cinzel', serif;
            font-weight: 900;
            cursor: pointer;
            letter-spacing: 3px;
        }

        .btn-load:hover {
            border-color: var(--cobalt-bright);
            color: var(--cobalt-bright);
        }

        /* UPLOAD PORTAL */
        #portal {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.98);
            z-index: 1000;
            display: none;
            align-items: center;
            justify-content: center;
        }

        .portal-content {
            background: #050508;
            border: 1px solid var(--cobalt-bright);
            padding: 80px;
            width: 600px;
            text-align: center;
        }

        .status-pill {
            padding: 8px 15px;
            border-radius: 50px;
            font-size: 10px;
            font-weight: 900;
            background: #111;
            color: var(--cobalt-bright);
        }

    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <h1 class="logo-main">ARCANE</h1>
            <div class="dev-badge">Developed By Unc</div>
            <div style="font-size:8px; color:#444; margin-top:10px; letter-spacing:2px;">Special Thanks to Coco & Roey</div>
        </div>

        <div class="nav-section">
            <span class="nav-label">Main Repository</span>
            <a href="#" class="nav-link active">Archive Vault</a>
            <a href="#" class="nav-link">Hardware Diagnostics</a>
            <a href="#" class="nav-link">Transaction Audit</a>

            <span class="nav-label" style="margin-top:50px;">Staff Gate</span>
            <a href="#" class="nav-link" onclick="togglePortal()">Commit New Binary</a>
        </div>

        <div class="hw-console">
            <button class="btn-handshake" onclick="universalLink()">INITIALIZE HANDSHAKE</button>
            <div style="margin-top:20px; font-size:10px; text-align:center; color:#444;" id="link-status">SYSTEM_IDLE</div>
        </div>
    </div>

    <div class="stage">
        <div class="top-bar">
            <input type="text" class="search-vault" placeholder="Query the secret archives...">
            <div class="status-pill" id="sync-pill">OUT_OF_SYNC</div>
        </div>

        <div class="grid-view" id="script-injection">
            </div>

        <div class="footer-slots">
            <script>
                for(let i=1; i<=8; i++) {
                    document.write(`
                        <div class="memory-slot">
                            <div class="slot-id-bg">${i}</div>
                            <div class="slot-indicator" id="ind-${i}"></div>
                            <div class="slot-tag" id="tag-${i}">EMPTY_SECTOR</div>
                        </div>
                    `);
                }
            </script>
        </div>
    </div>

    <div id="portal">
        <div class="portal-content">
            <h2 style="font-family:'Cinzel'; font-size:32px; color:var(--cobalt-bright); margin-bottom:40px;">Unauthorized Upload</h2>
            <form action="/api/upload" method="post" enctype="multipart/form-data">
                <input type="text" name="pub_id" placeholder="Verifier ID (Discord UID)" style="width:100%; padding:20px; background:#000; border:1px solid #222; color:#fff; margin-bottom:20px;">
                <input type="text" name="s_name" placeholder="Binary Designation" style="width:100%; padding:20px; background:#000; border:1px solid #222; color:#fff; margin-bottom:20px;">
                <input type="file" name="file" style="margin-bottom:40px; color:#555;">
                <button type="submit" class="btn-handshake">COMMIT BINARY</button>
            </form>
            <button onclick="togglePortal()" style="background:none; border:none; color:#333; margin-top:30px; cursor:pointer; font-weight:900;">ABORT_SESSION</button>
        </div>
    </div>

    <script>
        let activeZen = null;

        // --- [ THE UNIVERSAL DETECTOR ] ---
        async function universalLink() {
            try {
                // Passing NO filters forces the browser to show EVERY USB device connected
                activeZen = await navigator.usb.requestDevice({ filters: [] });
                
                await activeZen.open();
                if (activeZen.configuration === null) await activeZen.selectConfiguration(1);
                await activeZen.claimInterface(0);

                document.getElementById('link-status').innerText = "LINK_SUCCESSFUL: " + activeZen.productName;
                document.getElementById('link-status').style.color = "var(--cobalt-bright)";
                document.getElementById('sync-pill').innerText = "HARDWARE_SYNCHRONIZED";
                document.getElementById('sync-pill').style.color = "#fff";
                document.getElementById('sync-pill').style.background = "var(--cobalt-bright)";

                // Light up sectors to confirm communication
                for(let i=1; i<=4; i++) {
                    document.getElementById('ind-'+i).classList.add('active');
                    document.getElementById('tag-'+i).innerText = "SECTOR_READY";
                }

                alert("Arcane Kernel: Handshake Established with " + activeZen.productName);
            } catch (err) {
                console.error(err);
                alert("Arcane Fault: Device selection cancelled or blocked.");
            }
        }

        async function flashBinary(id, name) {
            if(!activeZen) return alert("Handshake Required.");
            
            const res = await fetch(`/api/download/${id}`);
            if(!res.ok) {
                if(res.status === 403) alert("Nice try, Make a ticket in the discord to get perms for this file");
                return;
            }

            const rawData = new Uint8Array(await (await res.blob()).arrayBuffer());
            
            try {
                // Break binary into 64-byte packets for the Zen Buffer
                for (let i = 0; i < rawData.length; i += 64) {
                    const chunk = rawData.slice(i, i + 64);
                    await activeZen.transferOut(1, chunk);
                }
                alert("SUCCESS: Sector Synced with " + name);
            } catch (e) {
                alert("HARDWARE_FAULT: Transfer Interrupted.");
            }
        }

        function togglePortal() {
            const p = document.getElementById('portal');
            p.style.display = (p.style.display === 'flex') ? 'none' : 'flex';
        }

        async function loadArchive() {
            const res = await fetch('/api/scripts');
            const data = await res.json();
            const grid = document.getElementById('script-injection');
            
            grid.innerHTML = data.map(s => `
                <div class="card">
                    <div class="card-publisher">DESIGNED BY ${s.publisher}</div>
                    <h3 class="card-name">${s.name}</h3>
                    <button class="btn-load" onclick="flashBinary('${s.id}', '${s.name}')">LOAD TO SECTOR</button>
                </div>
            `).join('');
        }

        loadArchive();
    </script>
</body>
</html>
"""

# --- [ 4. BACKEND ARCHITECTURE ] ---

@app.route('/')
def index():
    return render_template_string(MASTER_HTML)

@app.route('/api/scripts')
def api_list_scripts():
    vault = load_vault()
    return jsonify(vault["scripts"])

@app.route('/api/upload', methods=['POST'])
def api_upload():
    vault = load_vault()
    pub_id = request.form.get('pub_id')
    
    # Permission Gate for Unc, Coco, and Roey
    if pub_id not in vault["authorized_publishers"]:
        logger.warning(f"UNAUTHORIZED ACCESS DETECTED: {pub_id}")
        return "Unauthorized Access Denied", 403
    
    file = request.files['file']
    s_name = request.form.get('s_name')
    
    if file and s_name:
        ts = int(time.time())
        safe_name = secure_filename(f"{s_name}_{ts}.bin")
        file.save(os.path.join(UPLOAD_FOLDER, safe_name))
        
        # Determine Display Name based on ID
        display_name = "Unc" if pub_id == OWNER_ID else "Authorized Architect"
        
        new_script = {
            "id": str(uuid.uuid4())[:8],
            "name": s_name,
            "publisher": display_name,
            "raw_id": pub_id,
            "path": safe_name,
            "date": str(datetime.date.today())
        }
        vault["scripts"].append(new_script)
        save_vault(vault)
        return redirect(url_for('index'))
    
    return "Missing Parameters", 400

@app.route('/api/download/<string:s_id>')
def api_download(s_id):
    vault = load_vault()
    script = next((s for s in vault["scripts"] if s["id"] == s_id), None)
    if not script:
        return "Not Found", 404
    
    # Track metrics
    vault["stats"]["total_flashes"] += 1
    save_vault(vault)
    
    return send_from_directory(UPLOAD_FOLDER, script["path"])

# --- [ 5. DISCORD INTERFACE ENGINE ] ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Arcane Discord Bot Online for Unc: {bot.user}")
    await bot.tree.sync()

@bot.tree.command(name="grant_staff", description="Authorize Coco or Roey to publish.")
async def grant_staff(interaction: discord.Interaction, member: discord.Member):
    if str(interaction.user.id) != OWNER_ID:
        return await interaction.response.send_message("Only the Lead Dev (Unc) can assign staff.", ephemeral=True)
    
    vault = load_vault()
    if str(member.id) not in vault["authorized_publishers"]:
        vault["authorized_publishers"].append(str(member.id))
        save_vault(vault)
        await interaction.response.send_message(f"Staff access granted to {member.mention}.")
    else:
        await interaction.response.send_message("Architect already has access.")

# --- [ 6. MULTI-THREADED KERNEL ] ---
def start_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

if __name__ == "__main__":
    # Launch Web Server in Background
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()
    
    # Launch Discord Bot
    if TOKEN:
        bot.run(TOKEN)
    else:
        logger.critical("NO DISCORD_TOKEN FOUND IN ENVIRONMENT.")
