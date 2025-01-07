import json
import sys
from PIL import Image, ImageDraw
from rc_soup_pages import getPageId

def load_json(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        sys.exit(1)

def convert_list_to_dict(data):
    return {item["id"]: item for item in data}

TOOL_COLORS = {
    "tool-text": (255, 0, 0),
    "tool-simpletext": (0, 255, 0),
    "tool-picture": (0, 0, 255),
    "tool-audio": (255, 255, 0),
    "tool-video": (255, 0, 255),
    "tool-shape": (0, 255, 255),
    "tool-pdf": (255, 165, 0),
    "tool-slideshow": (128, 0, 128),
    "tool-embed": (0, 128, 128),
    "tool-iframe": (128, 128, 0)
}

def get_default_page(data_dict, expo_id):
    exposition = data_dict.get(expo_id)
    if exposition:
        return exposition.get("default-page")
    return None

def get_scaling_factor(tools, target_width, target_height):
    max_x = max_y = 0
    for tool in tools:
        x, y, width, height = tool["dimensions"]
        max_x = max(max_x, x + width)
        max_y = max(max_y, y + height)
    
    scale_x = target_width / max_x if max_x > 0 else 1
    scale_y = target_height / max_y if max_y > 0 else 1
    return min(scale_x, scale_y)

def generate_image(expo_id, exposition, output_image_file, target_width=800, target_height=600):
    internal_research = load_json("research/internal_research.json")
    internal_research_dict = convert_list_to_dict(internal_research)
    
    try:
        default_page_id = getPageId(get_default_page(internal_research_dict, expo_id))
    except Exception as e:
        print(f"Error getting default page ID: {e}")
        default_page_id = None
        
    if default_page_id is None:
        print(f"No default page found for exposition ID {expo_id}")
        return

    if "pages" not in exposition:
        print(f"No 'pages' key found in exposition data for ID {expo_id}")
        return

    if default_page_id not in exposition["pages"]:
        print(f"No page data found for default page ID {default_page_id} in exposition ID {expo_id}")
        return
    
    first_page = exposition["pages"][default_page_id]

    all_tools = []
    for key, value in first_page.items():
        if isinstance(value, list):
            all_tools.extend(value)
        else:
            print(f"Skipping non-tool entry {key}: {type(value)}")

    scaling_factor = get_scaling_factor(all_tools, target_width, target_height)

    img = Image.new('RGB', (target_width, target_height), color='white')
    draw = ImageDraw.Draw(img)

    for tool_type, tools in first_page.items():
        if tool_type in TOOL_COLORS and isinstance(tools, list):
            for tool in tools:
                x, y, width, height = tool["dimensions"]
                scaled_x = int(x * scaling_factor)
                scaled_y = int(y * scaling_factor)
                scaled_width = int(width * scaling_factor)
                scaled_height = int(height * scaling_factor)
                if scaled_width == 0: scaled_width = 1
                if scaled_height == 0: scaled_height = 1
                draw.rectangle([scaled_x, scaled_y, scaled_x + scaled_width, scaled_y + scaled_height], outline=TOOL_COLORS[tool_type], width=3)
                draw.text((scaled_x + 5, scaled_y + 5), tool_type, fill=(0, 0, 0))

    img.save(output_image_file)
    print(f"Image saved to {output_image_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python json2image.py <exposition_id>")
        sys.exit(1)
    
    try:
        expo_id = int(sys.argv[1])
    except ValueError:
        print("Exposition ID must be an integer.")
        sys.exit(1)
    
    input_json_file = f"research/{expo_id}.json"
    output_image_file = f"maps/{expo_id}.png"
    
    exposition = load_json(input_json_file)
    generate_image(expo_id, exposition, output_image_file)

if __name__ == "__main__":
    main()