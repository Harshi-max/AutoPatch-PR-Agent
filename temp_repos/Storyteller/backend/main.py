from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import requests
import random
import os
from gtts import gTTS
import io
import base64
from typing import Optional

app = FastAPI(title="StoryShort API")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000", "https://*.replit.dev", "https://*.replit.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class ScriptRequest(BaseModel):
    prompt: str
    length: Optional[str] = "short"  # short, medium, long
    voice: Optional[str] = "en"

class VideoRequest(BaseModel):
    script: str
    voice: Optional[str] = "en"

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.get("/")
async def root():
    return {"message": "StoryShort API is running"}

@app.post("/api/generate-script")
async def generate_script(request: ScriptRequest):
    """Generate a script from user prompt using DeepSeek Chat"""
    try:
        # Prepare the prompt for script generation
        system_prompt = f"""You are a creative storyteller specializing in creating engaging, viral-worthy short video scripts. 
        Create a compelling narrative script that would work well for a {request.length} video (30-60 seconds for short, 60-90 seconds for medium, 90-180 seconds for long).
        
        Guidelines:
        - Start with a hook that grabs attention immediately
        - Use vivid, descriptive language that paints a picture
        - Include emotional elements that connect with viewers
        - Keep sentences short and impactful for voice narration
        - End with a memorable conclusion or cliffhanger
        - Write in a conversational, engaging tone
        - Focus on storytelling elements that work well with visuals
        
        Return only the script text, no additional formatting or explanations."""
        
        # Use OpenRouter with DeepSeek Chat
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek/deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.8
        }
        
        if OPENROUTER_API_KEY:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                script = result["choices"][0]["message"]["content"].strip()
            else:
                # Fallback to a simple script generation
                script = f"Here's an interesting story about {request.prompt}. This captivating tale will take you on a journey through fascinating events and memorable moments. The story unfolds with unexpected twists and engaging characters that will keep you hooked until the very end."
        else:
            # Fallback when no API key is provided
            script = f"Here's an interesting story about {request.prompt}. This captivating tale will take you on a journey through fascinating events and memorable moments. The story unfolds with unexpected twists and engaging characters that will keep you hooked until the very end."
        
        return {"script": script, "success": True}
        
    except Exception as e:
        print(f"Script generation error: {e}")
        # Return a fallback script
        fallback_script = f"Here's an interesting story about {request.prompt}. This captivating tale will take you on a journey through fascinating events and memorable moments."
        return {"script": fallback_script, "success": True, "fallback": True}

@app.post("/api/generate-audio")
async def generate_audio(request: VideoRequest):
    """Generate audio from script using gTTS"""
    try:
        # Create TTS audio
        voice_lang = request.voice or "en"
        tts = gTTS(text=request.script, lang=voice_lang, slow=False)
        
        # Save to bytes buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Convert to base64 for frontend
        audio_base64 = base64.b64encode(audio_buffer.getvalue()).decode()
        
        return {
            "audio_data": audio_base64,
            "duration": len(request.script) * 0.1,  # Rough estimation
            "success": True
        }
        
    except Exception as e:
        print(f"Audio generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

@app.get("/api/random-media")
async def get_random_media():
    """Get random selection of images and videos"""
    # Sample CC0 images from Unsplash/Pexels
    images = [
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&h=1080&fit=crop",
        "https://images.unsplash.com/photo-1519904981063-b0cf448d479e?w=1920&h=1080&fit=crop", 
        "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=1920&h=1080&fit=crop"
    ]
    
    # Sample CC0 videos from Pexels
    videos = [
        "https://cdn.pixabay.com/vimeo/720459042/clouds-132348.mp4",
        "https://cdn.pixabay.com/vimeo/720459041/ocean-132347.mp4",
        "https://cdn.pixabay.com/vimeo/720459040/forest-132346.mp4"
    ]
    
    selected_media = {
        "image": random.choice(images),
        "video": random.choice(videos),
        "success": True
    }
    
    return selected_media

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)