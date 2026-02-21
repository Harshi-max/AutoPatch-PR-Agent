import streamlit as st
import os
import json
import folium
from datetime import datetime
from streamlit_folium import st_folium
from PIL import Image
from urllib.parse import quote
import time
import warnings

# Suppress Pydantic ArbitraryTypeWarning from google.genai
warnings.filterwarnings("ignore", message=".*<built-in function any> is not a Python type.*", category=UserWarning)

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from agents import get_agents, analyze_image_with_agent, get_agent_color
from utils import (
    recognize_speech,
    speak_text,
    get_nearby_services,
    alert_all_targets,
    get_user_location,
    detect_emergency,
    get_emergency_numbers,
    generate_whatsapp_link,
    generate_whatsapp_emergency_link,
    get_whatsapp_sandbox_join_link,
    generate_google_maps_link,
    generate_call_link,
    generate_sms_link,
    get_health_tips,
    get_first_aid_tips,
    get_common_medicines,
    generate_emergency_share_message,
    get_emergency_contacts,
    save_emergency_contacts,
    get_weather_alert,
    get_emergency_level_info,
    generate_directions_link
)

st.set_page_config(
    page_title="Pharmacy Operations AI Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


def trigger_rerun():
    """Try to rerun Streamlit. If `st.experimental_rerun` is unavailable,
    fallback to updating query params to force a reload."""
    try:
        # Preferred if available
        st.experimental_rerun()
    except Exception:
        try:
            params = dict(st.query_params)
            params["_rerun"] = [str(int(time.time()))]
            st.query_params = params
        except Exception:
            # Last resort: set a session_state flag
            st.session_state["_need_rerun"] = True

@st.cache_data(ttl=300, show_spinner=False)
def get_cached_services(lat, lon, service_type):
    location = {"lat": lat, "lon": lon}
    return get_nearby_services(location, service_type)

def get_all_services(location, service_types):
    all_services = []
    lat = location.get("lat", 28.6139)
    lon = location.get("lon", 77.2090)
    
    for stype in service_types:
        try:
            services = get_cached_services(lat, lon, stype)
            if services:
                all_services.extend(services)
        except Exception as e:
            print(f"Error fetching {stype}: {e}")
    
    return all_services


# Emergency contacts management in Sidebar
with st.sidebar.expander("Emergency Contacts", expanded=True):
    st.markdown("""
    **Manage Emergency Contacts**

    Add phone numbers (with country code), optional name and email.
    These are stored locally in `contacts.json`.
    """)

    contacts = get_emergency_contacts()

    # Display existing contacts with remove option
    to_keep = contacts.copy()
    if "remove_idx" not in st.session_state:
        st.session_state["remove_idx"] = None

    for idx, c in enumerate(contacts):
        label = f"{c.get('name') + ' - ' if c.get('name') else ''}{c.get('phone')}"
        cols = st.columns([4,1])
        cols[0].write(label)
        if cols[1].button("Remove", key=f"remove_{idx}"):
            st.session_state["remove_idx"] = idx
            break

    # If removal requested, apply and save
    if st.session_state.get("remove_idx") is not None:
        ridx = st.session_state.get("remove_idx")
        if 0 <= ridx < len(to_keep):
            removed = to_keep.pop(ridx)
            ok = save_emergency_contacts(to_keep)
            if ok:
                st.success(f"Removed {removed.get('phone')}")
            else:
                st.error("Failed to remove contact.")
        st.session_state["remove_idx"] = None
        trigger_rerun()

    st.markdown("---")
    with st.form(key="add_contact_form"):
        new_name = st.text_input("Name (optional)")
        new_phone = st.text_input("Phone (include +countrycode)")
        new_email = st.text_input("Email (optional)")
        submitted = st.form_submit_button("Add / Save Contacts")

    if submitted:
        if new_phone and new_phone.strip():
            to_keep.append({"name": new_name.strip() or None, "phone": new_phone.strip(), "email": new_email.strip() or None})
            ok = save_emergency_contacts(to_keep)
            if ok:
                st.success("Contacts saved to contacts.json")
                trigger_rerun()
            else:
                st.error("Failed saving contacts. Check permissions.")
        else:
            st.warning("Please provide a phone number before saving.")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .block-container {
        padding-top: 1rem;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 40px 30px;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        position: relative;
        overflow: hidden;
    }
    
    .header-glow {
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 60%);
        pointer-events: none;
    }
    
    .header-title {
        color: white;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        position: relative;
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.85);
        margin: 15px 0 25px 0;
        font-size: 1.1rem;
        position: relative;
    }
    
    .tech-badges {
        display: flex;
        justify-content: center;
        gap: 12px;
        flex-wrap: wrap;
        position: relative;
    }
    
    .tech-badge {
        padding: 10px 20px;
        border-radius: 30px;
        color: white;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
    }
    
    .badge-camel {
        background: linear-gradient(135deg, #667eea, #764ba2);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .badge-groq {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
    }
    
    .badge-twilio {
        background: linear-gradient(135deg, #4facfe, #00f2fe);
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
    }
    
    .badge-whatsapp {
        background: linear-gradient(135deg, #25D366, #128C7E);
        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.4);
    }
    
    .stat-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 20px;
        border-radius: 15px;
        color: #ffffff !important;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 5px 20px rgba(17, 153, 142, 0.3);
    }
    
    .stat-card h1, .stat-card h2, .stat-card h3, .stat-card h4, .stat-card p {
        color: #ffffff !important;
        margin: 5px 0;
        text-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    
    .info-card {
        background: #ffffff;
        padding: 18px 22px;
        border-radius: 12px;
        border-left: 5px solid #667eea;
        margin: 12px 0;
        color: #1a1a2e !important;
        font-size: 15px;
        line-height: 1.6;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
    }
    
    .info-card b, .info-card strong {
        color: #302b63 !important;
        font-weight: 700;
    }
    
    .location-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        padding: 18px 22px;
        border-radius: 14px;
        border: 2px solid #667eea;
        margin: 12px 0;
        color: #1a1a2e !important;
        font-size: 15px;
        line-height: 1.8;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.15);
    }
    
    .location-card b {
        color: #302b63 !important;
        font-weight: 700;
        font-size: 16px;
    }
    
    .emergency-card {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: #ffffff !important;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 5px 20px rgba(255, 65, 108, 0.3);
    }
    
    .emergency-card h3, .emergency-card p {
        color: #ffffff !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    
    .service-card {
        background: #ffffff;
        padding: 18px 22px;
        border-radius: 14px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
        margin: 12px 0;
        border-left: 5px solid #667eea;
        transition: transform 0.2s, box-shadow 0.2s;
        color: #1a1a2e !important;
        font-size: 15px;
        line-height: 1.6;
    }
    
    .service-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.18);
    }
    
    .service-card b, .service-card strong {
        color: #302b63 !important;
        font-weight: 700;
        font-size: 16px;
    }
    
    .chat-ai {
        background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
        padding: 20px 25px;
        border-radius: 18px 18px 18px 4px;
        margin: 12px 0;
        border: 2px solid #e0e0e0;
        color: #1a1a2e !important;
        font-size: 15px;
        line-height: 1.7;
        box-shadow: 0 3px 15px rgba(0,0,0,0.08);
    }
    
    .action-btn {
        display: block;
        padding: 15px 20px;
        border-radius: 12px;
        text-decoration: none;
        text-align: center;
        margin: 8px 0;
        color: #ffffff !important;
        font-weight: 600;
        font-size: 14px;
        transition: transform 0.2s, box-shadow 0.2s;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    
    .action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
        text-decoration: none;
        color: #ffffff !important;
    }
    
    .whatsapp-btn {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 100%);
    }
    
    .call-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .sms-btn {
        background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
    }
    
    .maps-btn {
        background: linear-gradient(135deg, #4285F4 0%, #1a73e8 100%);
    }
    
    .emergency-btn {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
    }
    
    .tip-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: #ffffff !important;
        padding: 28px 18px;
        border-radius: 16px;
        text-align: center;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 6px 25px rgba(17, 153, 142, 0.35);
        margin: 8px 0;
    }
    
    .tip-card h1 {
        font-size: 48px;
        margin-bottom: 12px;
    }
    
    .tip-card p {
        color: #ffffff !important;
        font-size: 14px;
        font-weight: 500;
        margin: 0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.15);
    }
    
    .weather-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #ffffff !important;
        padding: 28px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.35);
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .weather-card h2, .weather-card h3, .weather-card p {
        color: #ffffff !important;
        margin: 5px 0;
        text-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    
    .medicine-card {
        background: #ffffff;
        padding: 18px 22px;
        border-radius: 14px;
        border-left: 5px solid #4CAF50;
        margin: 12px 0;
        color: #1a1a2e !important;
        font-size: 15px;
        line-height: 1.6;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
    }
    
    .medicine-card b, .medicine-card strong {
        color: #2e7d32 !important;
        font-weight: 700;
        font-size: 16px;
    }
    
    .medicine-card small {
        color: #555555 !important;
        font-size: 13px;
    }
    
    .status-success {
        background: #d4edda;
        border: 2px solid #28a745;
        color: #155724 !important;
        padding: 14px 18px;
        border-radius: 10px;
        margin: 8px 0;
        font-weight: 500;
    }
    
    .status-error {
        background: #f8d7da;
        border: 2px solid #dc3545;
        color: #721c24 !important;
        padding: 14px 18px;
        border-radius: 10px;
        margin: 8px 0;
        font-weight: 500;
    }
    
    .sidebar-header {
        text-align: center;
        padding: 10px 0;
    }
    
    .emergency-numbers {
        background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%);
        padding: 18px;
        border-radius: 14px;
        color: #ffffff !important;
        font-size: 14px;
        line-height: 1.8;
        box-shadow: 0 4px 20px rgba(252, 74, 26, 0.3);
    }
    
    .emergency-numbers b {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    .services-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #ffffff !important;
        padding: 18px 25px;
        border-radius: 14px;
        text-align: center;
        margin: 15px 0;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    .services-header h3 {
        color: #ffffff !important;
        margin: 0;
        font-size: 18px;
        text-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    
    .health-section-title {
        background: linear-gradient(135deg, #302b63 0%, #24243e 100%);
        color: #ffffff !important;
        padding: 15px 22px;
        border-radius: 12px;
        margin: 15px 0 10px 0;
        font-size: 18px;
        font-weight: 600;
        box-shadow: 0 3px 15px rgba(0,0,0,0.2);
    }
    
    .warning-card {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        border: 2px solid #ffc107;
        border-left: 5px solid #ff9800;
        color: #856404 !important;
        padding: 18px 22px;
        border-radius: 12px;
        margin: 12px 0;
        font-size: 15px;
        font-weight: 500;
    }
    
    .cpr-card {
        background: linear-gradient(135deg, #e91e63 0%, #9c27b0 100%);
        color: #ffffff !important;
        padding: 30px;
        border-radius: 18px;
        text-align: center;
        margin: 15px 0;
        box-shadow: 0 6px 30px rgba(233, 30, 99, 0.35);
    }
    
    .cpr-card h2, .cpr-card p {
        color: #ffffff !important;
        margin: 8px 0;
        text-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    
    .level-card {
        padding: 15px 20px;
        border-radius: 12px;
        margin: 12px 0;
        font-size: 15px;
        font-weight: 500;
        border-left: 5px solid;
    }
    
    .stButton > button {
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "data/incidents.json"
os.makedirs("data", exist_ok=True)

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_incident(category, query, response, location=None, image_name=None):
    data = load_data()
    data.append({
        "id": len(data) + 1,
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "query": query,
        "response": response[:500] if response else "",
        "location": location,
        "image": image_name
    })
    save_data(data)

def create_emergency_map(user_location, services_list=None):
    lat = user_location.get("lat", 28.6139)
    lon = user_location.get("lon", 77.2090)
    
    if services_list is None:
        services_list = []

    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="OpenStreetMap")

    folium.Marker(
        [lat, lon],
        popup="📍 Your Location",
        tooltip="You are here",
        icon=folium.Icon(color="orange", icon="home", prefix="fa")
    ).add_to(m)

    styles = {
        "hospital": {"color": "blue", "icon": "plus-square"},
        "police": {"color": "darkblue", "icon": "shield"},
        "fire_station": {"color": "orange", "icon": "fire-extinguisher"},
        "pharmacy": {"color": "green", "icon": "medkit"},
        "clinic": {"color": "lightblue", "icon": "stethoscope"}
    }

    for service in services_list:
        style = styles.get(service.get("type", "hospital"), {"color": "gray", "icon": "info"})
        directions_url = f"https://www.google.com/maps/dir/{lat},{lon}/{service.get('lat', lat)},{service.get('lng', lon)}"
        
        popup_html = f"""
        <div style='width:220px; font-family: Arial;'>
            <b style='font-size: 14px; color: #333;'>{service.get('name', 'Unknown')}</b><br><br>
            <span style='color: #555;'>📞 {service.get('phone', 'N/A')}</span><br>
            <span style='color: #555;'>📍 {service.get('address', 'N/A')}</span><br><br>
            <a href="{directions_url}" target="_blank" style="
                background: #4285F4;
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                text-decoration: none;
                display: inline-block;
                font-weight: bold;
            ">🚗 Get Directions</a>
        </div>
        """
        
        try:
            folium.Marker(
                [service.get("lat", lat), service.get("lng", lon)],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=service.get('name', 'Service'),
                icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa")
            ).add_to(m)
        except:
            pass

    folium.Circle(
        [lat, lon], radius=2000, color="#667eea", fill=True, fill_opacity=0.1
    ).add_to(m)

    return m

if "user_query" not in st.session_state:
    st.session_state.user_query = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_location" not in st.session_state:
    st.session_state.user_location = get_user_location()
if "emergency_mode" not in st.session_state:
    st.session_state.emergency_mode = False
if "map_key" not in st.session_state:
    st.session_state.map_key = 0

st.markdown("""
<div class="main-header">
    <div class="header-glow"></div>
    <h1 class="header-title">🏥 Pharmacy Operations AI Assistant</h1>
    <p class="header-subtitle">Your intelligent pharmacy operations and safety guidelines assistant • Available 24/7</p>
    <div class="tech-badges">
        <span class="tech-badge badge-camel">🤖 CAMEL AI</span>
        <span class="tech-badge badge-groq">⚡ Groq LLM</span>
        <span class="tech-badge badge-twilio">📱 Twilio</span>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-header">', unsafe_allow_html=True)
    st.image("https://img.icons8.com/clouds/200/hospital.png", width=80)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.title("⚙️ Control Panel")
    
    agents = get_agents()
    selected_agent = st.selectbox(
        "🤖 Select AI Agent",
        list(agents.keys()),
        help="Choose the type of assistance you need"
    )
    
    st.divider()
    
    st.subheader("🎤 Voice Controls")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎙️ Speak", use_container_width=True, key="voice_btn"):
            with st.spinner("🎤 Listening..."):
                voice_text = recognize_speech()
                if voice_text and not voice_text.startswith("Error"):
                    st.session_state.user_query = voice_text
                    st.success(f"✅ {voice_text}")
                else:
                    st.error("❌ Could not recognize")
    
    with col2:
        if st.button("🔊 Test", use_container_width=True, key="tts_btn"):
            speak_text("Pharmacy Operations Assistant is ready")
            st.success("✅ Audio OK")
    
    st.divider()
    
    st.subheader("📍 Your Location")
    loc = st.session_state.user_location
    
    st.markdown(f"""
    <div class="location-card">
        🏙️ <b>{loc.get('city', 'Unknown')}</b><br>
        🗺️ <span style="color: #444;">{loc.get('region', 'Unknown')}</span><br>
        🌍 <span style="color: #444;">{loc.get('country', 'Unknown')}</span><br>
        📌 <span style="color: #666; font-size: 13px;">Lat: {loc.get('lat', 'N/A'):.4f}, Lon: {loc.get('lon', 'N/A'):.4f}</span>
    </div>
    """, unsafe_allow_html=True)
    
    maps_link = generate_google_maps_link(loc.get('lat'), loc.get('lon'))
    st.markdown(f'<a href="{maps_link}" target="_blank" class="action-btn maps-btn">🗺️ View on Maps</a>', unsafe_allow_html=True)
    
    if st.button("🔄 Refresh Location", use_container_width=True, key="refresh_loc"):
        st.session_state.user_location = get_user_location()
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    st.subheader("📞 Emergency Numbers")
    country = loc.get("country", "IN")
    numbers = get_emergency_numbers().get(country, get_emergency_numbers()["default"])
    
    emergency_display = "<div class='emergency-numbers'>"
    icons = {"police": "🚔", "ambulance": "🚑", "fire": "🚒", "emergency": "🆘"}
    for name, number in list(numbers.items())[:4]:
        icon = icons.get(name, "📞")
        emergency_display += f"{icon} <b>{name.title()}</b>: {number}<br>"
    emergency_display += "</div>"
    st.markdown(emergency_display, unsafe_allow_html=True)
    
    st.divider()
    
    st.subheader("💬 WhatsApp")
    wa_emergency = generate_whatsapp_emergency_link(loc)
    if wa_emergency:
        st.markdown(f'<a href="{wa_emergency}" target="_blank" class="action-btn whatsapp-btn">💬 Emergency WhatsApp</a>', unsafe_allow_html=True)
    
    sandbox = get_whatsapp_sandbox_join_link()
    with st.expander("🔧 Setup WhatsApp"):
        st.markdown(f"""
        1. Click button below
        2. Send: `join <your-code>`
        3. Get code from [Twilio](https://console.twilio.com/)
        """)
        st.markdown(f'<a href="{sandbox["link"]}" target="_blank" class="action-btn emergency-btn" style="font-size: 12px;">📱 Join Sandbox</a>', unsafe_allow_html=True)
    
    st.divider()
    
    st.subheader("🚨 Emergency SOS")
    if st.button("🆘 SEND SOS ALERT", use_container_width=True, type="primary", key="sos_btn"):
        st.session_state.emergency_mode = True
        with st.spinner("📡 Sending alerts..."):
            result = alert_all_targets(st.session_state.user_location, "SOS - Emergency Alert")
        
        st.success("✅ Alerts Sent!")
        
        alerts = result.get("alerts", {})
        for key, value in alerts.items():
            status = value.get("status", "unknown")
            if status in ["sent", "initiated"]:
                st.markdown(f'<div class="status-success">✅ {key}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="status-error">❌ {key}</div>', unsafe_allow_html=True)

        # Show summary counts
        summary = result.get("summary", {})
        total = summary.get("total", 0)
        success = summary.get("success", 0)
        failed = summary.get("failed", 0)

        cols = st.columns(3)
        cols[0].metric("Total Alerts", total)
        cols[1].metric("Successful", success)
        cols[2].metric("Failed", failed)

        # Expandable full result for debugging
        with st.expander("Full alert result (JSON)"):
            st.json(result)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "💬 AI Chat",
    "🗺️ Pharmacy Locator",
    "📱 Quick Actions",
    "💊 Pharmacy Guide",
    "📋 History",
    "🩹 Safety Protocols"
])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Describe Your Situation")
        
        uploaded_image = st.file_uploader(
            "📷 Upload Image (optional)",
            type=["jpg", "jpeg", "png"],
            key="image_upload"
        )
        
        if uploaded_image:
            img = Image.open(uploaded_image)
            st.image(img, caption="Uploaded Image", width=300)
        
        user_query = st.text_area(
            "What's happening?",
            value=st.session_state.user_query,
            height=120,
            placeholder="Ask about prescription rules, medicine storage, or dispensing procedures...",
            key="query_input"
        )
        
        c1, c2, c3, c4 = st.columns(4)
        get_advice = c1.button("🔍 Get Advice", use_container_width=True, type="primary", key="advice_btn")
        emergency_btn = c2.button("🚨 Emergency", use_container_width=True, key="emergency_btn")
        show_map = c3.button("🗺️ Find Help", use_container_width=True, key="find_help_btn")
        clear_btn = c4.button("🗑️ Clear", use_container_width=True, key="clear_btn")
        
        if clear_btn:
            st.session_state.user_query = ""
            st.session_state.chat_history = []
            try:
                agents[selected_agent].clear_history()
            except:
                pass
            st.rerun()
        
        if get_advice or emergency_btn:
            if not user_query.strip():
                st.error("⚠️ Please describe your situation first!")
            else:
                agent = agents[selected_agent]
                level, keyword = detect_emergency(user_query)
                level_info = get_emergency_level_info(level)
                
                st.markdown(f"""
                <div class="level-card" style="background: {level_info['color']}15; border-color: {level_info['color']}; color: #333;">
                    {level_info['emoji']} <b style="color: {level_info['color']};">Emergency Level: {level.upper()}</b> — {level_info['action']}
                </div>
                """, unsafe_allow_html=True)
                
                with st.spinner("🤖 AI is analyzing..."):
                    try:
                        if uploaded_image:
                            # Save uploaded image temporarily for analysis
                            import tempfile
                            import os

                            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_image.name)[1]) as tmp_file:
                                tmp_file.write(uploaded_image.getvalue())
                                temp_image_path = tmp_file.name

                            try:
                                response = analyze_image_with_agent(agent, temp_image_path, user_query)
                            finally:
                                # Clean up temporary file
                                try:
                                    os.unlink(temp_image_path)
                                except:
                                    pass
                        else:
                            response = agent.chat(user_query)
                    except Exception as e:
                        response = f"Error: {str(e)}. Please try again or call emergency services."
                
                st.subheader("🤖 AI Response")
                st.markdown(f'<div class="chat-ai">{response}</div>', unsafe_allow_html=True)
                
                st.session_state.chat_history.append({
                    "query": user_query,
                    "response": response,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "level": level
                })
                
                if emergency_btn or level in ["high", "critical"]:
                    st.warning("⚠️ Emergency Detected!")
                    
                    with st.spinner("🔍 Finding nearby services..."):
                        services = get_all_services(loc, ["hospital", "police", "pharmacy"])
                    
                    if services:
                        m = create_emergency_map(loc, services)
                        st.session_state.map_key += 1
                        st_folium(m, width=700, height=400, key=f"em_map_{st.session_state.map_key}")
                    
                    with st.spinner("📡 Sending alerts..."):
                        result = alert_all_targets(loc, f"Emergency: {keyword or user_query[:50]}")
                    
                    st.success("✅ Emergency alerts sent!")
                    with st.expander("📋 Alert Details"):
                        st.json(result)
                
                save_incident(selected_agent, user_query, response, loc, uploaded_image.name if uploaded_image else None)
                
                if st.checkbox("🔊 Read aloud", key="tts_response"):
                    speak_text(response[:500])
        
        if show_map:
            st.subheader("🗺️ Nearby Services")
            with st.spinner("🔍 Finding..."):
                services = get_all_services(loc, ["hospital", "police", "pharmacy", "fire_station"])
            
            m = create_emergency_map(loc, services)
            st.session_state.map_key += 1
            st_folium(m, width=700, height=450, key=f"help_map_{st.session_state.map_key}")
            
            if services:
                st.markdown(f'<div class="services-header"><h3>📋 Found {len(services)} Services Nearby</h3></div>', unsafe_allow_html=True)
                for s in services[:8]:
                    icons = {"hospital": "🏥", "police": "🚔", "fire_station": "🚒", "pharmacy": "💊"}
                    phone = s.get('phone', 'N/A')
                    address = s.get('address', 'Address not available')
                    st.markdown(f"""
                    <div class="service-card">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 24px;">{icons.get(s.get('type', ''), '📍')}</span>
                            <div>
                                <b>{s.get('name', 'Unknown')}</b><br>
                                <span style="color: #555;">📞 {phone}</span><br>
                                <span style="color: #777; font-size: 13px;">📍 {address[:50]}...</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("⚡ Quick Reports")
        
        quick_reports = [
            ("🔥 Fire", "Fire emergency! Need immediate help."),
            ("🩹 Medical", "Medical emergency, need assistance."),
            ("🚔 Crime", "Crime situation, I'm in danger!"),
            ("🚗 Accident", "Road accident with injuries."),
            ("💊 Overdose", "Drug overdose, need help now."),
            ("❤️ Heart Attack", "Heart attack symptoms: chest pain."),
        ]
        
        for idx, (label, text) in enumerate(quick_reports):
            if st.button(label, use_container_width=True, key=f"quick_{idx}"):
                st.session_state.user_query = text
                st.rerun()
        
        st.divider()
        
        st.subheader("💬 Recent Chats")
        if st.session_state.chat_history:
            for chat in reversed(st.session_state.chat_history[-5:]):
                level_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(chat.get("level", "low"), "⚪")
                with st.expander(f"{level_emoji} {chat['time']}"):
                    st.write(f"**You:** {chat['query'][:100]}...")
                    st.write(f"**AI:** {chat['response'][:200]}...")
        else:
            st.info("No chats yet")

with tab2:
    st.subheader("🗺️ Pharmacy & Healthcare Locator")
    
    col1, col2, col3, col4 = st.columns(4)
    show_hospitals = col1.checkbox("🏥 Hospitals", value=True, key="chk_hosp")
    show_pharmacy = col2.checkbox("💊 Pharmacies", value=True, key="chk_pharm")
    show_police = col3.checkbox("🚔 Police", value=False, key="chk_pol")
    show_fire = col4.checkbox("🚒 Fire", value=False, key="chk_fire")
    
    service_types = []
    if show_hospitals: service_types.append("hospital")
    if show_pharmacy: service_types.append("pharmacy")
    if show_police: service_types.append("police")
    if show_fire: service_types.append("fire_station")
    
    if service_types:
        with st.spinner("🔍 Loading..."):
            services = get_all_services(loc, service_types)
        
        m = create_emergency_map(loc, services)
        st_folium(m, width=None, height=500, key="main_map")
        
        if services:
            st.markdown(f'<div class="services-header"><h3>📋 Found {len(services)} Services</h3></div>', unsafe_allow_html=True)
            
            cols = st.columns(3)
            for i, service in enumerate(services):
                with cols[i % 3]:
                    icons = {"hospital": "🏥", "police": "🚔", "fire_station": "🚒", "pharmacy": "💊"}
                    svc_type = service.get('type', 'unknown')
                    st.markdown(f"""
                    <div class="service-card">
                        <span style="font-size: 22px;">{icons.get(svc_type, '📍')}</span>
                        <b> {service.get('name', 'Unknown')}</b><br>
                        <span style="color: #555;">📞 {service.get('phone', 'N/A')}</span><br>
                        <span style="color: #888; font-size: 12px;">Type: {svc_type.replace('_', ' ').title()}</span>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Select at least one service type to display on map")
        m = create_emergency_map(loc, [])
        st_folium(m, width=None, height=500, key="empty_map")

with tab3:
    st.subheader("📱 Quick Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="health-section-title">📞 Emergency Calls</div>', unsafe_allow_html=True)
        country = loc.get("country", "IN")
        numbers = get_emergency_numbers().get(country, get_emergency_numbers()["default"])
        
        for name, number in numbers.items():
            icons = {"police": "🚔", "ambulance": "🚑", "fire": "🚒", "emergency": "🆘", "women_helpline": "👩", "child_helpline": "👶"}
            icon = icons.get(name, "📞")
            st.markdown(f'<a href="tel:{number}" class="action-btn call-btn">{icon} {name.replace("_", " ").title()}: {number}</a>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="health-section-title">💬 WhatsApp Actions</div>', unsafe_allow_html=True)
        
        wa_link = generate_whatsapp_emergency_link(loc)
        if wa_link:
            st.markdown(f'<a href="{wa_link}" target="_blank" class="action-btn whatsapp-btn">🆘 Emergency WhatsApp</a>', unsafe_allow_html=True)
        
        share_data = generate_emergency_share_message(loc)
        st.markdown(f'<a href="{share_data["links"]["whatsapp"]}" target="_blank" class="action-btn whatsapp-btn">📍 Share My Location</a>', unsafe_allow_html=True)
        
        sandbox = get_whatsapp_sandbox_join_link()
        st.markdown(f'<a href="{sandbox["link"]}" target="_blank" class="action-btn emergency-btn">🔗 Join WhatsApp Sandbox</a>', unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown('<div class="health-section-title">📍 Share Your Location</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    maps_link = generate_google_maps_link(loc.get('lat'), loc.get('lon'))
    
    with col1:
        st.markdown(f'<a href="{maps_link}" target="_blank" class="action-btn maps-btn">🗺️ Google Maps</a>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<a href="{share_data["links"]["whatsapp"]}" target="_blank" class="action-btn whatsapp-btn">💬 WhatsApp</a>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<a href="{share_data["links"]["sms"]}" class="action-btn sms-btn">📱 SMS</a>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<a href="{maps_link}" target="_blank" class="action-btn call-btn">📧 Email</a>', unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown('<div class="health-section-title">🌤️ Current Weather</div>', unsafe_allow_html=True)
    weather = get_weather_alert(loc.get('lat'), loc.get('lon'))
    if weather:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'''
            <div class="weather-card">
                <h2 style="font-size: 40px; margin: 0;">{weather.get("icon", "🌤️")}</h2>
                <h3>{weather["condition"]}</h3>
            </div>
            ''', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="weather-card">
                <h3 style="font-size: 28px;">🌡️ {weather["temperature"]}</h3>
                <p>Temperature</p>
            </div>
            ''', unsafe_allow_html=True)
        with col3:
            st.markdown(f'''
            <div class="weather-card">
                <h3 style="font-size: 28px;">💨 {weather["windspeed"]}</h3>
                <p>Wind Speed</p>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("Weather data unavailable")
    
    st.divider()
    
    st.markdown('<div class="health-section-title">💡 Daily Pharmacy Tips</div>', unsafe_allow_html=True)
    tips = get_health_tips()
    cols = st.columns(len(tips))
    for i, tip in enumerate(tips):
        with cols[i]:
            st.markdown(f"""
            <div class="tip-card">
                <h1>{tip['icon']}</h1>
                <p><b>{tip.get('title', '')}</b></p>
                <p>{tip['tip']}</p>
            </div>
            """, unsafe_allow_html=True)

with tab4:
    st.subheader("💊 Pharmacy Operations Guide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="health-section-title">📋 Prescription Handling Rules</div>', unsafe_allow_html=True)
        st.markdown('<div class="warning-card">⚠️ <b>Important:</b> Always follow regulatory guidelines. This is for informational purposes only.</div>', unsafe_allow_html=True)
        
        prescription_rules = {
            "validation": {
                "name": "Prescription Validation",
                "rules": "Verify prescription authenticity, check for completeness, validate prescriber credentials, ensure prescription is current and not expired."
            },
            "controlled": {
                "name": "Controlled Substances",
                "rules": "Maintain separate storage, require additional verification, document chain of custody, follow DEA regulations for Schedule I-V drugs."
            },
            "labeling": {
                "name": "Labeling Requirements",
                "rules": "Include patient name, drug name/strength, directions, prescriber name, pharmacy info, date filled, expiration date, and auxiliary labels."
            },
            "transfers": {
                "name": "Prescription Transfers",
                "rules": "Verify prescription validity, obtain patient consent, contact original pharmacy, document transfer, maintain records for regulatory compliance."
            }
        }
        
        for rule_id, rule in prescription_rules.items():
            with st.expander(f"📋 {rule['name']}"):
                st.markdown(f"""
                <div style="color: #333; line-height: 1.8;">
                    <p><b style="color: #4CAF50;">Guidelines:</b> {rule['rules']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="health-section-title">💊 Medicine Storage Guidelines</div>', unsafe_allow_html=True)
        storage_rules = [
            ("🌡️ Temperature Control", "Store most medications at room temperature (59-86°F). Refrigerate items requiring cold storage. Avoid freezing unless specified."),
            ("💧 Humidity Protection", "Keep medications in cool, dry places. Use desiccants in pill bottles if needed. Avoid bathroom storage due to moisture."),
            ("☀️ Light Protection", "Store light-sensitive medications in original containers. Keep away from direct sunlight and fluorescent lighting."),
            ("👶 Child Safety", "Store all medications in locked cabinets or high shelves. Use child-resistant containers. Keep poisons separate from medications."),
            ("📅 Expiration Monitoring", "Check expiration dates regularly. Discard expired medications properly. Never use medications past their expiration date."),
            ("🔒 Security Measures", "Secure controlled substances in locked safes. Maintain inventory logs. Report any thefts or losses immediately.")
        ]
        for rule_title, rule_desc in storage_rules:
            st.markdown(f'''
            <div class="medicine-card">
                <b>{rule_title}</b><br>
                <small style="color: #555;">{rule_desc}</small>
            </div>
            ''', unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown('<div class="health-section-title">🏥 Pharmacy Best Practices</div>', unsafe_allow_html=True)
    tips = [
        {"icon": "�", "title": "Double Check", "tip": "Always verify prescriptions twice before dispensing"},
        {"icon": "📋", "title": "Documentation", "tip": "Maintain accurate records for all controlled substances"},
        {"icon": "🕐", "title": "Time Management", "tip": "Process prescriptions within regulatory timeframes"},
        {"icon": "🎯", "title": "Accuracy First", "tip": "Zero tolerance for medication dispensing errors"},
        {"icon": "🧠", "title": "Continuous Learning", "tip": "Stay updated with latest pharmacy regulations"},
        {"icon": "🤝", "title": "Patient Focus", "tip": "Clear communication improves medication adherence"},
    ]
    
    cols = st.columns(3)
    for i, tip in enumerate(tips):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="stat-card">
                <h1 style="font-size: 48px; margin: 0;">{tip['icon']}</h1>
                <h4 style="margin: 10px 0 5px 0;">{tip['title']}</h4>
                <p style="font-size: 14px; margin: 0;">{tip['tip']}</p>
            </div>
            """, unsafe_allow_html=True)

with tab5:
    st.subheader("📋 Incident History")
    
    logs = load_data()
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🗑️ Clear All History", key="clear_logs"):
            save_data([])
            st.success("✅ History cleared!")
            st.rerun()
    
    if logs:
        st.markdown(f'''
        <div class="services-header">
            <h3>📊 Total Incidents Recorded: {len(logs)}</h3>
        </div>
        ''', unsafe_allow_html=True)
        
        for log in reversed(logs[-20:]):
            timestamp = log.get('timestamp', '')[:16].replace('T', ' ')
            with st.expander(f"📝 #{log.get('id', '?')} | {timestamp}"):
                st.markdown(f"""
                <div style="color: #333; line-height: 1.8;">
                    <p><b style="color: #667eea;">Category:</b> {log.get('category', 'N/A')}</p>
                    <p><b style="color: #11998e;">Query:</b> {log.get('query', 'N/A')}</p>
                    <p><b style="color: #764ba2;">Response:</b> {log.get('response', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-card">
            📭 <b>No incidents recorded yet.</b><br>
            <span style="color: #666;">Your incident history will appear here after you use the AI chat feature.</span>
        </div>
        """, unsafe_allow_html=True)

with tab6:
    st.subheader("🩹 Pharmacy Safety Protocols")
    
    st.markdown("""
    <div class="emergency-card">
        <h3 style="margin-top: 0;">⚠️ Important Disclaimer</h3>
        <p style="margin-bottom: 0;">This guide provides pharmacy safety and operational protocols. Always follow your pharmacy's policies and local regulations. Contact regulatory authorities for compliance questions.</p>
    </div>
    """, unsafe_allow_html=True)
    
    safety_protocols = {
        "🏥 Dispensing Safety": {
            "steps": "1. Verify prescription authenticity and completeness\n2. Check for drug interactions and allergies\n3. Count medications accurately\n4. Provide clear labeling and instructions\n5. Counsel patient on proper usage",
            "color": "#e91e63"
        },
        "🔒 Controlled Substances": {
            "steps": "1. Maintain secure storage with double locks\n2. Document all transactions meticulously\n3. Verify patient identity for Schedule II-V drugs\n4. Report suspicious activities immediately\n5. Conduct regular inventory audits",
            "color": "#f44336"
        },
        "🧪 Hazardous Materials": {
            "steps": "1. Store in designated hazardous waste containers\n2. Wear appropriate PPE during handling\n3. Follow spill cleanup procedures\n4. Dispose through authorized medical waste services\n5. Maintain Material Safety Data Sheets (MSDS)",
            "color": "#ff5722"
        },
        "📋 Documentation": {
            "steps": "1. Record all prescription information accurately\n2. Maintain patient counseling records\n3. Document adverse drug reactions\n4. Keep inventory logs current\n5. Retain records for regulatory compliance periods",
            "color": "#9c27b0"
        },
        "🚨 Emergency Response": {
            "steps": "1. Know location of emergency equipment\n2. Have poison control numbers readily available\n3. Train staff in emergency procedures\n4. Maintain first aid kits and AED access\n5. Establish emergency communication protocols",
            "color": "#ffc107"
        },
        "🛡️ Personal Safety": {
            "steps": "1. Never work alone during off-hours\n2. Be aware of suspicious customer behavior\n3. Have clear view of all pharmacy areas\n4. Use security cameras and alarm systems\n5. Follow robbery prevention protocols",
            "color": "#ff9800"
        },
    }
    
    cols = st.columns(2)
    for i, (title, data) in enumerate(safety_protocols.items()):
        with cols[i % 2]:
            with st.expander(title, expanded=False):
                st.markdown(f"""
                <div style="color: #333; line-height: 1.8; padding: 10px 0;">
                    {data['steps'].replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("""
    <div class="cpr-card">
        <h2 style="margin-top: 0;">🏥 Regulatory Compliance: Key Principles</h2>
        <p style="font-size: 20px;"><b>P</b>atient Safety → <b>A</b>ccurate Dispensing → <b>B</b>est Practices</p>
        <p style="font-size: 16px; margin-bottom: 0;">Always verify: <b>Right drug, Right dose, Right patient, Right time</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="health-section-title">📚 Pharmacy Compliance Resources</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="stat-card">
            <h1>🏛️</h1>
            <h4>FDA Guidelines</h4>
            <p>Official regulatory standards</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="stat-card">
            <h1>📋</h1>
            <h4>Pharmacy Manual</h4>
            <p>Operational procedures guide</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="stat-card">
            <h1>🔬</h1>
            <h4>DEA Resources</h4>
            <p>Controlled substances guidelines</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.markdown("""
<div style="text-align: center; padding: 20px; color: #666;">
    <p>🏥 <b>Pharmacy Operations AI Assistant</b> | Built with ❤️ for pharmacy safety and compliance</p>
    <p style="font-size: 12px;">Powered by Gemini Flash, Groq LLM & CAMEL AI</p>
</div>
""", unsafe_allow_html=True)