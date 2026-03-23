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
from flask import Flask, jsonify, request, render_template_string, send_from_directory, redirect, url_for, session, abort
from werkzeug.utils import secure_filename
from discord.ext import commands, tasks
import discord
from dotenv import load_dotenv

# ==============================================================================
# [ 1. KERNEL & IDENTITY CONFIGURATION ]
# ==============================================================================
load_dotenv()
TOKEN = os.environ.get("DISCORD_TOKEN")
LOG_CHANNEL_ID = 1485513827222290572  # UNC's Private Logs
OWNER_ID = 638512345678901234 

# Pathing Logic
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH = os.path.join(BASE_DIR, "temple_vault.json")
BINARY_DIR = os.path.join(BASE_DIR, "vault_binaries")
LOG_DIR = os.path.join(BASE_DIR, "kernel_logs")

for path in [BINARY_DIR, LOG_DIR]:
    if not os.path.exists(path): os.makedirs(path)

# Kernel Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [UNC_KERNEL] %(message)s',
    handlers=[logging.FileHandler(os.path.join(LOG_DIR, "kernel.log")), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ArcaneTemple")

# ==============================================================================
# [ 2. DATABASE ENGINE ]
# ==============================================================================
def initialize_vault():
    if not os.path.exists(VAULT_PATH):
        schema = {
            "publishers": {}, 
            "users": {},      
            "scripts": [],
            "blacklist": [], 
            "system_stats": {"total_flashes": 0, "active_bonds": 0}
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
        /* --- [ THE AZTEC PALETTE ] --- */
        :root {
            --obsidian: #050705;
            --stone: #121612;
            --emerald: #00ff88;
            --mayan-gold: #c5a059;
            --jade-shadow: 0 0 30px rgba(0, 255, 136, 0.2);
            --gold-glow: 0 0 20px rgba(197, 160, 89, 0.2);
            --transition: 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        /* --- [ KINETIC ANIMATIONS ] --- */
        @keyframes pulse_jade {
            0% { filter: drop-shadow(0 0 5px var(--emerald)); opacity: 0.8; }
            50% { filter: drop-shadow(0 0 25px var(--emerald)); opacity: 1; }
            100% { filter: drop-shadow(0 0 5px var(--emerald)); opacity: 0.8; }
        }
        
        @keyframes stone_float {
            0% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0); }
        }

        @keyframes bg_scroll {
            from { background-position: 0 0; }
            to { background-position: 100% 100%; }
        }

        * { box-sizing: border-box; outline: none; transition: var(--transition); }
        
        body {
            background: linear-gradient(rgba(5, 7, 5, 0.98), rgba(0, 0, 0, 0.99)), url('https://www.transparenttextures.com/patterns/dark-matter.png');
            background-color: var(--obsidian);
            color: #f0f0f0; font-family: 'Montserrat', sans-serif;
            margin: 0; height: 100vh; display: flex; overflow: hidden;
            border: 6px solid var(--mayan-gold);
            animation: bg_scroll 120s linear infinite;
        }

        /* --- [ SIDEBAR ARCHITECTURE ] --- */
        .sidebar {
            width: 480px; background: var(--stone);
            border-right: 4px solid var(--mayan-gold);
            display: flex; flex-direction: column; z-index: 100;
            box-shadow: 30px 0 100px rgba(0,0,0,1);
            position: relative;
        }

        .sidebar::before {
            content: ''; position: absolute; right: -10px; top: 0; bottom: 0; width: 4px;
            background: var(--emerald); filter: blur(10px); opacity: 0.3;
        }

        .sidebar-header { padding: 110px 60px; text-align: center; position: relative; }
        .logo { 
            font-family: 'Cinzel Decorative'; font-size: 60px; font-weight: 900;
            letter-spacing: 15px; color: var(--mayan-gold); margin: 0;
            text-shadow: var(--gold-glow);
        }
        .signature { 
            font-size: 11px; color: var(--emerald); letter-spacing: 8px; 
            font-weight: 900; margin-top: 30px; text-transform: uppercase;
        }

        .nav-container { flex: 1; padding: 80px 60px; }
        .nav-label { font-size: 10px; color: #3a4a3a; font-weight: 900; letter-spacing: 6px; margin-bottom: 50px; display: block; }
        
        .nav-button {
            display: block; width: 100%; padding: 28px;
            color: #556655; font-weight: 900; text-decoration: none;
            font-size: 14px; letter-spacing: 4px; text-transform: uppercase;
            border: 1px solid transparent; cursor: pointer; margin-bottom: 25px;
            background: rgba(0,0,0,0.1);
        }
        .nav-button:hover, .nav-button.active {
            color: #fff; background: rgba(0, 255, 136, 0.04);
            border-left: 4px solid var(--emerald);
            padding-left: 40px;
        }

        /* --- [ REGISTRATION PORTAL ] --- */
        .registration {
            padding: 60px; background: rgba(0,0,0,0.6);
            border-top: 3px solid var(--mayan-gold);
        }
        .aztec-input {
            width: 100%; padding: 25px; background: #000; border: 2px solid #1a1a1a;
            color: var(--emerald); font-family: 'Cinzel Decorative';
            margin-bottom: 30px; text-align: center; letter-spacing: 6px; font-size: 18px;
            box-shadow: inset 0 0 20px rgba(0,0,0,1);
        }
        .aztec-input:focus { border-color: var(--emerald); box-shadow: 0 0 30px rgba(0,255,136,0.1); }

        /* --- [ MAIN VIEWPORT ] --- */
        .stage { flex: 1; display: flex; flex-direction: column; position: relative; }
        
        .top-bar {
            height: 140px; padding: 0 100px; display: flex; align-items: center; justify-content: space-between;
            background: rgba(0,0,0,0.8); border-bottom: 2px solid rgba(197, 160, 89, 0.1);
        }
        .status-pill {
            padding: 12px 30px; border: 1px solid var(--mayan-gold);
            font-size: 10px; font-weight: 900; letter-spacing: 4px; color: var(--mayan-gold);
        }

        .relic-vault {
            flex: 1; padding: 120px;
            display: grid; grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 80px; overflow-y: auto;
        }

        /* --- [ RELIC CARDS ] --- */
        .relic {
            background: rgba(10, 16, 10, 0.98); border: 2px solid #1a221a;
            padding: 100px 70px; text-align: center; position: relative;
            clip-path: polygon(15% 0, 85% 0, 100% 15%, 100% 85%, 85% 100%, 15% 100%, 0 85%, 0 15%);
            animation: stone_float 6s ease-in-out infinite;
        }
        .relic:hover { border-color: var(--emerald); animation-play-state: paused; transform: scale(1.02); }
        .relic-title { font-family: 'Cinzel Decorative'; font-size: 42px; color: #fff; margin-bottom: 60px; letter-spacing: 5px; }

        /* --- [ 8-SLOT MEMORY TRAY ] --- */
        .tray-engine {
            height: 420px; background: #000; border-top: 5px solid var(--mayan-gold);
            display: grid; grid-template-columns: repeat(4, 1fr); padding: 35px; gap: 30px;
        }

        .stone-block {
            background: #0a0d0a; border: 2px solid rgba(0, 255, 136, 0.05);
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            position: relative; transition: 0.3s;
        }
        .stone-block:hover { background: #111; border-color: var(--emerald); }

        .glyph-id { font-family: 'Cinzel Decorative'; font-size: 130px; color: var(--mayan-gold); opacity: 0.03; position: absolute; z-index: 1; }
        .block-info { z-index: 10; text-align: center; }
        .block-label { font-size: 10px; color: var(--emerald); font-weight: 900; letter-spacing: 5px; opacity: 0.6; }
        .block-data { font-size: 16px; color: #fff; font-weight: 700; margin-top: 20px; text-transform: uppercase; letter-spacing: 3px; }

        .jade-status {
            width: 14px; height: 14px; border-radius: 50%; background: #1a1a1a;
            position: absolute; top: 30px; right: 30px; border: 2px solid #000;
        }
        .jade-status.active { background: var(--emerald); box-shadow: 0 0 20px var(--emerald); animation: pulse_jade 2s infinite; }

        .btn-temple {
            width: 100%; padding: 28px; background: none; border: 2px solid var(--mayan-gold);
            color: var(--mayan-gold); font-family: 'Cinzel Decorative'; font-weight: 900;
            cursor: pointer; letter-spacing: 8px; font-size: 16px;
        }
        .btn-temple:hover { background: var(--mayan-gold); color: #000; box-shadow: 0 0 60px rgba(197, 160, 89, 0.4); }

        .credit-footer { position: absolute; bottom: 40px; right: 60px; font-size: 11px; color: #2a352a; letter-spacing: 5px; font-weight: 900; }

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

        <div class="nav-container">
            <span class="nav-label">HIDDEN_ARCHIVES</span>
            <div class="nav-button active">Relic Repository</div>
            <div class="nav-button">Bonded Totems</div>
            <div class="nav-button">System Pulse</div>
            
            <span class="nav-label" style="margin-top:80px;">ARCHITECT_ACCESS</span>
            <div class="nav-button" onclick="toggleCommit()">Commit New Binary</div>
        </div>

        <div class="registration">
            <div style="font-size:11px; color:var(--mayan-gold); margin-bottom:25px; letter-spacing:5px; text-align:center;">BOND_SERIAL_NUMBER</div>
            <input type="text" id="serial_num" class="aztec-input" placeholder="XXXX-XXXX-XXXX">
            <button class="btn-temple" onclick="bondHardware()">BOND DEVICE</button>
            <div id="bond-msg" style="text-align:center; font-size:10px; color:#222; margin-top:30px; font-weight:900; letter-spacing:4px;">STATUS: OFFLINE</div>
        </div>
    </div>

    <div class="stage">
        <div class="top-bar">
            <div class="status-pill">UNC_KERNEL_LINK: READY</div>
            <div style="display:flex; gap:60px;">
                <div style="font-size:12px; color:var(--emerald); font-weight:900; letter-spacing:5px;">USER: <span id="u-name" style="color:#fff">AUTHORIZED</span></div>
                <div style="font-size:12px; color:var(--mayan-gold); font-weight:900; letter-spacing:5px;">RELICS: <span id="r-count" style="color:#fff">0</span></div>
            </div>
        </div>

        <div class="relic-vault" id="relic-mount"></div>

        <div class="tray-engine">
            <script>
                for(let i=1; i<=8; i++) {
                    document.write(`
                        <div class="stone-block">
                            <div class="glyph-id">${i}</div>
                            <div class="block-info">
                                <div class="block-label">MEMORY_BLOCK_0${i}</div>
                                <div class="block-data" id="slot-n${i}">EMPTY</div>
                            </div>
                            <div class="jade-status" id="led-n${i}"></div>
                        </div>
                    `);
                }
            </script>
        </div>
        <div class="credit-footer">CREDITS: COCO & ROEY</div>
    </div>

    <div id="commit-portal" style="position:fixed; inset:0; background:rgba(0,0,0,0.99); z-index:1000; display:none; align-items:center; justify-content:center; backdrop-filter:blur(60px);">
        <div style="border:4px solid var(--mayan-gold); padding:120px; width:850px; background:#050705; text-align:center; box-shadow: 0 0 200px rgba(0, 255, 136, 0.1);">
            <h2 style="font-family:'Cinzel Decorative'; color:var(--mayan-gold); font-size:55px; margin-bottom:80px; letter-spacing:12px;">SACRIFICE BINARY</h2>
            <form action="/api/upload" method="post" enctype="multipart/form-data">
                <input type="password" name="key" class="aztec-input" placeholder="MASTER_KEY" required>
                <input type="text" name="name" class="aztec-input" placeholder="RELIC_NAME" required>
                <input type="file" name="file" style="margin-bottom:80px; color:#333;" required>
                <button type="submit" class="btn-temple">EXECUTE SACRIFICE</button>
            </form>
            <button onclick="toggleCommit()" style="background:none; border:none; color:#1a1a1a; margin-top:50px; cursor:pointer; font-weight:900; letter-spacing:6px;">ABORT_PROCEDURE</button>
        </div>
    </div>

    <script>
        let bridge = null;

        async function bondHardware() {
            try {
                bridge = await navigator.usb.requestDevice({ 
                    filters: [{ vendorId: 0x2508 }] 
                });
                await bridge.open();
                if (bridge.configuration === null) await bridge.selectConfiguration(1);
                await bridge.claimInterface(0);
                
                document.getElementById('bond-msg').innerText = "LINKED: " + (bridge.productName || "ZEN_HW");
                document.getElementById('bond-msg').style.color = "var(--emerald)";
                for(let i=1; i<=8; i++) document.getElementById('led-n'+i).classList.add('active');
                
                alert("Hardware Bond established through Unc Kernel.");
            } catch (err) { alert("Temple Error: No Zen detected on PROG port."); }
        }

        async function syncRelic(id, name) {
            if(!bridge) return alert("Bonding required to flash.");
            const btn = event.target;
            btn.innerText = "SACRIFICING...";
            
            try {
                const res = await fetch(`/api/download/${id}`);
                if (!res.ok) throw new Error();
                
                const blob = await res.blob();
                const buffer = await blob.arrayBuffer();
                const bytes = new Uint8Array(buffer);

                // Transfer packetization
                for (let i = 0; i < bytes.length; i += 64) {
                    await bridge.transferOut(1, bytes.slice(i, i + 64));
                }

                document.getElementById('slot-n1').innerText = name.toUpperCase();
                document.getElementById('slot-n1').style.color = "var(--emerald)";
                btn.innerText = "SYNC_COMPLETE";
                setTimeout(() => btn.innerText = "SYNC TO ZEN", 3000);
            } catch (err) { alert("Access Denied: Relic locked."); btn.innerText = "SYNC_FAILED"; }
        }

        async function refreshArchives() {
            const res = await fetch('/api/scripts');
            const data = await res.json();
            document.getElementById('r-count').innerText = data.length;
            const vault = document.getElementById('relic-mount');
            vault.innerHTML = data.map(s => `
                <div class="relic">
                    <span style="font-size:10px; color:var(--emerald); letter-spacing:5px;">ARCHIVE_RELIC_${s.id}</span>
                    <h2 class="relic-title">${s.name}</h2>
                    <button class="btn-temple" onclick="syncRelic('${s.id}', '${s.name}')">SYNC TO ZEN</button>
                </div>
            `).join('');
        }

        function toggleCommit() {
            const p = document.getElementById('commit-portal');
            p.style.display = (p.style.display === 'flex') ? 'none' : 'flex';
        }

        refreshArchives();
    </script>
</body>
</html>
"""

# ==============================================================================
# [ 4. FLASK BACKEND KERNEL ]
# ==============================================================================

@app.route('/')
def home():
    return render_template_string(MASTER_UI)

@app.route('/api/scripts')
def api_scripts():
    v = initialize_vault()
    return jsonify(v["scripts"])

@app.route('/api/upload', methods=['POST'])
def api_upload():
    v = initialize_vault()
    # Replace with a secure key
    if request.form.get('key') != "UNC_MASTER_ADMIN": return abort(403)
    
    f = request.files['file']
    name = request.form.get('name')
    if f and name:
        filename = secure_filename(f"{name}_{int(time.time())}.bin")
        f.save(os.path.join(BINARY_DIR, filename))
        
        entry = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "file": filename,
            "timestamp": str(datetime.datetime.now())
        }
        v["scripts"].append(entry)
        sync_vault(v)
    return redirect(url_for('home'))

@app.route('/api/download/<sid>')
def api_download(sid):
    v = initialize_vault()
    script = next((s for s in v["scripts"] if s["id"] == sid), None)
    if not script: return abort(404)
    
    # Optional: Logic to check user's Discord role before allowing download
    v["system_stats"]["total_flashes"] += 1
    sync_vault(v)
    return send_from_directory(BINARY_DIR, script['file'])

# ==============================================================================
# [ 5. DISCORD BOT ENGINE ]
# ==============================================================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

async def dispatch_log(msg):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="ARCANE_KERNEL_UPDATE", description=f"```fix\n{msg}```", color=0x00ff88)
        embed.timestamp = datetime.datetime.now()
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    await dispatch_log("Great Temple Online. All scripts synced to Unc Kernel.")
    await bot.tree.sync()

@bot.tree.command(name="register_zen", description="Bonds your Zen Serial to the Temple.")
async def register_zen(interaction: discord.Interaction, serial_number: str):
    v = initialize_vault()
    uid = str(interaction.user.id)
    
    v["users"][uid] = {
        "serial": serial_number,
        "authorized": True,
        "date": str(datetime.datetime.now())
    }
    v["system_stats"]["active_bonds"] += 1
    sync_vault(v)
    
    await dispatch_log(f"NEW_BOND: User {interaction.user.name} linked Serial {serial_number}")
    await interaction.response.send_message(f"✅ **Serial Bonded.** {serial_number} is now linked to your spirit.", ephemeral=True)

# ==============================================================================
# [ 6. EXECUTION ]
# ==============================================================================
def run_web():
    app.run(host='0.0.0.0', port=10000, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    if TOKEN:
        bot.run(TOKEN)
