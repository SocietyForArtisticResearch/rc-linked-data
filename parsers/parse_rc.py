import sys
import json
import requests
import getpass
from common import rc_internal_research as rcMisc
from common.rc_session import rc_session
from parse_expo import main as parse_expo
    
def print_usage():
    usage = """
Usage: python script_name.py <debug> <download> <shot> [auth]
    
Arguments:
    <debug>     : Debug mode (1 for enabled, 0 for disabled).
    <download>  : Download assets (1 for enabled, 0 for disabled).
    <shot>      : Take screenshots (1 for enabled, 0 for disabled).
    [auth]      : Optional. If provided, prompts for authentication (email and password).

Examples:
    Without authentication:
        python script_name.py 1 1 0

    With authentication:
        python script_name.py 1 1 0 auth
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
    except ValueError:
        print("Error: debug, download, and shot must be integers (1 or 0).")
        print_usage()
        sys.exit(1)

    if len(sys.argv) > 4 and sys.argv[4] == "auth":
        user = input("Email: ")
        password = getpass.getpass("Password: ")
        session = rc_session({'username': user, 'password': password})
    else:
        session = requests.Session()
        print("Proceeding without authentication.")
    
    rcMisc.getInternalResearch("../research")
    
    with open("../research/internal_research.json", "r") as file:
        research = json.load(file)
    for exposition in research:
        url = exposition["default-page"]
        meta = {key: value for key, value in exposition.items()}
        parse_expo(url, debug, download, shot, session, **meta)