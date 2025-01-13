import mimetypes

def download_file(session, file_url, folder, name):
    
    try:
        response = session.get(file_url)

        if response.status_code == 200:
            # Guess extension from response headers
            content_type = response.headers.get('Content-Type')
            file_extension = mimetypes.guess_extension(content_type)
            
            if not file_extension and save_path is None:
                print("Unable to determine the file extension.")
                return False
            
            if save_path is None:
                # If no save path is provided, use the URL to extract the file name
                save_path = f'{folder}{name}{file_extension if file_extension else ".bin"}'
            
            with open(save_path, 'wb') as file:
                file.write(response.content)
            
            print(f"File downloaded successfully and saved as {save_path}")
            return True
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False