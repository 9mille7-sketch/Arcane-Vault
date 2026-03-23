import os
import json
import threading
import discord
from discord.ext import commands
from flask import Flask, jsonify, request, render_template_string, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# --- 1. ENVIRONMENT & SECURITY ---
load_dotenv()
# Pulled from Render Environment Variables for security
TOKEN = os.environ.get("DISCORD_TOKEN")
OWNER_ID = os.environ.get("OWNER_ID") 

DB_FILE = "arcane_vault.json"
# Matches the 'mountPath' in your render.yaml disk settings
UPLOAD_FOLDER = "scripts_vault"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def load_db():
    if not os.path.exists(DB_FILE):
        return {"scripts": [], "auth_publishers": [OWNER_ID], "settings": {"theme": "dark"}}
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

app = Flask(__name__)

# --- 2. THE C-MIND MIRROR UI (CSS & HTML) ---
# This section is expanded to replicate the exact layout and high-def visuals
MIRROR_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE | Marketplace</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');

        :root {
            --neon-orange: #ff5e00;
            --arcane-red: #da0a0a;
            --bg-black: #000000;
            --sidebar-width: 320px;
            --glass: rgba(12, 12, 12, 0.95);
            --border: rgba(255, 94, 0, 0.15);
            --text-main: #e0e0e0;
            --text-dim: #444;
        }

        * { box-sizing: border-box; transition: all 0.2s ease-in-out; }

        body {
            background-color: var(--bg-black);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            margin: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* --- SIDEBAR LEDGER --- */
        .sidebar {
            width: var(--sidebar-width);
            background: #050505;
            border-right: 1px solid #111;
            display: flex;
            flex-direction: column;
            padding: 0;
            z-index: 100;
        }

        .sidebar-brand {
            padding: 50px 40px;
            background: linear-gradient(180deg, #0a0a0a 0%, #050505 100%);
        }

        .logo {
            color: var(--neon-orange);
            font-size: 42px;
            font-weight: 900;
            letter-spacing: 6px;
            text-shadow: 0 0 20px rgba(255, 94, 0, 0.4);
            margin: 0;
        }

        .version-label {
            font-size: 10px;
            color: var(--text-dim);
            letter-spacing: 3px;
            font-weight: 800;
            margin-top: 5px;
        }

        .nav-section {
            flex: 1;
            padding: 20px 0;
            overflow-y: auto;
        }

        .nav-group-label {
            padding: 20px 40px 10px;
            font-size: 10px;
            color: #222;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .nav-item {
            padding: 16px 40px;
            display: flex;
            align-items: center;
            cursor: pointer;
            color: #555;
            font-size: 13px;
            font-weight: 700;
            border-left: 3px solid transparent;
        }

        .nav-item:hover {
            color: #fff;
            background: rgba(255,255,255,0.02);
        }

        .nav-item.active {
            color: var(--neon-orange);
            background: rgba(255, 94, 0, 0.03);
            border-left: 3px solid var(--neon-orange);
        }

        /* --- HARDWARE LIVE MONITOR --- */
        .hw-panel {
            margin: 20px 30px;
            background: #080808;
            border: 1px solid #111;
            padding: 25px;
            border-radius: 4px;
        }

        .led-indicator {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .led-bulb {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #1a1a1a;
        }

        .led-bulb.online {
            background: #00d2ff;
            box-shadow: 0 0 15px #00d2ff;
        }

        /* --- MAIN DASHBOARD CANVAS --- */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: radial-gradient(circle at top right, #100804 0%, #000 100%);
        }

        .top-nav {
            height: 90px;
            border-bottom: 1px solid #111;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 60px;
            background: rgba(0,0,0,0.5);
            backdrop-filter: blur(10px);
        }

        .search-container {
            width: 450px;
            position: relative;
        }

        .search-bar {
            width: 100%;
            background: #0a0a0a;
            border: 1px solid #1a1a1a;
            padding: 14px 25px;
            border-radius: 4px;
            color: #fff;
            outline: none;
            font-size: 13px;
        }

        .search-bar:focus { border-color: var(--neon-orange); }

        .slot-config {
            display: flex;
            align-items: center;
            gap: 20px;
            background: #000;
            padding: 10px 25px;
            border-radius: 50px;
            border: 1px solid #222;
        }

        /* --- SCRIPT GRID ARCHITECTURE --- */
        .grid-container {
            flex: 1;
            padding: 60px;
            overflow-y: auto;
        }

        .script-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 30px;
        }

        .script-card {
            background: var(--glass);
            border: 1px solid var(--border);
            border-radius: 4px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        .script-card:hover {
            border-color: var(--neon-orange);
            transform: translateY(-10px);
            box-shadow: 0 25px 50px rgba(0,0,0,0.9);
        }

        .card-preview {
            height: 200px;
            background: #050505;
            display: flex;
            align-items: center;
            justify-content: center;
            border-bottom: 1px solid #111;
        }

        .card-details { padding: 35px; }

        .author-tag {
            font-size: 11px;
            font-weight: 900;
            color: var(--neon-orange);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .script-name {
            font-size: 28px;
            font-weight: 300;
            margin: 15px 0 30px;
            letter-spacing: -1px;
        }

        .btn-action {
            width: 100%;
            padding: 18px;
            background: var(--neon-orange);
            color: #000;
            border: none;
            font-weight: 900;
            text-transform: uppercase;
            cursor: pointer;
            border-radius: 4px;
            letter-spacing: 1px;
        }

        .btn-action:hover { background: #fff; }

        /* --- MODAL SYSTEM --- */
        .overlay {
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.95);
            z-index: 1000;
            display: none;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(10px);
        }

        .modal-content {
            width: 500px;
            background: #0a0a0a;
            border: 1px solid var(--neon-orange);
            padding: 60px;
            border-radius: 4px;
        }

        input, select {
            width: 100%;
            background: #000;
            border: 1px solid #222;
            padding: 15px;
            color: #fff;
            margin-bottom: 20px;
            outline: none;
        }

        input:focus { border-color: var(--neon-orange); }

    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-brand">
            <h1 class="logo">ARCANE</h1>
            <div class="version-label">CORE_MARKETPLACE_SYSTEM</div>
        </div>

        <div class="hw-panel">
            <div class="led-indicator">
                <div id="status-led" class="led-bulb"></div>
                <span id="status-text" style="font-size:11px; font-weight:800; color:#333;">HARDWARE_IDLE</span>
            </div>
        </div>

        <div class="nav-section">
            <div class="nav-group-label">Navigation</div>
            <div class="nav-item active">Repository Marketplace</div>
            <div class="nav-item">Device Input Monitor</div>
            <div class="nav-item">GPC Compiler Console</div>

            <div class="nav-group-label">Developer Access</div>
            <div class="nav-item" onclick="openPortal()">Push Binary to Vault</div>
        </div>

        <div style="padding:40px;">
            <button class="btn-action" onclick="handshake()">Initialize Zen</button>
        </div>
    </div>

    <div class="main-content">
        <div class="top-nav">
            <div class="search-container">
                <input type="text" class="search-bar" placeholder="Filter through optimized binaries...">
            </div>
            <div class="slot-config">
                <span style="font-size:10px; font-weight:900; color:#444;">DESTINATION:</span>
                <select id="active-slot" style="background:none; border:none; margin:0; padding:0; width:auto; font-weight:900; color:#fff;">
                    <option value="1">SLOT 01</option><option value="2">SLOT 02</option>
                    <option value="3">SLOT 03</option><option value="4">SLOT 04</option>
                </select>
            </div>
        </div>

        <div class="grid-container">
            <div class="script-grid" id="main-grid">
                </div>
        </div>
    </div>

    <div class="overlay" id="dev-modal">
        <div class="modal-content">
            <h2 style="font-weight:200; color:var(--neon-orange); margin-top:0;">Vault Synchronization</h2>
            <form action="/api/upload" method="post" enctype="multipart/form-data">
                <input type="text" name="pub_id" placeholder="Access Identifier (Discord ID)" required>
                <input type="text" name="s_name" placeholder="Binary Name" required>
                <input type="file" name="file" required>
                <button type="submit" class="btn-action">Upload to Cloud</button>
            </form>
            <button onclick="openPortal()" style="background:none; border:none; color:#222; width:100%; margin-top:20px; cursor:pointer; font-weight:900;">CLOSE_SESSION</button>
        </div>
    </div>

    <script>
        let device = null;

        function openPortal() {
            const m = document.getElementById('dev-modal');
            m.style.display = (m.style.display === 'flex') ? 'none' : 'flex';
        }

        async function handshake() {
            try {
                device = await navigator.usb.requestDevice({ filters: [{ vendorId: 0x1209, productId: 0x2188 }] });
                await device.open();
                await device.claimInterface(0);
                document.getElementById('status-led').classList.add('online');
                document.getElementById('status-text').innerText = "ZEN_LINK_ACTIVE";
                document.getElementById('status-text').style.color = "#fff";
            } catch (e) { alert("Handshake Failed. Verify PROG mode."); }
        }

        async function triggerFlash(id, name) {
            if(!device) return alert("Initialize hardware link first.");
            const slot = document.getElementById('active-slot').value;
            const res = await fetch(`/api/download/${id}`);
            if(!res.ok) return alert("Authorization Fault.");

            const data = new Uint8Array(await (await res.blob()).arrayBuffer());
            await device.transferOut(1, data);
            alert(`SUCCESS: ${name} deployed to Slot ${slot}`);
        }

        async function refreshGrid() {
            const r = await fetch('/api/scripts');
            const d = await r.json();
            document.getElementById('main-grid').innerHTML = d.map(s => `
                <div class="script-card">
                    <div class="card-preview"><span style="font-size:80px; color:#080808; font-weight:900;">GPC</span></div>
                    <div class="card-details">
                        <div class="author-tag">AUTHOR: ${s.publisher}</div>
                        <h3 class="script-name">${s.name}</h3>
                        <button class="btn-action" onclick="triggerFlash('${s.id}', '${s.name}')">Deploy to Zen</button>
                    </div>
                </div>
            `).join('');
        }
        refreshGrid();
    </script>
</body>
</html>
"""

# --- 3. CORE API & DISCORD ---
@app.route('/')
def home(): return render_template_string(MIRROR_UI)

@app.route('/api/scripts')
def get_scripts(): return jsonify(load_db()["scripts"])

@app.route('/api/upload', methods=['POST'])
def upload():
    db = load_db()
    pub_id = request.form.get('pub_id')
    if pub_id not in db["auth_publishers"]: return "Unauthorized", 403
    
    file = request.files['file']
    s_name = request.form.get('s_name')
    filename = secure_filename(f"{s_name}.bin")
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    db["scripts"].append({
        "id": len(db["scripts"]) + 1,
        "name": s_name,
        "publisher": pub_id,
        "file": filename
    })
    save_db(db)
    return redirect(url_for('home'))

@app.route('/api/download/<int:s_id>')
def download(s_id):
    db = load_db()
    script = next((s for s in db["scripts"] if s["id"] == s_id), None)
    if not script: return "404", 404
    return send_from_directory(UPLOAD_FOLDER, script["file"])

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.tree.command(name="authorize")
async def authorize(interaction: discord.Interaction, member: discord.Member):
    if str(interaction.user.id) != OWNER_ID: return
    db = load_db()
    if str(member.id) not in db["auth_publishers"]:
        db["auth_publishers"].append(str(member.id))
        save_db(db)
        await interaction.response.send_message(f"Vault access granted to {member.mention}")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    if TOKEN:
        bot.run(TOKEN)
