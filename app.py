import os
import json
import threading
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, jsonify, request, render_template_string, send_from_directory, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# --- SECURE CONFIGURATION ---
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
        return {"scripts": [], "auth_publishers": [OWNER_ID], "slot_config": {}}
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

app = Flask(__name__)

# --- THE MIRROR INTERFACE (HTML/CSS/JS) ---
# Replicated from image_2.png with WebUSB and Access Denied pop-up
MIRROR_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ARCANE | Marketplace</title>
    <style>
        :root {
            --neon-orange: #ff5e00; --bg-black: #000;
            --sidebar-width: 320px; --glass-bg: rgba(10, 10, 10, 0.98);
        }
        
        body {
            background-color: var(--bg-black); color: #e0e0e0;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            margin: 0; display: flex; height: 100vh; overflow: hidden;
        }

        /* SIDEBAR (CMIND STYLE) */
        .sidebar {
            width: var(--sidebar-width); background: #050505;
            border-right: 1px solid #151515; display: flex; flex-direction: column;
            z-index: 100; box-shadow: 5px 0 30px rgba(0,0,0,0.5);
        }

        .sidebar-header { padding: 40px 30px; border-bottom: 1px solid #111; }
        .logo { color: var(--neon-orange); font-size: 38px; font-weight: 900; letter-spacing: 4px; text-shadow: 0 0 15px var(--neon-orange); }
        .version-tag { font-size: 10px; color: #333; letter-spacing: 2px; text-transform: uppercase; margin-top: 5px; }

        .sidebar-content { flex: 1; padding: 30px; overflow-y: auto; }
        .nav-item { padding: 15px; border-radius: 4px; border: 1px solid transparent; cursor: pointer; margin-bottom: 10px; transition: 0.2s; color: #666; font-size: 13px; font-weight: 700; }
        .nav-item:hover { background: rgba(255,255,255,0.02); color: #fff; }
        .nav-item.active { border-color: var(--neon-orange); color: var(--neon-orange); background: rgba(255, 94, 0, 0.05); }

        /* HARDWARE STATUS (LIVE) */
        .hw-status { background: #0a0a0a; border: 1px solid #111; padding: 20px; border-radius: 6px; margin: 20px 0; }
        .hw-label { font-size: 9px; color: #444; font-weight: 800; text-transform: uppercase; margin-bottom: 15px; }
        .led-row { display: flex; align-items: center; gap: 10px; font-size: 11px; color: #888; }
        .led { width: 10px; height: 10px; border-radius: 50%; background: #222; }
        .led.active { background: #00d2ff; box-shadow: 0 0 10px #00d2ff; }

        /* MAIN CANVAS */
        .main-canvas { flex: 1; display: flex; flex-direction: column; background: radial-gradient(circle at top right, #100804 0%, #000 100%); }
        .top-bar { height: 80px; border-bottom: 1px solid #111; display: flex; align-items: center; justify-content: space-between; padding: 0 50px; }
        .search-box { background: #111; border: 1px solid #222; width: 400px; padding: 12px 20px; border-radius: 4px; color: #fff; outline: none; }

        .content-area { flex: 1; padding: 50px; overflow-y: auto; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 30px; }

        /* SCRIPT CARD ARCHITECTURE */
        .card {
            background: var(--glass-bg); border: 1px solid #1a1a1a; border-radius: 4px;
            overflow: hidden; transition: 0.4s; display: flex; flex-direction: column;
        }
        .card:hover { border-color: var(--neon-orange); transform: translateY(-8px); }
        .card-img { height: 180px; background: #080808; border-bottom: 1px solid #111; display: flex; align-items: center; justify-content: center; }
        .card-body { padding: 30px; }
        .card-title { font-size: 26px; font-weight: 300; margin: 0 0 10px 0; letter-spacing: -0.5px; }
        .card-meta { display: flex; justify-content: space-between; font-size: 10px; font-weight: 900; color: #444; text-transform: uppercase; }
        
        .btn-flash {
            background: var(--neon-orange); color: #000; border: none; padding: 16px;
            width: 100%; border-radius: 4px; font-weight: 900; cursor: pointer; margin-top: 30px;
            text-transform: uppercase; transition: 0.3s;
        }
        .btn-flash:hover { background: #fff; box-shadow: 0 0 30px var(--neon-orange); }

        /* SLOT SELECTOR OVERLAY */
        .slot-pill {
            background: #000; border: 1px solid #222; padding: 10px 20px; border-radius: 50px;
            font-size: 11px; font-weight: 900; color: #fff; cursor: pointer; display: flex; align-items: center; gap: 10px;
        }
        .slot-pill:hover { border-color: var(--neon-orange); }

        /* PUBLISHER MODAL */
        #pub-modal {
            position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 200;
            display: none; align-items: center; justify-content: center;
        }
        .modal-box { background: #0a0a0a; border: 1px solid var(--neon-orange); padding: 50px; width: 500px; border-radius: 4px; }
        input, select { width: 100%; background: #000; border: 1px solid #222; color: #fff; padding: 15px; margin-bottom: 15px; }

        /* --- Memory Slots Layout --- */
        .memory-slots {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            padding: 20px;
            background-color: #121212;
            border-top: 1px solid #1a1a1a;
        }

        .memory-slot {
            background-color: #1a1a1a;
            color: #4a90e2;
            padding: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-radius: 4px;
        }

        .slot-number {
            font-size: 1.2rem;
            font-weight: bold;
            margin-right: 10px;
        }

        .slot-content {
            display: flex;
            align-items: center;
            flex-grow: 1;
        }

        .slot-indicator {
            width: 20px;
            height: 20px;
            background-color: #333;
            border-radius: 50%;
            margin-right: 10px;
        }

        .slot-text {
            color: #fff;
            flex-grow: 1;
        }

        .slot-actions {
            display: flex;
            gap: 5px;
        }

        .icon-btn {
            background: none;
            border: none;
            color: #888;
            cursor: pointer;
            padding: 2px;
        }

        .icon-btn:hover {
            color: #fff;
        }

    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-header">
            <div class="logo">ARCANE</div>
            <div class="version-tag">MARKETPLACE</div>
        </div>

        <div class="sidebar-content">
            <div class="hw-status">
                <div id="led" class="led"></div>
                <span id="hw-name" style="font-size:11px; color:#444;">Disconnected</span>
            </div>

            <div class="nav-item active">Repository Marketplace</div>
            <div class="nav-item">Device Input Monitor</div>
            <div class="nav-item" onclick="toggleModal()">Upload Binary</div>
            
            <div style="margin-top:auto; padding:30px;">
                <button class="btn-flash" style="background-color: #ff6600;" onclick="connect()">Initialize Zen</button>
            </div>
        </div>
    </div>

    <div class="main-canvas">
        <div class="top-bar">
            <input type="text" class="search-box" placeholder="Filter through optimized binaries...">
            <div class="slot-pill">
                <span style="color:#444">Destination:</span>
                <select id="target-slot" style="background:none; border:none; color:#fff; font-weight:900; width:auto; padding:0; margin:0; cursor:pointer;">
                    <option value="1">SLOT 01</option><option value="2">SLOT 02</option>
                    <option value="3">SLOT 03</option><option value="4">SLOT 04</option>
                </select>
            </div>
        </div>

        <div class="content-area">
            <div class="grid" id="script-grid"></div>
        </div>

        <div class="memory-slots">
            <div class="memory-slot">
                <div class="slot-number">1</div>
                <div class="slot-content">
                    <div class="slot-indicator"></div>
                    <div class="slot-text"></div>
                </div>
                <div class="slot-actions">
                    <button class="icon-btn">⚙</button>
                    <button class="icon-btn">×</button>
                </div>
            </div>
            <div class="memory-slot">
                <div class="slot-number">2</div>
                <div class="slot-content">
                    <div class="slot-indicator"></div>
                    <div class="slot-text"></div>
                </div>
                <div class="slot-actions">
                    <button class="icon-btn">⚙</button>
                    <button class="icon-btn">×</button>
                </div>
            </div>
            <div class="memory-slot">
                <div class="slot-number">3</div>
                <div class="slot-content">
                    <div class="slot-indicator"></div>
                    <div class="slot-text"></div>
                </div>
                <div class="slot-actions">
                    <button class="icon-btn">⚙</button>
                    <button class="icon-btn">×</button>
                </div>
            </div>
            <div class="memory-slot">
                <div class="slot-number">4</div>
                <div class="slot-content">
                    <div class="slot-indicator"></div>
                    <div class="slot-text"></div>
                </div>
                <div class="slot-actions">
                    <button class="icon-btn">⚙</button>
                    <button class="icon-btn">×</button>
                </div>
            </div>
            <div class="memory-slot">
                <div class="slot-number">5</div>
                <div class="slot-content">
                    <div class="slot-indicator"></div>
                    <div class="slot-text"></div>
                </div>
                <div class="slot-actions">
                    <button class="icon-btn">⚙</button>
                    <button class="icon-btn">×</button>
                </div>
            </div>
            <div class="memory-slot">
                <div class="slot-number">6</div>
                <div class="slot-content">
                    <div class="slot-indicator"></div>
                    <div class="slot-text"></div>
                </div>
                <div class="slot-actions">
                    <button class="icon-btn">⚙</button>
                    <button class="icon-btn">×</button>
                </div>
            </div>
            <div class="memory-slot">
                <div class="slot-number">7</div>
                <div class="slot-content">
                    <div class="slot-indicator"></div>
                    <div class="slot-text"></div>
                </div>
                <div class="slot-actions">
                    <button class="icon-btn">⚙</button>
                    <button class="icon-btn">×</button>
                </div>
            </div>
            <div class="memory-slot">
                <div class="slot-number">8</div>
                <div class="slot-content">
                    <div class="slot-indicator"></div>
                    <div class="slot-text"></div>
                </div>
                <div class="slot-actions">
                    <button class="icon-btn">⚙</button>
                    <button class="icon-btn">×</button>
                </div>
            </div>
        </div>
    </div>

    <div id="pub-modal"><div class="modal-box">
        <h2 style="color:var(--neon-orange);">Vault Upload</h2>
        <form action="/api/upload" method="post" enctype="multipart/form-data">
            <input type="text" name="pub_id" placeholder="Discord ID" required>
            <input type="text" name="s_name" placeholder="Script Name" required>
            <input type="file" name="file" required>
            <button type="submit" class="btn-flash">Sync to Cloud</button>
        </form>
        <button onclick="toggleModal()" style="background:none; border:none; color:#444; width:100%; margin-top:20px; cursor:pointer;">CANCEL</button>
    </div></div>
    
    <script>
        let device = null;
        // Vendor ID and Product ID for Cronus Zen
        const VENDOR_ID = 0x0C1C; 
        const PRODUCT_ID = 0x1D01; 

        function toggleModal() { const m = document.getElementById('pub-modal'); m.style.display = (m.style.display === 'flex') ? 'none' : 'flex'; }
        
        // --- WebUSB Connect with Zen IDs ---
        async function connect() {
            try {
                // Request access to a USB device with the specific vendor and product IDs
                device = await navigator.usb.requestDevice({ filters: [{ vendorId: VENDOR_ID, productId: PRODUCT_ID }] });
                await device.open(); 
                await device.claimInterface(0); 
                document.getElementById('led').classList.add('active');
                document.getElementById('hw-name').innerText = "ZEN_ACTIVE";
                document.getElementById('hw-name').style.color = "#fff";
                alert("Connected to Zen device.");
            } catch (e) { 
                console.error("USB connection failed:", e);
                alert("Connect Zen via PROG port."); 
            }
        }
        
        // --- Flash with Access Denied Pop-up ---
        async function flash(id, name) {
            if(!device) return alert("Hardware Link Required.");
            const res = await fetch(`/api/download/${id}`);
            if(!res.ok) {
                // Specific pop-up for access denied
                if(res.status === 403) {
                    alert("Nice try, Make a ticket in the discord to get perms for this file");
                } else {
                    alert("Authorization Fault.");
                }
                return; // Stop flashing
            }

            const data = new Uint8Array(await (await res.blob()).arrayBuffer());
            await device.transferOut(1, data);
            alert(`SUCCESS: ${name} deployed to Slot ${document.getElementById('target-slot').value}`);
        }

        async function load() {
            const r = await fetch('/api/scripts');
            const d = await r.json();
            document.getElementById('script-grid').innerHTML = d.map(s => `
                <div class="card"><div class="card-body">
                    <div style="font-size:10px; color:var(--neon-orange); font-weight:900;">${s.publisher}</div>
                    <h3>${s.name}</h3>
                    <button class="btn-flash" onclick="flash('${s.id}', '${s.name}')">Load to Device</button>
                </div></div>
            `).join('');
        }
        load();
    </script>
</body>
</html>
"""

# --- BACKEND ---
@app.route('/')
def home(): return render_template_string(MIRROR_UI)

@app.route('/api/scripts')
def get_scripts(): return jsonify(load_db()["scripts"])

@app.route('/api/upload', methods=['POST'])
def upload():
    db = load_db()
    if request.form.get('pub_id') not in db["auth_publishers"]: return "403", 403
    file = request.files['file']
    s_name = request.form.get('s_name')
    filename = secure_filename(f"{s_name}.bin")
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    db["scripts"].append({"id": len(db["scripts"])+1, "name": s_name, "publisher": request.form.get('pub_id'), "file": filename})
    save_db(db)
    return redirect(url_for('home'))

@app.route('/api/download/<int:s_id>')
def download(s_id):
    db = load_db()
    script = next((s for s in db["scripts"] if s["id"] == s_id), None)
    if not script: return "404", 404
    
    # Check if a user ID is provided in the request
    user_id = request.args.get('user_id')
    
    # Simple check for demo. In production, this would be a real permission check.
    # For now, it just returns a 403 if no user_id is provided or if it's not the owner.
    # This will trigger the specfic pop-up on the client side.
    if user_id != OWNER_ID:
        return "403 Forbidden - Permission required", 403
        
    return send_from_directory(UPLOAD_FOLDER, script["file"])

# --- DISCORD ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"--- ARCANE ENGINE ONLINE ---")
    await bot.tree.sync()

@bot.tree.command(name="authorize_publisher")
async def add_pub(interaction: discord.Interaction, member: discord.Member):
    if str(interaction.user.id) != OWNER_ID:
        return await interaction.response.send_message("Architect Access Required.")
    db = load_db()
    if str(member.id) not in db["auth_publishers"]:
        db["auth_publishers"].append(str(member.id))
        save_db(db)
        await interaction.response.send_message(f"Authorized {member.mention} for Vault Uploads.")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("CRITICAL: No DISCORD_TOKEN found in Environment.")
