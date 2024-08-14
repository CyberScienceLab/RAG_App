from transformers import AutoTokenizer, AutoModelForCausalLM
import requests
import os
import json

import torch
torch.cuda.empty_cache()

from transformers.utils import logging
logging.set_verbosity_error()

from cve_rag import Cve_Rag


GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'
SYSTEM_INDEX = 0
USER_INDEX = 1


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

cve_rag = Cve_Rag(tokenizer, model)


# prompt specified model and rag
# return response string and relevant chunks
def prompt(prompt: str, model: str, rag_type: str, num_chunks: int, extra_context: str) -> dict[str, str]:
    print(f"[CSL] model: {model} -- rag type: {rag_type} -- num chunks: {num_chunks} -- file uploaded: {len(extra_context) > 0}")

    if len(extra_context) == 0:
        extra_context = 'No File / extra context given.'

    messages = []
    chunks = []
    match rag_type:
        case 'CVE':
            messages, chunks = cve_rag.get_messages_with_context(prompt, extra_context, num_chunks)

        case _:
            messages = default_messages(prompt, extra_context)


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


def prompt_llama3(messages: list[str]) -> str:
    input_ids = tokenizer.apply_chat_template(
        messages, 
        add_generation_prompt=True, 
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(
        input_ids, 
        max_new_tokens=700, 
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


def prompt_gemini(messages: list[str]) -> str:
    # must use REST to communicate with Gemini LLM, the Python library
    # google.generativeai has dependency version issues that couldn't be resolved

    headers = { 'x-goog-api-key': GOOGLE_API_KEY }
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
def extract_json_array_if_present(text: str) -> str:
    start_index = -1
    end_index = -1

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
    
    prompt_message = 'Please provide me with some information on the following CVEs: CVE-2024-0008 and CVE-2024-0010'
    res = prompt(prompt_message, 'Llama3', 'CVE', '5', '')

    print("RES:::")
    print(res["response"])

    # prompt_message = 'Please verify if the following CVEs have been used correctly in the following Threat Intelligence Report'
    # res = prompt(prompt_message, 'Gemini', 'CVE', '5', report)

    # prompt_message = 'Please provide me with some information on the following CVEs: CVE-2024-0008 and CVE-2024-0010'
    # res = prompt(prompt_message, 'Gemini', 'CVE', '5', '')

    # # print(res['chunks'])
    # print("RES:::")
    # print(res["response"])


