from flask import current_app, g
from pymongo import MongoClient
import logging

def get_db():
    if 'db' not in g:
        client = MongoClient(current_app.config['MONGO_URI'])
        g.db = client.bookstore
    return g.db

def init_db(app):
    app.config['MONGO_URI'] = "mongodb://kashyap:password@mongo:27017/"
    logging.info(f"Connecting to MongoDB at {app.config['MONGO_URI']}")
    try:
        mongo_client = MongoClient(app.config['MONGO_URI'])
        db = mongo_client.bookstore
        logging.info("Successfully connected to MongoDB")
        return db
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise e

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.client.close()
