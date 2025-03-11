import os
import re
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
if not hf_api_key:
    raise ValueError("Hugging Face API Key not set in environment variable")

text_generation_client = InferenceClient(token=hf_api_key, model="mistralai/Mistral-Nemo-Instruct-2407")

def extract_field(text, field_name):
    # Use a simple regex to extract the requested field.
    pattern = rf"{field_name}:\s*(.*)"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return ""

def generate_alternative_suggestion(analysis_text):
    # Extract key fields for context (if available)
    product_name = extract_field(analysis_text, "Product Name")
    health_score = extract_field(analysis_text, "Health Score")
    sustainability_score = extract_field(analysis_text, "Sustainability Score")
    
    prompt = (
        "You are a sustainability and health analyst. Based on the product analysis below, suggest two alternative products that have improved health or sustainability characteristics. "
        "For each alternative, provide its name and a brief explanation. Use the following format exactly:\n\n"
        "Alternative 1: <Name> - <Explanation>\n"
        "Alternative 2: <Name> - <Explanation>\n\n"
        "Product Analysis:\n" + analysis_text + "\n\nYour suggestions:\n"
    )
    
    generation_parameters = dict(
        temperature=0.2,
        max_new_tokens=150,
        top_p=0.96,
        repetition_penalty=1.0,
        do_sample=True,
        seed=42,
    )
    
    generated_text_stream = text_generation_client.text_generation(
        prompt,
        **generation_parameters,
        stream=True,
        details=True,
        return_full_text=True,
    )
    
    final_output_text = ""
    for text_segment in generated_text_stream:
        final_output_text += text_segment.token.text
    
    return final_output_text

if __name__ == "__main__":
    sample_analysis = (
        "Product Name: Sample Drink\n"
        "Description: A beverage with moderate sugar and artificial additives.\n"
        "Health Score: 50\n"
        "Sustainability Score: 45\n"
    )
    alt_suggestion = generate_alternative_suggestion(sample_analysis)
    print("Alternative Suggestion:")
    print(alt_suggestion)