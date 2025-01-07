import os
import subprocess
import sys
import pandas as pd
import json
from rc_soup_pages import *
import requests

getInternalResearch()
RES = pd.read_json("research/internal_research.json")
URLS = RES["default-page"]

def make_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

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
    directory = "maps"
    make_dir(directory)
    
    for url in urls:
        expo_id = getExpositionId(url)
        filename = expo_id + ".png"
        output_file = os.path.join(directory, filename)

        if os.path.exists(output_file):
            print(f"Map already exists for {url}.")
        else:
            print(f"Processing {url} and saving to {output_file}")
            
            call_json2image(expo_id)
                
            
if __name__ == "__main__":
    debug = 0
    call_main_for_urls(URLS, debug)