import os
import subprocess
import sys
import pandas as pd
import json
from rc_soup_pages import *

getInternalResearch()
RES = pd.read_json("research/internal_research.json")
URLS = RES["default-page"]

def make_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def merge_json_files(directory):
    merged_data = []

    for filename in os.listdir(directory):
        if filename.endswith(".json") and filename != "merged_expositions.json":
            file_path = os.path.join(directory, filename)
            
            try:
                with open(file_path, "r") as file:
                    data = json.load(file)
                    
                    if "id" in data:
                        merged_data.append(data)
                    else:
                        print(f"Warning: 'id' field not found in {filename}, skipping file.")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error reading {filename}: {e}")
    
    merged_data.sort(key=lambda x: x.get("id", float("inf"))) 
    
    merged_output_file = os.path.join(directory, "merged_expositions.json")
    
    with open(merged_output_file, "w") as outfile:
        json.dump(merged_data, outfile, indent=2)
    
    print(f"Merged JSON saved to {merged_output_file}")

def call_json2image(expo_id):
    try:
        result = subprocess.run(
            [sys.executable, 'json2image.py', str(expo_id)],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Script output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error calling script: {e}")
        print(f"Script error output:\n{e.stderr}")
        
def call_main_for_urls(urls, debug):
    directory = "research"
    make_dir(directory)
    
    for url in urls:
        expo_id = getExpositionId(url)
        filename = expo_id + ".json"
        output_file = os.path.join(directory, filename)

        if os.path.exists(output_file):
            print(f"File already exists for {url}, skipping parsing.")
        else:
            print(f"Processing {url} and saving to {output_file}")
            
            result = subprocess.run([sys.executable, 'rc_soup_main.py', url, str(debug)], capture_output=True, text=True)
            
            if result.returncode == 0:
                with open(output_file, "w") as outfile:
                    outfile.write(result.stdout)
                merge_json_files(directory)
    
            else:
                print(f"Error processing {url}: {result.stderr}")
                
            #call_json2image(expo_id)
            
if __name__ == "__main__":
    debug = 0
    call_main_for_urls(URLS, debug)