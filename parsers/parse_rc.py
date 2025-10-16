from bs4 import BeautifulSoup
import sys
import json
import requests
import getpass
import os
from common import rc_internal_research as rcMisc
from common.rc_session import rc_session
from parse_expo import main as parse_expo


def print_usage():
    usage = """
Usage: python3 parse_rc.py <debug> <download> <shot> <maps> <force> <resume> [auth] [research_folder] [lookup]
    
Arguments:
    <debug>           : Debug mode (1 for enabled, 0 for disabled).
    <download>        : Download assets (1 for enabled, 0 for disabled).
    <shot>            : Take screenshots (1 for enabled, 0 for disabled).
    <maps>            : Generate visual maps (1 for enabled, 0 for disabled).
    <force>           : Always parse an exposition, even when it has been parsed before (1 for enabled, 0 for disabled).
    <resume>          : Update everything older than three days, even with force.
    [auth]            : Optional. If provided, prompts for authentication (email and password).
    [research_folder] : Optional. Path to research output folder (default: ../research/)
    [lookup]          : Optional. Provide a url, will look for exposition links in that page and download only those.

Examples:
    Without authentication:
        python3 parse_rc.py 1 1 0 0 0 0 ./my_research

    With authentication:
        python3 parse_rc.py 1 1 0 0 0 0 auth ./secure_research

    With lookup:
        python3 parse_rc.py 1 1 0 0 0 0 auth ./secure_research lookup
"""
    print(usage)


if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Error: Missing required arguments.")
        print_usage()
        sys.exit(1)

    try:
        debug = int(sys.argv[1])
        download = int(sys.argv[2])
        shot = int(sys.argv[3])
        maps = int(sys.argv[4])
        force = int(sys.argv[5])
        resume = int(sys.argv[6])
    except ValueError:
        print("Error: debug, download, shot, maps, force, and resume must be integers (1 or 0).")
        print_usage()
        sys.exit(1)

    # --- authentication & research folder handling ---
    research_folder = "../research/"  # default
    session = None

    if len(sys.argv) > 7 and sys.argv[7] == "auth":
        user = input("Email: ")
        password = getpass.getpass("Password: ")
        session = rc_session({'username': user, 'password': password})
        if len(sys.argv) > 8:
            research_folder = sys.argv[8]
            lookup_arg_index = 9
        else:
            lookup_arg_index = 8
    else:
        session = requests.Session()
        print("Proceeding without authentication.")
        if len(sys.argv) > 7:
            research_folder = sys.argv[7]
            lookup_arg_index = 8
        else:
            lookup_arg_index = 7

    # normalize and create research folder if missing
    research_folder = os.path.abspath(research_folder)
    os.makedirs(research_folder, exist_ok=True)

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

    # --- lookup mode ---
    if len(sys.argv) > lookup_arg_index:
        page_url = sys.argv[lookup_arg_index]
        print(f"Looking for research in: {page_url}")
        page = session.get(page_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        buttons = soup.find_all('a', class_='button consult-research')
        research = [button['href'] for button in buttons]
        print(f"Found {len(research)} expositions")

        for index, url in enumerate(research):
            print(f"Processing exposition {index + 1}/{len(research)}")
            expo = parse_expo(url, debug, download, shot, maps, force, session, research_folder=research_folder)
            if expo:
                rc_dict[expo["id"]] = expo
                rc_advanced[expo["id"]] = expo["meta"]

                with open(rc_dict_path, 'w') as outfile:
                    json.dump(rc_dict, outfile, indent=2)
                with open(advanced_research_dict_path, 'w') as outfile:
                    json.dump(rc_advanced, outfile, indent=2)

    # --- internal research mode ---
    else:
        rcMisc.getInternalResearch(research_folder, resume)
        print("Using internal research")

        if resume:
            print("Resuming parsing.")
            adv_research = os.path.join(research_folder, "outdated_expositions.json")
        else:
            if force:
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
            expo = parse_expo(url, debug, download, shot, maps, force, session,
                              research_folder=research_folder, **meta)
            if expo:
                rc_dict[expo["id"]] = expo
                with open(rc_dict_path, 'w') as outfile:
                    json.dump(rc_dict, outfile, indent=2)