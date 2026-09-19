import requests
import time
from datetime import datetime, timezone

# ====================== ΡΥΘΜΙΣΕΙΣ ======================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1550957260149235735/sJcwpn47D0dEd87IP7ELHEsAvTZRiD6tBt8Cw_fFtZmHiTTYhaRVNE6zSI1Tnv-pbPul"
REGION = "EU"
CHECK_INTERVAL = 300   # Έλεγχος κάθε 5 λεπτά (σε δευτερόλεπτα)
# =======================================================

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

sent_events = set()
finished_events = set()

def get_events():
    # Χρήση του αξιόπιστου Fortnite-API endpoint
    url = "https://fortnite-api.com/v2/news/br"
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Παίρνουμε τα MOTDs / Messages που περιέχουν τα events
                motds = data.get("data", {}).get("motds", [])
                return motds if isinstance(motds, list) else []
            else:
                print(f"⚠️ HTTP Error {response.status_code}. Retry {attempt + 1}/3...", flush=True)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error (attempt {attempt + 1}/3): {e}", flush=True)
        
        time.sleep(3)
        
    return []

def is_skin_cup(event):
    title = str(event.get("title", "")).lower()
    body = str(event.get("body", "")).lower()
    keywords = ["skin", "icon", "cup", "override", "champion", "focus", "collab", "edgerunners", "ironmouse", "lucy", "tournament"]
    return any(keyword in title or keyword in body for keyword in keywords)

def send_start_webhook(event):
    title = event.get("title") or "Skin Cup"
    body = event.get("body") or "Check in-game Compete tab for details."
    image_url = event.get("image") or "https://cdn2.unrealengine.com/fortnite-logo-1920x1080-1920x1080-1920x1080-1920x1080.jpg"

    embed = {
        "title": f"🏆 New Skin Cup Detected: {title}",
        "description": (
            f"**Region:** {REGION}\n\n"
            f"📝 **Details:**\n{body}\n\n"
            f"📊 **Scoring Rules & Requirements:**\n"
            f"• Points per kill & placement vary per tournament.\n"
            f"• Check the **Compete** tab in-game for exact session times.\n"
            f"• Typical requirement in EU is usually **Top 300–500** for the free skin."
        ),
        "color": 0x00ff99,
        "image": {"url": image_url},
        "footer": {
            "text": "Fortnite Skin Cup Tracker • EU • Live"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    payload = {
        "username": "Fortnite Skin Cup Tracker",
        "avatar_url": "https://cdn2.unrealengine.com/fortnite-logo-1920x1080-1920x1080-1920x1080-1920x1080.jpg",
        "embeds": [embed]
    }

    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        print(f"✅ Sent START notification: {title}", flush=True)
    except Exception as e:
        print(f"Discord error: {e}", flush=True)

def send_finished_webhook(event):
    title = event.get("title") or "Skin Cup"

    embed = {
        "title": f"🔴 Skin Cup Finished: {title}",
        "description": (
            f"**Region:** {REGION}\n\n"
            f"🏁 This tournament / event has ended.\n"
            f"Check in-game for final leaderboards and skin rewards!"
        ),
        "color": 0xff0055,  # Κόκκινο χρώμα για λήξη
        "footer": {
            "text": "Fortnite Skin Cup Tracker • Event Ended"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    payload = {
        "username": "Fortnite Skin Cup Tracker",
        "avatar_url": "https://cdn2.unrealengine.com/fortnite-logo-1920x1080-1920x1080-1920x1080-1920x1080.jpg",
        "embeds": [embed]
    }

    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        print(f"🛑 Sent FINISHED notification: {title}", flush=True)
    except Exception as e:
        print(f"Discord error: {e}", flush=True)

def main():
    print("🚀 Skin Cup Tracker started (EU - English)", flush=True)
    print(f"Checking every {CHECK_INTERVAL // 60} minutes...", flush=True)
    
    while True:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Checking events...", flush=True)
        events = get_events()
        
        for event in events:
            if not is_skin_cup(event):
                continue
                
            event_id = str(event.get("id") or event.get("title"))
            
            # 1. Νέο Event -> Στέλνει Webhook
            if event_id not in sent_events:
                send_start_webhook(event)
                sent_events.add(event_id)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
    
