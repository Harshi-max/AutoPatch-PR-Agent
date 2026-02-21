import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


AGENT_CONFIGS = {
    "🏥 Pharmacy Operations Assistant": {
        "system": """You are an expert Pharmacy Operations AI Assistant.
        - Explain prescription handling rules and procedures
        - Clarify medicine storage guidelines and safety protocols
        - Describe dispensing rules and regulatory requirements
        - Provide information about pharmacy operations and workflows
        IMPORTANT: You do NOT diagnose conditions, recommend medications, or provide medical advice.
        Focus only on operational procedures, safety guidelines, and regulatory explanations.""",
        "color": "#FF6B6B"
    },
    "📋 Prescription Guide": {
        "system": """You are a Prescription Handling & Interpretation Specialist AI.
        - Explain prescription validation and verification processes
        - Describe controlled substance handling requirements
        - Clarify prescription labeling and documentation rules
        - Provide guidance on prescription transfer procedures
        - When given the text of a prescription, help the user understand WHAT is written:
          • Identify medicine names, strengths, dosage frequency, duration, and special instructions
          • Explain operational handling rules for those medicines (e.g., storage, controlled status)
        IMPORTANT LIMITS:
        - Do NOT change the prescribed regimen, dosage, or frequency
        - Do NOT recommend alternative medicines or diagnose conditions
        - Do NOT give therapeutic advice; stay strictly with explanation and operational guidance.""",
        "color": "#4ECDC4"
    },
    "💊 Medicine Storage Advisor": {
        "system": """You are a Medicine Storage and Safety AI Advisor.
        - Explain proper medicine storage conditions (temperature, light, humidity)
        - Describe expiration date handling and disposal procedures
        - Provide guidelines for different medication types (liquids, tablets, injectables)
        - Clarify safety protocols for hazardous medications
        IMPORTANT: Focus only on storage guidelines, not medication usage or effects.""",
        "color": "#45B7D1"
    },
    "🏪 Dispensing Specialist": {
        "system": """You are a Dispensing Rules AI Specialist.
        - Explain step-by-step dispensing procedures
        - Describe accuracy checking and verification protocols
        - Provide guidance on patient counseling requirements
        - Clarify regulatory compliance for dispensing operations
        IMPORTANT: You do NOT recommend medications or provide therapeutic advice.""",
        "color": "#96CEB4"
    }
}

class SimpleAgent:
    def __init__(self, name, system_prompt):
        self.name = name
        self.system_prompt = system_prompt
        self.history = []
    
    def chat(self, user_message):
        try:
            # Try Grok first for pharmacy operations
            from groq import Groq
            client = Groq(api_key=GROQ_API_KEY)

            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.history,
                {"role": "user", "content": user_message}
            ]

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )

            reply = response.choices[0].message.content

            self.history.append({"role": "user", "content": user_message})
            self.history.append({"role": "assistant", "content": reply})

            return reply

        except Exception as e:
            # Fallback response if Grok fails
            fallback_reply = f"I apologize, but I'm experiencing technical difficulties. Please try again or contact support. Error: {str(e)}"
            return fallback_reply
    
    def clear_history(self):
        self.history = []

def get_agents():
    agents = {}
    for name, config in AGENT_CONFIGS.items():
        agents[name] = SimpleAgent(name, config["system"])
    return agents

