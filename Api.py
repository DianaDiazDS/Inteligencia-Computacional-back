import io
import os

import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from mido import MidiFile, MidiTrack, Message

app = Flask(__name__)
CORS(app)


def add_instruments_to_midi(input_midi_path, output_midi_path):
    # Programas MIDI para los instrumentos
    guitar_program = 25
    bass_program = 33

    # Crea un nuevo archivo MIDI
    new_midi = MidiFile()

    # Abre el archivo MIDI original
    with MidiFile(input_midi_path) as midi:
        for i, track in enumerate(midi.tracks):
            new_track = MidiTrack()
            new_midi.tracks.append(new_track)

            # Asigna el programa de instrumento adecuado a cada canal

            if i == 1:
                program = guitar_program
            elif i == 2:
                program = bass_program
            else:
                program = None  # No especificamos un programa para canales adicionales

            # Agrega un mensaje de cambio de programa para establecer el instrumento
            if program is not None:
                new_track.append(Message('program_change', program=program, time=0))

            # Copia los mensajes de la pista original
            for msg in track:
                if msg.type == 'program_change':
                    continue  # Saltar mensajes de cambio de programa de la pista original
                new_track.append(msg)

    # Guarda el archivo MIDI modificado
    new_midi.save(output_midi_path)


def preprocess_text(text):
    import nltk
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('punkt')
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from textblob import TextBlob
    from langdetect import detect
    from googletrans import Translator

    if detect(text) == 'en':
        lang = 'english'
    elif detect(text) == 'es':
        lang = 'spanish'
    else:
        lang = 'english'

    translator = Translator()
    traduccion = translator.translate(text, dest="en")
    sentiment = TextBlob(traduccion.text)
    sentiment = sentiment.polarity

    # Tokenización
    tokens = word_tokenize(text, language=lang)

    # Lista de stopwords en español
    stop_words = set(stopwords.words(lang))

    # Eliminación de stopwords
    cleaned_tokens = [tokens[0]] + [word for word in tokens[1:] if word not in stop_words]

    # Convertir tokens de nuevo a texto
    preprocessed_text = ' '.join(cleaned_tokens)

    return sentiment, preprocessed_text


@app.route('/api/upload_midi', methods=['POST'])
def upload_midi():
    if 'file' not in request.files:
        return jsonify({'error': 'No se ha enviado ningún archivo'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nombre de archivo vacío'}), 400

    # Guardar el archivo en el servidor con un nombre único
    file_path = os.path.join('', file.filename)
    file.save(file_path)

    # Ruta para el archivo de salida modificado
    output_file_path = os.path.join('', 'modified_' + file.filename)

    # Agregar instrumentos al archivo MIDI
    add_instruments_to_midi(file_path, output_file_path)

    # Leer el contenido del archivo modificado
    with open(output_file_path, 'rb') as f:
        file_content = f.read()

    blob = io.BytesIO(file_content)

    # # Eliminar el archivo modificado después de leer su contenido
    os.remove(file_path)
    os.remove(output_file_path)

    # Enviar el archivo modificado como respuesta
    return blob, 200, {'Content-Type': 'audio/midi'}


# Configura la clave API de OpenAI GPT-4
openai.api_key = "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"


# Api gratis
# openai.api_key = "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"

@app.route('/api/token', methods=['POST'])
def token():
    # Obtiene el mensaje del usuario desde la solicitud POST
    user_input = request.json.get('user_input')
    result = preprocess_text(user_input)
    print(preprocess_text(user_input))
    # Devuelve la respuesta como JSON
    return jsonify({'response': result})


@app.route('/api/chat', methods=['POST'])
def chat():
    # Obtiene el mensaje del usuario desde la solicitud POST
    sentiment, user_input = preprocess_text(request.json.get('user_input'))

    if sentiment > 0.1:
        estado_emocional = 'alegre'
    elif sentiment < -0.1:
        estado_emocional = 'triste'
    else:
        estado_emocional = 'neutro'

    system_message = "Dame una respuesta con SOLO las notas en formato ABC QUE DUREN POR LO MENOS 15 SEGUNDOS Y MÁXIMO 30. NO DEBES REPONDER CON MÁS TEXTO DE LO QUE SE TE PIDE. LA RESPUESTA DEBE INCLUIR LOS INSTUMENTOS PIANO, GUITARRA Y BAJO. EL TITULO DE LA CANCIÓN SIMPRE ES 'IA Song'. El genero de la canción debe ser o asemejarse al que te piden, para esto puedes basarte en otras canciones del genero buscando sus notas y hacinedo una canción nueva parecida. El sentimiento del prompt es " + estado_emocional + "."

    # Interactúa con GPT-4
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ],
        max_tokens=3000,
        temperature=1,
        top_p=1,
        n=1,
    )

    # Extrae la respuesta del modelo GPT-4
    gpt_response = response['choices'][0]['message']['content']
    # Devuelve la respuesta como JSON
    return jsonify({'response': gpt_response})


@app.route('/')
def home():
    return "Back del proyecto de inteligencia"


if __name__ == '__main__':
    app.run(debug=True)
