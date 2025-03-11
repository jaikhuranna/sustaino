import os
import requests
from dotenv import load_dotenv
from tavily import TavilyClient
from huggingface_hub import InferenceClient

load_dotenv()
print("Environment Keys Loaded:", os.getenv('HUGGINGFACE_API_KEY'))

hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
if not hf_api_key:
    raise ValueError("Hugging Face API Key not set in environment variable")

# Instantiate the text-generation client
text_generation_client = InferenceClient(token=hf_api_key, model="mistralai/Mistral-Nemo-Instruct-2407")

tavily_api_key = os.getenv('TAVILY_API_KEY')
if not tavily_api_key:
    raise ValueError("Tavily API Key not set in environment variable")
tavily_client = TavilyClient(api_key=tavily_api_key)

def encode_image_to_bytes(image_path):
    with open(image_path, "rb") as image_file:
        return image_file.read()

def analyze_image(image_path):
    api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    headers = {
        "Authorization": f"Bearer {hf_api_key}",
        "Content-Type": "image/jpeg"
    }
    image_data = encode_image_to_bytes(image_path)
    try:
        response = requests.post(api_url, headers=headers, data=image_data)
    except Exception:
        return "Demo Product\nThis is a fallback description due to API error."
    
    if response.status_code == 200:
        try:
            return response.json()[0]["generated_text"]
        except Exception:
            return "Demo Product\nThis is a fallback description due to parsing error."
    else:
        return "Demo Product\nThis is a fallback description due to API error."

def format_prompt_for_model(user_prompt, product_info=None):
    # New strict prompt: exactly four lines, one per field.
    prompt = (
        "You are a professional sustainability and health analyst. "
        "Based on the product description below, return exactly four lines formatted exactly as follows:\n\n"
        "Product Name: <concise product name>\n"
        "Description: <a brief description in one or two sentences>\n"
        "Health Score: <an integer from 0 to 100>\n"
        "Sustainability Score: <an integer from 0 to 100>\n\n"
        "Do not include any extra commentary or repetition. "
        "Ensure that each field is on its own line exactly as specified.\n\n"
        "Product Description:\n" + user_prompt
    )
    if product_info:
        prompt += "\nAdditional Information:\n" + product_info
    return prompt

def search_product_information(product_name):
    try:
        health_query = f"{product_name} nutritional value health impact"
        health_results = tavily_client.search(query=health_query, search_depth="advanced")
        
        sustainability_query = f"{product_name} sustainability packaging environmental impact"
        sustainability_results = tavily_client.search(query=sustainability_query, search_depth="advanced")
        
        health_info = "HEALTH DATA:\n"
        for result in health_results.get('results', [])[:3]:
            health_info += f"- {result.get('title')}: {result.get('content')[:100]}...\n"
        
        sustainability_info = "\nSUSTAINABILITY DATA:\n"
        for result in sustainability_results.get('results', [])[:3]:
            sustainability_info += f"- {result.get('title')}: {result.get('content')[:100]}...\n"
        
        return health_info + sustainability_info
    except Exception as e:
        return f"Error retrieving product information: {str(e)}"

def generate_product_analysis(image_path):
    try:
        product_text = analyze_image(image_path)
        # Use fallback if the API returns a demo message.
        if product_text.startswith("Demo Product"):
            return (
                "Product Name: Demo Product\n"
                "Description: This is a fallback product description.\n"
                "Health Score: 75\n"
                "Sustainability Score: 80\n"
            )
        
        # Extract a tentative product name from the first line.
        product_name = product_text.split("\n")[0].strip() if "\n" in product_text else " ".join(product_text.split()[0:2])
        
        product_info = search_product_information(product_name)
        prompt = f"Analyze the following product:\n\n{product_text}\n"
        full_prompt = format_prompt_for_model(prompt, product_info)
        
        generation_parameters = dict(
            temperature=0.2,
            max_new_tokens=256,
            top_p=0.96,
            repetition_penalty=1.0,
            do_sample=True,
            seed=42,
        )
        
        generated_text_stream = text_generation_client.text_generation(
            full_prompt,
            **generation_parameters,
            stream=True,
            details=True,
            return_full_text=True
        )
        
        final_output_text = ""
        for text_segment in generated_text_stream:
            final_output_text += text_segment.token.text
        
        # If the expected fields are missing, provide a fallback.
        if "Product Name:" not in final_output_text:
            final_output_text = (
                f"Product Name: {product_name}\n"
                f"Description: {final_output_text}\n"
                "Health Score: 70\n"
                "Sustainability Score: 70\n"
            )
        return final_output_text
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

def classify_product_category(analysis_text):
    # Use text generation to classify the product category.
    prompt = (
        "Based on the following product analysis, classify the product into one of these categories:\n"
        "plastic_bottle, aluminum_can, glass_bottle, cardboard_box, polythene_bag, paper_waste, chip_packet, plastic_box, tin_box, foam_container.\n"
        "Return only the category name.\n\n" + analysis_text
    )
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
        prompt,
        **generation_parameters,
        stream=True,
        details=True,
        return_full_text=True,
    )
    for text_segment in generated_text_stream:
        category += text_segment.token.text
    return category.strip()

if __name__ == "__main__":
    image_path = "can.jpg"
    result = generate_product_analysis(image_path)
    print("Generated Product Analysis:")
    print(result)