from interview.speech_to_text import record_audio, transcribe_with_groq
from interview.text_to_speech import  text_to_speech_with_gtts
from interview.captool import analyze_image_with_query
from interview.conversation import take_interview, sanitize_content
import os 
import datetime
import threading
import time

def read_resume_file(resume_path):
    """Read resume content from file"""
    try:
        with open(resume_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading resume: {str(e)}"

def play_audio_async(text, use_elevenlabs=True):
    """Play audio in a separate thread"""
    def play_audio():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_file = f"temp_audio_{timestamp}.mp3"
        text_to_speech_with_gtts(text, audio_file)
            
        time.sleep(2)
        if os.path.exists(audio_file):
            os.remove(audio_file)
    
    thread = threading.Thread(target=play_audio)
    thread.daemon = True
    thread.start()

def get_vision_context():
    """Get vision context from camera"""
    try:
        query = "Analyze this person during interview: body language, confidence, eye contact, appearance. Keep brief."
        return analyze_image_with_query(query)
    except Exception as e:
        return f"Vision unavailable: {str(e)}"