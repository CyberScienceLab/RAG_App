# TODO:
# - update the system prompt, getting bad output for verifying usage
# - add llama sug

import re
import json 

CVE_FILE_PATH = '../../aeiyan/testingThings/cvelistV5/cves'


class Cve_Rag:

    def __init__(self, tokenizer, model) -> None:
        self.tokenizer = tokenizer
        self.model = model

    
    # get messages array to prompt the LLM that contains any relevant context retrieved by the 
    # RAG to help with generating the response
    def get_messages_with_context(self, prompt: str, extra_context: str, num_chunks: int) -> list[str, str]:
        all_text = prompt + extra_context

        all_cves = self.extract_cves_from_text(all_text)

        cve_descriptions, cves_not_found = self.retrieve_cve_descriptions(all_cves)

        if len(cves_not_found) > 0:
            # work with aeiyan on this part since he made llamasug
            pass

        return self.build_messages(prompt, extra_context, cve_descriptions)


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
    def retrieve_cve_descriptions(self, cves: list[str]) -> tuple[str, list[str]]:  
        cve_descriptions = ''
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
                    cve_descriptions += f"CVE Number: {cve_number}, Vendor: {vendor_name}, Product: {product_name}, Description: {description} [DESCRIPTION_END]"

            except FileNotFoundError:
                not_found.append(cve)
                
            
        return cve_descriptions, not_found


    def build_messages(self, prompt: str, extra_context: str, cve_descriptions: str) -> list[str, str]:
        return [
            {
                'role': 'system',
                'content': f'''You are an advanced CVE information system designed to assist users in verifying the usage of CVEs (Common Vulnerabilities and Exposures) in security reports and providing detailed descriptions of CVEs. Your responsibilities include:

                                Correct CVE Descriptions:
                                {cve_descriptions}

                                Instructions:
                                1. Verifying CVE Usage: A CVE is used correctly when it closely matches the provided Correct CVE Description. 
                                   Incorrect usage includes citing non-existent CVEs, misrepresenting the Correct CVE Description, or inaccurately applying the CVE.
                                   Analyze text from the file given and follow the below steps:
                                    a) Verify each CVE mentioned in the user-provided report.
                                    b) Indicate whether each CVE is used correctly or not.
                                    c) You must provide a detailed explanation with direct quotes from both the report and the Correct CVE Description. A CVE in the report is incorrect if it describes a different vulnerability, even if the report accurately describes the vulnerability and its impact, and provides mitigation recommendations.
                                2. Providing CVE Descriptions: When given a CVE identifier, return a comprehensive description of the CVE, including its CVE ID, Vendor, Product and description.

                                Examples:
                                1. Input: "Please verify the CVE usage in this report?"
                                Output: "Example Output:

                                <h2>CVE-2023-1234: Buffer Overflow in Software X</h2>
                                <ul>
                                    <li>Correct Description: Buffer overflow vulnerability in software Y.</li>
                                    <li>Report Excerpt: "Software X is facing a buffer overflow vulnerability."</li>
                                    <li>Explanation: The report mentions a buffer overflow in Software X, which closely matches the correct CVE description of a buffer overflow in software Y. Although the software names differ, the nature of the vulnerability is accurately represented.
                                    CVE-2024-2342: Cross-Site Scripting (XSS) in XYZ Web Server</li>
                                </ul><br />

                                2. Input: "Provide information about the following CVEs CVE-2021-22986 and CVE-2022-22987."
                                Output: 
                                - CVE-2021-22986: [ID, Vendor, Product, Description]
                                - CVE-2022-22987: [ID, Vendor, Product, Description]
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
        for cve in not_found:
            pass
        pass
