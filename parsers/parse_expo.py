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
import os
import shutil
import re
from urllib.parse import urlparse, urlunparse, unquote


def clean_url(url):
    parsed_url = urlparse(url)
    clean_path = unquote(parsed_url.path)
    return urlunparse(parsed_url._replace(path=clean_path.strip()))


def main(url, debug, download, shot, maps, force, session=None, research_folder="../research/", username=None, password=None, screenshots_root=None, always_reparse=False, **meta):
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
    print(session)
    print("Getting exposition: " + url)
    expo = session.get(clean_url(url))
    print("Parsing exposition: " + url)
    print(f"Response status: {expo.status_code}")
    parsed = BeautifulSoup(expo.content, 'html.parser')

    # access restrictions
    if "Authentication required" in parsed.get_text():
        print("Exposition with restricted visibility.")
        if username and password:
            print("Attempting authentication with provided credentials...")
            session = rc_session(username, password)
            expo = session.get(clean_url(url))
            parsed = BeautifulSoup(expo.content, 'html.parser')
            if "Authentication required" in parsed.get_text():
                print("Authentication failed.")
                return None
            else:
                print("Authentication successful.")
        else:
            print("No credentials provided for restricted exposition.")
            return None
    
    if "You do not have permissions to access this research!" in parsed.get_text():
        print("Exposition not accessible.")
        return None

    # metadata
    if meta:
        meta_page_url = meta["meta-data-page"]
        print(meta_page_url)
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
            print(meta_page_url)
            meta = parse_meta_page(meta_page_url, session)
            modified = meta["last-modified"]
            print(f"Last-modified at: {datetime.datetime.fromtimestamp(modified)}")
        except Exception:
            print("Failed to parse meta page.")
            return None

    # check if local copy exists
    if always_reparse:
        print(f"Redo mode: reparsing {output_folder} regardless of timestamp, keeping existing files in place.")
    elif os.path.exists(output_folder):
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

        screenshots_base = None
        if shot:
            if screenshots_root:
                screenshots_base = os.path.join(screenshots_root, num)
            else:
                screenshots_base = os.path.join(output_folder, "screenshots")
            os.makedirs(screenshots_base, exist_ok=True)

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
                    if screenshots_base:
                        weave_folder = os.path.join(screenshots_base, str(pageNumber))
                        os.makedirs(weave_folder, exist_ok=True)
                        screenshot = rcScreenshot.screenshotGraphical(clean_url(page), weave_folder, 1)

                case "weave-block":
                    toolsDict = rcParsers.parse_block(parsed, debug)
                    hrefs = rcPages.getLinks(url, parsed)
                    if screenshots_base:
                        weave_folder = os.path.join(screenshots_base, str(pageNumber))
                        os.makedirs(weave_folder, exist_ok=True)
                        screenshot = rcScreenshot.screenshotBlock(clean_url(page), weave_folder, 1)

                case "weave-text":
                    if screenshots_base:
                        weave_folder = os.path.join(screenshots_base, str(pageNumber))
                        os.makedirs(weave_folder, exist_ok=True)
                        screenshot = rcScreenshot.screenshotText(clean_url(page), weave_folder, 1)

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
            if hrefs:
                for category, links in hrefs.items():
                    all_links[category].update(links)
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

    if copyrights and isinstance(exp_dict, dict):
        exp_dict["pages"] = insert_copyrights(
            copyrights, exp_dict["pages"], session, media_folder, download
        )
    elif copyrights and isinstance(exp_dict, (str, bytes)):
        print(f"ERROR: exp_dict is unexpectedly a string/bytes: {exp_dict}")
    # If no copyrights, just continue without inserting them

    exp_dict["meta"] = meta

    exp_dict["hyperlinks"] = {k: sorted(v) for k, v in all_links.items()}
    
    # concatenate all tool-text and tool-simpletext
    all_tool_text = []

    for page_id, page_data in exp_dict.get("pages", {}).items():
        tools = page_data.get("tools", {})

        for tool_data in tools.get("tool-text", []):
            src = tool_data.get("src")
            if src:
                all_tool_text.append(src.strip())

        for tool_data in tools.get("tool-simpletext", []):
            src = tool_data.get("src")
            if src:
                all_tool_text.append(src.strip())
                
    all_tool_text = " ".join(all_tool_text)

    exp_dict["text"] = {}
    exp_dict["text"]["content"] = all_tool_text
    exp_dict["text"]["charcount"] = len(all_tool_text)
    exp_dict["text"]["wordcount"] = len(all_tool_text.split())    
    
    # extract simple URLs from all_tool_text
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    urls = re.findall(url_pattern, all_tool_text)
    found_urls = [url.rstrip('.,)') for url in urls]
    
    exp_dict["hyperlinks"]["simpleurls"] = found_urls
                
    with open(output_file_path, "w") as outfile:
        json.dump(exp_dict, outfile, indent=2)
        print("Done.")

    return exp_dict


def build_parser():
    parser = argparse.ArgumentParser(description="Parse a single Research Catalogue exposition.")
    parser.add_argument("url", help="Default page URL of the exposition to process.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    parser.add_argument("--download", action="store_true", help="Download media assets.")
    parser.add_argument("--shot", action="store_true", help="Take screenshots of weaves.")
    parser.add_argument("--maps", action="store_true", help="Generate visual tool maps.")
    parser.add_argument("--force", action="store_true", help="Re-parse even if already parsed.")
    parser.add_argument("--username", default=None, help="Email for RC authentication.")
    parser.add_argument("--password", default=None, help="Password for RC authentication.")
    parser.add_argument("--research-folder", default="../research/", help="Path to research output folder (default: ../research/).")
    parser.add_argument("--screenshots-root", default=None, help="Root path for screenshots, stored as root/expo_id/weave_id/1.png.")
    return parser


if __name__ == "__main__":
    import argparse

    args = build_parser().parse_args()

    if args.username and args.password:
        print(f"Using provided credentials for user: {args.username}")
        session = rc_session(args.username, args.password)
    else:
        print("Proceeding without authentication.")
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

    screenshots_root = None
    if args.screenshots_root:
        screenshots_root = os.path.abspath(args.screenshots_root)

    main(args.url, args.debug, args.download, args.shot, args.maps, args.force,
         session=session, research_folder=args.research_folder,
         username=args.username, password=args.password,
         screenshots_root=screenshots_root)