from flask import Flask, render_template
from pymongo import MongoClient
import logging
import pymongo

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Connect to MongoDB directly
mongo_uri = "mongodb://kashyap:password@mongo:27017/"
logging.info(f"Connecting to MongoDB at {mongo_uri}")
try:
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client.bookstore
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    raise e

# Fetch product data from MongoDB
products = db.products.find()

# Iterate over products and extract relevant information
product_list = []
for product in products:
    # Iterate over SKUs
    for sku in product.get('skus', []):
        product_info = {
            'name': product['name'],
            'author': product['author'],
            'price': sku['Price'],  # Get price from SKU
            'feature': sku['feature']
        }
        product_list.append(product_info)
logging.info(f"Fetched {len(product_list)} products from MongoDB")

@app.route('/')
def index():
    try:
        products = list(db.products.find())
        logging.info(f"Fetched {len(products)} products from MongoDB")
        return render_template('index.html', products=product_list)
    except Exception as e:
        logging.error(f"Error fetching products: {e}")
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True)
