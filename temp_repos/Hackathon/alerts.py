import os
import smtplib
import ssl
import certifi
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_WHATSAPP_NUMBER = "+14155238886"

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMERGENCY_EMAIL = os.getenv("EMERGENCY_EMAIL")
EMERGENCY_CONTACTS = os.getenv("EMERGENCY_CONTACTS", "").split(",")

from utils import get_emergency_contacts, generate_whatsapp_link


twilio_client = None
try:
    from twilio.rest import Client
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        print("✅ Twilio initialized successfully")
except Exception as e:
    print(f"❌ Twilio error: {e}")



def get_location_info():
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        loc = data.get("loc", "28.6139,77.2090")
        lat, lon = loc.split(",") if "," in loc else ("28.6139", "77.2090")
        return {
            "city": data.get("city", "Unknown"),
            "region": data.get("region", "Unknown"),
            "country": data.get("country", "IN"),
            "loc": loc,
            "lat": lat,
            "lon": lon,
            "ip": data.get("ip", "Unknown")
        }
    except:
        return {
            "city": "Unknown", "region": "Unknown", "country": "IN",
            "loc": "28.6139,77.2090", "lat": "28.6139", "lon": "77.2090", "ip": "Unknown"
        }



def build_alert_message(location, emergency_type="Emergency"):
    lat = location.get("lat", "")
    lon = location.get("lon", "")
    loc = location.get("loc", "")
    
    if lat and lon:
        map_link = f"https://www.google.com/maps?q={lat},{lon}"
        coords = f"{lat},{lon}"
    elif loc:
        map_link = f"https://www.google.com/maps?q={loc}"
        coords = loc
    else:
        map_link = "Location unavailable"
        coords = "N/A"

    return f"""🚨 EMERGENCY ALERT 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Emergency Type: {emergency_type}

📍 LOCATION DETAILS:
   🏙️ City: {location.get('city', 'Unknown')}
   🗺️ Region: {location.get('region', 'Unknown')}
   🌍 Country: {location.get('country', 'Unknown')}
   📌 Coordinates: {coords}

🗺️ GOOGLE MAPS LINK:
   {map_link}

🕐 TIME: {datetime.now().strftime("%d-%m-%Y %H:%M:%S")}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆘 PLEASE RESPOND IMMEDIATELY!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sent via Pharmacy Operations AI Assistant
"""



def send_sms(to_number, message):
    global twilio_client
    if not twilio_client:
        # Try REST API fallback if credentials present
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
            try:
                to_clean = to_number.strip().replace(" ", "").replace("-", "")
                if not to_clean.startswith("+"):
                    to_clean = "+" + to_clean
                url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
                data = {"From": TWILIO_PHONE_NUMBER, "To": to_clean, "Body": message}
                resp = requests.post(url, data=data, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=10)
                if resp.status_code in (200,201):
                    j = resp.json()
                    return {"status": "sent", "sid": j.get("sid"), "to": to_clean}
                return {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text}"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "error", "message": "Twilio not configured"}

    try:
        to_clean = to_number.strip().replace(" ", "").replace("-", "")
        if not to_clean.startswith("+"):
            to_clean = "+" + to_clean

        msg = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_clean
        )
        print(f"✅ SMS sent to {to_clean} | SID: {msg.sid}")
        return {"status": "sent", "sid": msg.sid, "to": to_clean}
    except Exception as e:
        error = str(e)
        # Detect Twilio nested module import error and disable Twilio client to avoid repeated failures
        if "auth_registrations_credential_list_mapping" in error or isinstance(e, ModuleNotFoundError):
            print(f"❌ SMS Twilio module error detected; disabling Twilio: {error}")
            twilio_client = None
            # Attempt REST API fallback
            if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
                try:
                    to_clean = to_number.strip().replace(" ", "").replace("-", "")
                    if not to_clean.startswith("+"):
                        to_clean = "+" + to_clean
                    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
                    data = {"From": TWILIO_PHONE_NUMBER, "To": to_clean, "Body": message}
                    resp = requests.post(url, data=data, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=10)
                    if resp.status_code in (200,201):
                        j = resp.json()
                        return {"status": "sent", "sid": j.get("sid"), "to": to_clean}
                    return {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text}"}
                except Exception as e2:
                    return {"status": "error", "message": str(e2)}
            return {"status": "error", "message": "Twilio internal module error; Twilio disabled"}

        print(f"❌ SMS Error: {error}")
        if "21614" in error or "unverified" in error.lower():
            return {"status": "error", "message": "Phone not verified in Twilio"}
        return {"status": "error", "message": error}


