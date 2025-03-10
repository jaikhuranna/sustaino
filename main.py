import os
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
from typing import Dict, Any
import tempfile
import shutil

from models.multimodal import generate_product_analysis
from models.alternatives import generate_alternative_suggestion

app = FastAPI(title="SustainoAPI", description="Product Sustainability Analysis API")


@app.get("/")
async def root():
    return {"message": "Welcome to Product Sustainability Analysis API"}


@app.post("/analyze-product/")
async def analyze_product(file: UploadFile = File(...)):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:
        result = generate_product_analysis(temp_path)

        os.unlink(temp_path)

        return {"result": result}
    except Exception as e:
        os.unlink(temp_path)
        return {"error": str(e)}


@app.post("/suggest-alternatives/")
async def suggest_alternatives(file: UploadFile = File(...)):

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name

    try:

        analysis_result = generate_product_analysis(temp_path)

        alternatives_result = generate_alternative_suggestion(analysis_result)

        os.unlink(temp_path)

        return {"analysis": analysis_result, "alternatives": alternatives_result}
    except Exception as e:
        os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-with-alternatives/")
async def analyze_with_alternatives(analysis_json: Dict[str, Any]):

    try:

        product_analysis = analysis_json.get("result", analysis_json)

        alternatives_result = generate_alternative_suggestion(product_analysis)

        return {"alternatives": alternatives_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
