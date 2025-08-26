import os
import json
import re
import signal
from collections import defaultdict

main_directory = "../research" 
output_file = "../research/merged_stats.json"
pid_file = "flask_server.pid"  # <-- PID file to send SIGUSR1 to

merged_data = {}

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
                        "tool-counts": defaultdict(int),
                        "link-counts": defaultdict(int),
                        "total-number-of-tools": 0
                    }

                    default_page_url = data.get("url", "")
                    result_entry["default-page"] = default_page_url

                    parts = default_page_url.rstrip("/").split("/")
                    if len(parts) >= 6:
                        default_page_id = parts[5]

                        if default_page_id in pages:
                            default_page_data = pages[default_page_id]
                            result_entry["default-page-type"] = default_page_data.get("type", None)

                            if result_entry["default-page-type"] == "weave-graphical":
                                metrics = default_page_data.get("metrics", {})
                                if metrics:
                                    result_entry["metrics"] = metrics

                    for page_data in pages.values():
                        tools = page_data.get("tools", {})
                        for tool_type, tool_list in tools.items():
                            tool_count = len(tool_list)
                            result_entry["tool-counts"][tool_type] += tool_count
                            result_entry["total-number-of-tools"] += tool_count
                            
                        links = page_data.get("hyperlinks", {})
                        for link_type, link_list in links.items():
                            link_count = len(link_list)
                            result_entry["link-counts"][link_type] += link_count

                    result_entry["tool-counts"] = dict(result_entry["tool-counts"])
                    result_entry["link-counts"] = dict(result_entry["link-counts"])

                    merged_data[folder_name] = result_entry

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in {json_file}: {e}")
            except Exception as e:
                print(f"Unexpected error processing {json_file}: {e}")

with open(output_file, "w", encoding="utf-8") as outfile:
    json.dump(merged_data, outfile, indent=4)

print(f"Processed {len(merged_data)} JSON files into {output_file}.")

# 🔔 Send SIGUSR1 to Flask server
try:
    with open(pid_file, "r") as f:
        pid = int(f.read().strip())
    os.kill(pid, signal.SIGUSR1)
    print(f"Sent SIGUSR1 to Flask server (PID {pid}) to reload data.")
except FileNotFoundError:
    print(f"PID file '{pid_file}' not found. Flask server may not be running.")
except ProcessLookupError:
    print(f"No process found with PID {pid}.")
except Exception as e:
    print(f"Failed to send signal: {e}")
