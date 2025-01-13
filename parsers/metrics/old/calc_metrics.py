import json
import numpy as np
import sys
import os

def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

# Extract rectangle properties
def extract_rectangles(page):
    rectangles = []
    for tools in page.values():
        if isinstance(tools, list):
            for tool in tools:
                x, y, width, height = tool["dimensions"]
                rectangles.append((x, y, width, height))
    return rectangles

# Calculate total area covered by rectangles
def calculate_total_area(rectangles):
    return sum(w * h for x, y, w, h in rectangles)

# Calculate the intersection area between two rectangles
def calculate_intersection(rect1, rect2):
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2
    
    # Calculate the intersection rectangle coordinates
    x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
    y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
    
    # Calculate overlap area
    return x_overlap * y_overlap

# Calculate the total overlap area between all rectangles
def calculate_total_overlap(rectangles):
    overlap_area = 0
    for i in range(len(rectangles)):
        for j in range(i + 1, len(rectangles)):
            overlap_area += calculate_intersection(rectangles[i], rectangles[j])
    return overlap_area

# Calculate overlap percentage
def calculate_overlap_percentage(rectangles):
    total_area = calculate_total_area(rectangles)
    if total_area == 0:
        return 0  # If no rectangles, no overlap
    overlap_area = calculate_total_overlap(rectangles)
    return (overlap_area / total_area) * 100

# Calculate white space percentage
def calculate_white_space(rectangles):
    if not rectangles:
        return 100.0  # If no rectangles, the white space is 100%

    max_x = max(x + w for x, y, w, h in rectangles)
    max_y = max(y + h for x, y, w, h in rectangles)
    effective_canvas_area = max_x * max_y
    
    if effective_canvas_area == 0:
        return 100.0  # Avoid division by zero if effective canvas area is zero

    total_rectangles_area = calculate_total_area(rectangles)
    white_space_area = effective_canvas_area - total_rectangles_area
    white_space_percentage = (white_space_area / effective_canvas_area) * 100
    return white_space_percentage

# Calculate alignment scores
def calculate_alignment_scores(rectangles):
    x_coords = [x for x, y, w, h in rectangles]
    y_coords = [y for x, y, w, h in rectangles]
    
    mean_x = np.mean(x_coords)
    mean_y = np.mean(y_coords)
    
    x_alignment_scores = [1 if abs(x - mean_x) < 1e-5 else 1 - min(abs(x - mean_x) / 1000, 1) for x in x_coords]
    y_alignment_scores = [1 if abs(y - mean_y) < 1e-5 else 1 - min(abs(y - mean_y) / 1000, 1) for y in y_coords]
    
    alignment_scores = [(xa + ya) / 2 for xa, ya in zip(x_alignment_scores, y_alignment_scores)]
    return np.mean(alignment_scores)

# Calculate spacing scores
def calculate_spacing_scores(rectangles):
    if len(rectangles) < 2:
        return 1.0  # Perfect score if there is only one rectangle
    
    x_coords = sorted(x for x, y, w, h in rectangles)
    y_coords = sorted(y for x, y, w, h in rectangles)
    
    x_spacings = [x_coords[i+1] - x_coords[i] for i in range(len(x_coords) - 1)]
    y_spacings = [y_coords[i+1] - y_coords[i] for i in range(len(y_coords) - 1)]
    
    mean_x_spacing = np.mean(x_spacings)
    mean_y_spacing = np.mean(y_spacings)
    
    x_spacing_scores = [1 if abs(s - mean_x_spacing) < 1e-5 else 1 - min(abs(s - mean_x_spacing) / 1000, 1) for s in x_spacings]
    y_spacing_scores = [1 if abs(s - mean_y_spacing) < 1e-5 else 1 - min(abs(s - mean_y_spacing) / 1000, 1) for s in y_spacings]
    
    spacing_scores = x_spacing_scores + y_spacing_scores
    return np.mean(spacing_scores)

# Calculate size uniformity scores
def calculate_size_uniformity_scores(rectangles):
    widths = [w for x, y, w, h in rectangles]
    heights = [h for x, y, w, h in rectangles]
    
    mean_width = np.mean(widths)
    mean_height = np.mean(heights)
    
    width_scores = [1 if abs(w - mean_width) < 1e-5 else 1 - min(abs(w - mean_width) / 1000, 1) for w in widths]
    height_scores = [1 if abs(h - mean_height) < 1e-5 else 1 - min(abs(h - mean_height) / 1000, 1) for h in heights]
    
    size_scores = width_scores + height_scores
    return np.mean(size_scores)

# Calculate horizontal/vertical ratio
def calculate_horizontal_vertical_ratio(rectangles):
    # Find the leftmost, rightmost, topmost, and bottommost rectangles
    leftmost_x = min(x for x, y, w, h in rectangles)
    rightmost_x = max(x + w for x, y, w, h in rectangles)
    topmost_y = min(y for x, y, w, h in rectangles)
    bottommost_y = max(y + h for x, y, w, h in rectangles)
    
    # Calculate effective width and height
    effective_width = rightmost_x - leftmost_x
    effective_height = bottommost_y - topmost_y
    
    # Calculate the ratio (width / height)
    if effective_height == 0:
        return float('inf')  # Avoid division by zero if height is zero
    
    return effective_width / effective_height

# Main function
def main():
    if len(sys.argv) != 2:
        print("Usage: python3 calc_metrics.py ID")
        sys.exit(1)

    id = sys.argv[1]
    input_json_file = f'research/{id}.json'

    if not os.path.exists(input_json_file):
        print(f"Warning: File '{input_json_file}' not found. Skipping calculation.")
        sys.exit(0)
    
    # Ensure the 'metrics' directory exists
    os.makedirs('metrics', exist_ok=True)
    
    output_json_file = f'metrics/{id}.json'
    
    # Check if the output file already exists
    if os.path.exists(output_json_file):
        print(f"Output file '{output_json_file}' already exists. Skipping calculation.")
        sys.exit(0)
    
    exposition = load_json(input_json_file)
    
    results = {}
    
    for page_id, page in exposition["pages"].items():
        # Process only if the page type is "weave-graphical"
        page_type = page.get("type")
        if page_type == "weave-graphical":
            rectangles = extract_rectangles(page)
            
            # Calculate the individual metrics
            alignment_score = calculate_alignment_scores(rectangles)
            spacing_score = calculate_spacing_scores(rectangles)
            size_uniformity_score = calculate_size_uniformity_scores(rectangles)
            overlap_percentage = calculate_overlap_percentage(rectangles)
            white_space_percentage = calculate_white_space(rectangles)
            horizontal_vertical_ratio = calculate_horizontal_vertical_ratio(rectangles)
            
            # Store the results for the current page
            results[page_id] = {
                "alignment_score": alignment_score,
                "spacing_score": spacing_score,
                "size_uniformity_score": size_uniformity_score,
                "overlap_percentage": overlap_percentage,
                "white_space_percentage": white_space_percentage,
                "horizontal_vertical_ratio": horizontal_vertical_ratio,
                "overall_regular_score": (alignment_score + spacing_score + size_uniformity_score) / 3
            }
        else:
            # Store the page type for non-weave-graphical pages
            results[page_id] = page_type
    
    # Save results to a JSON file
    with open(output_json_file, 'w') as f:
        json.dump(results, f, indent=4)
    
    print(f"Results saved to {output_json_file}")

if __name__ == "__main__":
    main()