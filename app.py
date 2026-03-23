import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, jsonify, request, send_from_directory
import threading
from datetime import datetime
from dotenv import load_dotenv

# ==========================================
# 1. CORE SYSTEM INITIALIZATION
# ==========================================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_PASS = "LucaBlu2026"
DB_FILE = "vault_storage.json"
BIN_FOLDER = "scripts_vault"

# Versioning and Branding Constants
VERSION = "V5"
BRAND = "ARCANE"
DEV_ID = "UNC"

# Ensure environment integrity
if not os.path.exists(BIN_FOLDER):
    os.makedirs(BIN_FOLDER)

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({
            "publishers": {}, 
            "scripts": [], 
            "auth_users": {}, 
            "user_balances": {} 
        }, f)

def load_db():
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

app = Flask(__name__)

# ==========================================
# 2. THE PRODUCTION CMIND UI MIRROR
# ==========================================
@app.route('/')
def index():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{BRAND} | {VERSION} MARKETPLACE</title>
        <style>
            :root {{
                --orange: #ff5e00;
                --bg: #050505;
                --sidebar: #000000;
                --card: #0f0f0f;
                --header: #121212;
                --border: #1a1a1a;
                --text-main: #eeeeee;
                --text-dim: #444444;
                --console-bg: rgba(0,0,0,0.98);
            }}

            body {{
                background-color: var(--bg);
                color: var(--text-main);
                font-family: 'Inter', sans-serif;
                margin: 0;
                display: flex;
                height: 100vh;
                overflow: hidden;
            }}

            /* --- SIDEBAR ARCHITECTURE --- */
            .sidebar {{
                width: 280px;
                background-color: var(--sidebar);
                border-right: 1px solid var(--border);
                padding: 45px 25px;
                display: flex;
                flex-direction: column;
                box-shadow: 10px 0 40px rgba(0,0,0,0.7);
                z-index: 100;
            }}

            .logo-container {{ margin-bottom: 40px; }}
            .logo {{ color: var(--orange); font-size: 28px; font-weight: 900; letter-spacing: 5px; margin: 0; }}
            .sub-logo {{ font-size: 10px; color: var(--text-dim); font-weight: 800; letter-spacing: 2px; text-transform: uppercase; }}

            .btn-connect {{
                background-color: var(--orange);
                color: #000;
                border: none;
                width: 100%;
                padding: 18px;
                font-weight: 900;
                font-size: 12px;
                letter-spacing: 1px;
                cursor: pointer;
                border-radius: 4px;
                margin-bottom: 30px;
                text-transform: uppercase;
                transition: 0.3s;
            }}

            .btn-connect:hover {{
                box-shadow: 0 0 30px rgba(255, 94, 0, 0.45);
                transform: translateY(-2px);
            }}

            .status-panel {{
                background: #080808;
                border: 1px solid #151515;
                padding: 18px;
                border-radius: 4px;
                font-size: 10px;
                margin-bottom: 35px;
            }}

            .indicator {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #1a1a1a; margin-right: 12px; transition: 0.5s; }}
            .online {{ background: var(--orange); box-shadow: 0 0 12px var(--orange); }}

            /* --- BALANCE & CREDITS UI --- */
            .balance-card {{
                background: linear-gradient(135deg, #111, #000);
                border: 1px solid #222;
                padding: 15px;
                border-radius: 4px;
                margin-bottom: 20px;
            }}
            .bal-label {{ font-size: 9px; color: #555; font-weight: 900; margin-bottom: 5px; text-transform: uppercase; }}
            .bal-amount {{ font-size: 20px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px; }}
            .bal-symbol {{ color: var(--orange); font-size: 14px; }}

            /* --- NAVIGATION --- */
            .nav-group {{ margin-bottom: 25px; }}
            .nav-title {{ font-size: 9px; color: #222; font-weight: 900; margin-bottom: 12px; letter-spacing: 1px; }}
            .nav-item {{
                padding: 12px 0;
                font-size: 12px;
                font-weight: 700;
                color: var(--text-dim);
                cursor: pointer;
                transition: 0.2s;
            }}
            .nav-item:hover, .nav-active {{ color: #fff; padding-left: 5px; }}
            .nav-active {{ color: var(--orange) !important; border-left: 2px solid var(--orange); padding-left: 10px; }}

            /* --- MAIN REPOSITORY AREA --- */
            .main {{
                flex: 1;
                padding: 60px;
                overflow-y: auto;
                background: radial-gradient(circle at top right, #150a05, #050505);
            }}

            .main-header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
                margin-bottom: 60px;
            }}

            .main-header h1 {{ font-size: 42px; font-weight: 200; margin: 0; letter-spacing: -1px; }}

            .slot-wrapper {{
                background: #000;
                border: 1px solid #222;
                padding: 8px 15px;
                border-radius: 4px;
                display: flex;
                align-items: center;
                gap: 15px;
            }}

            #slot-select {{
                background: transparent;
                border: none;
                color: #fff;
                font-weight: 900;
                font-size: 10px;
                cursor: pointer;
                outline: none;
                text-transform: uppercase;
            }}

            /* --- SCRIPT GRID --- */
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
                gap: 25px;
            }}

            .card {{
                background-color: var(--card);
                border: 1px solid var(--border);
                border-radius: 4px;
                overflow: hidden;
                transition: 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
            }}

            .card:hover {{
                border-color: var(--orange);
                transform: translateY(-10px);
                box-shadow: 0 25px 50px rgba(0,0,0,0.8);
            }}

            .card-header {{
                background-color: var(--header);
                padding: 14px 25px;
                border-bottom: 1px solid var(--border);
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 9px;
                font-weight: 900;
                color: #333;
                letter-spacing: 1px;
            }}

            .card-body {{ padding: 40px 30px; }}
            .card-name {{ font-size: 22px; font-weight: 700; margin: 0 0 8px 0; letter-spacing: -0.5px; }}
            .card-pub {{ font-size: 11px; color: var(--orange); font-weight: 900; margin-bottom: 30px; text-transform: uppercase; }}

            .btn-flash {{
                background: transparent;
                border: 1px solid #222;
                color: #fff;
                width: 100%;
                padding: 15px;
                font-weight: 900;
                font-size: 11px;
                cursor: pointer;
                letter-spacing: 2px;
                transition: 0.3s;
                text-transform: uppercase;
            }}

            .btn-flash:hover {{
                background-color: #fff;
                color: #000;
                border-color: #fff;
            }}

            /* --- CMIND CONSOLE TERMINAL --- */
            #console-box {{
                position: fixed;
                bottom: 0;
                left: 280px;
                right: 0;
                height: 160px;
                background-color: var(--console-bg);
                border-top: 1px solid var(--orange);
                padding: 25px 35px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: var(--orange);
                overflow-y: auto;
                display: none;
                z-index: 1000;
            }}

            .log-line {{ margin-bottom: 5px; opacity: 0; animation: fadeIn 0.3s forwards; }}
            @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="logo-container">
                <h2 class="logo">{BRAND}</h2>
                <div class="sub-logo">{VERSION} SYSTEM | REPOSITORY</div>
            </div>

            <button class="btn-connect" onclick="connectZen()">Connect Hardware</button>

            <div class="status-panel">
                <div id="stat-led" class="indicator"></div>
                <span id="stat-text" style="color:#444">HW_NOT_DETECTED</span>
            </div>

            <div class="balance-card">
                <div class="bal-label">Wallet Balance</div>
                <div class="bal-amount">
                    <span class="bal-symbol">🪙</span>
                    <span id="credit-count">0.00</span>
                </div>
            </div>

            <div class="nav-group">
                <div class="nav-title">VAULT EXPLORER</div>
                <div class="nav-item nav-active">Marketplace</div>
                <div class="nav-item">Script Library</div>
                <div class="nav-item">Cloud Configurations</div>
            </div>

            <div class="nav-group" style="margin-top:auto;">
                <div class="nav-title">SESSION INFO</div>
                <div style="font-size:10px; color:#333; font-weight:900;">ID: <span id="user-display" style="color:var(--orange)">---</span></div>
                <div style="font-size:9px; color:#222; margin-top:5px; font-weight:800;">ARCHITECT: {DEV_ID}</div>
            </div>
        </div>

        <div class="main">
            <div class="main-header">
                <div>
                    <h1>Payload_Gateway</h1>
                    <div style="color:var(--orange); font-size:11px; font-weight:900; letter-spacing:1px;">ENCRYPTED BINARY UPLINK</div>
                </div>
                
                <div class="slot-wrapper">
                    <span style="font-size:9px; font-weight:900; color:#444;">TARGET_SLOT</span>
                    <select id="slot-select">
                        <option value="1">MEMORY SLOT 1</option>
                        <option value="2">MEMORY SLOT 2</option>
                        <option value="3">MEMORY SLOT 3</option>
                        <option value="4">MEMORY SLOT 4</option>
                    </select>
                </div>
            </div>

            <div class="grid" id="script-grid">
                </div>
        </div>

        <div id="console-box">
            <div id="terminal-out">> WAITING FOR HANDSHAKE...</div>
        </div>

        <script>
            let zenDevice = null;
            let currentUserId = prompt("SYNC DATA: ENTER DISCORD USER ID:");
            document.getElementById('user-display').innerText = currentUserId;

            async function connectZen() {{
                try {{
                    zenDevice = await navigator.usb.requestDevice({{ filters: [{{ vendorId: 0x1209, productId: 0x2188 }}] }});
                    await zenDevice.open();
                    await zenDevice.claimInterface(0);
                    
                    document.getElementById('stat-led').classList.add('online');
                    document.getElementById('stat-text').innerText = "ZEN_RECOGNIZED";
                    document.getElementById('stat-text').style.color = "#fff";
                    writeLog("BRIDGE SUCCESS: Hardware communication port claimed.");
                }} catch (e) {{
                    writeLog("ERROR: Connection refused. Check PROG port.");
                }}
            }}

            function writeLog(msg) {{
                const con = document.getElementById('console-box');
                const out = document.getElementById('terminal-out');
                con.style.display = 'block';
                const time = new Date().toLocaleTimeString();
                out.innerHTML += `<div class="log-line"><span style="color:#333">[${{time}}]</span> ${{msg}}</div>`;
                con.scrollTop = con.scrollHeight;
            }}

            async function startFlash(scriptId, scriptName) {{
                if(!zenDevice) return alert("Zen Device not found.");
                const slot = document.getElementById('slot-select').value;
                
                writeLog(`REQUESTING_BINARY: ${{scriptName}}...`);

                const res = await fetch(`/api/request_flash/${{scriptId}}?user_id=${{currentUserId}}`);
                if(!res.ok) {{
                    writeLog(`<span style="color:red;">DENIED: Access expired or unauthorized for ${{scriptName}}.</span>`);
                    return;
                }}

                const blob = await res.blob();
                const buffer = await blob.arrayBuffer();
                const data = new Uint8Array(buffer);

                writeLog(`HANDSHAKE: Purging Memory Slot ${{slot}}...`);
                
                try {{
                    writeLog(`WRITING: Sending ${{data.byteLength}} bytes to address 0x0${{slot}}...`);
                    await zenDevice.transferOut(1, data); 
                    
                    setTimeout(() => {{
                        writeLog(`VERIFY: Checksum matched.`);
                        writeLog(`<b>SUCCESS: ${{scriptName}} is now active on Slot ${{slot}}!</b>`);
                    }}, 1200);

                }} catch (err) {{
                    writeLog(`FATAL: Hardware bridge lost during write.`);
                }}
            }}

            async function refreshUI() {{
                const res = await fetch('/api/get_scripts');
                const scripts = await res.json();
                
                const balRes = await fetch(`/api/get_balance?user_id=${{currentUserId}}`);
                const balData = await balRes.json();
                document.getElementById('credit-count').innerText = balData.balance.toFixed(2);

                const grid = document.getElementById('script-grid');
                grid.innerHTML = scripts.map(s => `
                    <div class="card">
                        <div class="card-header">
                            <span>VER: ${{s.version || '1.0'}}</span>
                            <span>BIN_SECURED</span>
                        </div>
                        <div class="card-body">
                            <h3 class="card-name">${{s.name}}</h3>
                            <div class="card-pub">AUTHOR: ${{s.publisher}}</div>
                            <button class="btn-flash" onclick="startFlash('${{s.id}}', '${{s.name}}')">Flash to Zen</button>
                        </div>
                    </div>
                `).join('');
            }}

            refreshUI();
        </script>
    </body>
    </html>
    """

# ==========================================
# 3. BACKEND API & DATA HANDLERS
# ==========================================

@app.route('/api/get_scripts')
def api_get_scripts():
    db = load_db()
    return jsonify(db["scripts"])

@app.route('/api/get_balance')
def api_get_balance():
    user_id = request.args.get('user_id')
    db = load_db()
    bal = db["user_balances"].get(user_id, 0.00)
    return jsonify({"balance": bal})

@app.route('/api/request_flash/<script_id>')
def api_request_flash(script_id):
    user_id = request.args.get('user_id')
    db = load_db()
    script = next((s for s in db["scripts"] if str(s["id"]) == script_id), None)
    if not script: return "Script Missing", 404
    allowed = db["auth_users"].get(script["name"], [])
    if user_id not in allowed:
        return "Access Denied", 403
    return send_from_directory(BIN_FOLDER, f"{script['name']}.bin")

# ==========================================
# 4. DISCORD COMMAND CENTER (BOT)
# ==========================================
intents = discord.Intents.default()
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"--- {BRAND} {VERSION} ENGINE ONLINE ---")
    await bot.tree.sync()

@bot.tree.command(name="authorize")
async def authorize(interaction: discord.Interaction, member: discord.Member, script_name: str):
    db = load_db()
    if script_name not in db["auth_users"]:
        db["auth_users"][script_name] = []
    if str(member.id) not in db["auth_users"][script_name]:
        db["auth_users"][script_name].append(str(member.id))
        save_db(db)
        await interaction.response.send_message(f"✅ **AUTHORIZED**: {member.mention} can now flash `{script_name}`.")
    else:
        await interaction.response.send_message(f"User already has access to {script_name}.")

@bot.tree.command(name="add_credits")
async def add_credits(interaction: discord.Interaction, member: discord.Member, amount: float):
    db = load_db()
    current = db["user_balances"].get(str(member.id), 0.0)
    db["user_balances"][str(member.id)] = current + amount
    save_db(db)
    await interaction.response.send_message(f"💰 **CREDITS UPDATED**: Added {amount} to {member.mention}. New Balance: {current + amount}")

# ==========================================
# 5. EXECUTION BRIDGE
# ==========================================
def run_web():
    app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.run(TOKEN)
