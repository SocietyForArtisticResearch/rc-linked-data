from common import rc_internal_research as rcMisc
from expo import rc_soup_pages as expoParsers
from pathlib import Path
import json

rcMisc.getInternalResearch("../research")
outdated_expositions = []

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

with open("../research/outdated_expositions.json", "w") as outfile:
    json.dump(outdated_expositions, outfile, indent=2)