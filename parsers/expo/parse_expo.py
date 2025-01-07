import requests
from bs4 import BeautifulSoup
from rc_soup_pages import *
from rc_soup_tools import *
from rc_soup_parsers import *
import json
import sys
import os
from urllib.parse import urlparse, urlunparse, unquote

def clean_url(url):
    parsed_url = urlparse(url)
    clean_path = unquote(parsed_url.path)
    cleaned_url = urlunparse(parsed_url._replace(path=clean_path.strip()))

    return cleaned_url

def main(url, debug):
    num = getExpositionId(url)
    output_folder = 'parsed'
    os.makedirs(output_folder, exist_ok=True)
    output_file_path = os.path.join(output_folder, f'{num}.json')
    exp_dict = {"id": int(num), "url": url, "pages": {}}
      
    print("Parsing exposition " + url)
    
    expo = requests.get(clean_url(url))
    parsed = BeautifulSoup(expo.content, 'html.parser')
    pages = getAllPages(url, parsed)
    exp_dict["pages"] = {getPageNumber(page): {} for page in pages}
    print(f"Found {len(pages)} pages.")

    for index, page in enumerate(pages):
        subpage = requests.get(clean_url(page))
        parsed = BeautifulSoup(subpage.content, 'html.parser')
        
        pageNumber = getPageNumber(page)
        pageType = getPageType(parsed)
        pageType = str(pageType[0])
        print(f"Processing page {index+1}/{len(pages)}: {page}, {pageType}")
        
        match pageType:
            case "weave-graphical":
                toolsDict = parse_graphical(parsed, debug)
            case "weave-block":
                toolsDict = parse_block(parsed, debug)
            case _:
                toolsDict = None
                
        page_dict = {
            "id": pageNumber, 
            "type": pageType,
            "tools": toolsDict
        }
            
        exp_dict["pages"][pageNumber] = page_dict
            
    exp_json = json.dumps(exp_dict, indent=2)
    with open(output_file_path, 'w') as outfile:
        outfile.write(exp_json)
        print("Done.")


if __name__ == "__main__":
    url = str(sys.argv[1])
    debug = int(sys.argv[2])
    main(url, debug)