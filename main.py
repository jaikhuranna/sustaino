import time
import traceback
from threading import Thread

# firestore
USE_DUMMY_DB = True

if USE_DUMMY_DB:
    class DummyDocument:
        def __init__(self, id, data):
            self.id = id
            self.data = data

        def to_dict(self):
            return self.data

        def update(self, update_dict):
            self.data.update(update_dict)
            print(f"Dummy Document {self.id} updated: {self.data}")

    class DummyCollection:
        def __init__(self, documents):
            self.documents = documents

        def where(self, field, op, value):
            filtered_docs = {}
            for doc_id, data in self.documents.items():
                if op == "==" and data.get(field) == value:
                    filtered_docs[doc_id] = data
            return DummyCollection(filtered_docs)

        def stream(self):
            for doc_id, data in self.documents.items():
                yield DummyDocument(doc_id, data)

        def document(self, doc_id):
            doc_data = self.documents.get(doc_id, {})
            return DummyDocument(doc_id, doc_data)

    class DummyFirestore:
        def __init__(self):
            self.collections = {
                "ocr_requests": {
                    "doc1": {"extracted_text": '''### Nutritional Information  
- **Serving size**: Usually 200ml or 355ml per bottle[3][7].  
- **Calories**: Approximately 44 kcal per 100ml or 150 kcal per 355ml serving[3][7].  
- **Total sugars**: Around 10.6g per 100ml or 39g per 355ml[3][7].  
- **Sodium**: 8.5mg per 100ml or 85mg per 355ml[3][7].  
- **Caffeine**: ~8.7mg per 100g[3].  

### Ingredients  
- Carbonated water  
- Sugar or cane sugar  
- Acidity regulator (e.g., phosphoric acid)  
- Caramel color (150d)  
- Natural flavorings  
- Caffeine[3][7].''', "processed": False},
                    "doc2": {"extracted_text": "", "processed": False},  # This document has no text
                    "doc3": {"extracted_text": "Already processed text", "processed": True},
                    "doc4": {"extracted_text": "Already processed text", "processed": False},
                    "doc5": {"extracted_text": "Already processed text", "processed": False},
                }
            }

        def collection(self, collection_name):
            return DummyCollection(self.collections.get(collection_name, {}))

    db = DummyFirestore()
else:
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()

# fastapi

from fastapi import FastAPI
from models.sustainable import generate_product_analysis   

app = FastAPI()

def process_ocr_requests():
    while True:
        try:
            # Query documents in 'ocr_requests' where "processed" is False
            docs = db.collection("ocr_requests").where("processed", "==", False).stream()
            for doc in docs:
                data = doc.to_dict()
                extracted_text = data.get("extracted_text", "")

                if not extracted_text:
                    # Log a warning if no text is found and mark as processed with an error
                    print(f"Warning: Document {doc.id} has no extracted_text. Marking as processed with error.")
                    db.collection("ocr_requests").document(doc.id).update({
                        "processed": True,
                        "error": "No text provided for processing",
                        "processedAt": "SERVER_TIMESTAMP"
                    })
                    continue

                print(f"Processing document {doc.id} with text: {extracted_text}")
                try:
                    suggestions = generate_product_analysis(extracted_text)

                    # Update the document with the model response, mark it as processed,
                    # and add a timestamp (dummy value for now)
                    db.collection("ocr_requests").document(doc.id).update({
                        "modelResponse": suggestions,
                        "processed": True,
                        "processedAt": "SERVER_TIMESTAMP"  # Replace with real timestamp in Firebase
                    })
                    print(f"Document {doc.id} updated successfully with model response.")
                except Exception as e:
                    print(f"Error processing document {doc.id}: {str(e)}")
                    # Log error and mark as processed to avoid reprocessing
                    db.collection("ocr_requests").document(doc.id).update({
                        "error": str(e),
                        "processed": True,
                        "processedAt": "SERVER_TIMESTAMP"
                    })
        except Exception as ex:
            print("Error while polling Firestore: ", str(ex))
            traceback.print_exc()

        time.sleep(5)

# start polling thread
@app.on_event("startup")
def startup_event():
    thread = Thread(target=process_ocr_requests, daemon=True)
    thread.start()

# health check
@app.get("/health")
def health_check():
    return {"status": "FastAPI is running and polling the dummy DB."}

# run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)