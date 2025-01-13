import requests

login_url = "https://www.researchcatalogue.net/session/login"

login = {
    'username': 'email',
    'password': 'password',
}

def rc_session():
    session = requests.Session()
    
    response = session.post(login_url, data=login)
    print(response.text)

    if response.text.strip():
        print("login failed")
        return None
    else:
        print("login successful")
        return session