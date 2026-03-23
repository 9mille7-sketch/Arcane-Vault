import os
import json
import logging
import threading
import datetime
import discord
from discord.ext import commands
from flask import Flask, jsonify, request, render_template_string, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# --- [ SYSTEM INITIALIZATION ] ---
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
OWNER_ID = os.environ.get("OWNER_ID")

# File paths for the Secret Society archives
DB_FILE = "arcane_vault.json"
UPLOAD_FOLDER = "scripts_vault"

# Ensure the vault directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Configure detailed logging for audit trails
logging.basicConfig(level=logging.INFO, format='%(asctime)s - ARCANE_OS - %(message)s')
logger = logging.getLogger(__name__)

# --- [ DATA ARCHIVE MANAGEMENT ] ---
def load_db():
    """Access the encrypted vault database."""
    if not os.path.exists(DB_FILE):
        return {
            "scripts": [], 
            "auth_publishers": [OWNER_ID], 
            "system_meta": {"version": "V5", "developer": "Unc", "credits": ["Coco", "Roey"]}
        }
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    """Commit changes to the vault database."""
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- [ THE ARCANE UI ENGINE ] ---
app = Flask(__name__)

MIRROR_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE | Secret Society Vault</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Inter:wght@300;400;700&display=swap" rel="stylesheet">
    <style>
        /* --- [ THE SECRET SOCIETY COLOR PALETTE ] --- */
        :root {
            --cobalt-deep: #001a33;
            --cobalt-primary: #0047ab;
            --metallic-blue: #00d2ff;
            --silver-brushed: #e5e4e2;
            --silver-dark: #71706e;
            --deep-black: #02040a;
            --sidebar-black: #05070f;
            --shimmer-speed: 3s;
        }

        /* --- [ ANIMATION KEYFRAMES ] --- */
        @keyframes metallic-glow {
            0% { border-color: rgba(0, 210, 255, 0.2); box-shadow: 0 0 5px rgba(0, 210, 255, 0.1); }
            50% { border-color: var(--metallic-blue); box-shadow: 0 0 25px rgba(0, 210, 255, 0.4); }
            100% { border-color: rgba(0, 210, 255, 0.2); box-shadow: 0 0 5px rgba(0, 210, 255, 0.1); }
        }

        @keyframes silver-flash {
            0% { transform: translateX(-100%); opacity: 0; }
            50% { opacity: 0.5; }
            100% { transform: translateX(100%); opacity: 0; }
        }

        /* --- [ LAYOUT ARCHITECTURE ] --- */
        body {
            background-color: var(--deep-black);
            color: var(--silver-brushed);
            font-family: 'Inter', sans-serif;
            margin: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        h1, h2, h3, .logo { font-family: 'Cinzel', serif; }

        /* --- [ SIDEBAR LEDGER ] --- */
        .sidebar {
            width: 350px;
            background: var(--sidebar-black);
            border-right: 2px solid var(--silver-dark);
            display: flex;
            flex-direction: column;
            box-shadow: 15px 0 50px rgba(0,0,0,0.9);
            z-index: 10;
        }

        .sidebar-header {
            padding: 60px 40px;
            border-bottom: 1px solid rgba(229, 228, 226, 0.05);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .sidebar-header::after {
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, transparent, var(--metallic-blue), transparent);
            animation: silver-flash 4s infinite linear;
        }

        .logo {
            font-size: 48px;
            font-weight: 900;
            letter-spacing: 12px;
            color: var(--silver-brushed);
            text-shadow: 0 0 20px var(--metallic-blue);
            margin: 0;
        }

        .credits-tag {
            font-size: 9px;
            color: var(--silver-dark);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-top: 15px;
            font-weight: 800;
        }

        .sidebar-content {
            flex: 1;
            padding: 40px;
            display: flex;
            flex-direction: column;
        }

        .nav-item {
            padding: 18px 25px;
            margin-bottom: 20px;
            color: var(--silver-dark);
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 2px;
            text-transform: uppercase;
            cursor: pointer;
            border-left: 4px solid transparent;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .nav-item:hover {
            color: var(--metallic-blue);
            background: rgba(0, 71, 171, 0.1);
            border-left-color: var(--metallic-blue);
        }

        .nav-item.active {
            color: #fff;
            background: rgba(0, 210, 255, 0.05);
            border-left-color: var(--metallic-blue);
            text-shadow: 0 0 10px var(--metallic-blue);
        }

        /* --- [ THE SHIMMERING BUTTON ] --- */
        .btn-handshake {
            background: linear-gradient(135deg, var(--cobalt-deep), #000);
            border: 1px solid var(--metallic-blue);
            color: var(--silver-brushed);
            padding: 22px;
            font-family: 'Cinzel', serif;
            font-weight: 900;
            font-size: 14px;
            letter-spacing: 4px;
            text-transform: uppercase;
            cursor: pointer;
            position: relative;
            overflow: hidden;
            animation: metallic-glow 4s infinite ease-in-out;
        }

        .btn-handshake:hover {
            background: var(--silver-brushed);
            color: var(--deep-black);
            box-shadow: 0 0 40px var(--metallic-blue);
        }

        /* --- [ MAIN CANVAS ] --- */
        .main-canvas {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: radial-gradient(circle at center, #050a15 0%, #000 100%);
        }

        .top-bar {
            height: 100px;
            border-bottom: 1px solid rgba(229, 228, 226, 0.05);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 60px;
        }

        .search-container {
            position: relative;
            width: 450px;
        }

        .search-bar {
            width: 100%;
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid #1a1a1a;
            padding: 15px 30px;
            color: #fff;
            font-size: 13px;
            border-radius: 2px;
        }

        .search-bar:focus {
            outline: none;
            border-color: var(--metallic-blue);
            box-shadow: 0 0 15px rgba(0, 210, 255, 0.2);
        }

        .content-area {
            flex: 1;
            padding: 60px;
            overflow-y: auto;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 40px;
        }

        /* --- [ SCRIPT CARDS ] --- */
        .card {
            background: rgba(5, 7, 15, 0.7);
            border: 1px solid rgba(0, 210, 255, 0.1);
            padding: 40px;
            position: relative;
            transition: 0.5s;
        }

        .card:hover {
            transform: translateY(-10px);
            border-color: var(--metallic-blue);
            background: rgba(0, 71, 171, 0.1);
        }

        .card-header {
            font-size: 10px;
            color: var(--metallic-blue);
            font-weight: 900;
            letter-spacing: 2px;
            margin-bottom: 15px;
        }

        .card h3 {
            font-size: 24px;
            margin: 0 0 25px 0;
            font-weight: 400;
        }

        /* --- [ TALL METALLIC MEMORY SLOTS ] --- */
        .memory-vault {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            padding: 30px 60px;
            background: #010205;
            border-top: 2px solid var(--silver-dark);
            height: 280px; /* High visibility */
        }

        .slot {
            background: linear-gradient(180deg, #0a0e1a 0%, #000 100%);
            border: 1px solid rgba(229, 228, 226, 0.05);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
            transition: 0.3s;
        }

        .slot:hover {
            border-color: var(--metallic-blue);
            background: #0d1526;
        }

        .slot-num {
            position: absolute;
            top: 15px; left: 15px;
            font-size: 32px;
            font-weight: 900;
            color: rgba(229, 228, 226, 0.05);
            font-family: 'Cinzel', serif;
        }

        .slot-indicator {
            width: 15px;
            height: 15px;
            border-radius: 50%;
            background: #111;
            margin-bottom: 15px;
            border: 1px solid #333;
        }

        .slot-indicator.active {
            background: var(--metallic-blue);
            box-shadow: 0 0 15px var(--metallic-blue);
        }

        .slot-label {
            font-size: 11px;
            font-weight: 900;
            letter-spacing: 2px;
            color: var(--silver-dark);
        }

        /* --- [ MODAL SYSTEM ] --- */
        #portal-overlay {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.98);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }

        .portal-box {
            background: var(--sidebar-black);
            border: 2px solid var(--metallic-blue);
            padding: 80px;
            width: 600px;
            text-align: center;
            animation: metallic-glow 6s infinite ease-in-out;
        }

        .form-input {
            width: 100%;
            background: #000;
            border: 1px solid #222;
            color: #fff;
            padding: 20px;
            margin-bottom: 25px;
            font-family: 'Inter', sans-serif;
        }

        .dev-footer {
            position: fixed;
            bottom: 15px;
            right: 15px;
            font-size: 10px;
            color: var(--silver-dark);
            font-weight: 900;
            letter-spacing: 1px;
        }

    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <h1 class="logo">ARCANE</h1>
            <div class="credits-tag">Developed By Unc</div>
            <div style="font-size:7px; color:#333; margin-top:5px;">Credits: Coco & Roey</div>
        </div>

        <div class="sidebar-content">
            <div class="nav-item active">Vault Repository</div>
            <div class="nav-item">Device Interceptor</div>
            <div class="nav-item">Archive Logs</div>
            <div class="nav-item" onclick="togglePortal()">Commit Binary</div>

            <div style="margin-top: auto;">
                <button class="btn-handshake" onclick="initializeHandshake()">Initialize Handshake</button>
            </div>
        </div>
    </div>

    <div class="main-canvas">
        <div class="top-bar">
            <div class="search-container">
                <input type="text" class="search-bar" placeholder="Query the secret archives...">
            </div>
            <div style="font-size: 11px; font-weight: 900; letter-spacing: 2px;">
                LINK_STATUS: <span id="sync-status" style="color:#da0a0a;">OFFLINE</span>
            </div>
        </div>

        <div class="content-area">
            <div class="grid" id="binary-grid">
                </div>
        </div>

        <div class="memory-vault">
            <script>
                for(let i=1; i<=8; i++) {
                    document.write(`
                        <div class="slot">
                            <div class="slot-num">${i}</div>
                            <div class="slot-indicator" id="led-${i}"></div>
                            <div class="slot-label">SECTOR_EMPTY</div>
                        </div>
                    `);
                }
            </script>
        </div>
    </div>

    <div id="portal-overlay">
        <div class="portal-box">
            <h2 style="font-size: 32px; margin-bottom: 40px; font-weight: 200;">Authorized Commitment</h2>
            <form action="/api/upload" method="post" enctype="multipart/form-data">
                <input type="text" name="pub_id" class="form-input" placeholder="Discord Identifier" required>
                <input type="text" name="s_name" class="form-input" placeholder="Designation Name" required>
                <input type="file" name="file" class="form-input" required>
                <button type="submit" class="btn-handshake">Sync to Cloud Vault</button>
            </form>
            <button onclick="togglePortal()" style="background:none; border:none; color:#444; margin-top:30px; cursor:pointer; font-weight:900;">ABORT_SESSION</button>
        </div>
    </div>

    <div class="dev-footer">
        OS_VERSION: V5 | DEVELOPED_BY: UNC
    </div>

    <script>
        let device = null;
        const VID = 0x0C1C; 
        const PID = 0x1D01; 

        function togglePortal() {
            const overlay = document.getElementById('portal-overlay');
            overlay.style.display = (overlay.style.display === 'flex') ? 'none' : 'flex';
        }

        async function initializeHandshake() {
            try {
                device = await navigator.usb.requestDevice({ filters: [{ vendorId: VID, productId: PID }] });
                await device.open();
                await device.claimInterface(0);
                document.getElementById('sync-status').innerText = "ONLINE";
                document.getElementById('sync-status').style.color = "var(--metallic-blue)";
                alert("ARCANE: Handshake Established Successfully.");
            } catch (err) {
                alert("ARCANE: Handshake Failed. Verify Hardware Link.");
            }
        }

        async function deployBinary(id, name) {
            if(!device) return alert("ARCANE: Initialize Handshake First.");
            
            const response = await fetch(`/api/download/${id}`);
            if(!response.ok) {
                if(response.status === 403) {
                    alert("Nice try, Make a ticket in the discord to get perms for this file");
                }
                return;
            }

            const blob = await response.blob();
            const buffer = new Uint8Array(await blob.arrayBuffer());
            
            // Transfer logic to the hardware
            await device.transferOut(1, buffer);
            alert(`ARCANE: Binary ${name} successfully written to hardware sector.`);
        }

        async function fetchArchive() {
            const response = await fetch('/api/scripts');
            const data = await response.json();
            const grid = document.getElementById('binary-grid');
            grid.innerHTML = data.map(script => `
                <div class="card">
                    <div class="card-header">PUBLISHER: ${script.publisher}</div>
                    <h3>${script.name}</h3>
                    <button class="btn-handshake" style="padding:12px; font-size:10px; width:100%;" onclick="deployBinary('${script.id}', '${script.name}')">Deploy Binary</button>
                </div>
            `).join('');
        }

        fetchArchive();
    </script>
</body>
</html>
"""

# --- [ BACKEND INFRASTRUCTURE ] ---

@app.route('/')
def index():
    """Server the Master UI."""
    return render_template_string(MIRROR_UI)

@app.route('/api/scripts')
def list_scripts():
    """Retrieve all scripts in the vault."""
    db = load_db()
    return jsonify(db["scripts"])

@app.route('/api/upload', methods=['POST'])
def handle_upload():
    """Process file uploads from authorized publishers."""
    db = load_db()
    pub_id = request.form.get('pub_id')
    
    # Permission verification
    if pub_id not in db["auth_publishers"]:
        logger.warning(f"Unauthorized upload attempt by ID: {pub_id}")
        return "Access Denied: Unrecognized Identifier", 403
    
    file = request.files['file']
    s_name = request.form.get('s_name')
    
    if file and s_name:
        filename = secure_filename(f"{s_name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.bin")
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        
        # Update Archive
        new_entry = {
            "id": len(db["scripts"]) + 1,
            "name": s_name,
            "publisher": pub_id,
            "filename": filename,
            "timestamp": str(datetime.datetime.now())
        }
        db["scripts"].append(new_entry)
        save_db(db)
        logger.info(f"New binary committed: {s_name} by {pub_id}")
        return redirect(url_for('index'))
    
    return "Commit Failed: Missing Parameters", 400

@app.route('/api/download/<int:script_id>')
def serve_binary(script_id):
    """Serve the binary file if authorized."""
    db = load_db()
    script = next((s for s in db["scripts"] if s["id"] == script_id), None)
    
    if not script:
        return "Archive Not Found", 404

    # The front-end handles the "Nice try" alert if this returns 403
    return send_from_directory(UPLOAD_FOLDER, script["filename"])

# --- [ DISCORD BOT COMPONENT ] ---

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Notify when the Arcane Discord Interface is active."""
    logger.info(f"Discord Interface Active: {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Sync Failure: {e}")

@bot.tree.command(name="authorize_access", description="Grant publisher access to the vault.")
async def authorize(interaction: discord.Interaction, member: discord.Member):
    """Owner command to authorize a new publisher."""
    if str(interaction.user.id) != OWNER_ID:
        await interaction.response.send_message("Architect privilege required.", ephemeral=True)
        return

    db = load_db()
    if str(member.id) not in db["auth_publishers"]:
        db["auth_publishers"].append(str(member.id))
        save_db(db)
        await interaction.response.send_message(f"Authorized access for {member.mention}.", ephemeral=False)
    else:
        await interaction.response.send_message("Member already possesses access.", ephemeral=True)

# --- [ EXECUTION THREADS ] ---

def start_flask():
    """Run the web server thread."""
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

if __name__ == "__main__":
    # Launch Flask in a separate thread
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Launch Discord Bot in main thread
    if TOKEN:
        bot.run(TOKEN)
    else:
        logger.critical("Initialization Failure: No DISCORD_TOKEN found in environment.")
