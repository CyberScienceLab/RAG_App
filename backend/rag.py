from transformers import AutoTokenizer, AutoModelForCausalLM

import torch
torch.cuda.empty_cache()

from transformers.utils import logging
logging.set_verbosity_error()

# import cve_rag

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


def prompt(prompt: str, model: str, rag_type: list[str], num_chunks: int, extra_context: str) -> dict[str, str]:

    if len(extra_context) == 0:
        extra_context = 'No extra context given.'

    messages = []
    match rag_type:
        case 'CVE':
            messages = []
        #     messages = cve_rag.build_messages(prompt, extra_context, num_chunks)

        case _:
            messages = default_messages(prompt, extra_context)


    if model == 'Llama3':
        response = prompt_llama3(messages)
    elif model == 'Gemini':
        response = prompt_gemini(messages)

    # TODO: get chunks
    # cve rag, chunks can be the cve descriptions or something similar
    return {
        'response': response,
        'chunks': []
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
        temperature=0.3, 
        top_p=0.9
    )

    response = outputs[0][input_ids.shape[-1]:]
    return tokenizer.decode(response, skip_special_tokens=True)


def prompt_gemini(messages: list[str]) -> str:
    return "NOT_IMPLEMENTED"


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
