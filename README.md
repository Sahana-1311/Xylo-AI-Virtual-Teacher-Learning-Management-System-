# Xylo – AI Virtual Teacher & Learning Management System(Full Stack)

An AI-powered virtual teacher integrated with a Learning Management System for personalised student support.

## Overview
Xylo assists students with personalised learning by combining conversational AI with backend LMS workflows.

## Key Features
- AI-powered virtual teacher with real-time query handling
- Backend workflows and APIs for user interactions and response generation
- Conversational AI for student queries using prompt-based response generation
- LMS integration for tracking and personalised learning paths

## Tech Stack
Python · REST APIs · AI Applications · Prompt Engineering# Xylo-AI-Virtual-Teacher-Learning-Management-System-

Flask Routing & URLs MapBased on your current Python code, here is how your application's URLs are structured. If your Flask app runs locally on the default port (http://127.0.0.1:5000), your endpoints map out like this:Route PathFull Local URLHTTP MethodWhat it does/http://127.0.0.1:5000/GETLoads the main user interface (index.html)/processhttp://127.0.0.1:5000/processPOSTAccepts the audio file (audio_data), runs STT, calls the LLM, creates the TTS file, and returns JSON/static/response.wavhttp://127.0.0.1:5000/static/response.wavGETThe Audio URL: Flask automatically serves this file from your static/ directory so the frontend can play back the teacher's voice
