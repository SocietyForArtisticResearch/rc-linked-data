from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
from urllib.parse import urlparse, parse_qs

def parse_meta_page(url, session):
    print("Parsing meta page: " + url)
    meta = session.get(url)
    print(f"Response status: {meta.status_code}")
    print(f"Content length: {len(meta.content)} bytes")
    
    if meta.status_code != 200:
        print(f"ERROR: Received status code {meta.status_code}")
        return None
    
    if not meta.content:
        print("ERROR: Response content is empty")
        return None
    
    try:
        meta_page = BeautifulSoup(meta.content, 'html.parser')
        print("HTML parsed successfully with html.parser")
    except Exception as e:
        print(f"ERROR parsing HTML with html.parser: {e}")
        print(f"Attempting fallback with html5lib...")
        try:
            meta_page = BeautifulSoup(meta.content, 'html5lib')
            print("HTML parsed successfully with html5lib")
        except Exception as e2:
            print(f"ERROR: Failed to parse HTML with both parsers: {e2}")
            return None
    
    meta_section = meta_page.find('div', class_='meta-right-col')
    print(f"meta_section found: {meta_section is not None}")
    
    title_elem = meta_page.find("h2", {"class": "meta-headline"})
    print(f"title_elem found: {title_elem is not None}")
    if not title_elem:
        print("ERROR: Could not find title element")
        return None
    title = title_elem.text.strip()
    print(f"Title: {title}")
    
    temp = {"title": title}
    
    if meta_section:
        print("Extracting abstract and table data...")
        abstract_elem = meta_section.find('div', class_='meta-description')
        if abstract_elem:
            temp["abstract"] = abstract_elem.get_text(strip=True)
            print(f"Abstract found, length: {len(temp['abstract'])}")
        else:
            print("WARNING: abstract element not found")
            
        table = meta_section.find('table', class_='meta-table')
        print(f"table found: {table is not None}")
        if table:
            rows = table.find_all('tr')
            print(f"Found {len(rows)} table rows")
            for row in rows:
                headers = row.find_all('th')
                data = row.find_all('td')
                if headers and data:
                    key = headers[0].get_text(strip=True).lower()
                    value = data[0].get_text(strip=True)
                    temp[key] = value
                    print(f"  {key}: {value[:50]}...")
    else:
        print("WARNING: meta_section not found")
        
    people = []
    print("Extracting people...")
    all_links = meta_page.find_all('a', href=True)
    print(f"Found {len(all_links)} links total")
    for link in all_links: 
        href = link['href']
        person_id = None
        person_name = None
        
        # Check for new format: /researchers/ID
        if href.startswith('/researchers/'):
            match = re.search(r'/researchers/(\d+)', href)
            if match:
                person_id = match.group(1)
                person_name = link.get_text(strip=True)
        # Check for old format: /profile/?person=ID
        elif href.startswith('/profile/?person='):
            match = re.search(r'person=(\d+)', href)
            if match:
                person_id = match.group(1)
                person_name = link.get_text(strip=True)
        
        if person_id and person_name:
            print(f"  Found person: {person_name} (id: {person_id})")
            people.append({
                "id": int(person_id),
                "name": person_name
            })
    print(f"Total people found: {len(people)}")
                
    if len(people) > 1:
        temp["author"] = people[0]
        temp["coauthors"] = people[1:]
    elif len(people) == 1:
        temp["author"] = people[0]
        temp["coauthors"] = []
    else:
        print("WARNING: No people found")
        temp["author"] = None
        temp["coauthors"] = []
            
    img_tag = meta_page.find('div', class_='meta-media-preview')
    img_tag = img_tag.find('img') if img_tag else None
    print(f"img_tag found: {img_tag is not None}")
    thumb = img_tag.get('src') if img_tag else None
    temp["thumb"] = thumb
    print(f"Thumbnail: {thumb}")

    print("Building final data dict...")
    try:
        # Extract exposition ID - the last integer in the URL
        import re as regex
        url_numbers = regex.findall(r'\d+', url)
        exposition_id = int(url_numbers[-1]) if url_numbers else None
        print(f"Extracted exposition_id: {exposition_id}")
        
        data = {
            "id": exposition_id,  
            "type": temp.get("type"),
            "title": re.sub(r'\s*\(last edited:.*\)', '', temp.get("title", "")),
            "thumb": temp.get("thumb"),
            "default-page": temp.get("url"),
            "meta-data-page": url,
            "created": temp.get("date"),
            "last-modified": int(time.mktime(datetime.strptime(temp.get("last modified", "01/01/2000"), "%d/%m/%Y").timetuple())),
            "status": temp.get("status"),
            "license": temp.get("license", "").lower(),
            "author": temp.get("author"),
            "coauthors": temp.get("coauthors", []),
            "abstract": temp.get("abstract")
        }
        print("Final data dict created successfully")
    except Exception as e:
        print(f"ERROR building data dict: {e}")
        print(f"temp dict keys: {temp.keys()}")
        import traceback
        traceback.print_exc()
        return None
    
    kw = temp.get("keywords", None)
    doi = temp.get("doi", None)
    pb = temp.get("published", None)
    pbin = temp.get("published in", None)
    
    print(f"Optional fields - keywords: {kw is not None}, doi: {doi is not None}, published: {pb is not None}")
    
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
        
    print("parse_meta_page completed successfully")
    print("Final data dict:")
    print(data)
    return data