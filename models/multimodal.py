
# sustaino-main/models/multimodal.py
import os
import json
import re
import requests
from dotenv import load_dotenv
from tavily import TavilyClient
from huggingface_hub import InferenceClient, hf_hub_download
from huggingface_hub.utils import HfHubHTTPError # Import specific error
import logging
import time # Import time for retry delay

load_dotenv()
print("Environment Keys Loaded:", bool(os.getenv('HUGGINGFACE_API_KEY')))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
if not hf_api_key:
    logging.error("Hugging Face API Key not set in environment variable")

# Initialize client with timeout
try:
    text_generation_client = InferenceClient(
        token=hf_api_key,
        model="mistralai/Mistral-Nemo-Instruct-2407",
        timeout=120 # Keep timeout
    )
except Exception as e:
    logging.error(f"Failed to initialize Hugging Face InferenceClient: {e}")
    text_generation_client = None # Set to None if initialization fails

tavily_api_key = os.getenv('TAVILY_API_KEY')
if not tavily_api_key:
    logging.error("Tavily API Key not set in environment variable")
    tavily_client = None # Set to None if key is missing
else:
    try:
        tavily_client = TavilyClient(api_key=tavily_api_key)
    except Exception as e:
        logging.error(f"Failed to initialize TavilyClient: {e}")
        tavily_client = None

# --- Helper function for retry ---
def llm_generation_with_retry(client, prompt, params, max_retries=2, delay=3):
    """Attempts LLM generation with retries on specific errors."""
    if not client:
        raise Exception("LLM client is not initialized.")

    retries = 0
    while retries <= max_retries:
        try:
            logging.info(f"Attempt {retries + 1}/{max_retries + 1}: Sending request to LLM...")
            generated_text_stream = client.text_generation(
                prompt,
                **params,
                stream=True,
                details=True,
                return_full_text=True # Get full response including prompt potentially
            )
            final_output_text = ""
            for text_segment in generated_text_stream:
                # Ensure text_segment has text attribute
                token_text = getattr(text_segment.token, 'text', '') if hasattr(text_segment, 'token') else ''
                final_output_text += token_text


            logging.info("LLM call successful.")

            # Clean the response (remove prompt if included)
            inst_marker = "[/INST]"
            last_inst_pos = final_output_text.rfind(inst_marker)
            if last_inst_pos != -1:
                cleaned_output = final_output_text[last_inst_pos + len(inst_marker):].strip()
            else:
                logging.warning("Could not find [/INST] marker in LLM response, using full text.")
                cleaned_output = final_output_text.strip() # Use full text but strip whitespace

            logging.info(f"LLM Raw Output (cleaned): {cleaned_output[:200]}...")
            # Basic check if the cleaned output looks like JSON start/end
            if not (cleaned_output.startswith('{') and cleaned_output.endswith('}')):
                 logging.warning(f"Cleaned LLM output doesn't look like JSON: {cleaned_output[:100]}...")
                 # Depending on strictness, you could raise an error here or let parsing handle it

            return cleaned_output # Success

        except (HfHubHTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout, Exception) as e:
            error_type = type(e).__name__
            logging.warning(f"Attempt {retries + 1} failed with {error_type}: {e}")

            # Determine if error is retriable
            is_retriable = False
            if "ConnectionResetError" in str(e) or "Timeout" in error_type:
                is_retriable = True
            elif isinstance(e, HfHubHTTPError) and e.response and e.response.status_code >= 500:
                 is_retriable = True

            if is_retriable and retries < max_retries:
                retries += 1
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                # Max retries reached or non-retriable error
                logging.error(f"LLM generation failed after {retries + 1} attempt(s). Error: {error_type}: {e}")
                raise Exception(f"LLM generation failed ({error_type}): {e}") from e # Raise the captured exception

    # This line should theoretically not be reached if the loop logic is correct
    raise Exception("LLM generation failed unexpectedly after retry loop.")


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return image_file.read()

