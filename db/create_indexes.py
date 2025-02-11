from pymongo import MongoClient, ASCENDING

client = MongoClient('mongodb://localhost:27017/')
db = client['rcData']
collection = db['merged']

# Create an ascending index on the 'username' field
collection.create_index([("username", ASCENDING)])

print("Index created successfully!")
