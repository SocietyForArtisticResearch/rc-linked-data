from flask import Flask, jsonify, request
import json

app = Flask(__name__)

with open("../research/merged_stats.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# get top N entries sorted by a given tool type
def get_top_entries(tool_types, n, page_type=None):
    if isinstance(tool_types, str):
        tool_types = [tool_types]  
        
    filtered_entries = {
        k: v for k, v in data.items() if page_type is None or v.get("default-page-type") == page_type
    }

    # sort entries by total count of tool types
    sorted_entries = sorted(
        filtered_entries.items(),
        key=lambda x: sum(x[1]["tool-counts"].get(tool, 0) for tool in tool_types),
        reverse=True
    )

    return [{"id": entry[0], **entry[1]} for entry in sorted_entries[:n]]

@app.route("/highest-total-tools", methods=["GET"])
def highest_total_tools():
    n = int(request.args.get("n", 50))
    sorted_entries = sorted(data.items(), key=lambda x: x[1]["total-number-of-tools"], reverse=True)
    return jsonify([{"id": entry[0], **entry[1]} for entry in sorted_entries[:n]])

@app.route("/highest-total-pages", methods=["GET"])
def highest_total_pages():
    n = int(request.args.get("n", 50))
    sorted_entries = sorted(data.items(), key=lambda x: x[1]["number-of-pages"], reverse=True)
    return jsonify([{"id": entry[0], **entry[1]} for entry in sorted_entries[:n]])

@app.route("/most-video-tools", methods=["GET"])
def most_video_tools():
    n = int(request.args.get("n", 50))
    return jsonify(get_top_entries("tool-video", n))

@app.route("/most-audio-tools", methods=["GET"])
def most_audio_tools():
    n = int(request.args.get("n", 50))
    return jsonify(get_top_entries("tool-audio", n))

@app.route("/most-picture-tools", methods=["GET"])
def most_picture_tools():
    n = int(request.args.get("n", 50))
    return jsonify(get_top_entries("tool-picture", n))

@app.route("/most-slideshow-tools", methods=["GET"])
def most_slideshow_tools():
    n = int(request.args.get("n", 50))
    return jsonify(get_top_entries("tool-slideshow", n))

@app.route("/most-pdf-tools", methods=["GET"])
def most_pdf_tools():
    n = int(request.args.get("n", 50))
    return jsonify(get_top_entries("tool-pdf", n))

@app.route("/most-text-tools", methods=["GET"])
def most_text_tools():
    n = int(request.args.get("n", 50))
    page_type = request.args.get("page_type")
    return jsonify(get_top_entries(["tool-text", "tool-simpletext"], n, page_type))

if __name__ == "__main__":
    app.run(debug=True)
    
#examples:
#GET /most-text-tools?n=3
#GET /most-text-tools?n=3&page_type=weave-graphical