import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
from typing import Dict, Any
import tempfile
import shutil

from models.multimodal import generate_product_analysis
from models.alternatives import generate_alternative_suggestion
from models.diy import generate_diy_suggestions 

app = FastAPI(title="SustainoAPI", description="Product Sustainability Analysis API")


@app.get("/")
async def root():
    return {"message": "Welcome to Product Sustainability Analysis API"}


@app.post("/analyze-product/")
async def analyze_product(file: UploadFile = File(...)):
    """
    Analyze a product from an uploaded image
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        result = generate_product_analysis(temp_path)
        os.unlink(temp_path)
        return {"result": result}
    except Exception as e:
        os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-with-alternatives/")
async def analyze_with_alternatives(analysis_json: Dict[str, Any]):
    """
    Generate alternative product suggestions based on analysis
    """
    try:
        product_analysis = analysis_json.get("result", analysis_json)
        alternatives_result = generate_alternative_suggestion(product_analysis)
        return {"alternatives": alternatives_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/diy-suggestions/")
async def get_diy_suggestions(analysis_json: Dict[str, Any]):
    """
    Generate DIY suggestions based on product analysis
    """
    try:
        product_analysis = analysis_json.get("result", analysis_json)
        
        diy_suggestions = generate_diy_suggestions(product_analysis)
        
        diy_data = json.loads(diy_suggestions)
        
        return diy_data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)