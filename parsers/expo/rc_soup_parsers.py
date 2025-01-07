from rc_soup_pages import *
from rc_soup_tools import *

def parse_graphical(parsed, debug=0):
    tool_entries = {}
    for tool in ALLTOOLS:
        if tool in TEXTTOOLS:
            if (elements := getTexts(parsed, tool, debug)):
                tool_entries[tool] = elements
        else:
            if (elements := getTools(parsed, tool, debug)):
                tool_entries[tool] = elements
    
    return tool_entries

def parse_block(parsed, debug=0):
    tool_entries = {} 

    for tool in ALLTOOLS:
        if tool in TEXTTOOLS:
            if (elements := getTexts(parsed, tool, debug)):
                tool_entries[tool] = elements
        else:
            if (elements := getTools(parsed, tool, debug)):
                tool_entries[tool] = elements
    
    return tool_entries

def parse_iframe():
    # parse weave iframe
    return None

def parse_text():
    # parse weave text
    return None

def parse_html():
    # parse weave html
    return None
