import os
import json
import re
import requests
from dotenv import load_dotenv
from tavily import TavilyClient
from huggingface_hub import InferenceClient

load_dotenv()
print("Environment Keys Loaded:", os.getenv('HUGGINGFACE_API_KEY'))

hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
if not hf_api_key:
    raise ValueError("Hugging Face API Key not set in environment variable")

text_generation_client = InferenceClient(token=hf_api_key, model="mistralai/Mistral-Nemo-Instruct-2407")

tavily_api_key = os.getenv('TAVILY_API_KEY')
if not tavily_api_key:
    raise ValueError("Tavily API Key not set in environment variable")
tavily_client = TavilyClient(api_key=tavily_api_key)

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return image_file.read()  

def analyze_image(image_path):
    api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    headers = {
        "Authorization": f"Bearer {hf_api_key}",
        "Content-Type": "image/jpeg"
    }
    image_data = encode_image_to_base64(image_path)
    
    response = requests.post(api_url, headers=headers, data=image_data)
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

def format_prompt_for_model(user_prompt, product_info=None):
    system_context_prompt = (
        "You are an expert sustainability and health analyst specializing in evaluating consumer products. "
        "Your role is to critically analyze extracted text from product descriptions, labels, or related documents, "
        "and combine it with web-sourced data to provide an evidence-based assessment. "
        "Follow these steps:\n"
        "1. Analyze the provided extracted text to identify the product and its characteristics.\n"
        "2. Determine the product name from the text; if unclear, infer it logically from context.\n"
        "3. Provide a short description (1-2 sentences) summarizing the product based on available data.\n"
        "4. Calculate a health score (0-100) based on ingredients and nutritional content:\n"
        "   - Assign lower scores to products high in sugar, caffeine, saturated fats, or artificial additives.\n"
        "   - Assign higher scores to products with natural ingredients, low sugar/fat, or proven health benefits.\n"
        "5. Calculate a sustainability score (0-100) based on environmental impact:\n"
        "   - Evaluate packaging material (e.g., plastic vs. recyclable materials), recyclability, and carbon footprint.\n"
        "   - Assign higher scores to eco-friendly materials, renewable sourcing, and low environmental impact.\n"
        "6. Use the extracted text and web-sourced data for evidence-based analysis.\n"
        "Return your response strictly as a JSON object with these keys: "
        "'product_info' (containing 'name' and 'description'), 'health_score', and 'sustainability_score'. "
        "In the description, include brief reasoning for the scores based on evidence from the text and data. "
        "If data is insufficient, note it in the description and provide conservative score estimates."
        "if you do not recognise any product in the image then return saying that no product foun in the image"
    )
    
    complete_prompt = user_prompt
    if product_info:
        complete_prompt = f"{user_prompt}\n\nWeb-sourced product information:\n{product_info}"
    
    combined_prompt = f"<s>[SYS] {system_context_prompt} [/SYS]\n[INST] {complete_prompt} [/INST]"
    return combined_prompt

def search_product_information(product_name):
    try:
        health_query = f"{product_name} nutritional value health impact"
        health_results = tavily_client.search(query=health_query, search_depth="advanced")
        
        sustainability_query = f"{product_name} sustainability packaging environmental impact"
        sustainability_results = tavily_client.search(query=sustainability_query, search_depth="advanced")
        
        health_info = "HEALTH DATA:\n"
        for result in health_results.get('results', [])[:3]:
            health_info += f"- {result.get('title')}: {result.get('content')[:200]}...\n"
        
        sustainability_info = "\nSUSTAINABILITY DATA:\n"
        for result in sustainability_results.get('results', [])[:3]:
            sustainability_info += f"- {result.get('title')}: {result.get('content')[:200]}...\n"
        
        return health_info + sustainability_info
    except Exception as e:
        return f"Error retrieving product information: {str(e)}"

def generate_product_analysis(image_path):
    try:
        product_text = analyze_image(image_path)
        product_name = product_text.split("\n")[0].strip() if "\n" in product_text else " ".join(product_text.split()[0:2])
        
        product_info = search_product_information(product_name)
        prompt = f"Analyze the following product based on this description:\n\n{product_text}"
        
        generation_parameters = dict(
            temperature=0.2,
            max_new_tokens=1024,
            top_p=0.96,
            repetition_penalty=1.0,
            do_sample=True,
            seed=42,
        )

        model_ready_prompt = format_prompt_for_model(prompt, product_info)
        generated_text_stream = text_generation_client.text_generation(
            model_ready_prompt,
            **generation_parameters,
            stream=True,
            details=True,
            return_full_text=True
        )

        final_output_text = ""
        for text_segment in generated_text_stream:
            final_output_text += text_segment.token.text

        return final_output_text
    except Exception as e:
        error_json = json.dumps({
            "error": str(e),
            "product_info": {
                "name": "Error",
                "description": f"Failed to analyze image: {str(e)}"
            },
            "health_score": 0,
            "sustainability_score": 0
        })
        return error_json

def extract_json_from_markdown(text):
    """
    Extracts the JSON block from a markdown-formatted string.
    """
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    return text

def classify_product_category(raw_product_analysis):
    """
    Classify the product into a material category.
    This function extracts the JSON portion from the analysis and uses an LLM to determine the category.
    """
    # Extract JSON block from the analysis output
    json_text = extract_json_from_markdown(raw_product_analysis)
    
    system_context_prompt = (
        "You are a classifier tasked with determining the material category of a scanned product based on its JSON analysis. "
        "Given the product name and description, classify it into one of these categories: "
        "plastic_bottle, aluminum_can, glass_bottle, cardboard_box, polythene_bag, paper_waste, chip_packet, plastic_box, tin_box, foam_container. "
        "Return only the category name as plain text, nothing else."
    )
    complete_prompt = f"Classify this product:\n\n{json_text}"
    combined_prompt = f"<s>[SYS] {system_context_prompt} [/SYS]\n[INST] {complete_prompt} [/INST>"
    generation_parameters = dict(
        temperature=0.1,
        max_new_tokens=20,
        top_p=0.9,
        repetition_penalty=1.0,
        do_sample=False,
        seed=42,
    )
    category = ""
    generated_text_stream = text_generation_client.text_generation(
        combined_prompt,
        **generation_parameters,
        stream=True,
        details=True,
        return_full_text=True,
    )
    for text_segment in generated_text_stream:
        category += text_segment.token.text
    return category.strip()

if __name__ == "__main__":
    image_path = r"can.jpg"
    result = generate_product_analysis(image_path)
    print("Generated Product Analysis:")
    print(result)