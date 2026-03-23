import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, jsonify, request, send_from_directory
import threading
from dotenv import load_dotenv

# ==========================================
# 1. SYSTEM INITIALIZATION
# ==========================================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_PASS = "LucaBlu2026"
DB_FILE = "vault_storage.json"
BIN_FOLDER = "scripts_vault"

if not os.path.exists(BIN_FOLDER): os.makedirs(BIN_FOLDER)
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"publishers": {}, "scripts": [], "auth_users": {}}, f)

def load_db():
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

app = Flask(__name__)

# ==========================================
# 2. THE ULTIMATE CMIND MIRROR UI
# ==========================================
@app.route('/')
def index():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>ARCANE MARKETPLACE | PRO EDITION</title>
        <style>
            :root {{
                --orange: #ff5e00; --bg: #050505; --sidebar: #000; 
                --card: #0f0f0f; --border: #1a1a1a; --text: #eee;
            }}
            body {{ 
                background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; 
                margin: 0; display: flex; height: 100vh; overflow: hidden;
            }}
            
            /* SIDEBAR - 1:1 CMIND LAYOUT */
            .sidebar {{ 
                width: 280px; background: var(--sidebar); border-right: 1px solid var(--border); 
                padding: 40px 25px; display: flex; flex-direction: column;
            }}
            .logo {{ color: var(--orange); font-size: 24px; font-weight: 900; letter-spacing: 3px; margin-bottom: 5px; }}
            .sub-logo {{ font-size: 10px; color: #333; font-weight: 800; margin-bottom: 40px; }}
            
            .btn-main {{ 
                background: var(--orange); color: #000; border: none; width: 100%; padding: 16px; 
                font-weight: 900; cursor: pointer; border-radius: 4px; margin-bottom: 20px;
                text-transform: uppercase; transition: 0.3s;
            }}
            .btn-main:hover {{ box-shadow: 0 0 20px rgba(255,94,0,0.4); }}
            
            .status-box {{ 
                background: #0a0a0a; border: 1px solid #111; padding: 15px; border-radius: 4px;
                font-size: 11px; margin-bottom: 30px;
            }}
            .indicator {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #222; margin-right: 10px; }}
            .online {{ background: var(--orange); box-shadow: 0 0 8px var(--orange); }}

            /* MAIN CONTENT GRID */
            .main {{ flex: 1; padding: 60px; overflow-y: auto; background: linear-gradient(135deg, #080808 0%, #050505 100%); }}
            .header-flex {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 50px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; }}

            /* SCRIPT CARDS */
            .card {{ 
                background: var(--card); border: 1px solid var(--border); border-radius: 6px; 
                transition: 0.3s ease; position: relative;
            }}
            .card:hover {{ border-color: var(--orange); transform: translateY(-5px); }}
            .card-head {{ background: #121212; padding: 10px 20px; font-size: 10px; color: #444; display: flex; justify-content: space-between; }}
            .card-body {{ padding: 30px 20px; }}
            .card-title {{ font-size: 18px; font-weight: 700; margin-bottom: 5px; }}
            .card-author {{ color: var(--orange); font-size: 11px; font-weight: 800; text-transform: uppercase; }}
            
            .btn-flash {{ 
                background: transparent; border: 1px solid #222; color: #fff; width: 100%; 
                padding: 12px; margin-top: 20px; cursor: pointer; font-weight: 700; transition: 0.3s;
            }}
            .btn-flash:hover {{ background: #fff; color: #000; }}

            /* TERMINAL CONSOLE */
            #console {{ 
                position: fixed; bottom: 0; left: 280px; right: 0; height: 120px; 
                background: rgba(0,0,0,0.95); border-top: 1px solid var(--orange);
                padding: 15px 25px; font-family: monospace; font-size: 12px; color: var(--orange);
                overflow-y: auto; display: none;
            }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="logo">ARCANE</div>
            <div class="sub-logo">SYSTEM V5.8.2</div>

            <button class="btn-main" onclick="initZen()">Connect Cronus</button>

            <div class="status-box">
                <div id="stat-led" class="indicator"></div>
                <span id="stat-text">HARDWARE DISCONNECTED</span>
            </div>

            <div style="font-size:10px; color:#222; font-weight:900; margin-top:auto;">
                PORTAL ACCESS: GRANTED<br>ID: <span id="user-display">---</span>
            </div>
        </div>

        <div class="main">
            <div class="header-flex">
                <h1 style="margin:0; font-weight:200;">Available_Payloads</h1>
                <select id="slot-select" style="background:#000; color:#fff; border:1px solid #222; padding:5px;">
                    <option value="1">MEMORY SLOT 1</option>
                    <option value="2">MEMORY SLOT 2</option>
                    <option value="3">MEMORY SLOT 3</option>
                </select>
            </div>
            <div class="grid" id="market-grid"></div>
        </div>

        <div id="console">> SYSTEM IDLE...</div>

        <script>
            let device = null;
            let userId = prompt("ENTER DISCORD ID FOR PERMISSION SYNC:");
            document.getElementById('user-display').innerText = userId;

            async function initZen() {{
                try {{
                    // CMIND uses specific Filters to find the Zen among other USBs
                    device = await navigator.usb.requestDevice({{ 
                        filters: [{{ vendorId: 0x1209, productId: 0x2188 }}] 
                    }});
                    await device.open();
                    await device.claimInterface(0);
                    
                    document.getElementById('stat-led').classList.add('online');
                    document.getElementById('stat-text').innerText = "ZEN READY (PROG PORT)";
                    writeLog("HANDSHAKE SUCCESS: Hardware bridge active.");
                }} catch (err) {{
                    alert("Zen not found. Ensure you are using the PROG port (right side).");
                }}
            }}

            function writeLog(msg) {{
                const con = document.getElementById('console');
                con.style.display = 'block';
                con.innerHTML += `<br>[${{new Date().toLocaleTimeString()}}] ${{msg}}`;
                con.scrollTop = con.scrollHeight;
            }}

            async function flashScript(scriptId, fileName) {{
                if(!device) return alert("Please connect Zen first.");
                const slot = document.getElementById('slot-select').value;
                
                writeLog(`REQUESTING BYTES: ${{fileName}} (ID: ${{scriptId}})`);

                // Triple Check authorization via Backend
                const response = await fetch(`/api/get_bin/${{scriptId}}?user_id=${{userId}}`);
                if(!response.ok) {{
                    writeLog("CRITICAL ERROR: ACCESS DENIED. Unauthorized User ID.");
                    return;
                }}

                const blob = await response.blob();
                const buffer = await blob.arrayBuffer();
                const data = new Uint8Array(buffer);

                writeLog(`STREAMING: Writing ${{data.byteLength}} bytes to SLOT ${{slot}}...`);
                
                try {{
                    // The CMIND Flashing Protocol
                    // transferOut(Endpoint, Data)
                    await device.transferOut(1, data); 
                    writeLog("FLASH VERIFIED: Script successfully written to hardware.");
                }} catch (e) {{
                    writeLog("HARDWARE ERROR: Buffer overflow or connection lost.");
                }}
            }}

            async function loadMarket() {{
                const res = await fetch('/api/list_scripts');
                const data = await res.json();
                document.getElementById('market-grid').innerHTML = data.map(s => `
                    <div class="card">
                        <div class="card-head"><span>REV. ${{s.version || '1.0'}}</span><span>SECURED</span></div>
                        <div class="card-body">
                            <div class="card-title">${{s.name}}</div>
                            <div class="card-author">BY: ${{s.publisher}}</div>
                            <button class="btn-flash" onclick="flashScript('${{s.id}}', '${{s.name}}')">FLASH TO ZEN</button>
                        </div>
                    </div>
                `).join('');
            }}
            loadMarket();
        </script>
    </body>
    </html>
    """

# ==========================================
# 3. BACKEND LOGIC (API & DISCORD)
# ==========================================

@app.route('/api/list_scripts')
def list_scripts():
    return jsonify(load_db()["scripts"])

@app.route('/api/get_bin/<script_id>')
def get_bin(script_id):
    user_id = request.args.get('user_id')
    db = load_db()
    script = next((s for s in db["scripts"] if str(s["id"]) == script_id), None)
    
    if not script: return "404", 404
    
    # Permission Logic
    auth_list = db["auth_users"].get(script["name"], [])
    if user_id not in auth_list:
        return "Unauthorized", 403

    return send_from_directory(BIN_FOLDER, f"{{script['name']}}.bin")

# DISCORD BOT
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.tree.command(name="authorize")
async def authorize(interaction: discord.Interaction, member: discord.Member, script_name: str):
    db = load_db()
    if script_name not in db["auth_users"]: db["auth_users"][script_name] = []
    db["auth_users"][script_name].append(str(member.id))
    save_db(db)
    await interaction.response.send_message(f"Unlocked **{{script_name}}** for {{member.name}}")

def run_flask(): app.run(host='0.0.0.0', port=10000)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
