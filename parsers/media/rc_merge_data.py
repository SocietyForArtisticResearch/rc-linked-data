import mimetypes

def insert_copyrights(copyrights, exposition, session, folder, download=True):
    path_storage = {}
    
    for page_id, page_data in exposition.items():
        tools = page_data.get('tools')
        if tools:
            for tool_category, tools_list in page_data['tools'].items():
                for tool in tools_list:
                    tool_id = tool['id']
                    for media in copyrights:
                        if isinstance(media['id'], list) and tool_id in media['id']:
                            index = media['id'].index(tool_id) 
                            tool.update(media)
                            tool['id'] = tool_id 
                            tool['tool'] = media['tool'][index] 
                            if download:
                                if tool_category in ['tool-slideshow']:
                                    try:
                                        if isinstance(tool['src'], list):
                                            paths = []
                                            for index, src in enumerate(tool['src']):
                                                media_key = (tuple(media['id']) if isinstance(media['id'], list) else media['id'], index)
                                                if media_key not in path_storage:
                                                    unique_tool_id = f"{tool_id}_{index}"
                                                    path = download_media(session, src, folder, unique_tool_id)
                                                    path_storage[media_key] = path
                                                else:
                                                    path = path_storage[media_key]
                                                paths.append(path)
                                            tool["paths"] = paths
                                        else:
                                            media_key = tuple(media['id']) if isinstance(media['id'], list) else media['id']
                                            if index == 0:
                                                path = download_media(session, tool['src'], folder, tool_id)
                                                path_storage[media_key] = path
                                            else:
                                                path = path_storage.get(media_key)
                                            tool["path"] = path
                                    except Exception as e:
                                        print(f"An error occurred while downloading slideshow media: {e}")
                                elif tool_category in ['tool-picture', 'tool-audio', 'tool-video', 'tool-slideshow']:
                                    try:
                                        media_key = tuple(media['id']) 
                                        if index == 0:
                                            path = download_media(session, tool['src'], folder, tool_id)
                                            path_storage[media_key] = path 
                                        else:
                                            path = path_storage.get(media_key)
                                        tool["path"] = path
                                    except Exception as e:
                                        print(f"An error occurred while downloading media: {e}") 
                                else:
                                    print(f"{tool_id} not downloaded. Category: {tool_category}")
        else:
            print(f"No tools found for page {page_id}") 
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
        print(f"This media was not downloaded: {e}")
        return False