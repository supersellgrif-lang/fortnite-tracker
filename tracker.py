import requests
import time
from datetime import datetime, timezone

# ====================== ΡΥΘΜΙΣΕΙΣ ======================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1550957260149235735/sJcwpn47D0dEd87IP7ELHEsAvTZRiD6tBt8Cw_fFtZmHiTTYhaRVNE6zSI1Tnv-pbPul"
API_KEY = "ΒΑΛΕ_ΕΔΩ_ΝΕΟ_API_KEY"          # ← Πάρε νέο από api-fortnite.com
REGION = "EU"
CHECK_INTERVAL = 300   # 5 λεπτά
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
                # Το API επιστρέφει λίστα από GlobalEventDto
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("events", []) or data.get("data", []) or []
                return []
            else:
                print(f"⚠️ HTTP {response.status_code}: {response.text[:200]}", flush=True)
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Network error (attempt {attempt + 1}/3): {e}", flush=True)
        
        time.sleep(3)
    return []

def is_skin_cup(event_name: str, description: str = "") -> bool:
    text = (event_name + " " + description).lower()
    keywords = [
        "skin", "icon", "cup", "override", "champion", "focus",
        "collab", "edgerunners", "ironmouse", "lucy", "showdown",
        "victory cup", "reload cup", "zero build cup"
    ]
    return any(k in text for k in keywords)

def format_time(iso_string):
    if not iso_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y @ %H:%M UTC")
    except Exception:
        return iso_string

def extract_info(event):
    """Προσπαθεί να βγάλει όσο info γίνεται από τα διαθέσιμα πεδία"""
    name = (
        event.get("name")
        or event.get("shortTitle")
        or event.get("titleLine1")
        or "Unknown Cup"
    )
    
    description = event.get("description") or event.get("detailsDescription") or ""
    schedule = event.get("scheduleInfo") or ""
    
    # Ώρες από το πρώτο event της region
    begin_time = end_time = None
    regions = event.get("regions") or {}
    region_events = regions.get(REGION) or regions.get(REGION.upper()) or []
    
    if region_events:
        first = region_events[0]
        begin_time = first.get("beginTime")
        end_time = first.get("endTime")
        
        # Αν έχει windows, πάρε από το πρώτο window
        windows = first.get("eventWindows") or []
        if windows:
            begin_time = windows[0].get("beginTime") or begin_time
            end_time = windows[0].get("endTime") or end_time
    
    return {
        "name": name,
        "description": description,
        "schedule": schedule,
        "begin": begin_time,
        "end": end_time,
        "event_id": (region_events[0].get("eventId") if region_events else None) or event.get("id") or name
    }

def send_start_webhook(info):
    embed = {
        "title": f"🏆 New Skin Cup: {info['name']}",
        "description": (
            f"**Region:** {REGION}\n\n"
            f"⏰ **Start:** {format_time(info['begin'])}\n"
            f"🏁 **End:** {format_time(info['end'])}\n\n"
            f"📊 **Scoring:**\n"
            f"• Το API **δεν** δίνει points per kill / placement στο global endpoint.\n"
            f"• Συνήθως είναι **1 pt / elim** + placement points.\n"
            f"• Έλεγξε in-game στο **Compete** tab για ακριβή scoring & cutoff (Top X).\n\n"
            f"{('📝 ' + info['schedule']) if info['schedule'] else ''}"
        ),
        "color": 0x00ff99,
        "footer": {"text": "Fortnite Skin Cup Tracker • EU"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if info.get("description"):
        embed["description"] += f"\n\n**Info:** {info['description'][:300]}"

    payload = {
        "username": "Fortnite Skin Cup Tracker",
        "avatar_url": "https://cdn2.unrealengine.com/fortnite-logo-1920x1080-1920x1080-1920x1080-1920x1080.jpg",
        "embeds": [embed]
    }

    try:
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        print(f"✅ Sent START: {info['name']} (status {r.status_code})", flush=True)
    except Exception as e:
        print(f"Discord error: {e}", flush=True)

def send_finished_webhook(info):
    embed = {
        "title": f"🔴 Skin Cup Finished: {info['name']}",
        "description": (
            f"**Region:** {REGION}\n\n"
            f"🏁 Τελείωσε στις **{format_time(info['end'])}**.\n"
            f"Έλεγξε in-game για leaderboard & skin rewards."
        ),
        "color": 0xff0055,
        "footer": {"text": "Fortnite Skin Cup Tracker • Event Ended"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    payload = {
        "username": "Fortnite Skin Cup Tracker",
        "avatar_url": "https://cdn2.unrealengine.com/fortnite-logo-1920x1080-1920x1080-1920x1080-1920x1080.jpg",
        "embeds": [embed]
    }

    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        print(f"🛑 Sent FINISHED: {info['name']}", flush=True)
    except Exception as e:
        print(f"Discord error: {e}", flush=True)

def check_event_status(end_str):
    if not end_str:
        return False
    try:
        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) >= end_dt
    except Exception:
        return False

def main():
    print("🚀 Skin Cup Tracker started (EU)", flush=True)
    print(f"Checking every {CHECK_INTERVAL // 60} minutes...\n", flush=True)
    
    while True:
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        print(f"[{now}] Checking events...", flush=True)
        
        raw_events = get_events()
        print(f"   → Βρέθηκαν {len(raw_events)} global events", flush=True)
        
        for event in raw_events:
            info = extract_info(event)
            
            if not is_skin_cup(info["name"], info["description"]):
                continue
            
            event_id = str(info["event_id"])
            
            # Νέο event
            if event_id not in sent_events:
                print(f"   → Νέο Skin Cup: {info['name']}", flush=True)
                send_start_webhook(info)
                sent_events.add(event_id)
            
            # Έλεγχος λήξης
            if event_id in sent_events and event_id not in finished_events:
                if check_event_status(info["end"]):
                    send_finished_webhook(info)
                    finished_events.add(event_id)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
