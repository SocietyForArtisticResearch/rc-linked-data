import subprocess
import pandas as pd
import sys
from common.rc_internal_research import getInternalResearch

getInternalResearch()
RES = pd.read_json("../research/internal_research.json")
URLS = RES["default-page"]

def parse_expo(url, debug, download, shot):
    try:
        result = subprocess.run(
            [sys.executable, 'parse_expo.py', url, debug, download, shot],
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
        parse_expo(url, "1", "1", "0")     
            
if __name__ == "__main__":
    iterate(URLS)