import os
import json
import requests
import time
import random
from datetime import datetime
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

EMERGENCY_KEYWORDS = {
    "critical": ["dying", "heart attack", "stroke", "not breathing", "unconscious", "bleeding heavily", "choking", "suicide"],
    "high": ["fire", "accident", "attack", "robbery", "assault", "emergency", "help", "hurt", "injured", "burning"],
    "medium": ["sick", "fever", "headache", "dizzy", "nausea", "cough", "pain", "vomiting"],
    "low": ["tired", "stress", "anxiety", "worried", "information", "medicine", "medication", "advice"]
}

_cache = {}
_cache_time = {}

def generate_whatsapp_link(phone_number, message=""):
    clean_number = phone_number.replace("+", "").replace(" ", "").replace("-", "")
    encoded_message = quote(message) if message else ""
    if encoded_message:
        return f"https://wa.me/{clean_number}?text={encoded_message}"
    return f"https://wa.me/{clean_number}"

def generate_whatsapp_emergency_link(location=None):
    emergency_contacts = os.getenv("EMERGENCY_CONTACTS", "").split(",")
    if not emergency_contacts or not emergency_contacts[0]:
        return None
    
    phone = emergency_contacts[0].strip().replace("+", "")
    
    if location:
        message = f"""🚨 EMERGENCY ALERT!

I need immediate help!

📍 Location: {location.get('city', 'Unknown')}, {location.get('region', 'Unknown')}
🗺️ Map: https://www.google.com/maps?q={location.get('lat', 28.6139)},{location.get('lon', 77.2090)}
🕐 Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Please respond ASAP!"""
    else:
        message = "🚨 EMERGENCY! I need immediate help! Please call me ASAP!"
    
    return generate_whatsapp_link(phone, message)

def get_whatsapp_sandbox_join_link():
    return {
        "link": "https://wa.me/14155238886",
        "number": "+1 415 523 8886",
        "instruction": "Send 'join <your-code>' to this number. Get code from Twilio Console."
    }


def get_user_location():
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        loc = data.get("loc", "28.6139,77.2090").split(",")
        return {
            "lat": float(loc[0]),
            "lon": float(loc[1]),
            "city": data.get("city", "Unknown"),
            "region": data.get("region", "Unknown"),
            "country": data.get("country", "IN"),
            "loc": data.get("loc", "28.6139,77.2090"),
            "ip": data.get("ip", "Unknown"),
            "source": "ipinfo"
        }
    except:
        pass
    
    try:
        data = requests.get("http://ip-api.com/json/", timeout=5).json()
        return {
            "lat": data.get("lat", 28.6139),
            "lon": data.get("lon", 77.2090),
            "city": data.get("city", "Unknown"),
            "region": data.get("regionName", "Unknown"),
            "country": data.get("countryCode", "IN"),
            "loc": f"{data.get('lat', 28.6139)},{data.get('lon', 77.2090)}",
            "ip": data.get("query", "Unknown"),
            "source": "ip-api"
        }
    except:
        pass
    
    return {
        "lat": 28.6139, "lon": 77.2090, "city": "Delhi",
        "region": "Delhi", "country": "IN", "loc": "28.6139,77.2090",
        "ip": "Unknown", "source": "default"
    }

def generate_google_maps_link(lat, lon):
    return f"https://www.google.com/maps?q={lat},{lon}"

def generate_directions_link(from_lat, from_lon, to_lat, to_lon):
    return f"https://www.google.com/maps/dir/{from_lat},{from_lon}/{to_lat},{to_lon}"

def generate_call_link(phone_number):
    clean = phone_number.replace(" ", "").replace("-", "")
    return f"tel:{clean}"

def generate_sms_link(phone_number, message=""):
    clean = phone_number.replace(" ", "").replace("-", "")
    if message:
        return f"sms:{clean}?body={quote(message)}"
    return f"sms:{clean}"


def detect_emergency(text):
    text_lower = text.lower()
    for level, keywords in EMERGENCY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return level, keyword
    return "low", None

def get_emergency_level_info(level):
    levels = {
        "critical": {"color": "#FF0000", "emoji": "🔴", "action": "Call 112 immediately!", "priority": 1},
        "high": {"color": "#FF9800", "emoji": "🟠", "action": "Seek immediate medical attention", "priority": 2},
        "medium": {"color": "#FFEB3B", "emoji": "🟡", "action": "Monitor symptoms, consult doctor", "priority": 3},
        "low": {"color": "#4CAF50", "emoji": "🟢", "action": "Follow AI advice, rest", "priority": 4}
    }
    return levels.get(level, levels["low"])


def get_nearby_services(location, service_type="hospital"):
    lat = location.get("lat", 28.6139)
    lon = location.get("lon", 77.2090)
    
    cache_key = f"{service_type}_{round(lat,2)}_{round(lon,2)}"
    if cache_key in _cache and time.time() - _cache_time.get(cache_key, 0) < 300:
        return _cache[cache_key]
    
    services = _fetch_services_api(lat, lon, service_type)
    if not services:
        services = _get_fallback_services(lat, lon, service_type)
    
    _cache[cache_key] = services
    _cache_time[cache_key] = time.time()
    
    return services

