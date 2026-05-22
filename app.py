import os
import subprocess
import requests
import pyttsx3
from flask import Flask, render_template, request, jsonify
from faster_whisper import WhisperModel
from dotenv import load_dotenv
from openai import OpenAI
import wave
import tempfile
import uuid
import io

FFMPEG_PATH = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"

# ---------------- LOAD ENV ----------------
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = None
if openai_api_key:
    try:
        client = OpenAI(api_key=openai_api_key)
    except Exception as e:
        print(f"Warning: Could not initialize OpenAI client: {e}")
else:
    print("Warning: OPENAI_API_KEY not set. ChatGPT features will be disabled.")

app = Flask(__name__)

# ---------------- LOAD STT ----------------
stt_model = None

def get_stt_model():
    global stt_model
    if stt_model is None:
        print("Loading speech recognition model... This may take a moment on first run.")
        try:
            stt_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
            print("Whisper model loaded successfully!")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            try:
                stt_model = WhisperModel("tiny", device="cpu", compute_type="int8")
                print("Alternative Whisper model loaded successfully!")
            except Exception as e2:
                print(f"Error loading alternative Whisper model: {e2}")
                stt_model = None
    return stt_model

# ---------------- SPEECH TO TEXT ----------------
def speech_to_text(audio_path):
    model = get_stt_model()
    if model is None:
        raise Exception("Speech-to-text model is not loaded")
    segments, _ = model.transcribe(audio_path)
    return " ".join([seg.text for seg in segments]).strip()

# ---------------- INTERNET CHECK ----------------
def internet_available():
    try:
        requests.get("https://www.google.com", timeout=2)
        return True
    except:
        return False

# ---------------- FACT QUESTION ----------------
def is_fact_question(text):
    words = ["who", "when", "where", "year", "date", "capital"]
    return any(w in text.lower() for w in words)

# ---------------- WIKIPEDIA ----------------
def wiki_answer(query):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return r.json().get("extract")
    except:
        return None

# ---------------- CHATGPT ----------------
def chatgpt_answer(prompt):
    if client is None:
        raise Exception("OpenAI client not initialized. Please set OPENAI_API_KEY.")
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a friendly school teacher. Explain clearly and simply."},
            {"role": "user", "content": prompt}
        ]
    )
    return res.choices[0].message.content

# ---------------- LOCAL LLM ----------------
def local_llm(prompt):
    try:
        r = requests.post("http://localhost:11434/api/generate",
            json={
                "model": "llama3.1",
                "prompt": f"Explain clearly to a student:\n{prompt}",
                "stream": False
            }, timeout=10)
        return r.json()["response"]
    except requests.exceptions.ConnectionError:
        print("Ollama service not available.")
        return "I'm sorry, but the local AI service is not available. Please make sure Ollama is installed and running."
    except Exception as e:
        print(f"Error with local LLM: {e}")
        return "I'm sorry, but there was an error with the local AI service."

# ---------------- TEXT TO SPEECH ----------------
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 170)
    unique_filename = f"static/response_{uuid.uuid4().hex}.wav"
    engine.save_to_file(text, unique_filename)
    engine.runAndWait()
    return unique_filename

# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html", greeting="Hello! I am your AI Teacher.")

# ---------------- PROCESS AUDIO ----------------
@app.route("/process", methods=["POST"])
def process_audio():
    try:
        print("Processing audio request...")
        file = request.files["audio_data"]
        input_path = "temp/input.webm"
        wav_path = "temp/input.wav"

        file.save(input_path)
        print(f"Audio file saved to {input_path}")

        try:
            subprocess.run([
                FFMPEG_PATH, "-y", "-i", input_path,
                "-ar", "16000", "-ac", "1", wav_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print("Audio converted to WAV format using ffmpeg")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"FFmpeg error: {e}")
            try:
                text = speech_to_text(input_path)
                print("User:", text)
                answer = None
                if is_fact_question(text):
                    answer = wiki_answer(text)
                if not answer:
                    if internet_available():
                        try:
                            answer = chatgpt_answer(text)
                        except Exception as gpt_error:
                            print(f"GPT error: {gpt_error}")
                            answer = local_llm(text)
                    else:
                        answer = local_llm(text)
                if not answer:
                    answer = "I'm sorry, I couldn't find an answer to your question."
                print("AI:", answer)
                audio_file = speak(answer)
                return jsonify({"text": answer, "audio_url": "/" + audio_file})
            except Exception as stt_error:
                print(f"STT error: {stt_error}")
                return jsonify({"error": "Unable to process audio. Please install FFmpeg.", "details": str(stt_error)}), 500

        text = speech_to_text(wav_path)
        print("User:", text)

        answer = None
        if is_fact_question(text):
            answer = wiki_answer(text)

        if not answer:
            if internet_available():
                try:
                    answer = chatgpt_answer(text)
                    print("Source: ChatGPT")
                except Exception as gpt_error:
                    print(f"GPT error: {gpt_error}")
                    answer = local_llm(text)
            else:
                answer = local_llm(text)

        if not answer:
            answer = "Sorry, I couldn't find an answer to your question."

        print("AI:", answer)
        audio_file = speak(answer)

        return jsonify({"text": answer, "audio_url": "/" + audio_file})

    except Exception as e:
        print(f"General error: {e}")
        return jsonify({"error": "Processing failed", "details": str(e)}), 500

# ---------------- RUN ----------------
if __name__ == "__main__":
    os.makedirs("temp", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)
