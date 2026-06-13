import requests
from bs4 import BeautifulSoup

headers = {
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
}

login_url = "https://www.researchcatalogue.net/auth/login"

def rc_session(username, password):
    """
    Authenticate with Research Catalogue and return an authenticated session.
    
    Args:
        username: User email
        password: User password
        
    Returns:
        Authenticated requests.Session object or None if login failed
    """
    session = requests.Session()
    session.headers.update(headers)
    
    # First, fetch the login page to extract CSRF token
    try:
        login_page = session.get(login_url)
        login_page.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch login page: {e}")
        return None
    
    # Extract CSRF token from the login page
    soup = BeautifulSoup(login_page.text, 'html.parser')
    csrf_input = soup.find('input', {'name': '_csrf_token'})
    
    if not csrf_input:
        print("Could not find CSRF token")
        return None
    
    csrf_token = csrf_input.get('value')
    
    # Prepare login data
    login_data = {
        '_csrf_token': csrf_token,
        '_username': username,
        '_password': password,
        'submitbutton': 'login'
    }
    
    # Perform login
    try:
        response = session.post(login_url, data=login_data, headers=headers, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Login request failed: {e}")
        return None
    
    # Check if login was successful by looking for logout link or error indicators
    if 'logout' in response.text.lower() or response.status_code == 200:
        print("Login successful")
        return session
    else:
        print("Login failed")
        return None