import openai
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configura la clave API de OpenAI
openai.api_key = "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"


@app.route('/api/chat', methods=['POST'])
def chat():
    # Obtiene el mensaje del usuario desde la solicitud POST
    user_input = request.json.get('user_input')
    system_message = "Dame una respuesta con SOLO las notas en formato ABC QUE DUREN POR LO MENOS 15 SEGUNDOS Y MÁXIMO 30. NO DEBES REPONDER CON MÁS TEXTO DE LO QUE SE TE PIDE. LA RESPUESTA DEBE INCLUIR LOS INSTUMENTOS PIANO, GUITARRA Y BAJO. PONLE DE TITULO QUE SIMPRE SEA 'IA Song'"

    # Interactúa con GPT-3
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

    # Extrae la respuesta del modelo GPT-3
    gpt_response = response['choices'][0]['message']['content']

    # Devuelve la respuesta como JSON
    return jsonify({'response': gpt_response})


if __name__ == '__main__':
    app.run(debug=True)
