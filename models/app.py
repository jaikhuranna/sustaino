from flask import Flask, request, jsonify
from flask_cors import CORS
from models.sustainable import generate_product_analysis

app = Flask(__name__)
CORS(app)

@app.route('/check-sustainability', methods=['POST'])
def check_sustainability():
    try:
        data = request.json
        # Use a descriptive key, e.g., "product_description"
        product_description = data.get('product_description', '')

        if not product_description:
            return jsonify({'error': 'No product description provided'}), 400

        # Generate the sustainability assessment using the model
        sustainability_assessment = generate_product_analysis(product_description)

        return jsonify({'sustainability_assessment': sustainability_assessment})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)