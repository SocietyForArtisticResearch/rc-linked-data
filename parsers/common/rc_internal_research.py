#tools to parse hyperlinks in RC expositions and to locate subpages
from expo import rc_soup_pages as expoParsers
from pathlib import Path
import requests
import json
import os

RCURL = 'https://www.researchcatalogue.net'
JSONURL = "https://map.rcdata.org/internal_research.json"

outdated_expositions = []

def getInternalResearch(path="../research"):
    os.makedirs(path, exist_ok=True)
    response = requests.get(JSONURL)
    data = response.json()
    output_file = "../research/internal_research.json"
    with open(output_file, "w") as json_file:
        json.dump(data, json_file, indent=4) 
    
    print("internal research saved to " + output_file)
    
    with open("../research/internal_research.json", "r") as file:
        research = json.load(file)

        for index, exposition in enumerate(research):
            url = exposition["default-page"]
            id = expoParsers.getExpositionId(url)

            folder_path = Path("../research/" + id)

            if folder_path.exists() and folder_path.is_dir():
                mod_time = folder_path.stat().st_mtime
                last_modified = exposition["last-modified"]
                
                if mod_time < last_modified:
                    print(f"Folder '{id}' is outdated.")
                    outdated_expositions.append(exposition)
                else:
                    print(f"Folder '{id}' is up to date.")
            else:
                print(f"Folder '{id}' does not exist — treating as outdated.")
                outdated_expositions.append(exposition)

    print(f"{len(outdated_expositions)} new or outfdated expositions found.")
    
    with open("../research/outdated_expositions.json", "w") as outfile:
        json.dump(outdated_expositions, outfile, indent=2)