def send_whatsapp(to_number, message):
    global twilio_client
    if not twilio_client:
        # Try REST API fallback for WhatsApp if credentials present
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
            try:
                to_clean = to_number.strip().replace(" ", "").replace("-", "")
                if not to_clean.startswith("+"):
                    to_clean = "+" + to_clean
                url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
                data = {"From": f"whatsapp:{TWILIO_PHONE_NUMBER}", "To": f"whatsapp:{to_clean}", "Body": message}
                resp = requests.post(url, data=data, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=10)
                if resp.status_code in (200,201):
                    j = resp.json()
                    return {"status": "sent", "sid": j.get("sid"), "to": to_clean}
                return {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text}"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        return {"status": "error", "message": "Twilio not configured"}

    try:
        to_clean = to_number.strip().replace(" ", "").replace("-", "")
        if not to_clean.startswith("+"):
            to_clean = "+" + to_clean

        msg = twilio_client.messages.create(
            body=message,
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{to_clean}"
        )
        print(f"✅ WhatsApp sent to {to_clean} | SID: {msg.sid}")
        return {"status": "sent", "sid": msg.sid, "to": to_clean}
    except Exception as e:
        error = str(e)
        if "auth_registrations_credential_list_mapping" in error or isinstance(e, ModuleNotFoundError):
            print(f"❌ WhatsApp Twilio module error detected; disabling Twilio: {error}")
            twilio_client = None
            # Attempt REST API fallback for WhatsApp
            if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
                try:
                    to_clean = to_number.strip().replace(" ", "").replace("-", "")
                    if not to_clean.startswith("+"):
                        to_clean = "+" + to_clean
                    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
                    # Use the known WhatsApp sandbox number for the From field
                    data = {"From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}", "To": f"whatsapp:{to_clean}", "Body": message}
                    resp = requests.post(url, data=data, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=10)
                    if resp.status_code in (200,201):
                        j = resp.json()
                        return {"status": "sent", "sid": j.get("sid"), "to": to_clean}
                    return {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text}"}
                except Exception as e2:
                    return {"status": "error", "message": str(e2)}
            return {"status": "error", "message": "Twilio internal module error; Twilio disabled"}

        print(f"❌ WhatsApp Error: {error}")
        if "63007" in error:
            return {"status": "error", "message": "WhatsApp Sandbox not joined"}
        return {"status": "error", "message": error}


def make_emergency_call(to_number):
    global twilio_client
    if not twilio_client:
        return {"status": "error", "message": "Twilio not configured"}

    twiml = """
    <Response>
        <Say voice="Polly.Aditi" language="hi-IN">
            इमरजेंसी अलर्ट! यूजर को तुरंत मदद चाहिए। कृपया मैसेज चेक करें।
        </Say>
        <Pause length="1"/>
        <Say voice="Polly.Joanna" language="en-US">
            Emergency Alert! The user needs immediate help. Check your messages.
        </Say>
    </Response>
    """

    try:
        to_clean = to_number.strip().replace(" ", "").replace("-", "")
        if not to_clean.startswith("+"):
            to_clean = "+" + to_clean

        call = twilio_client.calls.create(
            twiml=twiml,
            from_=TWILIO_PHONE_NUMBER,
            to=to_clean
        )
        print(f"✅ Call initiated to {to_clean} | SID: {call.sid}")
        return {"status": "initiated", "sid": call.sid, "to": to_clean}
    except Exception as e:
        error = str(e)
        if "auth_registrations_credential_list_mapping" in error or isinstance(e, ModuleNotFoundError):
            print(f"❌ Call Twilio module error detected; disabling Twilio: {error}")
            twilio_client = None
            return {"status": "error", "message": "Twilio internal module error; Twilio disabled"}

        print(f"❌ Call Error: {e}")
        return {"status": "error", "message": str(e)}



