from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import json_util
from waitress import serve
import json
import re


app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['rcData']
collection = db['merged']

#http://127.0.0.1:5000/rc/order-by-page-count?format=ids or format=full
def format_records(records, format_type):
    if format_type == "ids":
        # only return the 'id' for each record
        return [{"id": record["id"]} for record in records]
    return records

#http://127.0.0.1:5000/rc/
@app.route('/rc', methods=['GET'])
def get_all_records():
    format_type = request.args.get('format', 'full')  # Get 'format' query parameter (default is 'full')
    result = list(collection.find({}, {"_id": 0}))
    formatted_result = format_records(result, format_type)
    
    return jsonify(formatted_result)

#http://127.0.0.1:5000/rc/653717
@app.route('/rc/<int:exposition_id>', methods=['GET'])
def get_exposition(exposition_id):
    format_type = request.args.get('format', 'full') 
    result = collection.find_one({"id": exposition_id}, {"_id": 0})  # Exclude MongoDB "_id"
    if result:
        formatted_result = format_records([result], format_type)
        return jsonify(formatted_result)
    return jsonify({"error": "Record not found"}), 404 

#http://127.0.0.1:5000/rc/by-default-page-type?type=weave-block
@app.route('/rc/by-default-page-type', methods=['GET'])
def filter_by_default_page_type():
    format_type = request.args.get('format', 'full') 
    page_type = request.args.get('type') 
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 256))

    if not page_type:
        return jsonify({"error": "Missing 'type' query parameter"}), 400

    matching_records = []

    # Pagination logic
    skip_count = (page - 1) * page_size
    
    cursor = collection.find({}, {"_id": 0}).skip(skip_count).limit(page_size)

    for record in cursor:
        match = re.search(r"/view/\d+/(\d+)", record.get("default-page", ""))
        
        if match:
            default_page_id = match.group(1)  # Extract page ID as string

            # Check if page ID exists in "pages" and matches the requested type
            if "pages" in record:
                for page_key, page_data in record["pages"].items():
                    if page_data.get("id") == int(default_page_id) and page_data.get("type") == page_type:
                        matching_records.append(record)
                        break  # Stop checking further pages in the same record

    formatted_result = format_records(matching_records, format_type)

    # Add pagination metadata
    response = {
        "page": page,
        "page_size": page_size,
        "total_results": collection.count_documents({}), 
        "data": formatted_result
    }

    return jsonify(response)


#http://127.0.0.1:5000/rc/by-page-type?type=weave-block
@app.route('/rc/by-page-type', methods=['GET'])
def filter_by_page_type():
    format_type = request.args.get('format', 'full')
    page_type = request.args.get('type')
    if not page_type:
        return jsonify({"error": "Missing 'type' query parameter"}), 400

    matching_records = []

    for record in collection.find({}, {"_id": 0}):  
        if "pages" in record:
            for page_id, page_data in record["pages"].items():
                if page_data.get("type") == page_type:
                    matching_records.append(record)
                    break  
                
    formatted_result = format_records(matching_records, format_type)
    return jsonify(formatted_result)

#http://127.0.0.1:5000/rc/by-tool-type-count?tool=tool-picture
@app.route('/rc/by-tool-type-count', methods=['GET'])
def filter_and_order_by_tool_type_count():
    format_type = request.args.get('format', 'full')
    tool_type = request.args.get('tool')

    if not tool_type:
        return jsonify({"error": "Missing 'tool' query parameter"}), 400

    matching_records = []

    for record in collection.find({}, {"_id": 0}):  
        tool_count = 0  
        
        if "pages" in record:
            for page_id, page_data in record["pages"].items():
                tool_count += len(page_data.get(tool_type, [])) 

        if tool_count > 0:
            record["tool_count"] = tool_count
            matching_records.append(record)

    matching_records.sort(key=lambda x: x["tool_count"], reverse=True)

    formatted_result = format_records(matching_records, format_type)
    return jsonify(formatted_result)

#http://127.0.0.1:5000/rc/order-by-page-count
@app.route('/rc/order-by-page-count', methods=['GET'])
def order_by_page_count():
    format_type = request.args.get('format', 'full')
    matching_records = []

    for record in collection.find({}, {"_id": 0}):  # Skip MongoDB "_id" field
        page_count = 0 

        if "pages" in record:
            page_count = len(record["pages"])

        record["page_count"] = page_count
        matching_records.append(record)

    matching_records.sort(key=lambda x: x["page_count"], reverse=True)

    formatted_result = format_records(matching_records, format_type)
    return jsonify(formatted_result)

#http://127.0.0.1:5000/rc/by-tool-types-count
@app.route('/rc/by-tool-types-count', methods=['GET'])
def count_by_multiple_tool_types():
    format_type = request.args.get('format', 'full')  # Get 'format' query parameter (default is 'full')
    tools_param = request.args.get('tools')  # Get tools from query parameters (comma-separated list)

    if not tools_param:
        return jsonify({"error": "Missing 'tools' query parameter"}), 400  # Bad request if no tools are provided

    tools = tools_param.split(',')

    valid_tools = {"tool-picture", "tool-video", "tool-text", "tool-pdf", "tool-shape", "tool-iframe", "tool-slideshow", "tool-audio", "tool-simpletext"}
    invalid_tools = [tool for tool in tools if tool not in valid_tools]
    if invalid_tools:
        return jsonify({"error": f"Invalid tool types: {', '.join(invalid_tools)}"}), 400

    matching_records = []

    for record in collection.find({}, {"_id": 0}):  
        tool_counts = {tool: 0 for tool in tools}  # initi counts

        if "pages" in record:
            for page_id, page_data in record["pages"].items():
                # for each page, count occurrences of the tool types
                for tool in tools:
                    tool_counts[tool] += len(page_data.get(tool, []))

        # if any tool type appears at least once, include the record
        if any(count > 0 for count in tool_counts.values()):
            record_data = {
                "id": record["id"],
                "tool_counts": [tool_counts[tool] for tool in tools]  # list of tool counts
            }
            matching_records.append(record_data)

    # sort by tools count in descending order
    matching_records.sort(key=lambda x: sum(x["tool_counts"]), reverse=True)
    formatted_result = format_records(matching_records, format_type)

    return jsonify(formatted_result)

if __name__ == '__main__':
    serve(app, host="0.0.0.0", port=5000)