def analyze_image(image_path):
    """Analyzes the image using the BLIP captioning model."""
    api_url = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
    headers = {
        "Authorization": f"Bearer {hf_api_key}",
        "Content-Type": "image/jpeg"
    }
    if not hf_api_key:
        raise Exception("Hugging Face API Key not configured for image analysis.")
    try:
        image_data = encode_image_to_base64(image_path)
        logging.info(f"Sending image ({len(image_data)} bytes) to BLIP API...")
        response = requests.post(api_url, headers=headers, data=image_data, timeout=(15, 60)) # 15s connect, 60s read
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        logging.info("BLIP API call successful.")
        # --- Safely access response data ---
        response_data = response.json()
        if isinstance(response_data, list) and len(response_data) > 0 and "generated_text" in response_data[0]:
             return response_data[0]["generated_text"]
        else:
             logging.error(f"Unexpected BLIP API response format: {response_data}")
             raise Exception("Invalid response format from image analysis (BLIP): Missing 'generated_text'")
        # ---
    except requests.exceptions.Timeout as e:
        logging.error(f"BLIP API request timed out: {e}")
        raise Exception(f"Image analysis (BLIP) timed out: {e}") from e
    except requests.exceptions.RequestException as e:
        status_code = e.response.status_code if e.response else 'N/A'
        response_text = e.response.text if e.response else 'N/A'
        logging.error(f"BLIP API request failed: {e}. Status: {status_code}, Response: {response_text[:200]}...") # Log snippet
        raise Exception(f"Image analysis (BLIP) failed: {e}") from e
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from BLIP API response: {e}")
        raise Exception(f"Invalid JSON response from image analysis (BLIP): {e}") from e
    except (KeyError, IndexError) as e:
        logging.error(f"Failed to parse BLIP API response structure: {e}")
        raise Exception(f"Invalid response format from image analysis (BLIP): {e}") from e


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
    )

    complete_prompt = user_prompt
    if product_info:
        complete_prompt = f"{user_prompt}\n\nWeb-sourced product information:\n{product_info}"

    combined_prompt = f"<s>[SYS] {system_context_prompt} [/SYS]\n[INST] {complete_prompt} [/INST]"
    return combined_prompt

def search_product_information(product_name):
    """Searches Tavily for product health and sustainability info."""
    if not tavily_client:
        logging.warning("Tavily client not initialized. Skipping web search.")
        return "Web search skipped (Tavily client not available)."
    try:
        logging.info(f"Searching Tavily for '{product_name}' health info...")
        health_query = f"{product_name} nutritional value health impact"
        health_results = tavily_client.search(query=health_query, search_depth="advanced")
        logging.info("Tavily health search successful.")

        logging.info(f"Searching Tavily for '{product_name}' sustainability info...")
        sustainability_query = f"{product_name} sustainability packaging environmental impact"
        sustainability_results = tavily_client.search(query=sustainability_query, search_depth="advanced")
        logging.info("Tavily sustainability search successful.")

        health_info = "HEALTH DATA:\n"
        for result in health_results.get('results', [])[:3]: # Limit results processed
            health_info += f"- {result.get('title', 'N/A')}: {result.get('content', 'N/A')[:200]}...\n"

        sustainability_info = "\nSUSTAINABILITY DATA:\n"
        for result in sustainability_results.get('results', [])[:3]: # Limit results processed
            sustainability_info += f"- {result.get('title', 'N/A')}: {result.get('content', 'N/A')[:200]}...\n"

        combined_info = health_info + sustainability_info
        logging.info(f"Combined web search results length: {len(combined_info)}")
        return combined_info

    except Exception as e:
        logging.error(f"Tavily search failed: {e}")
        return f"Error retrieving product information from web search: {str(e)}"


