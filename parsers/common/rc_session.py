import requests
from bs4 import BeautifulSoup

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
    
    # Prepare headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:151.0) Gecko/20100101 Firefox/151.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.researchcatalogue.net',
        'Referer': login_url,
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
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