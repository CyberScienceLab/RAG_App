# TODO: 
# - make the requirements.txt

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import fitz
import rag

app = Flask(__name__)
CORS(app) # TODO: maybe can remove this later, look into it


@app.route('/promptRag', methods=['POST'])
def prompt_rag():
    body = None
    file = None
    extra_context = ''

    if request.form and 'json' in request.form:
        body = json.loads(request.form.get('json'))
    else:
        return jsonify({'response': 'request body missing'}), 400

    if request.files and 'file' in request.files:
        file = request.files.get('file')

    
    # read file
    if file:
        filename = file.filename

        if filename.lower().endswith('.txt'):
            extra_context = file.read().decode('utf-8')

        elif filename.lower().endswith('.pdf'):
            pdf_reader = fitz.open(stream=file.read(), filetype='pdf')
            pdf_str = ''
            for page_num in range(len(pdf_reader)):
                page = pdf_reader.load_page(page_num)
                text = page.get_text('text')
                pdf_str += text

            extra_context = pdf_str

        else:
            return jsonify({'response': 'invalid file type passed'})
        

    rag_config = body['ragConfig']
    rag_type = rag_config['ragTypes'][0] if len(rag_config['ragTypes']) > 0 else ''

    res = rag.prompt(body['prompt'], rag_config['model'], 
                     rag_type, rag_config['chunks'], extra_context)

    return jsonify(res)


@app.route('/retrieveRagConfig', methods=['GET'])
def retrieve_rag_config_options():
    return jsonify({
        "models": [
            "Llama3",
            "Gemini"
        ],
        "ragTypes": [
            "CVE",
            "Threat Intelligence",
            "Pen-Testing",
            "Malware"
        ]
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
