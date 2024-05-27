from flask import render_template, request, redirect, url_for, session, flash
import bcrypt
import logging
from .database import init_db, get_db, close_db

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
                return redirect(url_for('home'))  # Redirect to home page after successful login
            else:
                flash('Invalid email/password combination')
                return render_template('login.html')  # Render login template with error message if credentials are incorrect
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
                    },
                    'shippingaddress': {
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
                return redirect(url_for('login'))  # Redirect to login page after successful registration
        return render_template('register.html')

    @app.route('/home', endpoint='home')
    def home():
        try:
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
                        'feature': sku['feature'],
                        'image_url': product.get('image_url')  # Get image URL from product
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
    
    @app.route('/book/<int:product_id>')
    def book_details(product_id):
        try:
            book = db.products.find_one({'_id': product_id})
            return render_template('productinfo.html', book=book)
        except Exception as e:
            logging.error(f"Error fetching book details: {e}")
            # Handle error appropriately, for example, redirect to home page with a flash message
            flash('Error fetching book details')
            return redirect(url_for('home'))
    
    @app.route('/home/my_account', endpoint='my_account')
    def my_account():
        # Check if the referrer is the home page
        if request.referrer and url_for('home') in request.referrer:
            # Fetch user details from the database based on the current session's email
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
            # If not coming from the home page, redirect to the home page
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
            # Update user information based on form input
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
            
            password = request.form.get('password')
            confirmPassword = request.form.get('confirmPassword')
            if password and password == confirmPassword:
                new_data['hashedPassword'] = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            db.users.update_one({'_id': session['email']}, {'$set': new_data})
            flash('Account details updated successfully')
            return redirect(url_for('my_account'))

        return render_template('edit_account.html', user=user)

