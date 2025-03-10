import os
import json
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from sustainable import generate_product_analysis

load_dotenv()

hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
if not hf_api_key:
    raise ValueError("Hugging Face API Key not set in environment variable")
text_generation_client = InferenceClient(token=hf_api_key, model="mistralai/Mistral-Nemo-Instruct-2407")

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
        {"name": "Kids’ Puzzle", "youtube_link": "https://www.youtube.com/watch?v=uvw34", "thumbnail": "https://img.youtube.com/vi/uvw34/0.jpg"}
    ]
}

def format_category_prompt(product_json):
    system_context_prompt = f"You are a classifier tasked with determining the material category of a scanned product based on its JSON analysis. Given the product name and description, classify it into one of these categories: plastic_bottle, aluminum_can, glass_bottle, cardboard_box, polythene_bag, paper_waste, chip_packet, plastic_box, tin_box, foam_container, or 'unknown' if it doesn’t fit. Return only the category name as plain text, nothing else."
    complete_prompt = f"Classify this product:\n\n{product_json}"
    combined_prompt = f"<s>[SYS] {system_context_prompt} [/SYS]\n[INST] {complete_prompt} [/INST]"
    return combined_prompt

def generate_diy_suggestions(extracted_text):
    final_output_text = generate_product_analysis(extracted_text)
    
    try:
        product_data = json.loads(final_output_text)
        sustainability_score = product_data['sustainability_score']
        if sustainability_score >= 70:
            return json.dumps({"diy_ideas": [], "message": "Sustainability score >= 70, no DIY suggestions provided."})
    except (json.JSONDecodeError, KeyError) as e:
        return json.dumps({"diy_ideas": [], "message": f"Error parsing product data: {str(e)}"})

    prompt = format_category_prompt(final_output_text)
    generation_parameters = dict(
        temperature=0.1,
        max_new_tokens=20,
        top_p=0.9,
        repetition_penalty=1.0,
        do_sample=False,
        seed=42,
    )

    generated_text_stream = text_generation_client.text_generation(prompt, **generation_parameters, stream=True, details=True, return_full_text=True)
    category = ""
    for text_segment in generated_text_stream:
        category += text_segment.token.text
    category = category.strip()

    if category in DIY_CATEGORIES:
        diy_ideas = DIY_CATEGORIES[category]
    else:
        diy_ideas = []

    return json.dumps({"diy_ideas": diy_ideas})