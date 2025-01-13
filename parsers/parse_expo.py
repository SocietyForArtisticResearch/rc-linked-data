from bs4 import BeautifulSoup
import expo.rc_soup_parsers as rcParsers
import expo.rc_soup_pages as rcPages
import media.extract_copyrights as mediaParser
from common.rc_session import rc_session
from media.rc_merge_data import insert_copyrights
from metrics.calc_metrics import calc_metrics
from metrics.generate_tools_map import generate_tools_map
import traceback
import json
import sys
import os
from urllib.parse import urlparse, urlunparse, unquote

session = rc_session() #with login
#session = requests.Session()

def clean_url(url):
    parsed_url = urlparse(url)
    clean_path = unquote(parsed_url.path)
    cleaned_url = urlunparse(parsed_url._replace(path=clean_path.strip()))

    return cleaned_url

def main(url, debug):
    num = rcPages.getExpositionId(url)
    research_folder = '../research/'
    output_folder = research_folder + 'parsed'
    media_folder = research_folder + 'media'
    copyrights_folder = research_folder + 'copyrights'
    os.makedirs(output_folder, exist_ok=True)
    output_file_path = os.path.join(output_folder, f'{num}.json')
    output_media_path = os.path.join(media_folder, f'{num}/')
    os.makedirs(output_media_path, exist_ok=True)
    exp_dict = {"id": int(num), "url": url, "pages": {}}
      
    print("Parsing exposition: " + url)
    
    expo = session.get(clean_url(url))
    parsed = BeautifulSoup(expo.content, 'html.parser')
    
    try:
        copyrights = mediaParser.extract_copyrights(rcPages.findMetaLink(parsed), session, copyrights_folder)
        pages = rcPages.getAllPages(url, parsed)
        exp_dict["pages"] = {rcPages.getPageNumber(page): {} for page in pages}
        print(f"Found {len(pages)} pages.")

        for index, page in enumerate(pages):
            subpage = session.get(clean_url(page))
            parsed = BeautifulSoup(subpage.content, 'html.parser')
            
            pageNumber = rcPages.getPageNumber(page)
            pageType = rcPages.getPageType(parsed)
            pageType = str(pageType[0])
            print(f"Processing page {index+1}/{len(pages)}: {page}, {pageType}")
            
            match pageType:
                case "weave-graphical":
                    toolsDict = rcParsers.parse_graphical(parsed, debug)
                    toolsMetrics = calc_metrics(**toolsDict)
                    map_file = f"{media_folder}/maps/{pageNumber}.jpg"
                    generate_tools_map(map_file, 800, 600, **toolsDict)
                case "weave-block":
                    toolsDict = rcParsers.parse_block(parsed, debug)
                    toolsMetrics = None
                case _:
                    toolsDict = None
                    toolsMetrics = None
                 
            # all pages have id and type   
            page_dict = {
                "id": pageNumber, 
                "type": pageType
            }
            
            # graphical and block pages have tools
            if toolsDict:
                page_dict["tools"] = toolsDict
            
            # graphical pages have metrics
            if toolsMetrics:
                page_dict["metrics"] = toolsMetrics
                page_dict["map"] = map_file
                
            exp_dict["pages"][pageNumber] = page_dict
            exp_dict["copyrights"] = copyrights

    except Exception as e:
        error = f"An error occurred: {e}. Traceback: {traceback.format_exc()}"
        print(error)
        exp_dict["pages"] = error
        
    exp_dict["pages"] = insert_copyrights(copyrights, exp_dict["pages"], session, output_media_path)
            
    exp_json = json.dumps(exp_dict, indent=2)
    with open(output_file_path, 'w') as outfile:
        outfile.write(exp_json)
        print("Done.")
        
    return exp_dict

if __name__ == "__main__":
    url = str(sys.argv[1])
    debug = int(sys.argv[2])
    main(url, debug)

