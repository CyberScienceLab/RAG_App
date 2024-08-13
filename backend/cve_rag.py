import re
import json 
import torch
import numpy as np
import pandas as pd
from sentence_transformers import util, SentenceTransformer

from transformers.utils import logging
logging.set_verbosity_error()


CVE_FILE_PATH = '../../aeiyan/testingThings/cvelistV5/cves'


class Cve_Rag:

    def __init__(self, tokenizer, model) -> None:
        self.tokenizer = tokenizer
        self.model = model

    
    # get messages array to prompt the LLM that contains any relevant context retrieved by the 
    # RAG to help with generating the response
    def get_messages_with_context(self, prompt: str, extra_context: str, num_chunks: int) -> tuple[list[dict[str, str]], list[str]]:
        all_text = prompt + extra_context

        all_cves = self.extract_cves_from_text(all_text)

        cve_descriptions, cves_not_found = self.retrieve_cve_descriptions(all_cves)

        assumptions = ''
        if len(cves_not_found) > 0:
            assumptions = self.generate_missing_cve_assumptions(cves_not_found, extra_context)
            extra_context += assumptions

        return self.build_messages(prompt, extra_context, str(cve_descriptions)), [*cve_descriptions, assumptions]


    # Extract CVEs
    def extract_cves_from_text(self, text):
        pattern = r'CVE-\d{4}-\d{4,7}'
        cve_matches = re.findall(pattern, text)
        return list(set(cve_matches))


    # Format CVE numbers for database lookup
    def parse_cve_numbers_from_code(self, cve_string):
        pattern = r'CVE-(\d{4})-(\d{4,7})'
        match = re.match(pattern, cve_string)
        if match:
            first_set = int(match.group(1))
            second_set = match.group(2)
            return first_set, second_set
        else:
            raise ValueError("String does not match the CVE pattern")


    # Add formatting for the second number set in the cve which is required
    # to find the cve using the path
    def format_second_number_set(self, second_set):
        if len(second_set) == 4:
            return second_set[0] + 'xxx'
        else:
            return second_set[:2] + 'xxx'
        

    # Load CVE descriptions from database
    # return (str containing cve descriptions, list of cve's that weren't found)
    def retrieve_cve_descriptions(self, cves: list[str]) -> tuple[list[str], list[str]]:  
        cve_descriptions = []
        not_found = []

        for cve in cves:
            try:
                first_set, second_set = self.parse_cve_numbers_from_code(cve)
                second_number_formatted = self.format_second_number_set(second_set)
                file_path = f"{CVE_FILE_PATH}/{first_set}/{second_number_formatted}/CVE-{first_set}-{second_set}.json"

                with open(file_path, 'r') as f:
                    data = json.load(f)
                    cve_number = data['cveMetadata']['cveId']
                    affected_info = data['containers']['cna']['affected'][0]

                    try:
                        vendor_name = affected_info['vendor']
                        product_name = affected_info['product']
                    except KeyError:
                        affected_info = data['containers']['cna']['affected'][1]
                        vendor_name = affected_info['vendor']
                        product_name = affected_info['product']

                    description = data['containers']['cna']['descriptions'][0]['value']
                    cve_descriptions.append(f"CVE Number: {cve_number}, Vendor: {vendor_name}, Product: {product_name}, Description: {description} [DESCRIPTION_END]\n\n")

            except FileNotFoundError:
                cve_descriptions.append(f"CVE Number: {cve} Description: CVE does not exist [DESCRIPTION_END]\n\n")
                not_found.append(cve)
                
            
        return cve_descriptions, not_found


    def build_messages(self, prompt: str, extra_context: str, cve_descriptions: str) -> list[str, str]:
        return [
            {
                'role': 'system',
                'content': f'''You are an advanced CVE information system designed to assist users in verifying the usage of CVEs (Common Vulnerabilities and Exposures) in security reports and providing detailed descriptions of CVEs.

                Correct CVE Descriptions:
                {cve_descriptions}

                Your Responsibilities and Instructions:

                You are an advanced CVE information system designed to assist users in verifying the usage of CVEs (Common Vulnerabilities and Exposures) mentioned in security reports. Your tasks include verifying CVE usage, providing detailed explanations, and identifying correct or incorrect applications of CVEs based on the provided descriptions.

                **Correct CVE Descriptions:**
                {cve_descriptions}

                **Responsibilities and Instructions:**

                1. **Verify CVE Usage in the File:**
                - **Objective:** Ensure that each CVE mentioned in the user report closely matches the provided Correct CVE Description.
                - **Steps:**
                    a) **Verify Each CVE:** For each CVE mentioned, compare the details in the user-provided report with the Correct CVE Description.
                        - **Vulnerability:** Compare the vulnerability in the report with the vulnerability from the Correct CVE Description. If they are not the same the CVE usage is incorrect.
                        - **Product and Context:** Confirm that the product and context described in the report align with the product and context in the description. If the products or contexts are not the same, the CVE usage is incorrect.
                    b) **State Usage:** Clearly indicate whether each CVE is used correctly or incorrectly.
                    c) **Provide Detailed Explanation:** For each CVE:
                        - Include direct quotes from both the Correct CVE Description and the report excerpt.
                        - Explain why the CVE is used correctly or incorrectly, highlighting any discrepancies or mismatches.
                        - A CVE in the report is considered incorrect if it describes a different vulnerability than the one specified in the Correct CVE Description, even if the report accurately describes the vulnerability and its impact.
                    d) **CVE Correction:** If the report includes for CVE corrections indicated by [CVE_CORRECTION], explicitly state the correct CVE as recommended. If no correction exists for the CVE, do not mention anything.
                - **Example Structure:**
                    **CVE-XXXX-YYYY: [Title]**
                    **Correct Description:** [Detailed description of the CVE from Correct CVE Descriptions]
                    **Report Excerpt:** "[Excerpt from the user-provided report]"
                    **Explanation:** [Detailed explanation on why the usage is correct or incorrect and CVE correction from the user-provided report if exists]


                2. **Provide CVE Descriptions:**
                - **Objective:** Use the information provided in the Correct CVE Descriptions to give a comprehensive explanation of each CVE mentioned.
                - **Details:** Ensure each CVE description includes the CVE ID, Vendor, Product, and a detailed description. Do not include unnecessary or unrelated information.
                - **Example Structure:**
                    **CVE-XXXX-YYYY**
                    **ID:** [CVE ID]
                    **Vendor:** [Vendor]
                    **Product:** [Product]
                    **Description:** [Detailed CVE description]

                    
                **Notes:** 
                - Make sure to format your response exactly as stated above in Example Structure.
                - Never include [DESCRIPTION_END] in the output, it is only used to is used to indicate end of CVE description for your processing.
                - The new CVE from CVE_CORRECTION must be included in the original CVE's Explanation and nowhere else.
                - Any CVE mentioned in CVE_CORRECTION is only to be displayed with the CVE it's replacing, not in it's own output
                - You only have on responsibility per request, never do both instructions 1 and 2 together
                '''
            },
            {
                'role': 'user',
                'content': f'{prompt} - File Input: {extra_context}'
            }
        ]
    

    

    # take list of cves mentioned in a file that do not exist in RAG's database
    # let llama3 make an assumption about what the correct CVE id was
    def generate_missing_cve_assumptions(self, not_found: list[str], file_text: str) -> str:

        llamaSug = ""
        for cve in not_found:
            messages = [
                {"role": "system", "content": "You are a chat bot."},
                {"role": "user", "content": f"In 2 sentences, could you describe the use of {cve} in the provided text. Provided text: {file_text}."}
            ]

            input_ids = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(input_ids, max_new_tokens=700, eos_token_id=self.tokenizer.eos_token_id, do_sample=True, temperature=0.3, top_p=0.9)
            response = outputs[0][input_ids.shape[-1]:]
            llamaDesc = self.tokenizer.decode(response, skip_special_tokens=True)

            theContext = self.asking_llama_for_advice(llamaDesc)

            messages = [
                {
                    "role": "system", 
                    "content": f""""You are a Q&A Assistant. You will be provided with relevant information about various CVEs. Based on this information, your task is to recommend the CVE number that most closely matches the description of the vulnerability.
                                    Provided Relevant Information: {theContext} """},
                {
                    "role": "user", 
                    "content": f""" Hello, could you recomend me a CVE that most closly resembles this chunk of text based of the relevant information that you have. Only give me the CVE ID, I don't want any other text in the response. Chunk of text: {llamaDesc}"""
                },
            ]   

            input_ids = self.tokenizer.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(input_ids, max_new_tokens=700, eos_token_id=self.tokenizer.eos_token_id, do_sample=True, temperature=0.3, top_p=0.9)
            response = outputs[0][input_ids.shape[-1]:]
            res = self.tokenizer.decode(response, skip_special_tokens=True)

            llamaSug += f"\n\n[[CVE_CORRECTION]: {cve} is used incorrectly in report, the correct CVE is: {res}]"
        
        return llamaSug
    

    def asking_llama_for_advice(self, cveDesp: str) -> str:
        device = "cuda" if torch.cuda.is_available() else "cpu"

        csv_path = '../../aeiyan/testingThings/RAG_LLM_hallucinations/test2.csv'

        chunk_embeddings_df = pd.read_csv(csv_path)

        chunk_embeddings_df["embedding"] = chunk_embeddings_df["embedding"].apply(lambda x: np.fromstring(x.strip("[]"), sep=" "))

        embeddings = torch.tensor(np.stack(chunk_embeddings_df["embedding"].tolist(), axis=0), dtype=torch.float32).to(device)

        pages_chunks = chunk_embeddings_df.to_dict(orient="records")

        embedding_model = SentenceTransformer(model_name_or_path="all-mpnet-base-v2", device=device)

        # n_resources_to_return could be the num chunks from rag.py
        indices = self.retrieve_context(query=cveDesp, embeddings=embeddings, model=embedding_model)

        context_items = [pages_chunks[i] for i in indices]

        context_str = "- " + "\n- ".join([item["sentence_chunk"] for item in context_items])

        return context_str


    def retrieve_context(self, query: str,
                embeddings: torch.tensor,
                model: SentenceTransformer,
                n_resources_to_return: int=5):
        """
        Embeds a query with model and returns top k scores and indices from embeddings.
        """

        # Embed the query
        query_embedding = model.encode(query, convert_to_tensor=True)

 
        dot_scores = util.dot_score(query_embedding, embeddings)[0]

        _, indices = torch.topk(input=dot_scores, k=n_resources_to_return)

        return indices
