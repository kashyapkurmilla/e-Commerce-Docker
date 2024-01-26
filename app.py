from flask import Flask, jsonify
import pymongo

app = Flask(__name__)

def check_mongodb_connection():
    try:
        client = pymongo.MongoClient("mongodb://mongo:27017/")
        client.server_info()  # Check if the client can connect to the server
        return True, None
    except pymongo.errors.ConnectionFailure as e:
        return False, str(e)

@app.route('/')
def check_connection():
    success, message = check_mongodb_connection()
    if success:
        return jsonify({'status': 'success', 'message': 'MongoDB connection is successful.'}), 200
    else:
        return jsonify({'status': 'error', 'message': f'MongoDB connection failed. Error: {message}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8082)
