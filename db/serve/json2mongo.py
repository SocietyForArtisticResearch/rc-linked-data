import json
import os
from pymongo import MongoClient, UpdateOne
import glob

client = MongoClient('mongodb://localhost:27017/')
db = client.rcData
collection = db.merged

def read_json(file_path):
    """Reads a JSON file and returns the data."""
    with open(file_path, 'r') as file:
        try:
            data = json.load(file)  
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from file {file_path}: {e}")
            return None 
    return data

def get_json(folders):
    """Returns a list of all JSON files in the specified folders."""
    all_files = []
    for folder in folders:
        # glob gets all jsons in folder
        folder_files = glob.glob(os.path.join(folder, '**', '*.json'), recursive=True)
        all_files.extend(folder_files)
    return all_files

folders = ['research', 'data', 'metrics']

files = get_json(folders)

for file in files:
    print(f"Processing file: {file}")
    documents = read_json(file)

    if documents is None:
        print(f"Skipping file {file} due to error parsing.")
        continue

    # If the file contains a single document (not a list), wrap it in a list
    if isinstance(documents, dict):
        documents = [documents]  # single document as list 
    
    print(f"Read {len(documents)} documents from {file}")
    
    bulk_operations = []
    for doc in documents:
        if isinstance(doc, dict) and 'id' in doc:
            # prepare update
            operation = UpdateOne(
                {'id': doc['id']},  # filter by 'id'
                {'$set': doc},      # update the document
                upsert=True         # insert if not found
            )
            bulk_operations.append(operation)
            print(f"Prepared operation for id: {doc['id']}")
        else:
            print(f"Skipping malformed document: {doc}")
    
    # bulk operations
    if bulk_operations:
        result = collection.bulk_write(bulk_operations)
        print(f"Bulk write result for {file}: {result.bulk_api_result}")
    else:
        print(f"No operations to execute for {file}")

print('Merging completed.')