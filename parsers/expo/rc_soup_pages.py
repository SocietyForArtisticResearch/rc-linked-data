#tools to parse hyperlinks in RC expositions and to locate subpages
from bs4 import BeautifulSoup
import requests
import json
import re
from urllib.parse import urlparse, unquote, urljoin
from urllib.parse import unquote

RCURL = 'https://www.researchcatalogue.net'
JSONURL = "https://map.rcdata.org/internal_research.json"

def getInternalResearch():
    response = requests.get(JSONURL)
    data = response.json()
    output_file = "research/internal_research.json"
    with open(output_file, "w") as json_file:
        json.dump(data, json_file, indent=4) 
    
    print("internal research saved to " + output_file)

def getPageType(page):
    try:
        html = page.find("html")
        type = html['class']
    except:
        type = "undefined"
    return type

def getExpositionId(fullUrl):
    return fullUrl.split("/")[4]

def resolveDefaultPageUrl(expoId, session):
    """RC serves the bare /view/{id} URL without redirecting to the default
    weave page. Fetch it and pull the default page id out of the page's own
    links, so callers that only have an exposition id can still build a
    proper /view/{id}/{page} url."""
    bare_url = f"{RCURL}/view/{expoId}"
    response = session.get(bare_url)
    match = re.search(rf'/view/{expoId}/(\d+)', response.text)
    if not match:
        raise ValueError(f"Could not resolve default page for exposition {expoId} at {bare_url}.")
    return f"{RCURL}/view/{expoId}/{match.group(1)}"

def getPageId(fullUrl):
    return fullUrl.split("/")[5]

def getPageNumber(url):
    print(url)
    page = url.split("/")[5].split("#")[0]
    page_number = ''.join(filter(str.isdigit, page))
    if not page_number:
        raise ValueError(f"Invalid page number: {page}")
    
    return int(page_number)

def isRelative(href):
    # Check if URL is relative (starts with /)
    return href.startswith('/')

def getHref(atag):
    try:
        href = atag['href']
        if isRelative(href):
            href = RCURL + href
    except:
        return "no href"
    return href

def getURL(atag):
    href = atag['href']
    if isRelative(href):
        href = RCURL + href
    return href

def findMetaLink(parsed):
    li_tag = parsed.find('li', class_='menu menu-meta')

    if li_tag:
        a_tag = li_tag.find('a')  # Find <a> tag inside the <li>
        if a_tag:
            href = a_tag.get('href')
            # Convert relative URLs to absolute
            if isRelative(href):
                href = RCURL + href
        else:
            print("Metapage: no <a> tag found.")
            href = None
    else:
        print("Metapage: no <li> tag with class 'menu menu-meta' found.")
        href = None
        
    return href

def findHrefsInPage(page):
    return page.find_all("a")

def removeHash(url):
    try:
        no_hash = url.split('#')[0]
        return no_hash
    except:
        return url

def notAnchorAtOrigin(url):
    try:
        anchor = "0".join(url.split("/")[6:])
        if anchor == "000":
            return False
        else:
            return True
    except:
        return True
    
def isSubPage(expositionUrl, url):
    """Check if url is a subpage of expositionUrl by comparing exposition IDs"""
    try:
        import re
        
        # Extract exposition ID from pattern: https://www.researchcatalogue.net/view/ID/...
        def extract_exposition_id(full_url):
            match = re.search(r'/view/(\d+)', full_url)
            if match:
                return match.group(1)
            return None
        
        expID = extract_exposition_id(expositionUrl)
        pageID = extract_exposition_id(url)
        
        if expID and pageID and expID == pageID:
            return True
        else:
            return False
    except:
        return False
    
def getDataFollowLinks(page):
    pix = page.find_all('div', class_='tool-picture')
    links = list(map(lambda div: div.get('data-follow-link'), pix))
    # Convert relative URLs to absolute
    links = [RCURL + link if isRelative(link) else link for link in links if link]
    return links

whitelist = ["doi.org", "dx.doi.org"]

def is_broken_link(url):
    try:
        if url.startswith("/"):
            return False
        if any(domain in url for domain in whitelist):
            return False
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code >= 400
    except requests.RequestException:
        return True

