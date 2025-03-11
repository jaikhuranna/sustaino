import requests
import json
import os


API_URL = "http://10.9.137.188:8000"


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


def test_diy_suggestions(analysis_json):
    print("\n--- Testing DIY Suggestions Endpoint ---")

    response = requests.post(
        f"{API_URL}/diy-suggestions/", json=analysis_json
    )

    if response.status_code == 200:
        print("✅ DIY suggestions from existing analysis successful!")
        result = response.json()
        print("Response:")
        print(json.dumps(result, indent=2))
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None


# def test_analyze_image_with_diy(image_path):
#     """
#     Test the analyze-image-with-diy endpoint (one-step process)
#     """
#     print("\n--- Testing Analyze Image With DIY Endpoint ---")
#     files = {"file": open(image_path, "rb")}

#     response = requests.post(f"{API_URL}/diy-suggestions/", files=files)

#     if response.status_code == 200:
#         print("✅ Combined analysis and DIY suggestions successful!")
#         result = response.json()
#         print("Response:")
#         print(json.dumps(result, indent=2))
#         return result
#     else:
#         print(f"❌ Error: {response.status_code}")
#         print(response.text)
#         return None


def run_all_tests(image_path):

    print("\n=== RUNNING ALL ENDPOINT TESTS ===")
    
    analysis_result = test_analyze_product(image_path)
    
    if analysis_result:
        test_analyze_with_alternatives(analysis_result)
        
        test_diy_suggestions(analysis_result)
    
    # test_analyze_image_with_diy(image_path)


if __name__ == "__main__":
    test_image_path = "models/can.jpg"

    if not os.path.exists(test_image_path):
        print(f"Error: File not found at {test_image_path}")
        exit(1)

    run_all_tests(test_image_path)
    
    # analysis_result = test_analyze_product(test_image_path)
    # if analysis_result:
    #     test_analyze_with_alternatives(analysis_result)
    #     test_diy_suggestions(analysis_result)
    # test_analyze_image_with_diy(test_image_path)
