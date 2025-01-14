import requests

login_url = "https://www.researchcatalogue.net/session/login"

def rc_session(login):
    session = requests.Session()
    response = session.post(login_url, data=login)
    print(response.text)

    if response.text.strip():
        print("Login failed")
        return None
    else:
        print("Login successful")
        return session