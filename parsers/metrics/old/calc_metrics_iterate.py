import subprocess
import sys
import pandas as pd
from rc_soup_pages import *

getInternalResearch()
RES = pd.read_json("research/internal_research.json")
URLS = RES["default-page"]

def calc_metrics(expo_id):
    try:
        result = subprocess.run(
            [sys.executable, 'calc_metrics.py', str(expo_id)],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Script output:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"Error calling script: {e}")
        print(f"Script error output:\n{e.stderr}")

def iterate(urls):
    
    for url in urls:
        expo_id = getExpositionId(url)
        calc_metrics(expo_id)
                
            
if __name__ == "__main__":
    iterate(URLS)