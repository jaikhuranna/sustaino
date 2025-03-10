import os
import json
from dotenv import load_dotenv
from multimodal import classify_product_category, generate_product_analysis, extract_json_from_markdown

load_dotenv()

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

def generate_diy_suggestions(image_path):
    # First get product analysis from multimodal
    product_analysis_output = generate_product_analysis(image_path)

    # Extract clean JSON
    product_json = extract_json_from_markdown(product_analysis_output)
    
    try:
        product_data = json.loads(product_json)
        sustainability_score = product_data.get('sustainability_score', 0)
        
        if sustainability_score >= 70:
            return json.dumps({
                "diy_ideas": [],
                "message": "Sustainability score >= 70, no DIY suggestions provided."
            })
    except json.JSONDecodeError as e:
        return json.dumps({
            "diy_ideas": [],
            "message": f"Error parsing product data: {str(e)}"
        })
    
    # Classify the category
    category = classify_product_category(product_json).lower().strip().replace("</s>", "")
    
    print("Classified category:", category)  # for debugging
    
    # Return DIY ideas directly from hardcoded categories
    diy_ideas = DIY_CATEGORIES.get(category, [])
    
    return json.dumps({"diy_ideas": diy_ideas})