def _fetch_services_api(lat, lon, service_type):
    tags = {
        "hospital": "amenity=hospital",
        "police": "amenity=police",
        "fire_station": "amenity=fire_station",
        "pharmacy": "amenity=pharmacy"
    }
    
    query = f"""[out:json][timeout:5];node[{tags.get(service_type, 'amenity=hospital')}](around:5000,{lat},{lon});out 8;"""
    
    try:
        time.sleep(0.3)
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query}, timeout=10,
            headers={"User-Agent": "HealthApp/1.0"}
        )
        
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        services = []
        
        for el in data.get("elements", [])[:8]:
            tags = el.get("tags", {})
            services.append({
                "name": tags.get("name", service_type.replace("_", " ").title()),
                "lat": el.get("lat", lat),
                "lng": el.get("lon", lon),
                "type": service_type,
                "phone": tags.get("phone", tags.get("contact:phone", "112")),
                "address": tags.get("addr:full", tags.get("addr:street", "Use map")),
                "opening_hours": tags.get("opening_hours", "24/7")
            })
        
        return services
    except:
        return []

def _get_fallback_services(lat, lon, service_type):
    data = {
        "hospital": [
            {"name": "AIIMS Hospital", "offset": (0.01, 0.01), "phone": "011-26588500"},
            {"name": "Safdarjung Hospital", "offset": (-0.015, 0.01), "phone": "011-26707437"},
            {"name": "Max Hospital", "offset": (0.02, -0.01), "phone": "011-26515050"},
            {"name": "Apollo Hospital", "offset": (-0.01, -0.015), "phone": "011-26825858"},
        ],
        "police": [
            {"name": "Police Station", "offset": (0.008, 0.008), "phone": "100"},
            {"name": "Police Control Room", "offset": (-0.01, 0.012), "phone": "112"},
        ],
        "fire_station": [
            {"name": "Fire Station", "offset": (0.012, 0.005), "phone": "101"},
        ],
        "pharmacy": [
            {"name": "Apollo Pharmacy 24x7", "offset": (0.005, 0.005), "phone": "1860-500-0101"},
            {"name": "MedPlus", "offset": (-0.008, 0.008), "phone": "040-67006700"},
        ]
    }
    
    services = []
    for item in data.get(service_type, data["hospital"]):
        services.append({
            "name": item["name"],
            "lat": lat + item["offset"][0],
            "lng": lon + item["offset"][1],
            "type": service_type,
            "phone": item["phone"],
            "address": "Use map for directions",
            "opening_hours": "24/7"
        })
    
    return services


def get_emergency_numbers():
    return {
        "IN": {
            "police": "100", "ambulance": "108", "fire": "101", "emergency": "112",
            "women_helpline": "1091", "child_helpline": "1098", "mental_health": "08046110007"
        },
        "US": {"police": "911", "ambulance": "911", "fire": "911", "emergency": "911"},
        "UK": {"police": "999", "ambulance": "999", "fire": "999", "emergency": "112"},
        "default": {"emergency": "112"}
    }

def get_health_tips():
    tips = [
        {"tip": "Always verify prescription authenticity before dispensing", "category": "safety", "icon": "🔍"},
        {"tip": "Check expiration dates on all medications regularly", "category": "compliance", "icon": "📅"},
        {"tip": "Store medications in proper temperature-controlled conditions", "category": "storage", "icon": "🌡️"},
        {"tip": "Document all controlled substance transactions meticulously", "category": "regulation", "icon": "📋"},
        {"tip": "Maintain clear communication with patients about medication usage", "category": "service", "icon": "💬"},
        {"tip": "Follow proper disposal procedures for expired medications", "category": "safety", "icon": "🗑️"},
        {"tip": "Regular inventory audits prevent medication errors", "category": "compliance", "icon": "📊"},
        {"tip": "Wear appropriate PPE when handling hazardous medications", "category": "safety", "icon": "🛡️"},
    ]
    return random.sample(tips, min(3, len(tips)))

def get_first_aid_tips(emergency_type):
    tips = {
        "heart_attack": {
            "title": "Heart Attack First Aid",
            "steps": ["Call 112", "Make person sit", "Loosen clothing", "Give aspirin", "Prepare for CPR"]
        },
        "choking": {
            "title": "Choking First Aid",
            "steps": ["5 back blows", "5 abdominal thrusts", "Repeat until clear"]
        }
    }
    return tips.get(emergency_type, tips["heart_attack"])

