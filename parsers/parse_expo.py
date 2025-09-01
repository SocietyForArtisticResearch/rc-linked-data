from bs4 import BeautifulSoup
from collections import defaultdict
from expo import rc_soup_parsers as rcParsers
from expo import rc_soup_pages as rcPages
from media import extract_copyrights as mediaParser
from screenshots import screenshot as rcScreenshot
from common.rc_session import rc_session
from media.rc_merge_data import insert_copyrights
from metrics.calc_metrics import calc_metrics
from metrics.generate_tools_map import generate_tools_map
from meta.parse_meta_page import parse_meta_page
import datetime
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
    return urlunparse(parsed_url._replace(path=clean_path.strip()))


def main(url, debug, download, shot, maps, force, session, research_folder="../research/", **meta):
    num = rcPages.getExpositionId(url)
    output_folder = os.path.join(research_folder, f"{num}")

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

    print("Parsing exposition: " + url)
    expo = session.get(clean_url(url))
    parsed = BeautifulSoup(expo.content, 'html.parser')

    # access restrictions
    if "Authentication required" in parsed.get_text():
        print("Exposition with restricted visibility.")
        return None
    if "You do not have permissions to access this research!" in parsed.get_text():
        print("Exposition not accessible.")
        return None

    # metadata
    if meta:
        meta_page_url = meta["meta-data-page"]
        modified = meta["last-modified"]
        print(f"Last-modified at: {datetime.datetime.fromtimestamp(modified)}")
    else:
        meta_page_url = rcPages.findMetaLink(parsed)
        if meta_page_url is None:
            print("Exposition does not exist.")
            print("Deleting folder.")
            shutil.rmtree(output_folder, ignore_errors=True)
            return None
        try:
            meta = parse_meta_page(meta_page_url, session)
            modified = meta["last-modified"]
            print(f"Last-modified at: {datetime.datetime.fromtimestamp(modified)}")
        except Exception:
            print("Failed to parse meta page.")
            return None

    # check if local copy exists
    if os.path.exists(output_folder):
        local_timestamp = os.path.getmtime(output_folder)
        print(f"Local folder timestamp: {datetime.datetime.fromtimestamp(local_timestamp)}")
        if modified + 86400 > local_timestamp:  # add one day tolerance
            print(f"Exposition already parsed, but maybe outdated. Reparsing at: {output_folder}.")
            shutil.rmtree(output_folder)
        else:
            print(f"Exposition already parsed at: {output_folder}. Skipping.")
            return

    # parse
    try:
        os.makedirs(output_folder, exist_ok=True)
        output_file_path = os.path.join(output_folder, f"{num}.json")

        media_folder = os.path.join(output_folder, "media")
        if download:
            # ensure trailing slash
            media_folder = media_folder + os.sep  
            os.makedirs(media_folder, exist_ok=True)
        else:
            media_folder = None

        screenshots_folder = os.path.join(output_folder, "screenshots") if shot else None
        if screenshots_folder:
            os.makedirs(screenshots_folder, exist_ok=True)

        maps_folder = os.path.join(output_folder, "maps") if maps else None
        if maps_folder:
            os.makedirs(maps_folder, exist_ok=True)

        exp_dict = {"id": int(num), "url": url, "pages": {}}
        copyrights = mediaParser.extract_copyrights(meta_page_url, session)
        pages = rcPages.getAllPages(url, parsed, meta_page_url, session)
        exp_dict["pages"] = {rcPages.getPageNumber(page): {} for page in pages}
        print(f"Found {len(pages)} pages.")
            all_links = defaultdict(set)

        for index, page in enumerate(pages):
            subpage = session.get(clean_url(page))
            parsed = BeautifulSoup(subpage.content, "html.parser")

            pageNumber = rcPages.getPageNumber(page)
            pageType = str(rcPages.getPageType(parsed)[0])
            print(f"Processing page {index+1}/{len(pages)}: {page}, {pageType}")

            toolsDict = None
            toolsMetrics = None
            hrefs = None
            screenshot = None
            map_file = None
            iframe_url = None

            match pageType:
                case "weave-graphical":
                    toolsDict = rcParsers.parse_graphical(parsed, debug)
                    toolsMetrics = calc_metrics(**toolsDict)
                    hrefs = rcPages.getLinks(url, parsed)
                    if maps_folder:
                        map_file = os.path.join(maps_folder, f"{pageNumber}.jpg")
                        generate_tools_map(map_file, 800, 600, **toolsDict)
                    if screenshots_folder:
                        screenshot = rcScreenshot.screenshotGraphical(clean_url(page), screenshots_folder, pageNumber)

                case "weave-block":
                    toolsDict = rcParsers.parse_block(parsed, debug)
                    hrefs = rcPages.getLinks(url, parsed)
                    if screenshots_folder:
                        screenshot = rcScreenshot.screenshotBlock(clean_url(page), screenshots_folder, pageNumber)

                case "iframe":
                    iframe_url = rcParsers.parse_iframe(parsed)

            page_dict = {"id": pageNumber, "type": pageType}
            if screenshot:
                page_dict["screenshot"] = screenshot
            if toolsDict:
                page_dict["tools"] = toolsDict
                exp_dict["copyrights"] = copyrights
            if toolsMetrics:
                page_dict["metrics"] = toolsMetrics
            if hrefs:
                page_dict["hyperlinks"] = hrefs
            if map_file:
                page_dict["map"] = map_file
            if iframe_url:
                page_dict["url"] = iframe_url

            exp_dict["pages"][pageNumber] = page_dict

    except Exception as e:
        error = f"An error occurred: {e}. Traceback: {traceback.format_exc()}"
        print(error)
            exp_dict["error"] = error
        exp_dict["pages"] = {}

    if copyrights and not isinstance(exp_dict, (str, bytes)):
        exp_dict["pages"] = insert_copyrights(
            copyrights, exp_dict["pages"], session, media_folder, download
        )
    else:
        print(f"exp_dict is not a string: {exp_dict}")

    exp_dict["meta"] = meta

        exp_dict["hyperlinks"] = {k: sorted(v) for k, v in all_links.items()}
                
    with open(output_file_path, "w") as outfile:
        json.dump(exp_dict, outfile, indent=2)
        print("Done.")

    return exp_dict


def print_usage():
    usage = """
Usage: python3 parse_expo.py <url> <debug> <download> <shot> <maps> <force> [auth] [research_folder]

Arguments:
    <url>             : Default page of the exposition to process.
    <debug>           : Debug mode (1 or 0).
    <download>        : Download assets (1 or 0).
    <shot>            : Take screenshots (1 or 0).
    <maps>            : Generate visual maps (1 or 0).
    <force>           : Always parse exposition, even if already parsed (1 or 0).
    [auth]            : Optional. If provided, prompts for authentication.
    [research_folder] : Optional. Path to research output folder (default: ../research/)
"""
    print(usage)


if __name__ == "__main__":
    if len(sys.argv) < 7:
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
        print("Error: debug, download, shot, maps, force must be integers (1 or 0).")
        print_usage()
        sys.exit(1)

    research_folder = "../research/"  # default

    if len(sys.argv) > 7 and sys.argv[7] == "auth":
        user = input("Email: ")
        password = getpass.getpass("Password: ")
        session = rc_session({"username": user, "password": password})
        if len(sys.argv) > 8:
            research_folder = sys.argv[8]
    else:
        session = requests.Session()
        print("Proceeding without authentication.")
        if len(sys.argv) > 7:
            research_folder = sys.argv[7]

    main(url, debug, download, shot, maps, force, session, research_folder=research_folder)