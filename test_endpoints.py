import requests
import json
import os


API_URL = "http://localhost:8000"


def test_analyze_product(image_path):
    """
    Test the analyze-product endpoint
    """
    print("\n--- Testing Analyze Product Endpoint ---")
    files = {"file": open(image_path, "rb")}

    response = requests.post(f"{API_URL}/analyze-product/", files=files)

    if response.status_code == 200:
        print("✅ Analysis successful!")
        result = response.json()
        print("Response:")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None





def test_analyze_with_alternatives(analysis_json):
    """
    Test the analyze-with-alternatives endpoint using an existing analysis
    """
    print("\n--- Testing Analyze With Alternatives Endpoint ---")

    response = requests.post(
        f"{API_URL}/analyze-with-alternatives/", json=analysis_json
    )

    if response.status_code == 200:
        print("✅ Alternatives from existing analysis successful!")
        result = response.json()
        print("Response:")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None


if __name__ == "__main__":

    test_image_path = "models\can.jpg"

    if not os.path.exists(test_image_path):
        print(f"Error: File not found at {test_image_path}")
        exit(1)

    analysis_result = test_analyze_product(test_image_path)
    

    if analysis_result:
        test_analyze_with_alternatives(analysis_result)
