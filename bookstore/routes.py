from flask import render_template, request, jsonify
import logging

def init_routes(app, db):
    # Fetch product data from MongoDB
    products = db.products.find()

    # Iterate over products and extract relevant information
    product_list = []
    for product in products:
        # Iterate over SKUs
        for sku in product.get('skus', []):
            product_info = {
                'id': str(product['_id']),
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
            return render_template('index.html', products=product_list)
        except Exception as e:
            logging.error(f"Error fetching products: {e}")
            return f"An error occurred: {e}", 500

    @app.route('/add_to_cart', methods=['POST'])
    def add_to_cart():
        try:
            product_id = request.json.get('product_id')
            user_id = "user123"  # Static user ID for this example, replace with real user authentication

            cart_item = {
                'user_id': user_id,
                'product_id': product_id
            }

            db.cart.insert_one(cart_item)
            logging.info(f"Product {product_id} added to cart for user {user_id}")

            return jsonify({'status': 'success'}), 200
        except Exception as e:
            logging.error(f"Error adding to cart: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/view_cart')
    def view_cart():
        try:
            user_id = "user123"  # Static user ID for this example, replace with real user authentication
            cart_items = db.cart.find({'user_id': user_id})
            
            cart_product_ids = [item['product_id'] for item in cart_items]
            cart_products = db.products.find({'_id': {'$in': cart_product_ids}})
            
            cart_list = []
            for product in cart_products:
                for sku in product.get('skus', []):
                    cart_item_info = {
                        'name': product['name'],
                        'author': product['author'],
                        'price': sku['Price'],
                        'feature': sku['feature']
                    }
                    cart_list.append(cart_item_info)
            
            logging.info(f"Fetched {len(cart_list)} items for user {user_id}")
            
            return render_template('view_cart.html', cart_items=cart_list)
        except Exception as e:
            logging.error(f"Error fetching cart items: {e}")
            return f"An error occurred: {e}", 500
