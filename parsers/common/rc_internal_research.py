#tools to parse hyperlinks in RC expositions and to locate subpages
import requests
import json

RCURL = 'https://www.researchcatalogue.net'
JSONURL = "https://map.rcdata.org/internal_research.json"

def getInternalResearch():
    response = requests.get(JSONURL)
    data = response.json()
    output_file = "../research/internal_research.json"
    with open(output_file, "w") as json_file:
        json.dump(data, json_file, indent=4) 
    
    print("internal research saved to " + output_file)