import os, json, discord, threading
from flask import Flask, request, jsonify
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = 1063556821517877258

app = Flask(__name__)
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@app.route('/verify-access', methods=['POST'])
def verify():
    user_id = int(request.json.get('discord_id'))
    if user_id == OWNER_ID: return jsonify({"role": "OWNER", "access": "ALL"})
    with open('registry.json', 'r') as f: reg = json.load(f)
    for g in reg['authorized_guilds']:
        guild = bot.get_guild(int(g['guild_id']))
        if guild:
            m = guild.get_member(user_id)
            if m and any(str(r.id) == str(g['publisher_role_id']) for r in m.roles):
                return jsonify({"role": "PUBLISHER", "folder": g['folder']})
    return jsonify({"role": "USER"})

def run_flask(): app.run(host='0.0.0.0', port=10000)
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
