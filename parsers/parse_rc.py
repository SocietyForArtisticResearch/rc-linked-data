from bs4 import BeautifulSoup
import argparse
import json
import requests
import getpass
import os
import traceback
from common import rc_internal_research as rcMisc
from common.rc_logging import setup_logger
from common.rc_session import rc_session
from expo import rc_soup_pages as rcPages
from parse_expo import main as parse_expo


def build_parser():
    parser = argparse.ArgumentParser(description="Parse Research Catalogue expositions.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    parser.add_argument("--download", action="store_true", help="Download media assets.")
    parser.add_argument("--shot", action="store_true", help="Take screenshots of weaves.")
    parser.add_argument("--maps", action="store_true", help="Generate visual tool maps.")
    parser.add_argument("--force", action="store_true", help="Re-parse expositions even if already parsed.")
    parser.add_argument("--resume", action="store_true", help="Update everything older than three days.")
    parser.add_argument("--auth", action="store_true", help="Prompt for RC login credentials.")
    parser.add_argument("--research-folder", default="../research/", help="Path to research output folder (default: ../research/).")
    parser.add_argument("--screenshots-root", default=None, help="Root path for screenshots, stored as root/expo_id/weave_id/1.png. If omitted, screenshots are stored inside each exposition's output folder.")
    parser.add_argument("--lookup", default=None, metavar="URL", help="Provide a URL; will look for exposition links in that page and download only those.")
    parser.add_argument("--screenshot-ids", default=None, metavar="FILE",
                         help="Path to a text file with one exposition id (integer) per line. Only these "
                              "expositions are processed: their TOC is (re-)parsed and their screenshots are "
                              "always retaken, ignoring any existing data. Other expositions are left untouched. "
                              "Errors are printed clearly and logged to <research-folder>/logs/parse_rc.log.")
    parser.add_argument("--log-retention-days", type=int, default=14,
                         help="How many days of logs to keep for --screenshot-ids runs (default: 14).")
    return parser


def run_screenshot_ids(args, session, research_folder, screenshots_root, rc_dict, rc_dict_path):
    logger = setup_logger(research_folder, retention_days=args.log_retention_days)

    with open(args.screenshot_ids, "r") as file:
        raw_lines = [line.strip() for line in file if line.strip()]

    ids = []
    for line in raw_lines:
        if line.isdigit():
            ids.append(int(line))
        else:
            logger.error(f"Skipping invalid exposition id in {args.screenshot_ids}: '{line}'")

    logger.info(f"Re-screenshotting {len(ids)} exposition(s): {ids}")

    # Reuse the locally cached internal_research.json (if present) so we don't
    # need network access just to look up exposition URLs/metadata.
    internal_research_path = os.path.join(research_folder, "internal_research.json")
    id_lookup = {}
    if os.path.exists(internal_research_path):
        with open(internal_research_path, "r") as file:
            for entry in json.load(file):
                id_lookup[entry["id"]] = entry
    else:
        logger.warning(
            f"No internal_research.json found in {research_folder}; exposition urls/metadata "
            "will be resolved directly from the live site instead."
        )

    failed_ids = set()
    for index, expo_id in enumerate(ids):
        logger.info(f"[{index + 1}/{len(ids)}] Exposition {expo_id}: starting")

        entry = id_lookup.get(expo_id)
        try:
            if entry:
                url = entry["default-page"]
                meta = dict(entry)
            else:
                url = rcPages.resolveDefaultPageUrl(expo_id, session)
                meta = {}

            expo = parse_expo(
                url, args.debug, False, True, False, False, session,
                research_folder=research_folder, screenshots_root=screenshots_root,
                always_reparse=True, **meta
            )
        except Exception:
            failed_ids.add(expo_id)
            logger.error(f"Exposition {expo_id}: failed to process.\n{traceback.format_exc()}")
            continue

        if not expo:
            failed_ids.add(expo_id)
            logger.error(f"Exposition {expo_id}: no data returned (inaccessible, restricted, or removed).")
            continue

        rc_dict[expo["id"]] = expo
        with open(rc_dict_path, "w") as outfile:
            json.dump(rc_dict, outfile, indent=2)

        if expo.get("error"):
            failed_ids.add(expo_id)
            logger.error(f"Exposition {expo_id}: TOC parsing error -- {expo['error']}")

        for page_id, page_data in expo.get("pages", {}).items():
            screenshot = page_data.get("screenshot")
            if screenshot and not str(screenshot.get("file", "")).lower().endswith(".png"):
                failed_ids.add(expo_id)
                logger.error(
                    f"Exposition {expo_id}, page {page_id}: screenshot failed -- {screenshot.get('file')}"
                )

        logger.info(f"[{index + 1}/{len(ids)}] Exposition {expo_id}: done")

    logger.info(f"Finished. {len(ids) - len(failed_ids)}/{len(ids)} exposition(s) processed without errors.")
    if failed_ids:
        logger.error(f"Expositions with errors: {sorted(failed_ids)}")


if __name__ == "__main__":
    args = build_parser().parse_args()

    # --- session ---
    if args.auth:
        user = input("Email: ")
        password = getpass.getpass("Password: ")
        session = rc_session(user, password)
    else:
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
        print("Proceeding without authentication.")

    # --- normalize paths ---
    research_folder = os.path.abspath(args.research_folder)
    os.makedirs(research_folder, exist_ok=True)

    screenshots_root = None
    if args.screenshots_root:
        screenshots_root = os.path.abspath(args.screenshots_root)
        os.makedirs(screenshots_root, exist_ok=True)

    # --- file paths ---
    rc_dict_path = os.path.join(research_folder, "rc_dict.json")
    advanced_research_dict_path = os.path.join(research_folder, "rc_advanced.json")

    # --- load existing dicts ---
    try:
        with open(rc_dict_path, "r") as file:
            rc_dict = json.load(file)
            print("RC dict loaded.")
    except FileNotFoundError:
        rc_dict = {}
        print(f"File '{rc_dict_path}' not found. New dict created.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        rc_dict = {}
    except Exception as e:
        print(f"An error occurred: {e}")
        rc_dict = {}

    try:
        with open(advanced_research_dict_path, "r") as file:
            rc_advanced = json.load(file)
            print("RC advanced dict loaded.")
    except FileNotFoundError:
        rc_advanced = {}
        print(f"File '{advanced_research_dict_path}' not found. New dict created.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        rc_advanced = {}
    except Exception as e:
        print(f"An error occurred: {e}")
        rc_advanced = {}

    # --- screenshot-ids mode ---
    if args.screenshot_ids:
        run_screenshot_ids(args, session, research_folder, screenshots_root, rc_dict, rc_dict_path)

    # --- lookup mode ---
    elif args.lookup:
        print(f"Looking for research in: {args.lookup}")
        page = session.get(args.lookup)
        soup = BeautifulSoup(page.content, 'html.parser')
        buttons = soup.find_all('a', class_='button consult-research')
        research = [button['href'] for button in buttons]
        print(f"Found {len(research)} expositions")

        for index, url in enumerate(research):
            print(f"Processing exposition {index + 1}/{len(research)}")
            expo = parse_expo(url, args.debug, args.download, args.shot, args.maps, args.force, session,
                              research_folder=research_folder, screenshots_root=screenshots_root)
            if expo:
                rc_dict[expo["id"]] = expo
                rc_advanced[expo["id"]] = expo["meta"]

                with open(rc_dict_path, 'w') as outfile:
                    json.dump(rc_dict, outfile, indent=2)
                with open(advanced_research_dict_path, 'w') as outfile:
                    json.dump(rc_advanced, outfile, indent=2)

    # --- internal research mode ---
    else:
        rcMisc.getInternalResearch(research_folder, args.resume)
        print("Using internal research")

        if args.resume:
            print("Resuming parsing.")
            adv_research = os.path.join(research_folder, "outdated_expositions.json")
        else:
            if args.force:
                print("Forcing re-parse of all expositions.")
                adv_research = os.path.join(research_folder, "internal_research.json")
            else:
                print("Skipping expositions that have already been parsed.")
                adv_research = os.path.join(research_folder, "outdated_expositions.json")

        with open(adv_research, "r") as file:
            research = json.load(file)

        print(f"Processing {len(research)} expositions.")
        for index, exposition in enumerate(research):
            print(f"Processing exposition {index + 1}/{len(research)}")
            url = exposition["default-page"]
            meta = {key: value for key, value in exposition.items()}
            expo = parse_expo(url, args.debug, args.download, args.shot, args.maps, args.force, session,
                              research_folder=research_folder, screenshots_root=screenshots_root, **meta)
            if expo:
                rc_dict[expo["id"]] = expo
                with open(rc_dict_path, 'w') as outfile:
                    json.dump(rc_dict, outfile, indent=2)