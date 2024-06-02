from flask import render_template, request, redirect, url_for, session, flash , jsonify
import bcrypt
import logging
from bson import ObjectId
from .database import init_db, get_db, close_db

logging.basicConfig(level=logging.DEBUG)

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

            return jsonify({'message': 'Item added to cart successfully!'}), 200
        except Exception as e:
            logging.error(f'Error: {str(e)}')
            return jsonify({'error': str(e)}), 500
        

    @app.route('/home/view_cart', endpoint='view_cart')
    def view_cart():
        try:
            if 'email' in session:
                user_id = session['email']
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

            return '', 200  # Empty response with status code 200
        except Exception as e:
            logging.error(f"Error removing item from cart: {e}")
            return jsonify({'error': str(e)}), 500