def analyze_image_with_agent(agent, image_path, query):
    try:
        # Check if image file exists
        if not os.path.exists(image_path):
            return agent.chat(f"I cannot access the uploaded image. User query: {query}. Please provide general guidance about prescription handling.")

        # Check if Grok API key is available
        groq_key = os.getenv("GROQ_API_KEY", "")
        if not groq_key:
            return agent.chat(f"Grok API key not configured. User query: {query}. Please provide general guidance about prescription handling.")

        # Try OCR + Grok analysis for prescription images
        from groq import Groq
        import PIL.Image
        import easyocr

        # Load and validate the image
        try:
            image = PIL.Image.open(image_path)
            # Convert to RGB if necessary for better OCR
            if image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
        except Exception as img_error:
            return agent.chat(f"I cannot process the uploaded image (error: {str(img_error)}). User query: {query}. Please describe the prescription or provide general guidance about prescription handling.")

        # Extract text using EasyOCR
        try:
            # Initialize the OCR reader (English language)
            reader = easyocr.Reader(['en'])
            # Convert PIL image to numpy array for EasyOCR
            import numpy as np
            image_array = np.array(image)
            # Extract text
            results = reader.readtext(image_array)
            # Combine all detected text
            extracted_text = ' '.join([result[1] for result in results if result[1].strip()])
            # Clean up the extracted text
            extracted_text = extracted_text.strip()
            if not extracted_text:
                extracted_text = "No text could be extracted from the image. The image may be unclear, contain no readable text, or the prescription may be handwritten in a way that's difficult to recognize."
        except Exception as ocr_error:
            extracted_text = f"OCR failed to extract text from image (error: {str(ocr_error)}). The prescription image could not be read."

        # Create Grok client
        client = Groq(api_key=groq_key)

        # Create comprehensive analysis + Q&A prompt
        analysis_prompt = f"""
        You are analyzing a prescription using OCR-extracted text.

        IMPORTANT REMINDERS:
        - You do NOT diagnose conditions, recommend medications, or provide medical advice.
        - Focus ONLY on: what is written on the prescription, how to handle/store those medicines,
          and regulatory / operational guidance.
        - Always emphasize following pharmacy regulations and consulting licensed pharmacists.

        User query (answer this directly at the end, using ONLY the prescription text plus general
        operational rules): {query}

        OCR-extracted text from the prescription image:
        ---
        {extracted_text}
        ---

        1) First, extract a structured summary from the OCR text (if present):
           - Patient name (if visible)
           - Prescriber name / clinic (if visible)
           - Date (if visible)
           - For each medicine you can identify, list:
             • name
             • strength (e.g., 500 mg)
             • dosage instructions (e.g., 1 tablet twice daily)
             • duration (e.g., 5 days)
             • any special notes (e.g., after food, at night, PRN)

        2) Then, based on that structured summary, answer the user's question
           SPECIFICALLY about THIS prescription. If the question asks for
           something that is not visible in the OCR text, clearly say that you
           cannot see it on the prescription and suggest the user ask a
           licensed pharmacist for clarification.

        3) Finally, briefly mention any operational / safety / storage rules
           that apply to the medicines you identified (e.g., controlled
           substance handling, cold-chain storage) WITHOUT changing the
           prescribed regimen.

        If the OCR text is unclear, incomplete, or empty, say that the
        prescription could not be reliably read and give general guidance on
        how to validate and handle prescriptions, asking the user to upload a
        clearer image or type what is written.
        """

        # Get analysis from Grok
        messages = [
            {"role": "system", "content": agent.system_prompt},
            {"role": "user", "content": analysis_prompt}
        ]

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024
        )

        analysis = response.choices[0].message.content

        # Add disclaimer to analysis
        disclaimer = "\n\n⚠️ **Important**: This analysis is based on OCR-extracted text from the image and may not be 100% accurate due to image quality, handwriting, or other factors. Always consult a licensed pharmacist and follow local regulations for actual prescription processing."

        full_response = analysis + disclaimer

        # Add to agent history
        agent.history.append({"role": "user", "content": f"Image analysis request: {query}"})
        agent.history.append({"role": "assistant", "content": full_response})

        return full_response

    except Exception as e:
        # Enhanced error reporting for debugging
        error_msg = f"Image analysis failed: {str(e)}"
        print(f"DEBUG: {error_msg}")  # This will show in console

        # Fallback to text-only analysis with error context
        fallback_prompt = f"""I encountered an issue analyzing the prescription image (technical error: {str(e)}).

        User query: {query}

        Since I cannot analyze the image directly, please:
        1. Describe what you see in the prescription image
        2. Ask specific questions about prescription handling procedures
        3. Inquire about regulatory requirements or safety guidelines

        Remember: I can provide general guidance about pharmacy operations, prescription validation, medicine storage, and dispensing rules, but always consult a licensed pharmacist for specific prescription processing."""

        return agent.chat(fallback_prompt)

def get_agent_color(agent_name):
    return AGENT_CONFIGS.get(agent_name, {}).get("color", "#667eea")