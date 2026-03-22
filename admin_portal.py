import requests, json, base64
GITHUB_TOKEN = "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"
GITHUB_USER = "9mille7-sketch"
REPO_NAME = "Arcane-Vault"

def setup_new_publisher():
    print("\n--- ARCANE NETWORK: PUBLISHER ONBOARDING ---")
    pub_name = input("Partner Name: ").strip()
    g_id = input("Partner Guild ID: ").strip()
    r_id = input("Partner Role ID: ").strip()
    folder = f"scripts/{pub_name.lower().replace(' ', '_')}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    res = requests.get(f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/registry.json", headers=headers).json()
    content = json.loads(base64.b64decode(res['content']).decode())
    content['authorized_guilds'].append({"guild_name": pub_name, "guild_id": g_id, "publisher_role_id": r_id, "folder": folder})
    
    payload = {"message": f"Added {pub_name}", "content": base64.b64encode(json.dumps(content, indent=4).encode()).decode(), "sha": res['sha']}
    requests.put(f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/registry.json", headers=headers, json=payload)
    
    # Auto-create folder with README
    requests.put(f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/{folder}/README.txt", headers=headers, json={"message": "Init folder", "content": base64.b64encode(b"Drop GPC files here.").decode()})
    print(f"SUCCESS: {pub_name} is live at {folder}")

if __name__ == "__main__": setup_new_publisher()
