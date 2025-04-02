# sustaino-main/models/alternatives.py
import os
import json
import re
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import logging
import time # For potential retry delay if used

# Assuming llm_generation_with_retry is in multimodal or a shared utils file
# If not, you need to define it here or import it properly
try:
    from .multimodal import llm_generation_with_retry
except ImportError:
    # Define a basic version or raise an error if retry is needed but not available
    logging.warning("llm_generation_with_retry not found, using direct call.")
    def llm_generation_with_retry(client, prompt, params, max_retries=0, delay=0):
         # Basic non-retry version
         generated_text_stream = client.text_generation(prompt, **params, stream=True, details=True, return_full_text=True)
         final_output_text = ""
         for text_segment in generated_text_stream:
            token_text = getattr(text_segment.token, 'text', '') if hasattr(text_segment, 'token') else ''
            final_output_text += token_text
         # Clean response
         inst_marker = "[/INST]"
         last_inst_pos = final_output_text.rfind(inst_marker)
         if last_inst_pos != -1:
            return final_output_text[last_inst_pos + len(inst_marker):].strip()
         return final_output_text.strip()


load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

hf_api_key = os.getenv("HUGGINGFACE_API_KEY")
if not hf_api_key:
    logging.error("Hugging Face API Key not set in environment variable for alternatives")

# Initialize client with timeout
try:
    text_generation_client_alt = InferenceClient(
        token=hf_api_key, model="mistralai/Mistral-Nemo-Instruct-2407", timeout=60
    )
except Exception as e:
    logging.error(f"Failed to initialize Hugging Face InferenceClient for alternatives: {e}")
    text_generation_client_alt = None

def extract_json_from_markdown(text):
    # Use the same robust extraction as in multimodal.py
    if not isinstance(text, str):
        return text
    json_match_fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if json_match_fenced:
        logging.info("Alternatives: Extracted JSON using fenced code block regex.")
        return json_match_fenced.group(1).strip()
    stripped_text = text.strip()
    if stripped_text.startswith('{') and stripped_text.endswith('}'):
        try:
            json.loads(stripped_text)
            logging.info("Alternatives: Extracted JSON using direct curly brace match (validated).")
            return stripped_text
        except json.JSONDecodeError:
            pass
    logging.warning(f"Alternatives: Could not extract JSON block from text: {text[:100]}...")
    return text


def format_alternatives_prompt(original_product_json_str): # Accept string
    system_context_prompt = "You are a sustainability and health analyst suggesting better alternatives to a consumer product. Based on the provided product analysis (JSON format), suggest ONE realistic alternative product that improves on either health or sustainability. Provide: 1. The alternative product name. 2. A brief reason (1-2 sentences) explaining why it's better, referencing the original product's scores if available. Return your response strictly as a JSON object with keys: 'alternative_product' and 'reason'. If data is insufficient, make a reasonable assumption."
    # Pass the already validated JSON string
    complete_prompt = f"Analyze this product JSON and suggest a better alternative:\n\n{original_product_json_str}"
    combined_prompt = (
        f"<s>[SYS] {system_context_prompt} [/SYS]\n[INST] {complete_prompt} [/INST]"
    )
    return combined_prompt


