import json
import os
import sys

def count_tool_types_and_generate_urls(pages, base_url):
    """Count the different tool types in the pages and generate URLs for each tool."""
    tool_types_count = {
        "text": 0,
        "picture": 0,
        "audio": 0,
        "video": 0,
        "shape": 0,
        "pdf": 0,
        "slideshow": 0,
        "embed": 0,
        "iframe": 0
    }

    tool_urls = {
        "text": [],
        "picture": [],
        "audio": [],
        "video": [],
        "shape": [],
        "pdf": [],
        "slideshow": [],
        "embed": [],
        "iframe": []
    }

    # Extract the base ID (this is the part after /view/)
    base_id = base_url.split("/view/")[-1].split('/')[0]  # Extract base ID after "/view/"
    
    base_url = base_url.split("/view/")[0]

    for page_id, page_content in pages.items():
        for tool_type, tools in page_content.items():
            if tool_type in ["tool-text", "tool-simpletext"]:
                tool_types_count["text"] += len(tools)
                if len(tools) > 0:
                    tool_urls["text"].append(generate_tool_url(base_url, base_id, page_id, tools[0]))
            else:
                cleaned_tool_type = tool_type.replace("tool-", "")
                if cleaned_tool_type in tool_types_count:
                    tool_types_count[cleaned_tool_type] += len(tools)
                    if len(tools) > 0:
                        tool_urls[cleaned_tool_type].append(generate_tool_url(base_url, base_id, page_id, tools[0]))

    return tool_types_count, tool_urls

def generate_tool_url(base_url, base_id, page_id, tool):
    """Generate the URL for a given tool."""
    # If the tool is a dictionary, extract the ID from it
    if isinstance(tool, dict):
        tool_id = tool.get("id")  # Assuming the tool ID is stored under the "id" key
        if tool_id is None:
            raise ValueError("Tool ID not found in the tool dictionary.")
    else:
        # If the tool is not a dictionary, it's probably just an ID in the format "tool-<ID>"
        tool_id = tool.split('-')[-1]  # Extract the ID if it's in the format "tool-<ID>"
    
    # Construct the full URL for the tool
    return f"{base_url}/view/{base_id}/{page_id}/#{tool_id}"

def generate_html_chart(id, tool_counts, tool_urls, output_html_file):
    """Generate an HTML file with a Chart.js pie chart."""
    labels = [key for key, value in tool_counts.items() if value > 0]
    sizes = [value for value in tool_counts.values() if value > 0]
    urls = {key: tool_urls[key] for key in labels}

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tool Distribution Pie Chart</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <canvas id="toolChart-{id}" width="400" height="400"></canvas>
        <script>
            const ctx = document.getElementById('toolChart-{id}').getContext('2d');
            const toolChart = new Chart(ctx, {{
                type: 'pie',
                data: {{
                    labels: {labels},
                    datasets: [{{
                        data: {sizes},
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(255, 206, 86, 0.2)',
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(153, 102, 255, 0.2)',
                            'rgba(255, 159, 64, 0.2)',
                            'rgba(201, 203, 207, 0.2)',
                            'rgba(140, 235, 140, 0.2)',
                            'rgba(235, 140, 140, 0.2)',
                            'rgba(140, 140, 235, 0.2)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)',
                            'rgba(255, 159, 64, 1)',
                            'rgba(201, 203, 207, 1)',
                            'rgba(140, 235, 140, 1)',
                            'rgba(235, 140, 140, 1)',
                            'rgba(140, 140, 235, 1)'
                        ],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'top',
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(tooltipItem) {{
                                    return tooltipItem.label + ': ' + tooltipItem.raw;
                                }}
                            }}
                        }}
                    }},
                    onClick: function(evt, elements) {{
                        if (elements.length > 0) {{
                            var elementIndex = elements[0].index;
                            var label = toolChart.data.labels[elementIndex];
                            var urlMap = {json.dumps(urls)};
                            var urlsForLabel = urlMap[label];
                            var url = urlsForLabel[0];  // Take the first URL for that tool
                            window.open(url, '_blank');
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    with open(output_html_file, 'w') as file:
        file.write(html_content)

    print(f"HTML file generated: {output_html_file}")

def main():
    # Parse the command line argument
    if len(sys.argv) != 2:
        print("Usage: python3 json2chart.py ID")
        sys.exit(1)

    id = sys.argv[1]
    json_file_path = f'research/{id}.json'

    if not os.path.exists(json_file_path):
        print(f"File not found: {json_file_path}")
        sys.exit(1)

    # Load the JSON data
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Process the JSON data to count the different types of tools and generate URLs
    base_url = data.get("url", "")  # Base URL before "/view"
    tool_counts, tool_urls = count_tool_types_and_generate_urls(data['pages'], base_url)

    # Generate the HTML file with the pie chart
    output_html_file = f'research/chart_{id}.html'
    generate_html_chart(id, tool_counts, tool_urls, output_html_file)

if __name__ == "__main__":
    main()