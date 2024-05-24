from flask import Flask
from bookstore.routes import init_routes
from bookstore.database import init_db

app = Flask(__name__)

# Initialize database
db = init_db(app)

# Initialize routes
init_routes(app, db)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True)