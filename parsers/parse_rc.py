import sys
import pandas as pd
import requests
import getpass
from common import rc_internal_research as rcMisc
from common.rc_session import rc_session
from parse_expo import main as parse_expo

rcMisc.getInternalResearch("../research")
RES = pd.read_json("../research/internal_research.json")
URLS = RES["default-page"]

def parse_rc(urls, debug, donwload, shot, session):
    for url in urls:
        parse_expo(url, debug, donwload, shot, session)
    
if __name__ == "__main__":
    debug = int(sys.argv[1])
    download = int(sys.argv[2])
    shot = int(sys.argv[3])
    if len(sys.argv) > 4:
        user = input("Email: ")
        password = getpass.getpass("Password: ")
        session = rc_session({'username': user, 'password': password})
    else:
        session = requests.Session()
        print("Proceeding without authentication.")
    parse_rc(URLS, debug, download, shot, session)