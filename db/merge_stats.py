import os
import json
import re
from collections import defaultdict

main_directory = "../research" 
output_file = "../research/merged_stats.json"

merged_data = {}

#id_pattern = re.compile(r"/(\d+)$")

for folder_name in os.listdir(main_directory):
    folder_path = os.path.join(main_directory, folder_name)

    if os.path.isdir(folder_path) and folder_name.isdigit():
        json_file = os.path.join(folder_path, f"{folder_name}.json")

        if os.path.exists(json_file):
            try:
                with open(json_file, "r", encoding="utf-8") as file:
                    data = json.load(file)

                    pages = data.get("pages", {})
                    number_of_pages = len(pages)

                    result_entry = {
                        "number-of-pages": number_of_pages,
                        "default-page-type": None,
                        "default-page": None,
                        "tool-counts": defaultdict(int),  # Default dictionary for counting tools
                        "total-number-of-tools": 0
                    }

                    #meta = data.get("meta", {})
                    default_page_url = data.get("url", "")

                    result_entry["default-page"] = default_page_url

                    match = default_page_url.rstrip("/").split("/")[5]
                    if match:
                        default_page_id = match#.group(1)  # Extracted ID as string

                        # Find the type of the default page in the pages dictionary
                        if default_page_id in pages:
                            default_page_data = pages[default_page_id]
                            result_entry["default-page-type"] = default_page_data.get("type", None)

                            # If the default-page type is "weave-graphical", copy over "metrics"
                            if result_entry["default-page-type"] == "weave-graphical":
                                metrics = default_page_data.get("metrics", {})
                                if metrics:
                                    result_entry["metrics"] = metrics

                    # Loop through all pages to count tools by type
                    for page_data in pages.values():
                        tools = page_data.get("tools", {})
                        for tool_type, tool_list in tools.items():
                            tool_count = len(tool_list)
                            result_entry["tool-counts"][tool_type] += tool_count
                            result_entry["total-number-of-tools"] += tool_count  # Update total count

                    # Convert defaultdict to regular dictionary
                    result_entry["tool-counts"] = dict(result_entry["tool-counts"])

                    # Store processed data under the folder name (ID)
                    merged_data[folder_name] = result_entry

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {json_file}: {e}")
            except Exception as e:
                print(f"Unexpected error processing {json_file}: {e}")

with open(output_file, "w", encoding="utf-8") as outfile:
    json.dump(merged_data, outfile, indent=4)

print(f"Processed {len(merged_data)} JSON files into {output_file}.")