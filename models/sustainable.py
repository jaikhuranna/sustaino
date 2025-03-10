from huggingface_hub import InferenceClient
import os
import re
from dotenv import load_dotenv
from tavily import TavilyClient

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

def format_prompt_for_model(user_prompt, product_info=None):
    system_context_prompt = (
        f"You are a sustainability and health analyst specializing in consumer product evaluation. "
        f"Your task is to analyze product information from extracted text and web research to provide: "
        f"1. Product name and a short description (1-2 sentences) based on available data. "
        f"2. Health rating score (0-100) based on ingredients, nutritional value, allergens, and health impacts. "
        f"3. Sustainability score (0-100) based on packaging, recyclability, carbon footprint, and sourcing. "
        f"Use the provided extracted text and web-sourced data for evidence-based analysis. "
        f"Return your response strictly as a JSON object with these keys: "
        f"'product_info' (containing 'name' and 'description'), 'health_score', and 'sustainability_score'. "
        f"Include brief reasoning in the description for the scores. "
        f"If data is insufficient, note it in the description and provide conservative estimates for scores."
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

def generate_product_analysis(
    extracted_text,
    creativity_level=0.2,
    max_tokens_to_generate=1024,
    top_p_filtering_ratio=0.96,
    repetition_penalty=1.0,
):
    product_name_match = re.search(r'(?i)product:?\s*([^,\n.]+)', extracted_text)
    if product_name_match:
        product_name = product_name_match.group(1).strip()
    else:
        words = extracted_text.split()
        product_name = " ".join(words[:min(5, len(words))]).strip()
    
    product_info = search_product_information(product_name)
    
    prompt = f"Analyze the following product based on the extracted text:\n\n{extracted_text}"
    
    creativity_level = float(creativity_level)
    if creativity_level < 1e-2:
        creativity_level = 1e-2
    top_p_filtering_ratio = float(top_p_filtering_ratio)

    generation_parameters = dict(
        temperature=creativity_level,
        max_new_tokens=max_tokens_to_generate,
        top_p=top_p_filtering_ratio,
        repetition_penalty=repetition_penalty,
        do_sample=True,
        seed=42,
    )

    model_ready_prompt = format_prompt_for_model(prompt, product_info)

    generated_text_stream = text_generation_client.text_generation(
        model_ready_prompt, **generation_parameters, stream=True, details=True, return_full_text=True
    )

    final_output_text = ""
    for text_segment in generated_text_stream:
        final_output_text += text_segment.token.text

    return final_output_text