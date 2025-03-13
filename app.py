from flask import Flask, request, jsonify, send_file, render_template
import os
import tempfile
import uuid
import requests
from datetime import datetime, timedelta
import schedule
import time
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder='frontend')

# Répertoire pour stocker les fichiers audio temporaires
AUDIO_TEMP_DIR = os.path.join(tempfile.gettempdir(), 'audio_files')
os.makedirs(AUDIO_TEMP_DIR, exist_ok=True)

# Identifiants API PlayHT
API_URL = "https://api.play.ht/api/v2/tts/stream"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('PLAYHT_API_KEY')}",
    "X-User-ID": os.getenv("PLAYHT_USER_ID"),
    "Content-Type": "application/json"
}

# Mapping des voix
VOICE_MAPPING = {
    "s3://voice-cloning-zero-shot/da861ac7-44d1-41c2-bdd7-5579b07e46de/original/manifest.json": "Vintage Radio",
    "s3://voice-cloning-zero-shot/87cd4c73-38a1-4ccd-9c34-f52ab84efc0d/original/manifest.json": "Preacher",
    "s3://voice-cloning-zero-shot/b16ae1b8-371b-4feb-b890-9995fdb48e36/original/manifest.json": "40s Movie Star",
    "s3://voice-cloning-zero-shot/ff240cd0-de2b-4c6c-8634-f802be2a73e0/original/manifest.json": "Old Rastaman",
    "s3://voice-cloning-zero-shot/26c2de86-1c4f-4e33-9950-767f9f0b07ad/original/manifest.json": "Film Noir",
    "s3://voice-cloning-zero-shot/988aab38-552c-4fa4-88ce-37538ba0c71b/original/manifest.json": "Epic Trailer",
    "s3://voice-cloning-zero-shot/4725cfd5-943a-4927-b8d5-90d99cbaf4fd/original/manifest.json": "Funky",
    "s3://voice-cloning-zero-shot/a0b0002b-952d-44b6-ac6f-33c4751f4b8b/original/manifest.json": "Vintage Documentary",
    "s3://voice-cloning-zero-shot/d69c5b6a-83e3-4f02-9daa-78c33e1a0cc4/original/manifest.json": "Italian Mafiosi",
    "s3://voice-cloning-zero-shot/2b82ecbf-d4b3-4a8e-a492-f14aef010de7/original/manifest.json": "Grandma"
}

# Nettoyage des fichiers audio temporaires
def clean_temp_files():
    now = datetime.now()
    for filename in os.listdir(AUDIO_TEMP_DIR):
        file_path = os.path.join(AUDIO_TEMP_DIR, filename)
        if (now - datetime.fromtimestamp(os.path.getmtime(file_path))) > timedelta(hours=1):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier {file_path}: {e}")

schedule.every(1).hours.do(clean_temp_files)

def run_pending():
    while True:
        schedule.run_pending()
        time.sleep(1)

Thread(target=run_pending, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    data = request.json
    voice_model_path = data.get('voiceModelPath')
    text = data.get('text')
    
    if not voice_model_path or not text:
        return jsonify({'error': 'Paramètres manquants'}), 400
    
    voice_name = VOICE_MAPPING.get(voice_model_path)
    if not voice_name:
        return jsonify({'error': 'Voix non supportée'}), 400
    
    # Définition des paramètres
    output_format = "wav"
    speed = float(data.get("speed", 1))
    temperature = float(data.get("temperature", 1.5))
    text_guidance = float(data.get("text_guidance", 1.5))
    voice_guidance = float(data.get("voice_guidance", 1.5))
    style_guidance = float(data.get("style_guidance", 7))
    emotion = data.get("emotion", "")  # Récupération de la valeur de emotion

    # Définition du voice_engine en fonction de la valeur de emotion
    if emotion:
        voice_engine = "PlayHT2.0"
    else:
        voice_engine = "Play3.0-mini"

    # Construction des paramètres pour l'API PlayHT
    params = {
        "voice_engine": voice_engine,
        "output_format": output_format,
        "text": text,
        "voice": voice_model_path,
        "speed": speed,
        "temperature": temperature,
        "text_guidance": text_guidance,
        "voice_guidance": voice_guidance,
        "style_guidance": style_guidance
    }

    # Ajout du paramètre emotion uniquement s'il n'est pas vide
    if emotion:
        params["emotion"] = emotion
    
    print(f"Params {params}")
    
    try:
        response = requests.post(API_URL, json=params, headers=HEADERS, stream=True)
        if response.status_code != 200:
            return jsonify({'error': f"Erreur API PlayHT: {response.text}"}), 500
        
        file_id = str(uuid.uuid4())
        file_path = os.path.join(AUDIO_TEMP_DIR, f'{file_id}.mp3')
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        return jsonify({'audio_url': f'/serve-audio/{file_id}.mp3'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/serve-audio/<filename>')
def serve_audio(filename):
    file_path = os.path.join(AUDIO_TEMP_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Fichier non trouvé'}), 404
    try:
        return send_file(file_path, mimetype='audio/mpeg', as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'envoi du fichier: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)