def generate_alternative_suggestion(product_analysis_input_str): # Renamed input
    """Generates alternative suggestions based on product analysis JSON string."""
    logging.info("Generating alternative suggestion...")
    analysis_data = None
    input_had_error = False

    if not isinstance(product_analysis_input_str, str):
         logging.error("Invalid input type for generate_alternative_suggestion, expected string.")
         return json.dumps({
             "alternative_product": "Error",
             "reason": "Invalid input type received."
         })

    # --- Check if the input string itself represents an error ---
    try:
        potential_error = json.loads(product_analysis_input_str)
        if isinstance(potential_error, dict) and "error" in potential_error:
            logging.warning("Input analysis contains an error. Skipping alternative generation.")
            input_had_error = True
            original_error_msg = potential_error.get("error", "Unknown error in input")
            return json.dumps({
                "alternative_product": "N/A",
                "reason": f"Cannot suggest alternatives: Input analysis failed. ({original_error_msg[:100]}...)",
             })
        analysis_data = potential_error # Store parsed data if valid
    except json.JSONDecodeError:
         # It's not error JSON, proceed assuming it's the LLM output string (might contain JSON)
         logging.info("Input for alternatives is not error JSON, attempting extraction.")
         pass
    # ---

    # Extract the actual analysis JSON string if not already parsed
    if analysis_data:
        json_content_str = json.dumps(analysis_data) # Use already parsed data
    else:
        json_content_str = extract_json_from_markdown(product_analysis_input_str)
        logging.info(f"Extracted JSON content for alternatives: {json_content_str[:200]}...")
        # Try parsing the extracted string now
        try:
             analysis_data = json.loads(json_content_str)
             logging.info("Successfully parsed extracted product data for alternatives.")
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing extracted product analysis JSON for alternatives: {e}")
            logging.error(f"Problematic extracted string: {json_content_str[:500]}")
            return json.dumps({
                "alternative_product": "Error",
                "reason": f"Failed to parse extracted product analysis data: {str(e)}."
            })

    # Basic check for expected structure in the parsed data
    if not isinstance(analysis_data, dict) or "product_info" not in analysis_data:
         logging.error(f"Parsed product data has unexpected structure: {analysis_data}")
         return json.dumps({
            "alternative_product": "Error",
            "reason": "Input product data structure was incomplete or invalid."
         })

    product_name = analysis_data.get("product_info", {}).get("name", "Unknown")
    health_score = analysis_data.get("health_score", "N/A")
    sustainability_score = analysis_data.get("sustainability_score", "N/A")
    logging.info(f"Product: {product_name}, Health: {health_score}, Sustainability: {sustainability_score}")


    # Format prompt using the validated JSON data (re-serialize)
    prompt = format_alternatives_prompt(json.dumps(analysis_data))
    logging.info("Formatted prompt for alternatives LLM.")

    generation_parameters = dict(
        temperature=0.2,
        max_new_tokens=256, # Reduced tokens for a single alternative + reason
        top_p=0.96,
        repetition_penalty=1.05, # Slightly discourage repetition
        do_sample=True,
        seed=42,
    )

    if not text_generation_client_alt:
        logging.error("Alternatives LLM client not initialized.")
        return json.dumps({ "alternative_product": "Error", "reason": "LLM client not available."})

    try:
        logging.info("Sending request to LLM for alternatives...")
        # Use retry helper or direct call
        final_output_text = llm_generation_with_retry(
            client=text_generation_client_alt,
            prompt=prompt,
            params=generation_parameters,
            max_retries=1 # Maybe 1 retry is sufficient here
        )
        logging.info(f"LLM alternatives response (cleaned): {final_output_text[:200]}...")

        # Extract and parse JSON from the LLM response
        json_output_str = extract_json_from_markdown(final_output_text)
        json_output = json.loads(json_output_str) # Parse the extracted JSON
        logging.info("Successfully parsed LLM alternatives response.")

        # Validate expected keys in the response
        if "alternative_product" not in json_output or "reason" not in json_output:
             logging.warning(f"Alternatives LLM response missing keys: {json_output}")
             raise json.JSONDecodeError("Missing expected keys in LLM response", json_output_str, 0)

        return json.dumps(json_output) # Return the final alternatives JSON string

    except json.JSONDecodeError as e:
         logging.error(f"Failed to parse JSON response from alternatives LLM: {e}")
         # Log the cleaned response that failed parsing
         logging.error(f"LLM raw cleaned response was: {final_output_text[:500]}")
         return json.dumps({
            "alternative_product": "Generic Sustainable Option",
            "reason": f"Failed to parse valid JSON from LLM ({e}); suggesting generic alternative.",
         })
    except Exception as e: # Catch other LLM call errors
         logging.exception("Error during alternatives LLM call.")
         return json.dumps({
            "alternative_product": "Error",
            "reason": f"LLM call for alternatives failed: {str(e)}.",
         })
