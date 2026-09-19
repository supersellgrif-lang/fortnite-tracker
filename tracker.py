import requests
import time
from datetime import datetime

# ====================== ΡΥΘΜΙΣΕΙΣ ======================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1550957260149235735/sJcwpn47D0dEd87IP7ELHEsAvTZRiD6tBt8Cw_fFtZmHiTTYhaRVNE6zSI1Tnv-pbPul"
API_KEY = "bd2c3863-2feb-489e-b732-5019fc13903f"
REGION = "EU"
CHECK_INTERVAL = 3600   # Ελέγχει κάθε 1 ώρα (σε δευτερόλεπτα)
# =======================================================

headers = {
    "x-api-key": API_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

sent_events = set()

def get_events():
    # Έγκυρο API endpoint για τα νέα / events του Fortnite
    url = "https://fortnite-api.com/v2/news/br"
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    # Επιστρέφει τη λίστα με τα events/news
                    return data.get("data", {}).get("motds", []) or data.get("data", [])
                return data if isinstance(data, list) else []
            else:
                print(f"⚠️ HTTP Error {response.status_code}. Retry {attempt + 1}/3...", flush=True)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error (attempt {attempt + 1}/3): {e}", flush=True)
        
        time.sleep(5)  # Αναμονή 5 δευτερολέπτων πριν τη νέα προσπάθεια
        
    return []

def is_skin_cup(event):
    name = str(event.get("name", "") or event.get("displayName", "") or event.get("title", "") or event.get("tabTitle", "")).lower()
    keywords = ["skin", "icon", "cup", "override", "champion", "focus", "collab", "edgerunners", "ironmouse", "lucy"]
    return any(keyword in name for keyword in keywords)

def send_to_discord(event):
    name = event.get("name") or event.get("displayName") or event.get("title") or event.get("tabTitle") or "Unknown Skin Cup"
    
    embed = {
        "title": f"🏆 New Skin Cup Detected: {name}",
        "description": (
            f"**Region:** EU\n\n"
            f"Check the **Compete** tab in-game for full details:\n"
            f"• Points per kill & placement\n"
            f"• Exact placement needed for the skin\n"
            f"• Session times\n\n"
            f"Typical requirement in EU is usually **Top 300–500** for the free skin."
        ),
        "color": 0x00ff99,
        "footer": {
            "text": "Fortnite Skin Cup Tracker • EU • English"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

    payload = {
        "username": "Fortnite Skin Cup Tracker",
        "avatar_url": "https://cdn2.unrealengine.com/fortnite-logo-1920x1080-1920x1080-1920x1080-1920x1080.jpg",
        "embeds": [embed]
    }

    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        print(f"✅ Sent notification: {name}", flush=True)
    except Exception as e:
        print(f"Discord error: {e}", flush=True)

def main():
    print("🚀 Skin Cup Tracker started (EU - English)", flush=True)
    print(f"Checking every {CHECK_INTERVAL // 60} minutes...", flush=True)
    
    while True:
        print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Checking for events...", flush=True)
        events = get_events()
        
        for event in events:
            event_id = str(event.get("eventId") or event.get("id") or event.get("name") or id(event))
            
            if event_id not in sent_events and is_skin_cup(event):
                send_to_discord(event)
                sent_events.add(event_id)
        
        print(f"Waiting for {CHECK_INTERVAL // 60} minutes...", flush=True)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
    
