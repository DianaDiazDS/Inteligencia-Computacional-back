import io
import os
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from mido import MidiFile, MidiTrack, Message

app = Flask(__name__)
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["Content-Type", "Authorization"])


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

@app.route('/api/chat', methods=['POST'])
def chat():
    # Obtiene el mensaje del usuario desde la solicitud POST
    user_input = request.json.get('user_input')
    system_message = "Dame una respuesta con SOLO las notas en formato ABC QUE DUREN POR LO MENOS 15 SEGUNDOS Y MÁXIMO 30. NO DEBES REPONDER CON MÁS TEXTO DE LO QUE SE TE PIDE. LA RESPUESTA DEBE INCLUIR LOS INSTUMENTOS PIANO, GUITARRA Y BAJO. PONLE DE TITULO QUE SIMPRE SEA 'IA Song'"

    # Interactúa con GPT-4
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ],
        max_tokens=2000,
        temperature=1,
        top_p=1,
        n=1,
    )

    # Extrae la respuesta del modelo GPT-4
    gpt_response = response['choices'][0]['message']['content']
    # Devuelve la respuesta como JSON
    return jsonify({'response': gpt_response})


if __name__ == '__main__':
    app.run(debug=True)
