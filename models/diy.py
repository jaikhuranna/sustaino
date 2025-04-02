# sustaino-main/models/diy.py
import os
import json
import re # Import re for cleaning
from dotenv import load_dotenv
# Import necessary functions carefully
try:
    from .multimodal import classify_product_category, extract_json_from_markdown
except ImportError as e:
     raise ImportError(f"Could not import required functions from .multimodal: {e}") from e

import logging

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


DIY_CATEGORIES = {
    "plastic_bottle": [
        {"name": "Bird Feeder", "youtube_link": "https://www.youtube.com/watch?v=12345", "thumbnail": "https://img.youtube.com/vi/12345/0.jpg"},
        {"name": "Planter", "youtube_link": "https://www.youtube.com/watch?v=67890", "thumbnail": "https://img.youtube.com/vi/67890/0.jpg"},
        {"name": "Storage Container", "youtube_link": "https://www.youtube.com/watch?v=abcde", "thumbnail": "https://img.youtube.com/vi/abcde/0.jpg"}
    ],
    "aluminum_can": [
        {"name": "Pen Holder", "youtube_link": "https://www.youtube.com/watch?v=xyz12", "thumbnail": "https://img.youtube.com/vi/xyz12/0.jpg"},
        {"name": "Lantern", "youtube_link": "https://www.youtube.com/watch?v=pqr34", "thumbnail": "https://img.youtube.com/vi/pqr34/0.jpg"},
        {"name": "Wind Chime", "youtube_link": "https://www.youtube.com/watch?v=lmn56", "thumbnail": "https://img.youtube.com/vi/lmn56/0.jpg"}
    ],
    "glass_bottle": [
        {"name": "Vase", "youtube_link": "https://www.youtube.com/watch?v=def78", "thumbnail": "https://img.youtube.com/vi/def78/0.jpg"},
        {"name": "Candle Holder", "youtube_link": "https://www.youtube.com/watch?v=ghi90", "thumbnail": "https://img.youtube.com/vi/ghi90/0.jpg"},
        {"name": "Terrarium", "youtube_link": "https://www.youtube.com/watch?v=jkl12", "thumbnail": "https://img.youtube.com/vi/jkl12/0.jpg"}
    ],
    "cardboard_box": [
        {"name": "Storage Bin", "youtube_link": "https://www.youtube.com/watch?v=mno34", "thumbnail": "https://img.youtube.com/vi/mno34/0.jpg"},
        {"name": "Cat House", "youtube_link": "https://www.youtube.com/watch?v=pqr56", "thumbnail": "https://img.youtube.com/vi/pqr56/0.jpg"},
        {"name": "Desk Organizer", "youtube_link": "https://www.youtube.com/watch?v=stu78", "thumbnail": "https://img.youtube.com/vi/stu78/0.jpg"}
    ],
    "polythene_bag": [
        {"name": "Reusable Tote", "youtube_link": "https://www.youtube.com/watch?v=vwx89", "thumbnail": "https://img.youtube.com/vi/vwx89/0.jpg"},
        {"name": "Woven Mat", "youtube_link": "https://www.youtube.com/watch?v=yza12", "thumbnail": "https://img.youtube.com/vi/yza12/0.jpg"},
        {"name": "Rain Protector", "youtube_link": "https://www.youtube.com/watch?v=bcd34", "thumbnail": "https://img.youtube.com/vi/bcd34/0.jpg"}
    ],
    "paper_waste": [
        {"name": "Paper Beads", "youtube_link": "https://www.youtube.com/watch?v=efg56", "thumbnail": "https://img.youtube.com/vi/efg56/0.jpg"},
        {"name": "Seedling Pots", "youtube_link": "https://www.youtube.com/watch?v=hij78", "thumbnail": "https://img.youtube.com/vi/hij78/0.jpg"},
        {"name": "Gift Tags", "youtube_link": "https://www.youtube.com/watch?v=klm90", "thumbnail": "https://img.youtube.com/vi/klm90/0.jpg"}
    ],
    "chip_packet": [
        {"name": "Keychain Pouch", "youtube_link": "https://www.youtube.com/watch?v=nop12", "thumbnail": "https://img.youtube.com/vi/nop12/0.jpg"},
        {"name": "Bookmark", "youtube_link": "https://www.youtube.com/watch?v=qrs34", "thumbnail": "https://img.youtube.com/vi/qrs34/0.jpg"},
        {"name": "Mini Wallet", "youtube_link": "https://www.youtube.com/watch?v=tuv56", "thumbnail": "https://img.youtube.com/vi/tuv56/0.jpg"}
    ],
    "plastic_box": [
        {"name": "Jewelry Organizer", "youtube_link": "https://www.youtube.com/watch?v=wxy78", "thumbnail": "https://img.youtube.com/vi/wxy78/0.jpg"},
        {"name": "Seed Starter", "youtube_link": "https://www.youtube.com/watch?v=zab90", "thumbnail": "https://img.youtube.com/vi/zab90/0.jpg"},
        {"name": "Tool Holder", "youtube_link": "https://www.youtube.com/watch?v=cde12", "thumbnail": "https://img.youtube.com/vi/cde12/0.jpg"}
    ],
    "tin_box": [
        {"name": "Spice Container", "youtube_link": "https://www.youtube.com/watch?v=fgh34", "thumbnail": "https://img.youtube.com/vi/fgh34/0.jpg"},
        {"name": "Sewing Kit", "youtube_link": "https://www.youtube.com/watch?v=ijk56", "thumbnail": "https://img.youtube.com/vi/ijk56/0.jpg"},
        {"name": "First Aid Box", "youtube_link": "https://www.youtube.com/watch?v=lmn78", "thumbnail": "https://img.youtube.com/vi/lmn78/0.jpg"}
    ],
    "foam_container": [
        {"name": "Pin Cushion", "youtube_link": "https://www.youtube.com/watch?v=opq90", "thumbnail": "https://img.youtube.com/vi/opq90/0.jpg"},
        {"name": "Stamp Block", "youtube_link": "https://www.youtube.com/watch?v=rst12", "thumbnail": "https://img.youtube.com/vi/rst12/0.jpg"},
        {"name": "Kids' Puzzle", "youtube_link": "https://www.youtube.com/watch?v=uvw34", "thumbnail": "https://img.youtube.com/vi/uvw34/0.jpg"}
    ],
    # Add defaults for fallback cases
    "unknown_category": [],
    "classification_skipped_due_to_error": []
}

