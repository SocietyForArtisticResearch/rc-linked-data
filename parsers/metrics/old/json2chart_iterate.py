import json
import os

def load_merged_json(file_path, limit=50):
    """Load the merged JSON file containing exposition data and return only the first `limit` entries."""
    with open(file_path, "r") as f:
        data = json.load(f)
    
    # Assuming the data is a list of entries
    if isinstance(data, list):
        return data[:limit]
    elif isinstance(data, dict):
        # If the JSON structure is a dictionary, you need to adapt to extract entries from the relevant key
        # For example, if the dictionary contains a key 'entries' that holds the list of data entries:
        # return data['entries'][:limit]
        # Adapt based on your actual JSON structure.
        return {key: data[key][:limit] for key in data if isinstance(data[key], list)}
    else:
        raise ValueError("Unexpected JSON structure")

def count_tool_types_for_exposition(exposition):
    """Count the different tool types for a given exposition."""
    tool_types_count = {
        "tool-text": 0,
        "tool-simpletext": 0,
        "tool-picture": 0,
        "tool-audio": 0,
        "tool-video": 0,
        "tool-shape": 0,
        "tool-pdf": 0,
        "tool-slideshow": 0,
        "tool-embed": 0,
        "tool-iframe": 0
    }
    
    # Count tools by type for each page in the exposition
    for page in exposition.get("pages", {}).values():
        for tool_type, tools in page.items():
            if tool_type in tool_types_count:
                tool_types_count[tool_type] += len(tools)  # Count tools by number of elements
    
    return tool_types_count

