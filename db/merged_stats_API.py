from flask import Flask, jsonify, request
import json

app = Flask(__name__)

with open("../research/merged_stats.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# get top N entries sorted by tool type
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


# get top N entries sorted by graphical metric
def get_top_graphical_entries(metric_key, n):
    filtered_entries = {
        k: v for k, v in data.items() if v.get("default-page-type") == "weave-graphical"
    }

    for k, v in filtered_entries.items():
        if "metrics" not in v:
            print(f"Warning: Entry {k} is missing 'metrics'")

    sorted_entries = sorted(
        filtered_entries.items(),
        key=lambda x: x[1].get("metrics", {}).get(metric_key, float("-inf")),
        reverse=True
    )

    return [{"id": entry[0], **entry[1]} for entry in sorted_entries[:n]]


# get top N entries sorted by total number of tools or pages
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


# sort by Total Number of Tools
@app.route("/highest-total-tools", methods=["GET"])
def highest_total_tools():
    n = int(request.args.get("n", 50))
    page_type = request.args.get("page_type")
    return jsonify(get_top_general("total-number-of-tools", n, page_type))


# sort by Total Number of Pages
@app.route("/highest-total-pages", methods=["GET"])
def highest_total_pages():
    n = int(request.args.get("n", 50))
    page_type = request.args.get("page_type")
    return jsonify(get_top_general("number-of-pages", n, page_type))


# sort by Tool Type Count
@app.route("/sort-by-tool", methods=["GET"])
def sort_by_tool():
    tool_type = request.args.get("tool")  # get the requested tool type
    n = int(request.args.get("n", 50))  # optional `n`, default to 50
    page_type = request.args.get("page_type")  # optional page type filter

    valid_tools = {
        "tool-video",
        "tool-audio",
        "tool-picture",
        "tool-slideshow",
        "tool-pdf",
        "tool-text",
        "tool-simpletext"
    }

    if not tool_type or tool_type not in valid_tools:
        return jsonify({"error": f"Invalid or missing tool type. Choose from: {', '.join(valid_tools)}"}), 400

    # text tools include both "tool-text" and "tool-simpletext"
    if tool_type == "tool-text":
        tool_type = ["tool-text", "tool-simpletext"]

    return jsonify(get_top_tools(tool_type, n, page_type))


# sort by Metrics
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


# filter by Default Page Type
@app.route("/filter-by-page-type", methods=["GET"])
def filter_by_page_type():
    page_type = request.args.get("page_type")
    if not page_type:
        return jsonify({"error": "Missing 'page_type' parameter"}), 400

    print(type(data))
    print(list(data.items())[:5])

    filtered_entries = {k: v for k, v in data.items() if v.get("default-page-type") == page_type}

    return jsonify([{"id": k, **v} for k, v in filtered_entries.items()])


if __name__ == "__main__":
    app.run(debug=True)
    

#examples
# GET /sort-by-tool?tool=tool-video
# GET /sort-by-tool?tool=tool-text&n=20&page_type=weave-graphical
# GET /sort-by-metric?metric=spacing_score
# GET /highest-total-tools?n=100
# GET /filter-by-page-type?page_type=weave-graphical