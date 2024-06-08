from flask import render_template, request, redirect, url_for, session, flash , jsonify 
import bcrypt
import logging
from bson import ObjectId
from datetime import datetime
from .database import init_db, get_db, close_db
import stripe
import random
import string

logging.basicConfig(level=logging.DEBUG)
stripe.api_key = 'privatekey' 

def init_routes(app, db):
    @app.route('/')
    def root():
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'], endpoint='login')
    def login():
        if request.method == 'POST':
            users = db.users
            login_user = users.find_one({'_id': request.form['email']})
            if login_user and bcrypt.checkpw(request.form['password'].encode('utf-8'), login_user['hashedPassword'].encode('utf-8')):
                session['email'] = request.form['email']
                return redirect(url_for('home'))
            else:
                flash('Invalid email/password combination')
                return render_template('login.html')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'], endpoint='register')
    def register():
        if request.method == 'POST':
            users = db.users
            existing_user = users.find_one({'_id': request.form['email']})
            if existing_user:
                flash('That email already exists!')
            else:
                hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
                user_data = {
                    '_id': request.form['email'],
                    'firstName': request.form['firstName'],
                    'lastName': request.form['lastName'],
                    'hashedPassword': hashpass.decode('utf-8'),
                    'address': {
                        'country': request.form['country'],
                        'street1': request.form['street1'],
                        'street2': request.form['street2'],
                        'city': request.form['city'],
                        'province': request.form['province'],
                        'zip': request.form['zip']
                    }
                }
                users.insert_one(user_data)
                session['email'] = request.form['email']
                return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/home', endpoint='home')
    def home():
        try:
            products = db.products.find()
            product_list = []
            for product in products:
                for sku in product.get('skus', []):
                    product_info = {
                        'id': str(product['_id']),
                        'name': product['name'],
                        'author': product['author'],
                        'price': sku['Price'],
                        'feature': sku['feature'],
                        'image_url': product.get('image_url')
                    }
                    product_list.append(product_info)
            logging.info(f"Fetched {len(product_list)} products from MongoDB")
            return render_template('index.html', products=product_list)
        except Exception as e:
            logging.error(f"Error fetching products: {e}")
            return f"An error occurred: {e}", 500

    @app.route('/logout', endpoint='logout')
    def logout():
        session.pop('email', None)
        return redirect(url_for('login'))

    @app.errorhandler(401)
    def unauthorized_error(error):
        flash('Invalid email/password combination')
        return redirect(url_for('login'))
    

    @app.route('/home/my_account', endpoint='my_account')
    def my_account():
        if request.referrer and url_for('home') in request.referrer:
            if 'email' in session:
                user = db.users.find_one({'_id': session['email']})
                if user:
                    return render_template('my_account.html', user=user)
                else:
                    flash('User not found')
                    return redirect(url_for('login'))
            else:
                flash('Please log in to access your account')
                return redirect(url_for('login'))
        else:
            flash('Access denied')
            return redirect(url_for('home'))

    @app.route('/home/edit_account', methods=['GET', 'POST'], endpoint='edit_account')
    def edit_account():
        if 'email' not in session:
            flash('Please log in to edit your account details')
            return redirect(url_for('login'))
        
        user = db.users.find_one({'_id': session['email']})
        if not user:
            flash('User not found')
            return redirect(url_for('home'))

        if request.method == 'POST':
            new_data = {
                'firstName': request.form['firstName'],
                'lastName': request.form['lastName'],
                'address': {
                    'country': request.form['country'],
                    'street1': request.form['street1'],
                    'street2': request.form['street2'],
                    'city': request.form['city'],
                    'province': request.form['province'],
                    'zip': request.form['zip']
                }
            }

            db.users.update_one({'_id': session['email']}, {'$set': new_data})
            flash('Account details updated successfully')
            return redirect(url_for('my_account'))

        return render_template('edit_account.html', user=user)

    @app.route('/home/change_password', methods=['GET', 'POST'], endpoint='change_password')
    def change_password():
        if 'email' not in session:
            flash('Please log in to change your password')
            return redirect(url_for('login'))

        user = db.users.find_one({'_id': session['email']})
        if not user:
            flash('User not found')
            return redirect(url_for('home'))

        if request.method == 'POST':
            current_password = request.form['currentPassword']
            new_password = request.form['newPassword']
            confirm_password = request.form['confirmPassword']

            if not bcrypt.checkpw(current_password.encode('utf-8'), user['hashedPassword'].encode('utf-8')):
                flash('Current password is incorrect')
                return render_template('change_password.html', user=user)

            if new_password != confirm_password:
                flash('New password and confirm password do not match')
                return render_template('change_password.html', user=user)

            new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            db.users.update_one({'_id': session['email']}, {'$set': {'hashedPassword': new_hashed_password.decode('utf-8')}})
            flash('Password changed successfully')
            return redirect(url_for('my_account'))

        return render_template('change_password.html', user=user)
    
    # @app.route('/home/book_details', methods=['GET'])
    # def book_details():
    #     book_id = request.args.get('bookId')
    #     feature = request.args.get('feature')
    #     # Fetch more book details from the database if needed using book_id
    #     return render_template('book_details.html', book_id=book_id, book_feature=feature)

    @app.route('/home/book_details', methods=['GET'])
    def book_details():
        book_id = request.args.get('bookId')
        feature = request.args.get('feature')
        
        try:
            book = db.products.find_one({'_id': ObjectId(book_id)})
            if not book:
                flash('Book not found')
                return redirect(url_for('home'))
            
            # Find the specific SKU
            sku = next((s for s in book['skus'] if s['feature'] == feature), None)
            if not sku:
                flash('Feature not found')
                return redirect(url_for('home'))

            book_details = {
                'bookId':book['_id'],
                'name': book['name'],
                'author': book['author'],
                'description': book.get('description', 'No description available'),
                'genre': book.get('genre', 'Unknown'),
                'price': sku['Price'],
                'quantity': sku['quantity'],
                'feature': sku['feature'],
                'image_url': book.get('image_url', 'static/images/book.png')
            }
            
            return render_template('book_details.html', book=book_details)
        except Exception as e:
            logging.error(f"Error fetching book details: {e}")
            flash('Error fetching book details')
            return redirect(url_for('home'))
            
    @app.route('/home/add_to_cart', methods=['POST'])
    def add_to_cart():
        try:
            data = request.json
            logging.debug(f'Received data: {data}')
            
            user_id = data.get('userId')
            product_id = ObjectId(data.get('bookId'))
            product_name = data.get('bookName', 'Unknown')  # Provide a default value
            author = data.get('author', 'Unknown')  # Provide a default value
            price = data.get('price')  # Provide a default value
            image_url = data.get('imageUrl', '')  # Provide a default value
            feature = data.get('feature', 'Unknown')  # Provide a default value

            existing_cart = db.cart_items.find_one({'user_id': user_id})
            logging.debug(f'Existing cart: {existing_cart}')
            
            if existing_cart:
                item_index = next((index for (index, item) in enumerate(existing_cart['items'])
                                if item['product_id'] == product_id and item['book_feature'] == feature), None)
                if item_index is not None:
                    # If the item exists, increment the quantity
                    result = db.cart_items.update_one(
                        {'user_id': user_id, f'items.{item_index}.product_id': product_id, f'items.{item_index}.book_feature': feature},
                        {'$inc': {f'items.{item_index}.quantity': 1}}
                    )
                    logging.debug(f'Incremented quantity result: {result.modified_count}')
                else:
                    # Add a new item if it does not exist
                    result = db.cart_items.update_one(
                        {'user_id': user_id},
                        {'$push': {
                            'items': {
                                'product_id': product_id,
                                'product_name': product_name,
                                'author': author,
                                'price': price,
                                'quantity': 1,
                                'image_url': image_url,
                                'book_feature': feature
                            }
                        }}
                    )
                    logging.debug(f'Added new item result: {result.modified_count}')
            else:
                # Create a new cart for the user
                new_cart = {
                    'user_id': user_id,
                    'items': [
                        {
                            'product_id': product_id,
                            'product_name': product_name,
                            'author': author,
                            'price': price,
                            'quantity': 1,
                            'image_url': image_url,
                            'book_feature': feature
                        }
                    ]
                }
                result = db.cart_items.insert_one(new_cart)
                logging.debug(f'Inserted new cart result: {result.inserted_id}')
            update_total_price(user_id, db)

            return jsonify({'message': 'Item added to cart successfully!'}), 200
        except Exception as e:
            logging.error(f'Error: {str(e)}')
            return jsonify({'error': str(e)}), 500
        

    @app.route('/home/view_cart', endpoint='view_cart')
    def view_cart():
        try:
            if 'email' in session:
                user_id = session['email']
                update_total_price(user_id, db)
                cart = db.cart_items.find_one({'user_id': user_id})
                if cart:
                    cart_items = cart.get('items', [])
                    total_price = sum(int(item['price']) * item['quantity'] for item in cart_items)
                    return render_template('view_cart.html', cart_items=cart_items, total_price=total_price)
                else:
                    flash('Your cart is empty')
                    return render_template('view_cart.html', cart_items=[], total_price=0)
            else:
                flash('Please log in to view your cart')
                return redirect(url_for('login'))
        except Exception as e:
            logging.error(f"Error fetching cart items: {e}")
            flash('Error fetching cart items')
            return redirect(url_for('home'))


    @app.route('/home/change_quantity', methods=['POST'])
    def change_quantity():
        try:
            data = request.json
            user_id = session.get('email')
            if not user_id:
                return jsonify({'error': 'User not logged in'}), 401

            item_id = ObjectId(data.get('itemId'))
            feature = data.get('feature')
            action = data.get('action')

            # Find the user's cart
            cart = db.cart_items.find_one({'user_id': user_id})
            if not cart:
                return jsonify({'error': 'Cart not found for user'}), 404

            # Find the item in the cart
            item_index = next((index for (index, item) in enumerate(cart['items'])
                            if item['product_id'] == item_id and item['book_feature'] == feature), None)
            if item_index is None:
                return jsonify({'error': 'Item not found in cart'}), 404

            # Update the quantity based on the action (increase or decrease)
            if action == 'increase':
                cart['items'][item_index]['quantity'] += 1
            elif action == 'decrease':
                if cart['items'][item_index]['quantity'] > 1:
                    cart['items'][item_index]['quantity'] -= 1
                else:
                    # If quantity is already 1 and user tries to decrease, remove the item from the cart
                    del cart['items'][item_index]

            # Update the cart in the database
            db.cart_items.update_one({'user_id': user_id}, {'$set': {'items': cart['items']}})
            update_total_price(user_id, db)

            return '', 200
        except Exception as e:
            logging.error(f"Error updating item quantity: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/home/remove_from_cart', methods=['POST'])
    def remove_from_cart():
        try:
            data = request.json
            user_id = session.get('email')
            if not user_id:
                return jsonify({'error': 'User not logged in'}), 401

            item_id = ObjectId(data.get('itemId'))
            feature = data.get('feature')

            # Find the user's cart
            cart = db.cart_items.find_one({'user_id': user_id})
            if not cart:
                return jsonify({'error': 'Cart not found for user'}), 404

            # Remove the item from the cart
            cart['items'] = [item for item in cart['items'] if item['product_id'] != item_id or item['book_feature'] != feature]

            # Update the cart in the database
            db.cart_items.update_one({'user_id': user_id}, {'$set': {'items': cart['items']}})
            update_total_price(user_id, db)

            return '', 200  # Empty response with status code 200
        except Exception as e:
            logging.error(f"Error removing item from cart: {e}")
            return jsonify({'error': str(e)}), 500
    
    def update_total_price(user_id, db):
        pipeline = [
            {
                '$match': {'user_id': user_id}
            },
            {
                '$addFields': {
                    'total_price': {
                        '$sum': {
                            '$map': {
                                'input': '$items',
                                'as': 'item',
                                'in': {
                                    '$multiply': [
                                        {'$toInt': '$$item.price'},
                                        '$$item.quantity'
                                    ]
                                }
                            }
                        }
                    }
                }
            },
            {
                '$merge': {
                    'into': 'cart_items',
                    'whenMatched': 'replace'
                }
            }
        ]
        db.cart_items.aggregate(pipeline)


    def get_user_by_email(email):
        user_collection = db['users']
        user = user_collection.find_one({'_id': email})
        return user

    @app.route('/home/checkout')
    def checkout():
        user_email = session.get('email')
        if not user_email:
            return redirect(url_for('login'))

        user = get_user_by_email(user_email)
        if not user:
            return "User not found", 404

        # Fetch the cart details
        cart = db.cart_items.find_one({'user_id': user_email})
        if not cart:
            flash('Your cart is empty')
            return ''

        # Pass user details, shipping addresses, and cart total price to the template
        shipping_addresses = user.get('shippingAddresses', [])
        total_price = cart.get('total_price', 0)
        
        return render_template('checkout.html', user=user, shipping_addresses=shipping_addresses, total_price=total_price)

    @app.route('/home/save_address', methods=['POST'])
    def save_address():
        if 'email' not in session:
            return jsonify({'success': False, 'error': 'User not logged in'})

        user_id = session['email']
        address_data = request.json

        try:
            user = db.users.find_one({'_id': user_id})
            if not user:
                return jsonify({'success': False, 'error': 'User not found'})

            address_data['addressId'] = str(ObjectId())  # Generate a unique addressId

            db.users.update_one(
                {'_id': user_id},
                {'$push': {'shippingAddresses': address_data}}
            )

            return jsonify({'success': True})
        except Exception as e:
            logging.error(f"Error saving address: {e}")
            return jsonify({'success': False, 'error': str(e)})



    @app.route('/home/checkout', methods=['POST'])
    def checkout_post():
        if 'email' not in session:
            return jsonify({'success': False, 'error': 'User not logged in'})

        user_id = session['email']
        total_price = request.json.get('total_price')
        discount_code = request.json.get('discount_code')
        shipping_address_id = request.json.get('shipping_address_id')
        payment_method = request.json.get('payment_method')
        card_details = request.json.get('card_details')

        # Generate random tracking ID
        tracking_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        try:
            # Get cart items
            cart = db.view_cart.find_one({'user_id': user_id})
            if cart:
                cart_items = cart.get('items', [])
            else:
                cart_items = []

            print("Cart Items:", cart_items)  # Debugging

            # Get shipping address details
            user = db.users.find_one({'_id': user_id})
            if not user:
                return jsonify({'success': False, 'error': 'User not found'})

            shipping_address = None
            for address in user.get('shippingAddresses', []):
                if address.get('addressId') == shipping_address_id:
                    shipping_address = address
                    break

            if not shipping_address:
                return jsonify({'success': False, 'error': 'Shipping address not found'})

            # Get current timestamp
            timestamp = datetime.now()

            # Save the order to the database
            order_data = {
                'userId': user_id,
                'totalPrice': total_price,
                'discountCode': discount_code,
                'cartItems': cart_items,
                'shippingAddress': shipping_address,
                'trackingId': tracking_id,
                'orderStatus': 'Pending',
                'paymentMethod': payment_method,
                'cardDetails': card_details,
                'timestamp': timestamp
            }

            # Insert order into the orders collection
            db.orders.insert_one(order_data)

            # Update product quantities and delete if necessary
            for item in cart_items:
                product_id = item.get('product_id')
                quantity = item.get('quantity')
                book_feature = item.get('book_feature')

                # Deduct the quantity from the products collection
                db.products.update_one({'_id': ObjectId(product_id), 'skus.feature': book_feature},
                                        {'$inc': {'skus.$.quantity': -quantity}})

                # Delete product if quantity reaches 0
                db.products.update_one({'_id': ObjectId(product_id), 'skus.feature': book_feature, 'skus.quantity': {'$lte': 0}},
                                        {'$pull': {'skus': {'feature': book_feature}}})

            # Delete cart document from view_cart collection
            db.cart_items.delete_one({'user_id': user_id})

            return jsonify({'success': True, 'tracking_id': tracking_id})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/home/ViewOrders')
    def view_orders():
        if 'email' not in session:
            return jsonify({'success': False, 'error': 'User not logged in'})

        user_id = session['email']

        # Retrieve orders for the logged-in user from the database
        orders = db.orders.find({'userId': user_id})

        return render_template('view_orders.html', orders=orders)

