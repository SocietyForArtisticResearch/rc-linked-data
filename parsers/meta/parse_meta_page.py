from bs4 import BeautifulSoup
import requests
from datetime import datetime
import time
import re
from urllib.parse import urlparse, parse_qs

def parse_meta_page(url):
    print("Parsing meta page: " + url)
    meta = requests.get(url)
    meta_page = BeautifulSoup(meta.content, 'html5lib')
    
    meta_section = meta_page.find('div', class_='meta-right-col')
    title = meta_page.find("h2", {"class": "meta-headline"}).text.strip()
    temp = {"title": title}
    
    if meta_section:
        temp["abstract"] = meta_section.find('div', class_='meta-description').get_text(strip=True)
        table = meta_section.find('table', class_='meta-table')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                headers = row.find_all('th')
                data = row.find_all('td')
                key = headers[0].get_text(strip=True).lower()
                value = data[0].get_text(strip=True)
                temp[key] = value
    
    people = []
    for link in meta_page.find_all('a', href=True): 
        href = link['href']
        if href.startswith('/profile/?person='):
            person_id = re.search(r'person=(\d+)', href)
            if person_id:
                person_id = person_id.group(1)
                person_name = link.get_text(strip=True)
                
                people.append({
                    "id": int(person_id),
                    "name": person_name
                })
                
    if len(people) > 1:
        temp["author"] = people[0]
        temp["coauthors"] = people[1:]
    else:
        temp["author"] = people[0]
        temp["coauthors"] = []
            
    img_tag = meta_page.find('img')
    thumb = img_tag.get('src') if img_tag else None
    temp["thumb"] = thumb  
    temp["author"] = people[0]          

    data = {
        "id": int(parse_qs(urlparse(url).query).get('exposition', [None])[0]),  
        "type": temp["type"],
        "title": re.sub(r'\s*\(last edited:.*\)', '', temp["title"]),
        "thumb": temp["thumb"],
        "default-page": temp["url"],
        "meta-data-page": url,
        "created": temp["date"],
        "last-modified": int(time.mktime(datetime.strptime(temp["last modified"], "%d/%m/%Y").timetuple())),
        "status": temp["status"],
        "license": temp["license"].lower(),
        "author": temp["author"],
        "coauthors": temp["coauthors"],
        "abstract": temp["abstract"]
    }
    
    kw = temp.get("keywords", None)
    doi = temp.get("doi", None)
    pb = temp.get("published", None)
    pbin = temp.get("published in", None)
    
    if kw:
        data["keywords"] = temp["keywords"].split(',')
        
    if doi: 
        data["doi"] = {
            "id": re.search(r'https://doi.org/(.*)', temp["doi"]).group(1),
            "url": temp["doi"]
        }
    
    if pb: 
        data["published"] = temp["published"]
        
    if pbin:
        data["published_in"] = temp["published in"] #inconsistent
        
    #"connected_to": [], #inconsistent
    #"issue": None, #inconsistent
    
    return data