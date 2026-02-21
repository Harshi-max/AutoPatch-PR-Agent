# 🏥 Pharmacy Operations AI Assistant

An intelligent Generative AI chatbot system that provides clear explanations of pharmacy operations, prescription handling rules, and medicine storage guidelines. Designed for pharmacy staff and customers to understand regulatory instructions and safety protocols.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- 🤖 **AI-Powered Chat** - Get instant explanations using Grok LLM
- 📋 **Prescription Guide** - Clear explanations of prescription handling rules
- 💊 **Medicine Storage** - Proper storage guidelines and safety protocols
- 🏪 **Dispensing Rules** - Step-by-step dispensing procedures and regulations
- 📱 **Quick Actions** - Emergency pharmacy services and contact information
- 🚨 **Safety Alerts** - Regulatory compliance and safety notifications
- 🩹 **First Aid Guide** - Basic emergency procedures (non-diagnostic)
- 💬 **Voice Support** - Speech recognition & text-to-speech
- 📍 **Location Services** - Find nearby pharmacies and healthcare facilities
- 📷 **Prescription Analysis** - Upload prescription images for AI-powered analysis

## 🎯 Domain Focus: Pharmacy / Healthcare Operations

This AI assistant specializes in **pharmacy operations and safety guidelines**, providing clear explanations for:

- **Prescription Handling**: Validation, verification, and transfer procedures
- **Medicine Storage**: Temperature control, light protection, and expiration management
- **Dispensing Rules**: Accuracy protocols, patient counseling, and regulatory compliance
- **Safety Protocols**: Hazardous materials handling, emergency response, and personal safety

### ⚠️ Important Notes
- **Non-Diagnostic**: The system does NOT provide medical advice or diagnose conditions
- **Regulatory Focus**: Emphasizes compliance with pharmacy regulations and best practices
- **Educational Purpose**: Designed to improve understanding of pharmacy operations

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Streamlit | Web UI Framework |
| Grok LLM | Fast AI Inference for text and vision |
| CAMEL AI | Multi-Agent AI Framework |
| Twilio | SMS, Calls, WhatsApp alerts |
| Folium | Interactive Maps |
| OpenStreetMap | Geolocation Services |

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/pharmacy-operations-ai-assistant.git
cd pharmacy-operations-ai-assistant
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file in the root directory:
```env
# Required API Keys
GROQ_API_KEY=your_groq_api_key_here

# Optional: For emergency communications
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Optional: For email alerts
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMERGENCY_EMAIL=emergency_contact@email.com
```

### 4. Get API Keys
- **Grok API Key**: Get from [Groq Console](https://console.groq.com/) - supports both text and vision models
- **Twilio** (optional): For SMS/WhatsApp alerts

### 5. Run the application
```bash
streamlit run app.py
```

### 6. Test the setup
Run this test script to verify everything is working:
```bash
python -c "
from dotenv import load_dotenv
load_dotenv()
import os
groq_key = os.getenv('GROQ_API_KEY', '')
print('✅ Groq API Key loaded:', bool(groq_key))
print('✅ Environment setup complete!')
"
```

## 🎯 Usage

1. **AI Chat**: Ask questions about prescription handling, medicine storage, or dispensing rules
2. **Prescription Analysis**: Upload prescription images and ask questions about validity, handling, or compliance
3. **Pharmacy Locator**: Find nearby pharmacies and healthcare facilities
4. **Quick Actions**: Emergency pharmacy services and regulatory contacts
5. **Pharmacy Guide**: Learn about prescription rules and medicine storage guidelines
6. **Safety Protocols**: Review pharmacy safety and compliance procedures

## 🔧 Troubleshooting

### Voice/Text-to-Speech Issues
If the "Read aloud" feature doesn't work:
- Ensure you have working audio drivers on your system
- Try restarting the application
- The feature uses `pyttsx3` which may require additional setup on some systems
- If TTS fails, the text will be displayed in the console with 🔊 prefix

### Map Loading Issues
- The map uses OpenStreetMap data which requires internet connection
- If no locations appear, check your internet connection
- Fallback locations are provided for offline/demo purposes

### API Key Issues
- Ensure your `GROQ_API_KEY` is correctly set in `.env`
- Check API key validity and quota limits

### Image Analysis Issues
- If image analysis falls back to text-only mode, check the console for debug messages
- Ensure the uploaded image is a clear JPG/PNG file under 10MB
- Verify that the Grok API key is properly configured
- The feature requires an active internet connection
- Check that `python-dotenv` is installed and `.env` file is in the project root