def generate_diy_suggestions(product_analysis_input_str):
    """
    Generate DIY suggestions based on product analysis string.
    Handles error input and uses hardcoded categories based on classification.

    Args:
        product_analysis_input_str (str): The raw product analysis text/JSON string.

    Returns:
        str: JSON string containing DIY suggestions list and a status message.
    """
    logging.info("Generating DIY suggestions...")
    analysis_data = None
    input_had_error = False
    original_error_msg = ""

    if not isinstance(product_analysis_input_str, str):
         logging.error("Invalid input type for generate_diy_suggestions, expected string.")
         return json.dumps({
             "diy_ideas": [],
             "message": "Invalid input type received."
         })

    # --- Check if the input string itself represents an error ---
    try:
        potential_error = json.loads(product_analysis_input_str)
        if isinstance(potential_error, dict) and "error" in potential_error:
            logging.warning("Input analysis contains an error. Skipping DIY generation.")
            input_had_error = True
            original_error_msg = potential_error.get("error", "Unknown error in input")
            return json.dumps({
                "diy_ideas": [],
                "message": f"Cannot suggest DIY: Input analysis failed. ({original_error_msg[:100]}...)",
            })
        analysis_data = potential_error # Store parsed data if valid
    except json.JSONDecodeError:
        # Input is not error JSON, might be the raw LLM output or already extracted JSON
        logging.info("Input for DIY is not error JSON, attempting extraction.")
        pass
    # ---

    # Extract or use the potentially already parsed JSON text
    if analysis_data:
         json_content_str = json.dumps(analysis_data) # Use already parsed data
    else:
         json_content_str = extract_json_from_markdown(product_analysis_input_str)
         logging.info(f"Extracted JSON content for DIY: {json_content_str[:200]}...")
         # Try parsing the extracted string now to get sustainability score
         try:
             analysis_data = json.loads(json_content_str)
             logging.info("Successfully parsed extracted product data for DIY.")
         except json.JSONDecodeError as e:
            logging.error(f"Error parsing extracted product analysis JSON for DIY: {e}")
            logging.error(f"Problematic extracted string: {json_content_str[:500]}")
            return json.dumps({
                "diy_ideas": [],
                "message": f"Error parsing extracted product data for DIY: {str(e)}"
            })

    # Check sustainability score threshold using parsed data
    try:
        # Ensure analysis_data is a dict before accessing keys
        if not isinstance(analysis_data, dict):
             raise TypeError("Parsed analysis data is not a dictionary.")

        # Use .get for safer access, default to a high score if missing to avoid unnecessary DIY
        sustainability_score = analysis_data.get('sustainability_score', 100)

        # Ensure score is an integer or float for comparison
        if isinstance(sustainability_score, (int, float)):
            if sustainability_score >= 70:
                 logging.info(f"Sustainability score ({sustainability_score}) >= 70. No DIY needed.")
                 return json.dumps({
                     "diy_ideas": [],
                     "message": f"Product is sustainable (Score: {sustainability_score} >= 70), no DIY suggestions needed."
                 })
        else:
             logging.warning(f"Sustainability score has unexpected type: {type(sustainability_score)}. Assuming high score.")
             # If score is not a number, assume it's sustainable to be safe
             return json.dumps({
                 "diy_ideas": [],
                 "message": "Could not determine numerical sustainability score. Assuming sustainable."
             })

    except (TypeError, KeyError) as e:
         logging.error(f"Error accessing sustainability score: {e}")
         return json.dumps({
             "diy_ideas": [],
             "message": f"Could not read sustainability score from analysis data: {e}"
         })


    # Classify the category using the original input string
    # classify_product_category should handle potential errors internally
    category = classify_product_category(product_analysis_input_str)
    logging.info(f"Classified category for DIY: {category}")

    # Return DIY ideas directly from hardcoded categories
    diy_ideas = DIY_CATEGORIES.get(category, []) # Default to empty list

    # Generate appropriate message based on classification result
    message = f"Showing DIY ideas for category: {category}"
    if category == "unknown_category":
        message = "Could not determine product category accurately. No specific DIY ideas available."
        diy_ideas = [] # Ensure empty list for unknown
    elif category == "classification_skipped_due_to_error":
         message = "Classification skipped due to error in analysis. No DIY ideas provided."
         diy_ideas = [] # Ensure empty list

    return json.dumps({"diy_ideas": diy_ideas, "message": message})

