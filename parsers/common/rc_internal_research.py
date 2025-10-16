# tools to parse hyperlinks in RC expositions and to locate subpages
from expo import rc_soup_pages as expoParsers
from pathlib import Path
import requests
import json
import os
import time

RCURL = 'https://www.researchcatalogue.net'
JSONURL = "https://map.rcdata.org/internal_research.json"

number_of_days = 3


def getInternalResearch(path="../research", resume=False):
    os.makedirs(path, exist_ok=True)

    # --- download internal research JSON ---
    response = requests.get(JSONURL)
    data = response.json()
    internal_file = os.path.join(path, "internal_research.json")
    with open(internal_file, "w") as json_file:
        json.dump(data, json_file, indent=4)

    print("internal research saved to " + internal_file)

    # --- read it back ---
    with open(internal_file, "r") as file:
        research = json.load(file)

    outdated_expositions = []

    for index, exposition in enumerate(research):
        url = exposition["default-page"]
        id = expoParsers.getExpositionId(url)

        folder_path = Path(os.path.join(path, id))

        if folder_path.exists() and folder_path.is_dir():
            mod_time = folder_path.stat().st_mtime
            if resume:
                # outdated if older than N days
                if (time.time() - mod_time) > (number_of_days * 24 * 3600):
                    outdated_expositions.append(exposition)
            else:
                last_modified = exposition["last-modified"]
                if mod_time < last_modified:
                    print(f"Folder '{id}' is outdated.")
                    outdated_expositions.append(exposition)
                else:
                    print(f"Folder '{id}' is up to date.")
        else:
            print(f"Folder '{id}' does not exist — treating as outdated.")
            outdated_expositions.append(exposition)

    print(f"{len(outdated_expositions)} new or outdated expositions found.")

    outdated_file = os.path.join(path, "outdated_expositions.json")
    with open(outdated_file, "w") as outfile:
        json.dump(outdated_expositions, outfile, indent=2)