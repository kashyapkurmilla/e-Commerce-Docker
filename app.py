from flask import Flask, render_template, request, jsonify
import pymongo

app = Flask(__name__)

# MongoDB connection setup
mongo_client = pymongo.MongoClient("mongodb://kashyap:password@mongo:27017/")
db = mongo_client.mydatabase  # Change 'mydatabase' to your actual database name


# Sample list of products
products = [
    {"id": 1, "name": "Product 1"},
    {"id": 2, "name": "Product 2"},
    {"id": 3, "name": "Product 3"},
    {"id": 4, "name": "Product 4"},
    {"id": 5, "name": "Product 5"},
    {"id": 6, "name": "Product 6"},
    {"id": 7, "name": "Product 7"},
    {"id": 8, "name": "Product 8"},
    {"id": 9, "name": "Product 9"},
    {"id": 10, "name": "Product 10"},
]

@app.route('/')
def index():
    return render_template('index.html', products=products)

@app.route('/add_to_db', methods=['POST'])
def add_to_db():
    product_id = request.form['product_id']
    product_name = request.form['product_name']

    try:
        # Insert product information into MongoDB
        db.products.insert_one({"id": product_id, "name": product_name})
        return jsonify({'status': 'success', 'message': 'Product added to MongoDB successfully.'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error adding product to MongoDB. {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8082)