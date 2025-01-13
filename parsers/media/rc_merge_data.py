import mimetypes

def insert_copyrights(copyrights, exposition, session, folder, download=True):
    for page_id, page_data in exposition.items():
        for tool_category, tools_list in page_data['tools'].items(): #might remove key text and simpletext, since they are not media
            for tool in tools_list:
                tool_id = tool['id']
                for media in copyrights:
                    if isinstance(media['id'], list) and tool_id in media['id']:
                        index = media['id'].index(tool_id) 
                        tool.update(media)
                        tool['id'] = tool_id 
                        tool['tool'] = media['tool'][index] 
                        if download:
                            try:
                                path = download_media(session, tool['src'], folder, tool_id)
                                tool["path"] = path
                            except Exception as e:
                                print(f"An error occurred while downloading media: {e}")  
    return exposition

def download_media(session, file_url, folder, name):
    try:
        response = session.get(file_url)

        if response.status_code == 200:
            # guess extension from response headers
            content_type = response.headers.get('Content-Type')
            file_extension = mimetypes.guess_extension(content_type)
            
           
            save_path = f'{folder}{name}{file_extension if file_extension else ".bin"}'
            
            with open(save_path, 'wb') as file:
                file.write(response.content)
            
            print(f"File downloaded successfully and saved as {save_path}")
            return save_path
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False