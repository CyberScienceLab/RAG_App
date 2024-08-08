# TODO: 
# - make the requirements.txt

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import fitz

app = Flask(__name__)
CORS(app) # TODO: maybe can remove this later, look into it


@app.route('/dummyLlama', methods=['POST'])
def dummyLlamaResponse():
    body = None
    file = None
    extraContext = ''

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
            extraContext = file.read().decode('utf-8')

        elif filename.lower().endswith('.pdf'):
            pdf_reader = fitz.open(stream=file.read(), filetype='pdf')
            pdf_str = ''
            for page_num in range(len(pdf_reader)):
                page = pdf_reader.load_page(page_num)
                text = page.get_text('text')
                pdf_str += text

            extraContext = pdf_str

        else:
            return jsonify({'response': 'invalid file type passed'})
        
    if len(extraContext) != 0:
        print(extraContext)

    # extraContext - file string uploaded
    # body['prompt'] - prompt
    # body['model'] - llm model
    # body['ragTypes'] - array of ragTypes to use can be empty can have multiple
    # body['chunks'] - # of chunks to use for context
    
    # return json object with 
    # {
    #     'response': '...',
    #     'chunks': [
    #         '...',
    #         ...
    #     ]
    # }

    return jsonify({
        "response": "A threat intelligence report is...",
        "chunks": [
            "CHUNK 1 - In recent years, the importance of data security has grown significantly as businesses and individuals alike increasingly rely on digital systems. With the rise of cyber-attacks and data breaches, ensuring the safety of sensitive information has become a top priority. Data security involves implementing various measures to protect data from unauthorized access, corruption, or theft. This can include using encryption to protect data in transit and at rest, employing firewalls and anti-virus software to prevent malicious attacks, and regularly updating software to patch vulnerabilities. Additionally, businesses must ensure that their employees are trained in data security best practices to avoid human error, which can often be a significant factor in data breaches. One critical aspect of data security is the management of access controls, ensuring that only authorized individuals have access to sensitive information. This can be achieved through the use of multi-factor authentication, strong password policies, and regular audits of access permissions. Furthermore, organizations should have a robust incident response plan in place to quickly address any security breaches that do occur, minimizing potential damage and restoring normal operations as swiftly as possible. By taking these precautions and staying informed about the latest threats and security technologies, organizations can better protect their data and maintain the trust of their customers and stakeholders.",
            "CHUNK 2 - Artificial Intelligence (AI) has rapidly evolved over the past decade, transforming numerous aspects of our daily lives and industries. AI technologies, such as machine learning, natural language processing, and computer vision, are being utilized to enhance various applications, from personalized recommendations on streaming platforms to advanced diagnostic tools in healthcare. Machine learning algorithms can analyze vast amounts of data to identify patterns and make predictions, which can lead to more efficient and accurate decision-making processes. In healthcare, AI-powered tools can assist in diagnosing diseases, predicting patient outcomes, and personalizing treatment plans. Natural language processing allows AI systems to understand and generate human language, enabling more intuitive interactions with virtual assistants and chatbots. Computer vision technology enables machines to interpret visual information, which is crucial for applications like autonomous vehicles and facial recognition systems. However, the widespread adoption of AI also raises ethical and privacy concerns. Issues such as data bias, algorithmic transparency, and the potential for job displacement need to be addressed as AI continues to advance. Ensuring that AI systems are developed and implemented responsibly is essential for maximizing their benefits while minimizing potential risks. As AI technology progresses, ongoing research and dialogue will be crucial in navigating the challenges and opportunities that lie ahead.",
            "CHUNK 3 - The concept of sustainable development has gained significant traction in recent years, driven by growing awareness of environmental issues and the need for economic and social progress. Sustainable development seeks to balance economic growth with environmental protection and social equity, ensuring that current and future generations can meet their needs without compromising the planet's health. One key aspect of sustainable development is the promotion of renewable energy sources, such as solar, wind, and hydroelectric power, which can reduce dependence on fossil fuels and lower greenhouse gas emissions. Additionally, sustainable practices in agriculture, such as organic farming and precision agriculture, can help preserve natural resources and reduce environmental impact. Urban planning and design also play a critical role in sustainability, with initiatives aimed at creating energy-efficient buildings, reducing waste, and promoting green spaces. Social sustainability involves addressing issues such as poverty, inequality, and access to education and healthcare, ensuring that all individuals have the opportunity to thrive. Governments, businesses, and individuals all have a role to play in advancing sustainable development, through policies, practices, and personal choices. By working together to create a more sustainable future, we can contribute to the health of our planet and the well-being of all its inhabitants.",
            "CHUNK 4 - djfkajslkfjalkfj kajfkajfkajfk dsja;kfja jfka jfkl sjdkf jksj fad dfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\ndfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\ndfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\n dfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\ndfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\ndfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\n dfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\ndfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\ndfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\n",
            "CHUNK 5 - dfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\ndfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\ndfasfasfjaksjdflkajsdkfjak dsjfka jdfk ajskfdj aksfj akds jfkdsfjadfa\n"
        ]
    })

@app.route('/retrieveRagConfig', methods=['GET'])
def retrieveRagConfigOptions():
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
