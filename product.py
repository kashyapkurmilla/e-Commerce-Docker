from flask import Flask, render_template, request
import pymongo

app = Flask(__name__)
client = pymongo.MongoClient("localhost:27017")
db = client["your_database_name"]
collection = db["your_collection_name"]

@app.route('/')
def index():
    data = collection.find()
    return render_template('index.html', data=data)

@app.route('/add', methods=['POST'])
def add():
    name = request.form['name']
    collection.insert_one({'name': name})
    return index()

@app.route('/delete', methods=['POST'])
def delete():
    name = request.form['name']
    collection.delete_one({'name': name})
    return index()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