def generate_html_page_with_pie_charts(expositions, output_html_file):
    """Generate an HTML page with pie charts for each exposition using Chart.js."""
    
    # Add the dropdown menu for sorting tool types, including sorting by total number of tools
    html_content = """
    <html>
    <head>
        <title>Exposition Tools Pie Charts</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 10px;
                margin: 0;
            }
            h1 {
                font-size: 1.5em;
                margin-bottom: 10px;
            }
            h2 {
                font-size: 1.2em;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            .chart-container {
                display: inline-block;
                margin: 10px;
                vertical-align: top;
            }
            canvas {
                display: block;
                margin: 0 auto;
            }
            .url-container {
                display: inline-block;
                max-width: 220px;
                word-wrap: break-word;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            select {
                font-size: 1.2em;
                padding: 10px;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <h1>Exposition Tools Visualization</h1>
        <p>This page contains pie charts showing the distribution of tools for each exposition.</p>
        
        <!-- Dropdown menu for sorting by tool type or number of tools -->
        <select id="sort-dropdown">
            <option value="tool-text">Sort by Text Tools</option>
            <option value="tool-picture">Sort by Picture Tools</option>
            <option value="tool-video">Sort by Video Tools</option>
            <option value="tool-audio">Sort by Audio Tools</option>
            <option value="tool-pdf">Sort by PDF Tools</option>
            <option value="num-tools">Sort by Number of Tools</option>
        </select>
        
        <div class="charts" id="charts-container">
    """
    
    # Create a list of charts with associated tool counts
    chart_data_list = []

    for exposition in expositions:
        exposition_id = exposition.get("id")
        exposition_url = exposition.get("url")
        tool_types_count = count_tool_types_for_exposition(exposition)
        
        # Calculate the total number of tools
        total_tools = sum(tool_types_count.values())
        
        # Adjust the size of the chart based on the total number of tools
        chart_size = max(100, min(500, total_tools))  # Set a min and max size for better visualization
        
        # Prepare data for the pie chart
        labels = [key.replace('tool-', '').capitalize() for key in tool_types_count.keys()]
        data = list(tool_types_count.values())
        
        chart_data = {
            "id": exposition_id,
            "url": exposition_url,
            "tool_types_count": tool_types_count,
            "total_tools": total_tools,  # Store total number of tools here
            "chart_data": {
                "labels": labels,
                "datasets": [{
                    "data": data,
                    "backgroundColor": [
                        "rgba(75, 192, 192, 0.6)",
                        "rgba(153, 102, 255, 0.6)",
                        "rgba(255, 159, 64, 0.6)",
                        "rgba(54, 162, 235, 0.6)",
                        "rgba(255, 99, 132, 0.6)",
                        "rgba(201, 203, 207, 0.6)",
                        "rgba(255, 205, 86, 0.6)",
                        "rgba(231, 233, 237, 0.6)",
                        "rgba(140, 232, 255, 0.6)",
                        "rgba(255, 205, 220, 0.6)"
                    ],
                    "borderColor": [
                        "rgba(75, 192, 192, 1)",
                        "rgba(153, 102, 255, 1)",
                        "rgba(255, 159, 64, 1)",
                        "rgba(54, 162, 235, 1)",
                        "rgba(255, 99, 132, 1)",
                        "rgba(201, 203, 207, 1)",
                        "rgba(255, 205, 86, 1)",
                        "rgba(231, 233, 237, 1)",
                        "rgba(140, 232, 255, 1)",
                        "rgba(255, 205, 220, 1)"
                    ],
                    "borderWidth": 1
                }]
            }
        }

        # Store the chart data for later use
        chart_data_list.append(chart_data)
        
        # Add a canvas for each pie chart
        html_content += f"""
        <div class="chart-container" id="chart-container-{exposition_id}" data-id="{exposition_id}" style="width:{chart_size}px; height:{chart_size}px;">
            <h2>
                <div class="url-container">
                    <a href="{exposition_url}" target="_blank">link</a>
                </div>
            </h2>
            <canvas id="chart_{exposition_id}"></canvas>
            <script>
                var ctx_{exposition_id} = document.getElementById('chart_{exposition_id}').getContext('2d');
                var chart_{exposition_id} = new Chart(ctx_{exposition_id}, {{
                    type: 'pie',
                    data: {json.dumps(chart_data['chart_data'])},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{
                                position: 'bottom',
                                labels: {{
                                    boxWidth: 15
                                }}
                            }},
                            tooltip: {{
                                enabled: true
                            }}
                        }}
                    }}
                }});
            </script>
        </div>
        """
    
    # Convert chart_data_list to a JSON string to inject into JavaScript
    chart_data_json = json.dumps(chart_data_list)

    # Closing HTML tags and inject the JSON data into JavaScript
    html_content += f"""
        </div>

        <script>
            // Function to sort the charts based on selected option
            document.getElementById('sort-dropdown').addEventListener('change', function () {{
                var selectedTool = this.value;
                var charts = Array.from(document.querySelectorAll('.chart-container'));
                
                console.log('Sorting by:', selectedTool);  // Debugging line
                
                // Sort the charts based on the selected option
                charts.sort(function(a, b) {{
                    var toolCountA = 0;
                    var toolCountB = 0;
                    
                    if (selectedTool === 'num-tools') {{
                        // Sort by total number of tools
                        chartDataList.forEach(function(chart) {{
                            if (chart.id == a.dataset.id) {{
                                toolCountA = chart.total_tools || 0;
                            }}
                            if (chart.id == b.dataset.id) {{
                                toolCountB = chart.total_tools || 0;
                            }}
                        }});
                    }} else {{
                        // Sort by specific tool type
                        chartDataList.forEach(function(chart) {{
                            if (chart.id == a.dataset.id) {{
                                toolCountA = chart.tool_types_count[selectedTool] || 0;
                            }}
                            if (chart.id == b.dataset.id) {{
                                toolCountB = chart.tool_types_count[selectedTool] || 0;
                            }}
                        }});
                    }}

                    return toolCountB - toolCountA; // Sort descending
                }});

                // Re-order the charts in the DOM based on sortedCharts
                var chartsContainer = document.getElementById('charts-container');
                chartsContainer.innerHTML = '';  // Clear existing charts
                charts.forEach(function(chart) {{
                    chartsContainer.appendChild(chart);  // Append sorted chart containers
                }});
            }});

            // Store the chart data in JavaScript for sorting
            var chartDataList = {chart_data_json};
        </script>

    </body>
    </html>
    """

    # Save the HTML content to a file
    with open(output_html_file, "w") as f:
        f.write(html_content)
    
    print(f"HTML page with pie charts saved to {output_html_file}")

def main(merged_json_file, output_html_file):
    """Main function to generate the HTML page with pie charts for each exposition."""
    # Load merged JSON
    file_path = "research/merged_expositions.json"
    data = load_merged_json(file_path, limit=250)
    
    # Generate the HTML page with pie charts
    generate_html_page_with_pie_charts(data, output_html_file)

if __name__ == "__main__":
    merged_json_file = "research/merged_expositions.json"  # Path to your merged JSON file
    output_html_file = "research/exposition_tools_pie_charts.html"  # Output HTML file
    
    # Ensure the 'research' directory exists
    if not os.path.exists("research"):
        os.makedirs("research")
    
    main(merged_json_file, output_html_file)