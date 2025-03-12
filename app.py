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
        user_id=os.getenv("PLAYHT_USER_ID"),
        api_key=os.getenv("PLAYHT_API_KEY"),
    ),
    "Preacher": Client(
        user_id=os.getenv("PLAYHT_USER_ID"),
        api_key=os.getenv("PLAYHT_API_KEY"),
    ),
    "Old Rastaman": Client(
        user_id=os.getenv("PLAYHT_USER_ID"),
        api_key=os.getenv("PLAYHT_API_KEY"),
    ),
    "Film Noir": Client(
        user_id=os.getenv("PLAYHT_USER_ID"),
        api_key=os.getenv("PLAYHT_API_KEY"),
    ),
    "Epic Trailer": Client(
        user_id=os.getenv("PLAYHT_USER_ID"),
        api_key=os.getenv("PLAYHT_API_KEY"),
    ),
    "Funky": Client(
        user_id=os.getenv("PLAYHT_USER_ID"),
        api_key=os.getenv("PLAYHT_API_KEY"),
    ),
    "Vintage Documentary": Client(
        user_id=os.getenv("PLAYHT_USER_ID"),
        api_key=os.getenv("PLAYHT_API_KEY"),
    ),
    "Italian Mafiosi": Client(
        user_id=os.getenv("PLAYHT_USER_ID"),
        api_key=os.getenv("PLAYHT_API_KEY"),
    ),
    "Grandma": Client(
        user_id=os.getenv("PLAYHT_USER_ID"),
        api_key=os.getenv("PLAYHT_API_KEY"),
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
    print(f"Requête JSON: {data}")
    voice_model_path = data['voiceModelPath']
    text = data['text']
    

    # Récupérer directement les paramètres de la requête JSON
    temperature = float(data.get('temperature', 0.8))  # Valeur par défaut: 0.8
    top_p = float(data.get('top_p', 0.8))  # Valeur par défaut: 0.8
    text_guidance = float(data.get('text_guidance', 3.0))  # Valeur par défaut: 3.0
    voice_guidance = float(data.get('voice_guidance', 7.0))  # Valeur par défaut: 7.0
    style_guidance = float(data.get('style_guidance', 8.0))  # Valeur par défaut: 8.0
    speed = float(data.get('speed', 0.7))  # Valeur par défaut: 0.7
    
    # Log des paramètres extraits
    print(f"Ensuite")
    print(f"voiceModelPath: {voice_model_path}")
    print(f"text: {text}")
    
    print(f"temperature: {temperature}")
    print(f"top_p: {top_p}")
    print(f"text_guidance: {text_guidance}")
    print(f"voice_guidance: {voice_guidance}")
    print(f"style_guidance: {style_guidance}")
    print(f"speed: {speed}")

    
    if not voice_model_path or not text:
        return jsonify({'error': 'Paramètres manquants'}), 400

    try:
        # Détermine la voix utilisée pour sélectionner le client approprié
        #compte dfluture
        if 'da861ac7-44d1-41c2-bdd7-5579b07e46de/original/manifest.json' in voice_model_path:
            voice_type = 'Vintage Radio'
        #compte dan.fmm
        elif '7eba2ab9-f733-4b44-b390-7f42a3d6cf3d/original/manifest.json' in voice_model_path:
            voice_type = 'Preacher'
        #compte glide orchestra
        elif 'ff240cd0-de2b-4c6c-8634-f802be2a73e0/original/manifest.json' in voice_model_path:
            voice_type = 'Old Rastaman'
        #compte Izwi
        elif '26c2de86-1c4f-4e33-9950-767f9f0b07ad/original/manifest.json' in voice_model_path:
            voice_type = 'Film Noir'
        #compte vocalzsnap1
        elif '988aab38-552c-4fa4-88ce-37538ba0c71b/original/manifest.json' in voice_model_path:
            voice_type = 'Epic Trailer'
        #compte dannasse
        elif '4725cfd5-943a-4927-b8d5-90d99cbaf4fd/original/manifest.json' in voice_model_path:
            voice_type = 'Funky'
        elif 'a0b0002b-952d-44b6-ac6f-33c4751f4b8b/original/manifest.json' in voice_model_path:
            voice_type = 'Vintage Documentary'
        elif 'd69c5b6a-83e3-4f02-9daa-78c33e1a0cc4/original/manifest.json' in voice_model_path:
            voice_type = 'Italian Mafiosi'
        elif '2b82ecbf-d4b3-4a8e-a492-f14aef010de7/original/manifest.json' in voice_model_path:
            voice_type = 'Grandma'
        else:
            return jsonify({'error': 'Voix non supportée'}), 400

        client = clients.get(voice_type, None)
        if not client:
            return jsonify({'error': 'Client PlayHT non initialisé'}), 500

       # Nouvelles options avec les paramètres ajustés récupérés de l'utilisateur
        options = TTSOptions(
            voice=voice_model_path,
            temperature=temperature,           # Valeur personnalisée
            top_p=top_p,                       # Valeur personnalisée
            text_guidance=text_guidance,       # Valeur personnalisée
            voice_guidance=voice_guidance,     # Valeur personnalisée
            style_guidance=style_guidance,     # Valeur personnalisée
            speed=speed                        # Valeur personnalisée
        )
        
        print(f"Enfin Options: {options}")

        response = client.tts(text, options, voice_engine='Play3.0-mini-http')

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