def send_email(subject, message, to_email=None):
    """Send email with SSL fix for macOS"""
    
    if not EMAIL_ADDRESS:
        return {"status": "error", "message": "EMAIL_ADDRESS not set"}
    
    if not EMAIL_PASSWORD:
        return {"status": "error", "message": "EMAIL_PASSWORD not set. Create App Password at: https://myaccount.google.com/apppasswords"}
    
    if to_email is None:
        to_email = EMERGENCY_EMAIL if EMERGENCY_EMAIL else EMAIL_ADDRESS

    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["X-Priority"] = "1"

       
        msg.attach(MIMEText(message, "plain", "utf-8"))

       
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <div style="background: linear-gradient(135deg, #ff416c, #ff4b2b); color: white; padding: 30px; text-align: center;">
                    <h1 style="margin: 0;">🚨 EMERGENCY ALERT 🚨</h1>
                </div>
                <div style="padding: 30px;">
                    <pre style="white-space: pre-wrap; font-family: Arial; font-size: 14px; line-height: 1.6; background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #ff416c;">{message}</pre>
                </div>
                <div style="background: #333; color: white; padding: 15px; text-align: center; font-size: 12px;">
                    Sent by Pharmacy Operations AI Assistant
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html", "utf-8"))

        print(f"📧 Connecting to Gmail SMTP...")
        
        
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}")
            return {"status": "sent", "to": to_email}
            
        except Exception as e1:
            print(f"⚠️ Method 1 failed: {e1}")
            
            
            try:
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                    server.send_message(msg)
                
                print(f"✅ Email sent to {to_email} (Method 2)")
                return {"status": "sent", "to": to_email}
                
            except Exception as e2:
                print(f"⚠️ Method 2 failed: {e2}")
                
                
                try:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    
                    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    print(f"✅ Email sent to {to_email} (Method 3)")
                    return {"status": "sent", "to": to_email}
                    
                except Exception as e3:
                    print(f"❌ All methods failed: {e3}")
                    raise e3

    except smtplib.SMTPAuthenticationError:
        return {
            "status": "error",
            "message": "Gmail login failed! Create App Password: https://myaccount.google.com/apppasswords"
        }
    except Exception as e:
        print(f"❌ Email Error: {e}")
        return {"status": "error", "message": str(e)}



def trigger_all_alerts(emergency_type="Emergency", custom_location=None):
    print("\n" + "="*50)
    print("🚨 TRIGGERING EMERGENCY ALERTS")
    print("="*50)
    
    if custom_location:
        location = {
            "city": custom_location.get("city", "Unknown"),
            "region": custom_location.get("region", "Unknown"),
            "country": custom_location.get("country", "IN"),
            "loc": custom_location.get("loc", f"{custom_location.get('lat', 28.6139)},{custom_location.get('lon', 77.2090)}"),
            "lat": str(custom_location.get("lat", 28.6139)),
            "lon": str(custom_location.get("lon", 77.2090)),
            "ip": custom_location.get("ip", "Unknown")
        }
    else:
        location = get_location_info()
    
    print(f"📍 Location: {location.get('city')}, {location.get('region')}")
    
    message = build_alert_message(location, emergency_type)
    
    results = {
        "location": location,
        "timestamp": datetime.now().isoformat(),
        "emergency_type": emergency_type,
        "alerts": {},
        "summary": {"total": 0, "success": 0, "failed": 0}
    }

    contacts = get_emergency_contacts()
    for c in contacts:
        contact = c.get("phone", "").strip()
        email_addr = c.get("email")
        if not contact:
            continue
        if not contact.startswith("+"):
            contact = "+" + contact

        print(f"\n📱 Processing: {contact}")

        # SMS
        print("  📤 SMS...")
        sms = send_sms(contact, message)
        results["alerts"][f"sms_{contact}"] = sms
        results["summary"]["total"] += 1
        results["summary"]["success" if sms.get("status") == "sent" else "failed"] += 1

        # WhatsApp (attempt via Twilio, fallback to wa.me link)
        print("  📤 WhatsApp...")
        wa = send_whatsapp(contact, message)
        results["alerts"][f"whatsapp_{contact}"] = wa
        results["summary"]["total"] += 1
        if wa.get("status") == "sent":
            results["summary"]["success"] += 1
        else:
            results["summary"]["failed"] += 1
            try:
                wa_link = generate_whatsapp_link(contact, message)
                results["alerts"][f"whatsapp_link_{contact}"] = {"status": "link_generated", "link": wa_link}
            except Exception as e:
                results["alerts"][f"whatsapp_link_{contact}"] = {"status": "error", "message": str(e)}

        # Call
        print("  📤 Call...")
        call = make_emergency_call(contact)
        results["alerts"][f"call_{contact}"] = call
        results["summary"]["total"] += 1
        results["summary"]["success" if call.get("status") == "initiated" else "failed"] += 1

        # Email per-contact (if provided)
        if email_addr:
            print("  📧 Email to contact...")
            em = send_email(f"🚨 EMERGENCY: {emergency_type}", message, to_email=email_addr)
            results["alerts"][f"email_{email_addr}"] = em
            results["summary"]["total"] += 1
            results["summary"]["success" if em.get("status") == "sent" else "failed"] += 1

    # Final summary
    print("\n" + "="*50)
    print("📊 ALERT SUMMARY")
    print("="*50)
    print(f"   Total: {results['summary']['total']}")
    print(f"   ✅ Success: {results['summary']['success']}")
    print(f"   ❌ Failed: {results['summary']['failed']}")
    print("="*50 + "\n")

    return results