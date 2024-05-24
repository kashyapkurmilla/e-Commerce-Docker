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
    
    @app.route('/home', endpoint='home')
    def home():
        try:
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
