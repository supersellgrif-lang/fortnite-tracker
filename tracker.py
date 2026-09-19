import requests
import time
from datetime import datetime

# ====================== ΡΥΘΜΙΣΕΙΣ ======================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1550957260149235735/sJcwpn47D0dEd87IP7ELHEsAvTZRiD6tBt8Cw_fFtZmHiTTYhaRVNE6zSI1Tnv-pbPul"
API_KEY = "bd2c3863-2feb-489e-b732-5019fc13903f"
REGION = "EU"
CHECK_INTERVAL = 1800   # Ελέγχει κάθε 30 λεπτά (σε δευτερόλεπτα)
# =======================================================

headers = {
    "x-api-key": API_KEY
}

sent_events = set()

def get_events():
    url = "https://prod.api-fortnite.com/api/v1/events/global"
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                return data.get("events", []) or data.get("data", []) or []
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error fetching events: {e}")
    return []

def is_skin_cup(event):
    name = str(event.get("name", "") or event.get("displayName", "") or event.get("title", "")).lower()
    keywords = ["skin", "icon", "cup", "override", "champion", "focus", "collab", "edgerunners", "ironmouse", "lucy"]
    return any(keyword in name for keyword in keywords)

def send_to_discord(event):
    name = event.get("name") or event.get("displayName") or event.get("title") or "Unknown Skin Cup"
    
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
        print(f"✅ Sent notification: {name}")
    except Exception as e:
        print(f"Discord error: {e}")

def main():
    print("🚀 Skin Cup Tracker started (EU - English)")
    print(f"Checking every {CHECK_INTERVAL // 60} minutes...")
    
    while True:
        events = get_events()
        for event in events:
            event_id = str(event.get("eventId") or event.get("id") or event.get("name") or id(event))
            
            if event_id not in sent_events and is_skin_cup(event):
                send_to_discord(event)
                sent_events.add(event_id)
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
