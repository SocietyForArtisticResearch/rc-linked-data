# input: dictionary of tools (per page). output: image file
import os
from PIL import Image, ImageDraw

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

def get_scaling_factor(tools, target_width, target_height):
    max_x = max_y = 0
    for tool in tools:
        x, y, width, height = tool["dimensions"]
        max_x = max(max_x, x + width)
        max_y = max(max_y, y + height)
    
    scale_x = target_width / max_x if max_x > 0 else 1
    scale_y = target_height / max_y if max_y > 0 else 1
    return min(scale_x, scale_y)

def generate_tools_map(output_file, target_width=800, target_height=600, **tools_dict):

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    all_tools = []
    for key, value in tools_dict.items():
        if isinstance(value, list):
            all_tools.extend(value)
        else:
            print(f"Skipping non-tool entry {key}: {type(value)}")

    scaling_factor = get_scaling_factor(all_tools, target_width, target_height)

    img = Image.new('RGB', (target_width, target_height), color='white')
    draw = ImageDraw.Draw(img)

    for tool_type, tools in tools_dict.items():
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

    img.save(output_file)
    print(f"Image saved to {output_file}")