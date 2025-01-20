from bs4 import BeautifulSoup
import sys
import json
import requests
import getpass
from common import rc_internal_research as rcMisc
from common.rc_session import rc_session
from parse_expo import main as parse_expo
    
def print_usage():
    usage = """
Usage: python3 parse_rc.py <debug> <download> <shot> <force> [auth] [lookup]
    
Arguments:
    <debug>     : Debug mode (1 for enabled, 0 for disabled).
    <download>  : Download assets (1 for enabled, 0 for disabled).
    <shot>      : Take screenshots (1 for enabled, 0 for disabled).
    <force>     : Always parse an exposition, even when it has been parsed before (1 for enabled, 0 for disabled).
    [auth]      : Optional. If provided, prompts for authentication (email and password).
    [lookup]    : Provide a url, will look for any exposition links in the content of the page and download only those

Examples:
    Without authentication:
        python script_name.py 1 1 0 0 

    With authentication:
        python script_name.py 1 1 0 0 auth
 
    With lookup:
       python script_name.py 1 1 0 0 auth lookup
"""
    print(usage)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Error: Missing required arguments.")
        print_usage()
        sys.exit(1)

    try:
        debug = int(sys.argv[1])
        download = int(sys.argv[2])
        shot = int(sys.argv[3])
        force = int(sys.argv[4])
    except ValueError:
        print("Error: debug, download, and shot must be integers (1 or 0).")
        print_usage()
        sys.exit(1)

    if len(sys.argv) > 5 and sys.argv[5] == "auth":
        user = input("Email: ")
        password = getpass.getpass("Password: ")
        session = rc_session({'username': user, 'password': password})
    else:
        session = requests.Session()
        print("Proceeding without authentication.")
        
    rc_dict_path = "../research/rc_dict.json"
    
    try:
        with open(rc_dict_path, "r") as file:
            rc_dict = json.load(file) 
            print("RC dict laoded.")
    except FileNotFoundError:
        rc_dict = {}
        print(f"File '{rc_dict_path}' not found. New dict created.")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        
    if len(sys.argv) > 6:
        page_url = sys.argv[6]
        print(f"Looking for research in: {page_url}")
        page = session.get(page_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        buttons = soup.find_all('a', class_='button consult-research')
        research = [button['href'] for button in buttons]
        print(f"Found {len(research)} expositions")
        for index, url in enumerate(research):
            print(f"Processing exposition {index + 1}/{len(research)}")
            expo = parse_expo(url, debug, download, shot, force, session)
            if expo:
                rc_dict[expo["id"]] = expo
                rc_json = json.dumps(rc_dict, indent=2)
                with open("../research/rc_dict.json", 'w') as outfile:
                    outfile.write(rc_json)
    else:
        rcMisc.getInternalResearch("../research")
        print(f"Using internal research")
        with open("../research/internal_research.json", "r") as file:
            research = json.load(file)
        for index, exposition in enumerate(research):
            print(f"Processing exposition {index + 1}/{len(research)}")
            url = exposition["default-page"]
            meta = {key: value for key, value in exposition.items()}
            expo = parse_expo(url, debug, download, shot, force, session, **meta)
            if expo:
                rc_dict[expo["id"]] = expo
                rc_json = json.dumps(rc_dict, indent=2)
                with open("../research/rc_dict.json", 'w') as outfile:
                    outfile.write(rc_json)