def generate_product_analysis(image_path):
    """Generates the main product analysis JSON string."""
    product_text = "No image analysis performed." # Default
    product_name = "Unknown Product"
    product_info = "No web data available."

    try:
        # Step 1: Analyze Image
        try:
            logging.info(f"Analyzing image: {image_path}")
            product_text = analyze_image(image_path)
            logging.info(f"Image analysis result: {product_text[:100]}...")
            # Attempt to extract a reasonable product name
            lines = product_text.split('\n')
            first_line = lines[0].strip()
            # Take first few words if the line is long, or the whole line if short
            potential_name = " ".join(first_line.split()[:5]) if len(first_line.split()) > 5 else first_line
            product_name = potential_name or "Inferred Product" # Ensure not empty
            logging.info(f"Extracted product name: {product_name}")
        except Exception as e:
            logging.error(f"Image analysis step failed: {e}")
            product_text = f"Error during image analysis: {e}. Proceeding without image text."
            # Keep product_name as "Unknown Product"


        # Step 2: Search Web Info
        if product_name != "Unknown Product" and product_name != "Inferred Product":
             try:
                 logging.info(f"Searching web info for: {product_name}")
                 product_info = search_product_information(product_name)
                 logging.info("Web search step completed.")
             except Exception as e:
                 logging.error(f"Web search step failed: {e}")
                 product_info = f"Error during web search: {e}. Proceeding without web data."
        else:
            logging.warning("Skipping web search due to unknown product name.")


        # Step 3: Generate Analysis with LLM (using retry helper)
        logging.info("Formatting prompt for LLM analysis...")
        prompt_for_llm = f"Analyze the following product based on this description:\n\n{product_text}"
        model_ready_prompt = format_prompt_for_model(prompt_for_llm, product_info)

        generation_parameters = dict(
            temperature=0.2,
            max_new_tokens=800, # Keep reduced token count from experiment
            top_p=0.96,
            repetition_penalty=1.0,
            do_sample=True, # Sample for variability if needed, False for deterministic
            seed=42,
        )

        # Use the retry helper function
        final_output_text = llm_generation_with_retry(
            client=text_generation_client,
            prompt=model_ready_prompt,
            params=generation_parameters
        )
        # At this point, final_output_text should be the cleaned JSON string or raise an exception
        return final_output_text


    except Exception as e:
        logging.exception("An error occurred in generate_product_analysis pipeline")
        error_message = f"Analysis pipeline failed: {str(e)}"
        error_details = f"Type: {type(e).__name__}, Message: {str(e)}"
        # Construct the error JSON string
        error_json_str = json.dumps({
            "error": error_message,
            "error_details": error_details,
            "product_info": {
                "name": product_name if product_name else "Error State",
                "description": f"Failed to complete analysis. Error occurred: {error_details}"
            },
            "health_score": 0,
            "sustainability_score": 0
        })
        return error_json_str # Return the error JSON as a string


def extract_json_from_markdown(text):
    """
    Extracts the JSON block from a markdown-formatted string.
    Handles optional 'json' language specifier and direct JSON.
    """
    if not isinstance(text, str):
        logging.warning("extract_json_from_markdown received non-string input.")
        return text # Return input if not a string

    # Try to find ```json { ... } ```
    json_match_fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if json_match_fenced:
        logging.info("Extracted JSON using fenced code block regex.")
        return json_match_fenced.group(1).strip()

    # Try to find { ... } directly if not fenced, ensure it's the main content
    # Check if the text *mostly* consists of a JSON object
    stripped_text = text.strip()
    if stripped_text.startswith('{') and stripped_text.endswith('}'):
        # Attempt to validate if it's likely JSON before returning
        try:
            json.loads(stripped_text) # Quick validation parse
            logging.info("Extracted JSON using direct curly brace match (validated).")
            return stripped_text
        except json.JSONDecodeError:
            logging.warning("Direct curly brace match failed JSON validation.")
            pass # Fall through if it's not valid JSON

    # Fallback if no clear JSON structure found
    logging.warning(f"Could not extract JSON block from text: {text[:100]}...")
    return text # Return original text


