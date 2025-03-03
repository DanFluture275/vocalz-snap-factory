from flask import Flask, request, jsonify, Response, render_template, send_file
from pyht import Client, TTSOptions
from dotenv import load_dotenv
import os
import tempfile
import uuid
from datetime import datetime, timedelta
import schedule
import time
from threading import Thread

load_dotenv()

app = Flask(__name__, template_folder='frontend')

# Initialisation des clients PlayHT pour chaque voix
clients = {
    "Vintage Radio": Client(
        user_id=os.getenv("RADIO_USER_ID"),
        api_key=os.getenv("RADIO_API_KEY"),
    ),
    "Preacher": Client(
        user_id=os.getenv("PREECHEUR_USER_ID"),
        api_key=os.getenv("PREECHEUR_API_KEY"),
    ),
    "Old Rastaman": Client(
        user_id=os.getenv("RASTA_USER_ID"),
        api_key=os.getenv("RASTA_API_KEY"),
    ),
    "Film Noir": Client(
        user_id=os.getenv("FILMNOIR.GUI_USER_ID"),
        api_key=os.getenv("FILMNOIR.GUI_API_KEY"),
    ),
    "Epic Trailer": Client(
        user_id=os.getenv("EPIC_TRAILER.GUI_USER_ID"),
        api_key=os.getenv("EPIC_TRAILER.GUI_API_KEY"),
    )
}

# Répertoire pour stocker les fichiers audio temporaires
AUDIO_TEMP_DIR = os.path.join(tempfile.gettempdir(), 'audio_files')

# Assurez-vous que le répertoire existe
os.makedirs(AUDIO_TEMP_DIR, exist_ok=True)
print(f"Chemin: {AUDIO_TEMP_DIR}")

def clean_temp_files():
    """Nettoie les fichiers audio temporaires plus vieux d'une heure"""
    now = datetime.now()
    for filename in os.listdir(AUDIO_TEMP_DIR):
        file_path = os.path.join(AUDIO_TEMP_DIR, filename)
        # Récupère la date de création du fichier
        creation_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        # Si le fichier a plus d'une heure
        if (now - creation_time) > timedelta(hours=1):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier {file_path}: {e}")

# Planifie le nettoyage toutes les heures
schedule.every(1).hours.do(clean_temp_files)

def run_pending():
    """Exécute les tâches planifiées"""
    while True:
        schedule.run_pending()
        time.sleep(1)

# Lance un thread pour exécuter les tâches en arrière-plan
clean_thread = Thread(target=run_pending)
clean_thread.daemon = True
clean_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    data = request.json
    voice_model_path = data['voiceModelPath']
    text = data['text']
    
    if not voice_model_path or not text:
        return jsonify({'error': 'Paramètres manquants'}), 400

    try:
        # Détermine la voix utilisée pour sélectionner le client approprié
        #compte dfluture
        if 'radio-voice/manifest.json' in voice_model_path:
            voice_type = 'Vintage Radio'
        #compte dan.fmm
        elif 'original/manifest.json' in voice_model_path:
            voice_type = 'Preacher'
        #compte glide orchestra
        elif 'voice-walking-glide-reggae/manifest.json' in voice_model_path:
            voice_type = 'Old Rastaman'
        #compte Izwi
        elif '0febc340-c457-41ef-ae04-ee67124f0e87/original/manifest.json' in voice_model_path:
            voice_type = 'Film Noir'
        #compte vocalzsnap1
        elif 'f8736760-92c8-4f2f-9d8b-038299901243/original/manifest.json' in voice_model_path:
            voice_type = 'Epic Trailer'
        else:
            return jsonify({'error': 'Voix non supportée'}), 400

        client = clients.get(voice_type, None)
        if not client:
            return jsonify({'error': 'Client PlayHT non initialisé'}), 500

        options = TTSOptions(voice=voice_model_path)

        response = client.tts(text, options, voice_engine='PlayDialog-http')

        # Génère un identifiant unique pour le fichier audio
        file_id = str(uuid.uuid4())
        file_path = os.path.join(AUDIO_TEMP_DIR, f'{file_id}.mp3')
        
        # Écrit le flux audio dans le fichier
        with open(file_path, 'wb') as f:
            for chunk in response:
                f.write(chunk)
        
        # Retourne l'URL où le fichier peut être téléchargé
        return jsonify({
            'audio_url': f'/serve-audio/{file_id}.mp3'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/serve-audio/<filename>')
def serve_audio(filename):
    # Chemin complet du fichier audio
    file_path = os.path.join(AUDIO_TEMP_DIR, filename)
    
    # Vérifie si le fichier existe
    if not os.path.exists(file_path):
        return jsonify({'error': 'Fichier non trouvé'}), 404
    
    try:
        # Envoie le fichier audio au client
        return send_file(
            file_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': f'Erreur lors de l\'envoi du fichier: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
