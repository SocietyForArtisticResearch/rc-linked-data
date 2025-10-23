#!/usr/bin/env python3
"""
Script to find expositions containing mouse events in tool-text elements.

This script iterates through the research folder, examines each JSON exposition file,
and identifies expositions that contain mouse events (onclick, onmousedown, etc.)
in their tool-text elements.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set


def find_mouse_events_in_text(text: str) -> Set[str]:
    """
    Find mouse events in a given text string.
    
    Args:
        text (str): The text to search for mouse events
        
    Returns:
        Set[str]: Set of found mouse events
    """
    mouse_events = [
        'onclick', 'onmousedown', 'onmouseup', 'onmouseover', 'onmouseout',
        'onmousemove', 'onmouseenter', 'onmouseleave', 'ondblclick',
        'oncontextmenu', 'onwheel'
    ]
    
    found_events = set()
    text_lower = text.lower()
    
    for event in mouse_events:
        if event in text_lower:
            # Exclude false positives like "scrollbar-onmouseover" (CSS classes)
            if event == 'onmouseover' and 'scrollbar-onmouseover' in text_lower:
                continue
            found_events.add(event)
    
    return found_events


def process_exposition_file(file_path: Path) -> Dict:
    """
    Process a single exposition JSON file to find mouse events.
    
    Args:
        file_path (Path): Path to the JSON file
        
    Returns:
        Dict: Information about found mouse events or None if no events found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        exposition_id = data.get('id')
        exposition_url = data.get('url', '')
        pages = data.get('pages', {})
        
        found_events = {}
        total_mouse_events = set()
        
        # Iterate through each page
        for page_id, page_data in pages.items():
            tools = page_data.get('tools', {})
            tool_texts = tools.get('tool-text', [])
            
            page_events = {}
            
            # Check each tool-text element
            for tool in tool_texts:
                tool_id = tool.get('id', 'unknown')
                tool_content = tool.get('tool', '')
                
                if tool_content:
                    events = find_mouse_events_in_text(tool_content)
                    if events:
                        # Create direct link to the tool
                        tool_link = f"https://www.researchcatalogue.net/view/{exposition_id}/{page_id}#{tool_id}"
                        page_events[tool_id] = {
                            'events': list(events),
                            'tool_link': tool_link
                        }
                        total_mouse_events.update(events)
            
            if page_events:
                found_events[page_id] = page_events
        
        if found_events:
            return {
                'exposition_id': exposition_id,
                'exposition_url': exposition_url,
                'file_path': str(file_path),
                'mouse_events_found': list(total_mouse_events),
                'pages_with_events': found_events,
                'total_pages': len(pages),
                'pages_with_mouse_events': len(found_events)
            }
        
        return None
        
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def main():
    """Main function to process all exposition files in the research folder."""
    
    # Get the script directory and construct research folder path
    script_dir = Path(__file__).parent
    research_dir = script_dir.parent / 'research'
    
    if not research_dir.exists():
        print(f"Research directory not found: {research_dir}")
        return
    
    print(f"Scanning research directory: {research_dir}")
    
    expositions_with_events = {}
    total_processed = 0
    total_with_events = 0
    
    # Iterate through all subdirectories in research folder
    for exposition_dir in research_dir.iterdir():
        if exposition_dir.is_dir():
            # Look for JSON file with same name as directory
            json_file = exposition_dir / f"{exposition_dir.name}.json"
            
            if json_file.exists():
                print(f"Processing: {json_file}")
                total_processed += 1
                
                result = process_exposition_file(json_file)
                if result:
                    expositions_with_events[exposition_dir.name] = result
                    total_with_events += 1
                    print(f"  -> Found mouse events: {result['mouse_events_found']}")
                else:
                    print(f"  -> No mouse events found")
    
    # Save results to JSON file
    output_file = script_dir / 'mouse_events.json'
    
    summary = {
        'scan_date': '2025-10-23',
        'total_expositions_processed': total_processed,
        'expositions_with_mouse_events': total_with_events,
        'research_directory': str(research_dir),
        'expositions': expositions_with_events
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\nScan complete!")
    print(f"Total expositions processed: {total_processed}")
    print(f"Expositions with mouse events: {total_with_events}")
    print(f"Results saved to: {output_file}")
    
    # Print summary of found events
    if expositions_with_events:
        print("\nSummary of found mouse events:")
        all_events = set()
        for exp_data in expositions_with_events.values():
            all_events.update(exp_data['mouse_events_found'])
        
        for event in sorted(all_events):
            count = sum(1 for exp_data in expositions_with_events.values() 
                       if event in exp_data['mouse_events_found'])
            print(f"  {event}: found in {count} expositions")


if __name__ == "__main__":
    main()