def classify_product_category(raw_product_analysis_str):
    """
    Classify the product into a material category based on analysis string.
    Handles error input and uses an LLM for classification.
    """
    logging.info("Attempting to classify product category...")
    analysis_data = None

    # --- Check if the input string represents an error JSON ---
    try:
        potential_error = json.loads(raw_product_analysis_str)
        if isinstance(potential_error, dict) and "error" in potential_error:
            logging.warning("Input analysis contains an error key. Skipping classification.")
            return "classification_skipped_due_to_error"
        analysis_data = potential_error # Store parsed data if valid
    except json.JSONDecodeError:
        # Input is not error JSON, might be the raw LLM output or already extracted JSON
        logging.info("Input for classification is not error JSON, attempting extraction/parsing.")
        pass
    # ---

    # Extract or use the potentially already parsed JSON text
    if analysis_data:
        # Use already parsed data if available
        json_text_for_prompt = json.dumps(analysis_data)
    else:
        # If not parsed above, extract from the raw string
        json_text_for_prompt = extract_json_from_markdown(raw_product_analysis_str)
        # Try parsing the extracted text for better prompt content if possible
        try:
            analysis_data = json.loads(json_text_for_prompt)
            # Use specific fields if helpful for classification
            name = analysis_data.get("product_info", {}).get("name", "Unknown")
            desc = analysis_data.get("product_info", {}).get("description", "")
            json_text_for_prompt = f"Name: {name}\nDescription: {desc}" # Use specific fields
            logging.info("Using specific fields for classification prompt.")
        except json.JSONDecodeError:
             logging.warning("Could not parse extracted text for classification prompt, using raw extracted text.")
             # Keep json_text_for_prompt as the extracted string

    system_context_prompt = (
        "You are a classifier determining the primary material category of a product based on its analysis data (name/description). "
        "Classify it into ONLY ONE of these exact categories: "
        "plastic_bottle, aluminum_can, glass_bottle, cardboard_box, polythene_bag, paper_waste, chip_packet, plastic_box, tin_box, foam_container. "
        "Return ONLY the single category name (e.g., 'plastic_bottle'), nothing else."
    )
    # Use the potentially refined json_text_for_prompt
    complete_prompt = f"Classify the product based on this data:\n\n{json_text_for_prompt}"
    combined_prompt = f"<s>[SYS] {system_context_prompt} [/SYS]\n[INST] {complete_prompt} [/INST]"

    generation_parameters = dict(
        temperature=0.1,
        max_new_tokens=30,
        top_p=0.9,
        repetition_penalty=1.1, # Slightly increase to discourage repetition
        do_sample=False, # Deterministic classification
        seed=42,
    )

    category = "unknown_category" # Default
    logging.info("Sending request to LLM for classification...")
    try:
        category_result = llm_generation_with_retry(
             client=text_generation_client,
             prompt=combined_prompt,
             params=generation_parameters,
             max_retries=1 # Less critical, only 1 retry
        )

        # Clean the response aggressively
        category = category_result.strip().lower()
        # Remove potential markdown or extra words
        category = re.sub(r'[^a-z_]', '', category.split()[0]) # Take first word, remove non-alpha/underscore

        logging.info(f"LLM classification result (cleaned): {category}")

        # Validate against known categories
        known_categories = [
            "plastic_bottle", "aluminum_can", "glass_bottle", "cardboard_box",
            "polythene_bag", "paper_waste", "chip_packet", "plastic_box",
            "tin_box", "foam_container"
        ]
        if category not in known_categories:
            logging.warning(f"LLM returned unknown or invalid category '{category}'. Mapping to 'unknown_category'.")
            category = "unknown_category"
        return category

    except Exception as e:
        logging.error(f"Error during LLM classification: {e}")
        return "unknown_category" # Return default on error


if __name__ == "__main__":
    image_path = os.path.join(os.path.dirname(__file__), "can.jpg")
    if not os.path.exists(image_path):
         print(f"Error: Test image not found at {image_path}")
    else:
        print(f"Testing with image: {image_path}")
        # generate_product_analysis now returns a JSON string
        result_str = generate_product_analysis(image_path)
        print("\nGenerated Product Analysis (JSON String):")
        # Try to pretty-print if it's valid JSON
        try:
            parsed = json.loads(result_str)
            print(json.dumps(parsed, indent=2))
            is_error_result = isinstance(parsed, dict) and "error" in parsed
        except json.JSONDecodeError:
             print(result_str) # Print raw string if not valid JSON
             is_error_result = True # Treat as error if analysis didn't produce valid JSON

        if not is_error_result:
             print("\nClassifying Product Category...")
             # Pass the result string to the classification function
             category = classify_product_category(result_str)
             print(f"Classified Category: {category}")
        else:
             print("\nSkipping classification due to analysis error or invalid JSON output.")
