from bs4 import BeautifulSoup
from expo import rc_soup_parsers as rcParsers
from expo import rc_soup_pages as rcPages
from media import extract_copyrights as mediaParser
from screenshots import screenshot as rcScreenshot
from common.rc_session import rc_session
from media.rc_merge_data import insert_copyrights
from metrics.calc_metrics import calc_metrics
from metrics.generate_tools_map import generate_tools_map
from meta.parse_meta_page import parse_meta_page
import traceback
import getpass
import requests
import json
import sys
import os
import shutil
from urllib.parse import urlparse, urlunparse, unquote

def clean_url(url):
    parsed_url = urlparse(url)
    clean_path = unquote(parsed_url.path)
    cleaned_url = urlunparse(parsed_url._replace(path=clean_path.strip()))

    return cleaned_url

def main(url, debug, download, shot, maps, force, session, **meta):
    num = rcPages.getExpositionId(url)
    research_folder = '../research/'
    output_folder = f"{research_folder}{num}/"
    if force:
        print(f"Force flag enabled. Processing exposition at: {output_folder}")
        try:
            shutil.rmtree(output_folder)
            print(f"Folder '{output_folder}' has been deleted.")
        except FileNotFoundError:
            print(f"Folder '{output_folder}' not found. Creating now.")
        except PermissionError:
            print(f"Permission denied: Unable to delete '{output_folder}'.")
        except Exception as e:
            print(f"An error occurred: {e}")
    if os.path.exists(output_folder):
        print(f"Exposition already parsed at: {output_folder}. Skipping.")
        return
    #copyrights_folder = output_folder + 'copyrights'
    os.makedirs(output_folder, exist_ok=True)
    output_file_path = os.path.join(output_folder, f'{num}.json')
    if download:
        media_folder = output_folder + 'media/'
        os.makedirs(media_folder, exist_ok=True)
    else:
        media_folder = None
    if shot:
        screenshots_folder = output_folder + 'screenshots'
        os.makedirs(screenshots_folder, exist_ok=True)
    if maps:
        maps_folder = output_folder + 'maps'
        os.makedirs(maps_folder, exist_ok=True)
    exp_dict = {"id": int(num), "url": url, "pages": {}}
      
    print("Parsing exposition: " + url)
    
    expo = session.get(clean_url(url))
    parsed = BeautifulSoup(expo.content, 'html.parser')
    
    if "Authentication required" in parsed.get_text():
        print("Exposition with restricted visibility.")
        return None
    
    if "You do not have permissions to access this research!" in parsed.get_text():
        print("Exposition not accessible.")
        return None
    
    else:
        try:
            meta_page_url = rcPages.findMetaLink(parsed)
            copyrights = mediaParser.extract_copyrights(meta_page_url, session)
            pages = rcPages.getAllPages(url, parsed, meta_page_url, session)
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
                        if maps:
                            map_file = f"{maps_folder}/{pageNumber}.jpg"
                            generate_tools_map(map_file, 800, 600, **toolsDict)
                        if shot:
                            screenshot = rcScreenshot.screenshotGraphical(clean_url(page), screenshots_folder, pageNumber)
                        else:
                            screenshot = None
                    case "weave-block":
                        toolsDict = rcParsers.parse_block(parsed, debug)
                        toolsMetrics = None
                        map_file = None
                        if shot:
                            screenshot = rcScreenshot.screenshotBlock(clean_url(page), screenshots_folder, pageNumber)
                        else:
                            screenshot = None
                    case "iframe":
                        url = rcParsers.parse_iframe(parsed)
                        toolsDict = None
                        toolsMetrics = None
                        screenshot = None
                        map_file = None
                    case _:
                        toolsDict = None
                        toolsMetrics = None
                        screenshot = None
                        map_file = None
                    
                # all pages have id and type   
                page_dict = {
                    "id": pageNumber, 
                    "type": pageType
                }
                
                if screenshot:
                    page_dict["screenshot"] = screenshot
                
                # graphical and block pages have tools
                if toolsDict:
                    page_dict["tools"] = toolsDict
                    exp_dict["copyrights"] = copyrights
                
                # graphical pages have metrics and maps
                if toolsMetrics:
                    page_dict["metrics"] = toolsMetrics
                
                if maps:
                    page_dict["map"] = map_file
                   
                # iframe 
                if url:
                    page_dict["url"] = url
                    
                exp_dict["pages"][pageNumber] = page_dict

        except Exception as e:
            error = f"An error occurred: {e}. Traceback: {traceback.format_exc()}"
            print(error)
            exp_dict["pages"] = error
        
        if copyrights: 
            exp_dict["pages"] = insert_copyrights(copyrights, exp_dict["pages"], session, media_folder, download)
            
        if meta:
            exp_dict["meta"] = meta
        else:
            try:
                meta = parse_meta_page(meta_page_url, session)
                exp_dict["meta"] = meta
            except:
                print("Failed to parse meta page.")
                
        exp_json = json.dumps(exp_dict, indent=2)
        with open(output_file_path, 'w') as outfile:
            outfile.write(exp_json)
            print("Done.")
            
        return exp_dict

def print_usage():
    usage = """
Usage: python3 parse_expo.py <url> <debug> <download> <shot> <maps> <force> [auth]
    
Arguments:
    <url>       : Default page of the exposition to process.
    <debug>     : Debug mode (1 for enabled, 0 for disabled).
    <download>  : Download assets (1 for enabled, 0 for disabled).
    <shot>      : Take screenshots (1 for enabled, 0 for disabled).
    <maps>      : Generate visual maps (1 for enabled, 0 for disabled).
    <force>     : Always parse an exposition, even when it has been parsed before (1 for enabled, 0 for disabled).
    [auth]      : Optional. If provided, prompts for authentication.

Examples:
    Without authentication:
        python3 parse_expo.py "default-page" 0 1 0 0

    With authentication:
        python3 parse_expo.py "default-page" 0 1 0 0 auth
"""
    print(usage)

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Error: Missing required arguments.")
        print_usage()
        sys.exit(1)

    url = str(sys.argv[1])
    try:
        debug = int(sys.argv[2])
        download = int(sys.argv[3])
        shot = int(sys.argv[4])
        maps = int(sys.argv[5])
        force = int(sys.argv[6])
    except ValueError:
        print("Error: debug, download, and shot must be integers (1 or 0).")
        print_usage()
        sys.exit(1)

    if len(sys.argv) > 7 and sys.argv[7] == "auth":
        user = input("Email: ")
        password = getpass.getpass("Password: ")
        session = rc_session({'username': user, 'password': password})
    else:
        session = requests.Session()
        print("Proceeding without authentication.")

    main(url, debug, download, shot, maps, force, session)