def get_common_medicines():
    return {
        "controlled_substances": {
            "name": "Controlled Substances (Schedule II-V)",
            "use": "Pain management, ADHD treatment, anxiety medication",
            "dosage": "As prescribed by physician",
            "max_daily": "As prescribed - no refills without authorization",
            "warning": "Require special storage, documentation, and patient verification"
        },
        "refrigerated_meds": {
            "name": "Refrigerated Medications",
            "use": "Insulin, certain antibiotics, vaccines",
            "dosage": "Check storage requirements on label",
            "max_daily": "As prescribed",
            "warning": "Must be stored between 36-46°F. Never freeze unless specified."
        },
        "light_sensitive": {
            "name": "Light-Sensitive Medications",
            "use": "Certain antibiotics, vitamins, chemotherapy drugs",
            "dosage": "As prescribed",
            "warning": "Store in original amber containers away from direct light"
        },
        "hazardous_drugs": {
            "name": "Hazardous Drugs",
            "use": "Chemotherapy agents, certain antivirals",
            "dosage": "Handle with extreme caution",
            "warning": "Require special PPE, containment, and disposal procedures"
        },
        "high_alert_meds": {
            "name": "High-Alert Medications",
            "use": "Insulin, opioids, anticoagulants",
            "dosage": "Double-check calculations and dosages",
            "warning": "Independent double-check required before dispensing"
        }
    }


def generate_share_links(title, message, url=""):
    encoded_message = quote(message)
    encoded_url = quote(url) if url else ""
    encoded_title = quote(title)
    
    return {
        "whatsapp": f"https://wa.me/?text={encoded_message}",
        "telegram": f"https://t.me/share/url?url={encoded_url}&text={encoded_message}",
        "twitter": f"https://twitter.com/intent/tweet?text={encoded_message}",
        "email": f"mailto:?subject={encoded_title}&body={encoded_message}",
        "sms": f"sms:?body={encoded_message}"
    }

def generate_emergency_share_message(location):
    lat = location.get("lat", 28.6139)
    lon = location.get("lon", 77.2090)
    city = location.get("city", "Unknown")
    
    message = f"""🚨 EMERGENCY!

I need help!

📍 Location: {city}
🗺️ Map: https://www.google.com/maps?q={lat},{lon}
🕐 Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Please respond!"""
    
    return {
        "message": message,
        "links": generate_share_links("Emergency Alert", message, f"https://www.google.com/maps?q={lat},{lon}")
    }

def get_emergency_contacts():
    # Prefer file-based contacts if available, else fallback to ENV
    contacts_file = os.path.join(os.path.dirname(__file__), "contacts.json")
    contacts = []

    try:
        if os.path.exists(contacts_file):
            with open(contacts_file, "r", encoding="utf-8") as f:
                data = f.read().strip()
                if data:
                    loaded = json.loads(data)
                else:
                    loaded = []

            for c in loaded:
                phone = str(c.get("phone", "")).strip()
                if not phone:
                    continue
                contacts.append({
                    "name": c.get("name"),
                    "phone": phone,
                    "email": c.get("email"),
                    "whatsapp_link": generate_whatsapp_link(phone),
                    "call_link": generate_call_link(phone),
                    "sms_link": generate_sms_link(phone)
                })
            return contacts
    except Exception:
        pass

    # Fallback to environment variable list
    contacts_str = os.getenv("EMERGENCY_CONTACTS", "")
    for contact in contacts_str.split(","):
        contact = contact.strip()
        if contact:
            contacts.append({
                "phone": contact,
                "whatsapp_link": generate_whatsapp_link(contact),
                "call_link": generate_call_link(contact),
                "sms_link": generate_sms_link(contact)
            })
    return contacts


def save_emergency_contacts(contacts_list):
    """Save contacts_list (list of dicts with keys: phone, name, email) to contacts.json."""
    contacts_file = os.path.join(os.path.dirname(__file__), "contacts.json")
    try:
        to_save = []
        for c in contacts_list:
            entry = {
                "phone": str(c.get("phone", "")).strip()
            }
            if c.get("name"):
                entry["name"] = c.get("name")
            if c.get("email"):
                entry["email"] = c.get("email")
            to_save.append(entry)

        with open(contacts_file, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_weather_alert(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        current = data.get("current_weather", {})
        temp = current.get("temperature", "N/A")
        windspeed = current.get("windspeed", "N/A")
        
        code = current.get("weathercode", 0)
        weather_types = {
            0: "Clear ☀️", 1: "Mainly clear 🌤️", 2: "Partly cloudy ⛅",
            3: "Overcast ☁️", 45: "Foggy 🌫️", 61: "Rain 🌧️",
            71: "Snow ❄️", 95: "Thunderstorm ⛈️"
        }
        
        return {
            "temperature": f"{temp}°C",
            "windspeed": f"{windspeed} km/h",
            "condition": weather_types.get(code, "Unknown"),
            "alert": "Stay safe!" if code >= 61 else None
        }
    except:
        return None


def recognize_speech():
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("🎤 Listening...")
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        return r.recognize_google(audio)
    except ImportError:
        return "Error: Install SpeechRecognition - pip install SpeechRecognition pyaudio"
    except Exception as e:
        return f"Error: {e}"

def speak_text(text):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.8)

        # Try to set a voice (helps on Windows)
        voices = engine.getProperty('voices')
        if voices:
            # Try to find an English voice
            for voice in voices:
                if 'english' in voice.name.lower() or 'en' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break

        engine.say(text)
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"🔊 TTS Error: {e}")
        print(f"🔊 {text}")
        return False


def alert_all_targets(location, emergency_type):
    try:
        from alerts import trigger_all_alerts
        return trigger_all_alerts(emergency_type, location)
    except Exception as e:
        return {"error": str(e)}