def is_researchcatalogue_domain(url):
    """Check if URL belongs to researchcatalogue.net domain or its subdomains"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Handle cases where domain might be empty (relative URLs)
        if not domain:
            return False
            
        # Check if it's exactly researchcatalogue.net or a subdomain
        return domain == 'researchcatalogue.net' or domain.endswith('.researchcatalogue.net')
    except Exception:
        return False
    
def is_media_url(url):
    """Filter out RC media server URLs and local file:// links."""
    parsed = urlparse(url)

    # local file links
    if parsed.scheme == "file":
        return True

    # RC media server
    if parsed.netloc == "media.researchcatalogue.net":
        return True

    return False

def clean_url(href: str, base: str = RCURL) -> str:
    """Normalize and sanitize a URL so requests can handle it."""
    if not href:
        return ""
    href = unquote(href).strip().strip('\'"').rstrip('/')
    if href.lower() == "no href":
        return ""
    if href.startswith("//"):
        href = "https:" + href
    if not href.startswith(("http://", "https://")):
        href = urljoin(base, href)
    href = requests.utils.requote_uri(href)
    return href

def categorize_urls(clean_urls, base_prefix=None):
    same_expo = []
    other_expo = []
    references = []
    external = []

    for url in clean_urls:

        if is_media_url(url):
            continue  # skip PDFs, videos, local files, etc.

        elif "reference" in url:
            references.append(url)

        elif base_prefix and url.startswith(base_prefix):
            same_expo.append(url)

        elif (
            url.startswith("/profile/show-exposition?exposition=")  # relative URL
            or is_researchcatalogue_domain(url)                    # any RC domain
            or "10.22501" in url                                   # RC DOI scope
        ):
            other_expo.append(url)

        else:
            external.append(url)

    return {
        "same_exposition": same_expo,
        "other_expositions": other_expo,
        "references": references,
        "external": external,
    }

def getLinks(expositionUrl, page):
    container_div = page.find('div', id='container-weave')
    atags = findHrefsInPage(container_div)  # extract all <a> tags
    hrefs = [getHref(tag) for tag in atags]
    picture_links = getDataFollowLinks(container_div)  # links in pictures
    urls = hrefs + picture_links

    clean_urls = list(set(
        clean_url(url)
        for url in urls
        if url and url.strip() and url.lower().strip() != "no href"
    ))

    parsed = urlparse(expositionUrl)
    parts = parsed.path.strip("/").split("/")
    base_id = parts[1] if len(parts) >= 2 and parts[0] == "view" else None
    base_prefix = f"https://www.researchcatalogue.net/view/{base_id}/" if base_id else None

    return categorize_urls(clean_urls, base_prefix=base_prefix)
    
def getPages(expositionUrl, page):
    atags = findHrefsInPage(page) #find all links in page
    urls = list(map(getHref, atags))
    urls = list(set(urls))
    subpages = list(filter(lambda url: isSubPage(expositionUrl, url), urls)) #filter to get only exposition subpages
    subpages = list(filter(notAnchorAtOrigin, subpages)) #filter out urls with anchor at 0/0
    subpages = list(map(removeHash, subpages)) #filter out urls with hash
    subpages.append(expositionUrl)
    subpages = list(set(subpages))
    return subpages

def getAllPages(expositionUrl, page, meta_page_url, session): #now we don't make a difference anymore btw TOC and subpages
    try:
        pages = getPages(expositionUrl, page)
        meta = session.get(meta_page_url)
        meta_soup = BeautifulSoup(meta.content, 'html.parser')
        meta_pages = getPages(expositionUrl, meta_soup)
        pages = list(set(pages + meta_pages))
    except:
        return [expositionUrl]
    return pages

'''old

def notAuthor(atag):
    try:
        if atag['rel'] == ['author']:
            return False
        else:
            return True
    except: #no 'rel' found
        return True
    
def getTOC(page):
    try:
        nav = page.find("ul", class_="submenu menu-home")
        contents = nav.find_all("a")
        toc = list(filter(notAuthor, contents))
        toc = list(map(getURL, toc))
    except:
        print("| No nav found")
        return []
    return toc
'''