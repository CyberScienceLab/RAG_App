from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/printBody', methods=['POST'])
def printRequestBody():
    body = request.json

    print(f"Reqeust:\n{body}")

    return jsonify({"response": "this is the response from the dummy server"})


@app.route('/dummyLlama', methods=['POST'])
def dummyLlamaResponse():
    body = request.json

    print(f"Request: \n{body}")

    return jsonify({
        "response": "A threat intelligence report is...",
        "chunks": [
            "CHUNK 0 - dfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa",
            "CHUNK 1 - djfkajslkfjalkfj kajfkajfkajfk dsja;kfja jfka jfkl sjdkf jksj fad",
            "CHUNK 2 - dfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa",
            "CHUNK 3 - djfkajslkfjalkfj kajfkajfkajfk dsja;kfja jfka jfkl sjdkf jksj fad",
            "CHUNK 4 - dfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa"
        ]
    })

@app.route('/retrieveRagConfig', methods=['GET'])
def retrieveRagConfigOptions():
    return jsonify({
        "models": [
            "llama3",
            "gemini"
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
