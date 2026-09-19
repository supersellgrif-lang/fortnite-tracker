import requests
import time
from datetime import datetime, timezone

# ====================== ΡΥΘΜΙΣΕΙΣ ======================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1550957260149235735/sJcwpn47D0dEd87IP7ELHEsAvTZRiD6tBt8Cw_fFtZmHiTTYhaRVNE6zSI1Tnv-pbPul"
API_KEY = "bd2c3863-2feb-489e-b732-5019fc13903f"
REGION = "EU"
CHECK_INTERVAL = 300   # Έλεγχος κάθε 5 λεπτά (σε δευτερόλεπτα)
# =======================================================

headers = {
    "x-api-key": API_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

sent_events = set()
finished_events = set()

def get_events():
    url = "https://prod.api-fortnite.com/api/v1/events/global"
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    return data.get("events", []) or data.get("data", []) or []
                return data if isinstance(data, list) else []
            else:
                print(f"⚠️ HTTP Error {response.status_code}. Retry {attempt + 1}/3...", flush=True)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error (attempt {attempt + 1}/3): {e}", flush=True)
        
        time.sleep(3)
        
    return []

def is_skin_cup(event):
    name = str(event.get("name", "") or event.get("displayName", "") or event.get("title", "")).lower()
    keywords = ["skin", "icon", "cup", "override", "champion", "focus", "collab", "edgerunners", "ironmouse", "lucy"]
    return any(keyword in name for keyword in keywords)

def format_time(iso_string):
    """Μετατρέπει ISO ημερομηνία σε αναγνώσιμη ώρα UTC/Local"""
    if not iso_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y @ %H:%M UTC")
    except Exception:
        return iso_string

def extract_scoring_rules(event):
    """Εξάγει τους πόντους Kills & Placement αν υπάρχουν στα data"""
    rules = event.get("rules") or event.get("scoringRules") or {}
    points_info = []

    # Αναζήτηση για elimination/kill points
    kills_pts = rules.get("pointsPerKill") or rules.get("eliminationPoints")
    if kills_pts is not None:
        points_info.append(f"• **Elimination:** {kills_pts} pts per kill")
    
    # Αναζήτηση για placement points
    placements = rules.get("placements") or rules.get("placementPoints")
    if isinstance(placements, list):
        for p in placements[:3]:  # Εμφάνιση των 3 πρώτων βαθμίδων
            points_info.append(f"• **Top {p.get('rank')}:** +{p.get('points')} pts")
    
    if not points_info:
        return "• Check in-game Compete tab for points breakdown."
    return "\n".join(points_info)

def send_start_webhook(event):
    name = event.get("name") or event.get("displayName") or event.get("title") or "Skin Cup"
    begin_time = format_time(event.get("beginTime") or event.get("startTime"))
    end_time = format_time(event.get("endTime"))
    scoring_text = extract_scoring_rules(event)

    embed = {
        "title": f"🏆 New Skin Cup Detected: {name}",
        "description": (
            f"**Region:** {REGION}\n\n"
            f"⏰ **Start Time:** {begin_time}\n"
            f"🏁 **End Time:** {end_time}\n\n"
            f"📊 **Scoring Rules:**\n"
            f"{scoring_text}\n\n"
            f"Typical requirement in EU is usually **Top 300–500** for the free skin."
        ),
        "color": 0x00ff99,
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
        print(f"✅ Sent START notification: {name}", flush=True)
    except Exception as e:
        print(f"Discord error: {e}", flush=True)

def send_finished_webhook(event):
    name = event.get("name") or event.get("displayName") or event.get("title") or "Skin Cup"
    end_time = format_time(event.get("endTime"))

    embed = {
        "title": f"🔴 Skin Cup Finished: {name}",
        "description": (
            f"**Region:** {REGION}\n\n"
            f"🏁 This tournament officially ended at **{end_time}**.\n"
            f"Check in-game for final leaderboards and skin distribution!"
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
        print(f"🛑 Sent FINISHED notification: {name}", flush=True)
    except Exception as e:
        print(f"Discord error: {e}", flush=True)

def check_event_status(event):
    """Ελέγχει αν το τουρνουά έχει τελειώσει με βάση την ώρα"""
    end_str = event.get("endTime")
    if not end_str:
        return False
    try:
        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) >= end_dt
    except Exception:
        return False

def main():
    print("🚀 Skin Cup Tracker started (EU - English)", flush=True)
    print(f"Checking every {CHECK_INTERVAL // 60} minutes...", flush=True)
    
    while True:
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] Checking events...", flush=True)
        events = get_events()
        
        for event in events:
            if not is_skin_cup(event):
                continue
                
            event_id = str(event.get("eventId") or event.get("id") or event.get("name") or id(event))
            
            # 1. Νέο Event -> Στέλνει Webhook Έναρξης
            if event_id not in sent_events:
                send_start_webhook(event)
                sent_events.add(event_id)

            # 2. Έλεγχος αν Τελείωσε -> Στέλνει Webhook Λήξης
            if event_id in sent_events and event_id not in finished_events:
                if check_event_status(event):
                    send_finished_webhook(event)
                    finished_events.add(event_id)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
    
