from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import json_util
import json

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/') 
db = client['rcData']
collection = db['merged']

@app.route('/query', methods=['GET'])
def query_database():
    # query parameters
    overall_score = request.args.get('overall-score', type=float)
    
    if overall_score is not None:
        # aggregation pipeline
        pipeline = [
            #uncomment to filter output result
            {
                "$project": {
                    "id": 1,
                    "metrics": 1
                }
            },
            {
                "$addFields": {
                    "filteredMetrics": {
                        "$filter": {
                            "input": { "$objectToArray": "$metrics" },
                            "as": "metric",
                            "cond": { "$gt": ["$$metric.v.overall_regular_score", overall_score] }
                        }
                    }
                }
            },
            {
                "$match": {
                    "filteredMetrics.0": { "$exists": True }
                }
            },
            {
                "$project": {
                    "id": 1,
                    "filteredMetrics": 1
                }
            }
        ]

        # aggregation query
        result = collection.aggregate(pipeline)
    else:
        result = collection.find()
    
    result_list = list(result)
    
    # result to JSON
    json_result = json.dumps(result_list, default=json_util.default)
    
    return jsonify(json.loads(json_result))

if __name__ == '__main__':
    app.run(debug=True)