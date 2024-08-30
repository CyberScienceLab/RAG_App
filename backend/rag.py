import sys
import requests
import os
import json
from transformers import AutoTokenizer, AutoModelForCausalLM

import torch
torch.cuda.empty_cache()

from transformers.utils import logging
logging.set_verbosity_error()

# CSL Imports =======================================================

# cve_rag was the first one setup, so we just moved it to this repository
# we have it separate from the actual repository here, but the rest should
# be done like pen_test_rag, malware_rag and otx_rag were done
from cve_rag import Cve_Rag

# must add the path to the project to use it directly as import
sys.path.append('./Penetration_Testing_Rag')
from pen_test_rag import Pen_Test_Rag

sys.path.append('./Malware_Analysis_Rag')
from mbTesting3 import Malware_Rag

sys.path.append('./Threat_Intelligence_Rag')
from OTXrag import OTX_Rag

# Constants =========================================================
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'
SYSTEM_INDEX = 0
USER_INDEX = 1

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY is None:
    print(f'[ERROR] Missing env variable: GOOGLE_API_KEY')
    exit(1)

PEN_TEST_PROJ_PATH = os.getenv('PEN_TEST_PROJ_PATH')
if PEN_TEST_PROJ_PATH is None:
    print(f'[ERROR] Missing env variable: PEN_TEST_PROJ_PATH')
    exit(1)
# ===================================================================

# initalize and return  llama3 tokenizer and model
def initialize_model():
    model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    return tokenizer, model

tokenizer, model = initialize_model()

# initialize all rags here
cve_rag = Cve_Rag(tokenizer, model)
pen_test_rag = Pen_Test_Rag(tokenizer, model, PEN_TEST_PROJ_PATH)
otx_rag = OTX_Rag()
malware_rag = Malware_Rag()


# prompt specified model and rag
# return response string and relevant chunks
def prompt(prompt: str, model: str, rag_type: str, num_chunks: int, extra_context: str) -> dict[str, str]:
    print(f"[CSL] model: {model} -- rag type: {rag_type} -- num chunks: {num_chunks} -- file uploaded: {len(extra_context) > 0}")

    if len(extra_context) == 0:
        extra_context = 'No File / extra context given.'

    num_chunks = max(num_chunks, 1)

    messages = []
    chunks = []

    # IMPORTANT! any new rags added must be added both here and in 
    #            server.py retrieve_rag_config_options()
    match rag_type:
        case 'CVE':
            messages, chunks = cve_rag.get_messages_with_context(prompt, extra_context, num_chunks)

        case 'Pen-Testing':
            messages, chunks = pen_test_rag.get_messages_with_context(prompt, '' if extra_context == 'No File / extra context given.' else extra_context, num_chunks)

        case 'Malware':
            messages, chunks = malware_rag.get_messages_with_context(prompt, extra_context, num_chunks)

        case 'Threat Intelligence':
            messages, chunks = otx_rag.get_messages_with_context(prompt, extra_context, num_chunks)

        case _:
            messages = default_messages(prompt, extra_context)


    # IMPORTANT! any new models added must be added both here and in 
    #            server.py retrieve_rag_config_options()
    match model:
        case  'Llama3':
            response = prompt_llama3(messages)
        
        case  'Gemini':
            response = prompt_gemini(messages)

        case _:
            response = f'{model} doesn\'t exist in the list off our LLM models available'


    return {
        'response': extract_json_array_if_present(response),
        'chunks': chunks
    }


