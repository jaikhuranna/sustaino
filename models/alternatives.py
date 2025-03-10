import os
import json
import re
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
if not hf_api_key:
    raise ValueError("Hugging Face API Key not set in environment variable")
text_generation_client = InferenceClient(
    token=hf_api_key, model="mistralai/Mistral-Nemo-Instruct-2407"
)


def extract_json_from_markdown(text):
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        return json_match.group(1)

    json_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if json_match:
        return json_match.group(1)

    return text


def format_alternatives_prompt(original_product_json):
    system_context_prompt = "You are a sustainability and health analyst tasked with suggesting better alternatives to a consumer product. Based on the provided product analysis (in JSON format), suggest two alternative product that improves on either health or sustainability (or both). Provide: 1. The alternative product name. 2. A brief reason (1-2 sentences) explaining why it's better, referencing the original product's health_score and sustainability_score. Return your response strictly as a JSON object with keys: 'alternative_product' and 'reason'. Use your knowledge to suggest a realistic alternative; if data is insufficient, make a reasonable assumption and note it in the reason."

    complete_prompt = f"Analyze this product JSON and suggest a better alternative:\n\n{original_product_json}"

    combined_prompt = (
        f"<s>[SYS] {system_context_prompt} [/SYS]\n[INST] {complete_prompt} [/INST]"
    )
    return combined_prompt


def generate_alternative_suggestion(product_analysis_json):

    try:
        json_content = extract_json_from_markdown(product_analysis_json)

        product_data = json.loads(json_content)

        product_name = product_data["product_info"]["name"]
        health_score = product_data["health_score"]
        sustainability_score = product_data["sustainability_score"]
    except (json.JSONDecodeError, KeyError) as e:
        return json.dumps(
            {
                "alternative_product": "Unknown Alternative",
                "reason": f"Error parsing original product data: {str(e)}. Suggesting a generic alternative.",
            }
        )

    prompt = format_alternatives_prompt(json.dumps(product_data))

    generation_parameters = dict(
        temperature=0.2,
        max_new_tokens=512,
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

    try:
        json_output_text = extract_json_from_markdown(final_output_text)
        json_output = json.loads(json_output_text)
        return json.dumps(json_output)
    except json.JSONDecodeError:
        return json.dumps(
            {
                "alternative_product": "Generic Sustainable Option",
                "reason": "Failed to generate valid JSON; suggesting a generic alternative based on typical improvements.",
            }
        )