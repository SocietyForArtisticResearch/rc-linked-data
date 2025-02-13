from flask import Flask, jsonify, request
from pymongo import MongoClient, ASCENDING, DESCENDING
import re

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['rcData']
collection = db['merged']

# ---- APPLYING INDEXES ----
print('start creating indexes')
#collection.create_index([("id", ASCENDING)])
#collection.create_index([("default-page", ASCENDING)])  # Improves default-page searches
#collection.create_index([("pages.type", ASCENDING)])  # Optimizes searches by page type
collection.create_index([("pages.tool_type", ASCENDING)])  # Faster tool-type queries
print('done indexing')

