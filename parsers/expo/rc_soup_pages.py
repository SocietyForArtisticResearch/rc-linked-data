#tools to parse hyperlinks in RC expositions and to locate subpages
from bs4 import BeautifulSoup
import requests
import json

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
    html = page.find("html");
    return html['class']

def getExpositionId(fullUrl):
    return fullUrl.split("/")[4]

def getPageId(fullUrl):
    return fullUrl.split("/")[5]

def getPageNumber(url):
    page = url.split("/")[5].split("#")[0]
    return int(page)

def isRelative(href):
    parts = href.split("/")
    if parts[1] == 'view':
        return True
    else:
        return False

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
        else:
            print("Metapage: no <a> tag found.")
    else:
        print("Metapage: no <li> tag with class 'menu menu-meta' found.")
        
    return href

def findHrefsInPage(page):
    return page.find_all("a")

def notContainsHash(url):
    try:
        page = url.split("/")[5]
        if "#" not in page:
            return True
        else:
            return False
    except:
        return False

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
    try:
        expID = getExpositionId(expositionUrl)
        pageID = getExpositionId(url)
        if expID == pageID:
            return True
        else:
            return False
    except:
        return False
    
def getPages(expositionUrl, page):
    atags = findHrefsInPage(page) #find all links in page
    urls = list(map(getHref, atags))
    urls = list(set(urls))
    subpages = list(filter(lambda url: isSubPage(expositionUrl, url), urls)) #filter to get only exposition subpages
    subpages = list(filter(notAnchorAtOrigin, subpages)) #filter out urls with anchor at 0/0
    subpages = list(filter(notContainsHash, subpages)) #filter out urls with hash
    subpages.append(expositionUrl)
    subpages = list(set(subpages))
    return subpages

def getAllPages(expositionUrl, page): #now we don't make a difference anymore btw TOC and subpages
    try:
        pages = getPages(expositionUrl, page)
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