# prompt local llama3 version running with hugging face
def prompt_llama3(messages: list[str]) -> str:
    input_ids = tokenizer.apply_chat_template(
        messages, 
        add_generation_prompt=True, 
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(
        input_ids, 
        max_new_tokens=1024, 
        eos_token_id=tokenizer.eos_token_id, 
        do_sample=True, 
        temperature=0.2, 
        top_p=0.9
    )

    response = tokenizer.decode(outputs[0][input_ids.shape[-1]:], skip_special_tokens=True)

    # local llama3 is a pain... so you have to replace all single quotes with double quotes
    # so JSON can properly be parsed by the fe
    response.replace("'", '\\\"')
    
    return response


# prompt gemini api
def prompt_gemini(messages: list[str]) -> str:
    # must use REST to communicate with Gemini LLM, the Python library
    # google.generativeai has dependency version issues that couldn't be resolved

    headers = { 'x-goog-api-key': GOOGLE_API_KEY }
    # must use the safetySettings as BLOCK_NONE or else many responses
    # won't be given back since it violates safety or another category
    body = {
        "system_instruction": {
            "parts": {
                "text": str(messages[SYSTEM_INDEX])
            }
        },
        "contents": [
            {
                "parts": [
                    {
                        "text": str(messages[USER_INDEX])
                    }
                ]
            }
        ],
        "safetySettings": [
            { "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE" },
            { "category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE" },
            { "category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE" },
            { "category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE" }
        ]
    }

    response = requests.post(GEMINI_URL, json=body, headers=headers)

    if response.ok:
        try:
            # need to retrieve nested text field from response json
            # other fields don't matter to us
            res = (
                response.json()
                    .get('candidates')[0]
                    .get('content')
                    .get('parts')[0]
                    .get('text') 
            )

            return res

        except (KeyError, IndexError, TypeError) as e:
            err = f'Bad response received from Gemini: {e}'
            print(err)
            return err
        

    err = f'Error occurred in Gemini request: {response.text}'
    print(err)
    return err


# default prompt to use if no rag type was selected
def default_messages(prompt: str, extra_context: str):
    return [
        {
            'role': 'system',
            'content': '''You are a chat bot, you are going to get a 
                       question and give a response to the best of your knowledge.
                       '''
        },
        {
            'role': 'user',
            'content': f'Question: {prompt}\nExtra context to answer question: {extra_context}'
        }
    ]


# extract json object from string if present else return text passed as argument
# required due to LLM's returning additional text in their responses
# also remove any text after **Code Snippet**, since llama doesn't listen
def extract_json_array_if_present(text: str) -> str:
    start_index = -1
    end_index = -1

    # remove **Code Snippet** and any following text
    code_snippet_index = text.find('**Code Snippet:**')
    if code_snippet_index != -1:
        text = text[:code_snippet_index]

    for i in range(len(text)):
        if text[i] == '[':
            start_index = i
            break

    for i in range(len(text) - 1, -1, -1):
        if text[i] == ']':
            end_index = i + 1
            break

    if start_index == -1 or end_index == -1:
        return text

    return text[start_index : end_index]


if __name__ == '__main__':
    print('rag.py')
    # prompt_message = 'Please provide me with some information on the following CVEs: CVE-2024-0008 and CVE-2024-0010'
    # res = prompt(prompt_message, 'Llama3', 'CVE', '5', '')

    # print("RES:::")
    # print(res["response"])

    ##prompt_message = 'Find me a few DOS exploits that target android'
    # prompt_message = 'Find me an exploit that was created by Metasploit'
    # prompt_message = 'Give me some examples of DOS exploits that were published in 2018.'
    # prompt_message = 'How do I break out of a Docker container?'
    # res = prompt(prompt_message, 'Llama3', 'Pen-Testing', 5, '')
    # res = prompt(prompt_message, 'Gemini', 'Pen-Testing', 5, '')

    #prompt_message = 'What is this about 9d948a18acdd4d4ea3c1fbab2ea72de766e1434b208ed78ce000b81ece996874'
    #res = prompt(prompt_message, 'Gemini', 'Malware', 5, '')

    # prompt_message = 'Can you give me IP addresses related to RDP intrusion attempt'
    # res = prompt(prompt_message, 'Gemini', 'OTX-Rag', 5, '')

    # print("RES:::")
    # print(res["response"])
    # print(res['chunks'])
    