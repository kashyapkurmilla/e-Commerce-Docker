from flask import render_template, request, redirect, url_for, session, flash
import bcrypt
import logging
from bson import ObjectId
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
    
    @app.route('/home/book/<string:product_id>', endpoint='book_details')
    def book_details(product_id):
        try:
            book = db.products.find_one({'_id': ObjectId(product_id)})
            if not book:
                flash('Book not found')
                return redirect(url_for('home'))
            return render_template('productinfo.html', book=book)
        except Exception as e:
            logging.error(f"Error fetching book details: {e}")
            flash('Error fetching book details')
            return redirect(url_for('home'))

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
