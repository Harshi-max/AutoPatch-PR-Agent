# StoryShort.ai Clone

## Overview
A Next.js and FastAPI application that replicates the core functionality of StoryShort.ai, allowing users to generate viral faceless videos from text prompts using AI.

## Current Status (September 12, 2025)
Successfully implemented core features:
- ✅ FastAPI backend with script generation, text-to-speech, and media selection
- ✅ Next.js frontend with Mantine UI components
- ✅ Remotion video composition and player functionality
- ✅ OpenRouter DeepSeek integration for AI script generation
- ✅ CC0 media assets from Unsplash/Pexels
- ✅ Export functionality (metadata download)

## Project Architecture

### Backend (FastAPI - Port 8000)
- `/api/generate-script` - AI script generation using DeepSeek Chat
- `/api/generate-audio` - Text-to-speech using gTTS
- `/api/random-media` - Random CC0 image/video selection

### Frontend (Next.js - Port 5000)
- Main form for user input (prompt, length, voice)
- Video composition using Remotion
- Export functionality for generated content
- Mantine UI components for styling

## User Preferences
- Clean, professional UI using Mantine components
- Fallback functionality when APIs are unavailable
- Free/open source integrations preferred
- Video preview using Remotion player

## Recent Changes
- Fixed CORS configuration for local development
- Updated DeepSeek model to valid OpenRouter endpoint
- Implemented video export as metadata JSON
- Added CC0 media assets for demonstration

## Known Issues
- API connectivity between frontend/backend may require manual testing
- Full video rendering requires additional FFmpeg setup
- Export currently provides metadata instead of actual video file

## Next Steps
- Implement full video rendering with @remotion/renderer
- Add health check for backend connectivity
- Enhance error handling and user feedback
