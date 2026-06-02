from bs4 import BeautifulSoup
import json
import os
import sys
from urllib.parse import urlparse, parse_qs

def extract_copyrights(url, session):
    print("Get copyrights: " + url)
    response = session.get(url)
    raw_html = response.text
    
    # use html5lib parser to correct table tags in simple-media
    soup = BeautifulSoup(raw_html, 'html5lib')
    # faster, but doesn't correct missing closing tags
    #soup = BeautifulSoup(raw_html, 'html.parser')

    # Extract exposition ID - the last integer in the URL
    import re
    url_numbers = re.findall(r'\d+', url)
    exposition_id = url_numbers[-1] if url_numbers else None
    if not exposition_id:
        print("No exposition ID found in the URL.")
        return

    print(f"Extracted exposition_id: {exposition_id}")

    # Find the "Copyrights" section and extract the simple-media entries
    simple_media_copyrights = []
    copyright_section = soup.find('div', class_='simple-media-copyright')
    if copyright_section:
        for media_div in copyright_section.find_all('div', recursive=False):
            media_data = {}
            table = media_div.find('table', class_='meta-table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    headers = row.find_all('th')
                    data = row.find_all('td')
                    key = headers[0].get_text(strip=True).lower()
                    value = data[0].get_text(strip=True)
                    media_data['tool'] = []
                    media_data['id'] = []
                    if 'usages' in key:
                        tool_links = data[0].find_all('a') 
                        for tool_link in tool_links:
                            tool_url = tool_link.get('href')
                            if tool_url:
                                media_data['tool'].append(tool_url)
                                media_data['id'].append(tool_url.split('#')[-1])
                    media_data[key] = value

                simple_media_copyrights.append(media_data)

    print(f"Extracted copyrights: {len(simple_media_copyrights)} items")
    print(json.dumps(simple_media_copyrights, indent=2))

    #with open(output_file_path, 'w') as json_file:
    #    json.dump(simple_media_copyrights, json_file, indent=4)

    #print(f"Data saved to {output_file_path}")
    return simple_media_copyrights

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_copyrights.py <URL>")
    else:
        extract_copyrights(sys.argv[1])