from flask import Flask, jsonify, request
from flask_cors import CORS
import json

app = Flask(__name__)
trusted_origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:3000",
    "https://keywords.sarconference2016.net",
]
CORS(app, origins=trusted_origins)

# Load data
with open("../research/merged_stats.json", "r", encoding="utf-8") as file:
    data = json.load(file)


# Utility functions
def get_top_tools(tool_type, n, page_type=None):
    if isinstance(tool_type, str):
        tool_type = [tool_type]

    filtered_entries = {
        k: v for k, v in data.items() if page_type is None or v.get("default-page-type") == page_type
    }

    sorted_entries = sorted(
        filtered_entries.items(),
        key=lambda x: sum(x[1]["tool-counts"].get(tool, 0) for tool in tool_type),
        reverse=True
    )

    return [{"id": entry[0], **entry[1]} for entry in sorted_entries[:n]]

def get_top_links(link_type, n):
    if isinstance(link_type, str):
        link_type = [link_type]
        
    filtered_entries = {
        k: v for k, v in data.items()
    }

    sorted_entries = sorted(
        filtered_entries.items(),
        key=lambda x: sum(x[1]["link-counts"].get(tool, 0) for tool in link_type),
        reverse=True
    )

    return [{"id": entry[0], **entry[1]} for entry in sorted_entries[:n]]


def get_top_graphical_entries(metric_key, n):
    filtered_entries = {
        k: v for k, v in data.items() if v.get("default-page-type") == "weave-graphical"
    }

    filtered_entries = {
        k: v for k, v in filtered_entries.items()
        if v.get("metrics", {}).get(metric_key) not in {0.0, 1.0}
    }

    sorted_entries = sorted(
        filtered_entries.items(),
        key=lambda x: x[1].get("metrics", {}).get(metric_key, float("-inf")),
        reverse=True
    )

    return [{"id": entry[0], **entry[1]} for entry in sorted_entries[:n]]


def get_top_general(sort_key, n, page_type=None):
    filtered_entries = {
        k: v for k, v in data.items() if page_type is None or v.get("default-page-type") == page_type
    }

    sorted_entries = sorted(
        filtered_entries.items(),
        key=lambda x: x[1].get(sort_key, 0),
        reverse=True
    )

    return [{"id": entry[0], **entry[1]} for entry in sorted_entries[:n]]


# Routes
@app.route("/highest-total-tools", methods=["GET"])
def highest_total_tools():
    n = int(request.args.get("n", 50))
    page_type = request.args.get("page_type")
    return jsonify(get_top_general("total-number-of-tools", n, page_type))


@app.route("/highest-total-pages", methods=["GET"])
def highest_total_pages():
    n = int(request.args.get("n", 50))
    page_type = request.args.get("page_type")
    return jsonify(get_top_general("number-of-pages", n, page_type))


@app.route("/sort-by-tool", methods=["GET"])
def sort_by_tool():
    tool_type = request.args.get("tool")
    n = int(request.args.get("n", 50))
    page_type = request.args.get("page_type")

    valid_tools = {
        "tool-video", "tool-audio", "tool-picture", "tool-slideshow",
        "tool-pdf", "tool-text", "tool-simpletext", "tool-shape"
    }

    if not tool_type or tool_type not in valid_tools:
        return jsonify({"error": f"Invalid or missing tool type. Choose from: {', '.join(valid_tools)}"}), 400

    if tool_type == "tool-text":
        tool_type = ["tool-text", "tool-simpletext"]

    return jsonify(get_top_tools(tool_type, n, page_type))


@app.route("/sort-by-link", methods=["GET"])
def sort_by_link():
    link_type = request.args.get("link_type")
    n = int(request.args.get("n", 50))

    valid_links = {
        "same_exposition", "other_expositions", "references", "external"
    }

    if not link_type or link_type not in valid_links:
        return jsonify({"error": f"Invalid or missing link type. Choose from: {', '.join(valid_links)}"}), 400

    return jsonify(get_top_links(link_type, n))


@app.route("/sort-by-metric", methods=["GET"])
def sort_by_graphical_metric():
    metric_key = request.args.get("metric")
    n = int(request.args.get("n", 50))

    valid_metrics = {
        "alignment_score",
        "horizontal_vertical_ratio",
        "overall_regular_score",
        "overlap_percentage",
        "size_uniformity_score",
        "spacing_score",
        "white_space_percentage"
    }

    if not metric_key or metric_key not in valid_metrics:
        return jsonify({"error": f"Invalid or missing metric. Choose from: {', '.join(valid_metrics)}"}), 400

    return jsonify(get_top_graphical_entries(metric_key, n))


@app.route("/filter-by-page-type", methods=["GET"])
def filter_by_page_type():
    page_type = request.args.get("page_type")
    if not page_type:
        return jsonify({"error": "Missing 'page_type' parameter"}), 400

    filtered_entries = {
        k: v for k, v in data.items() if v.get("default-page-type") == page_type
    }

    return jsonify([{"id": k, **v} for k, v in filtered_entries.items()])


@app.route("/exposition/<string:exposition_id>", methods=["GET"])
def get_exposition_by_id(exposition_id):
    exposition = data.get(exposition_id)
    if exposition:
        return jsonify({"id": exposition_id, **exposition})
    else:
        return jsonify({"error": "Exposition not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)