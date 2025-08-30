# tools to parse RC tools in expositions
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional

# ------------------------------
# Tool categories
# ------------------------------
TOOLS = [
    "tool-picture",
    "tool-audio",
    "tool-video",
    "tool-shape",
    "tool-pdf",
    "tool-slideshow",
    "tool-embed",
    "tool-iframe",
]

TEXTTOOLS = ["tool-text", "tool-simpletext"]

ALLTOOLS = TEXTTOOLS + TOOLS


# ------------------------------
# Generic helpers
# ------------------------------
def getId(tool):
    return tool.find("a")["id"]

def getStyle(tool):
    return tool["style"]

def getStyleAttributes(style: str):
    """Parses inline style like 'top:10px; left:20px; width:30px; height:40px;'"""
    attributes = []
    attrs = style.split("px;")
    for x in range(4):
        attr = attrs[x].split(":")
        attributes.append(int(attr[1]))
    return attributes

def getContent(tool):
    return tool.find("div", {"class": "tool-content"})

def removeStyle(text: str):
    """Remove <script> and <style> tags, return plain text."""
    soup = BeautifulSoup(text, features="html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    return soup.get_text()

def getAuthor(tool) -> Optional[str]:
    return tool.get("data-last-modified-by")

def getDate(tool) -> Optional[int]:
    """Return POSIX timestamp from ISO-8601 string if available."""
    try:
        date = tool["data-last-modified-at"]
        dt = datetime.fromisoformat(date)
        return int(dt.timestamp())
    except Exception:
        return None

def cellPercentage(tool):
    parent = tool.find_parent("div")
    cell = str(parent.get("class")[1])
    if isinstance(cell, str) and "cell-" in cell:
        parts = cell.split("-")
        width = int(parts[-1])
        return f"{(width / 12) * 100}%"
    return None


# ------------------------------
# Source extractors
# ------------------------------
def getImageSrc(content):
    if (img := content.find("img", src=True)):
        return img["src"]

    if (other := content.find(attrs={"src": True})):
        return other["src"]

    # check for <object data="..."> (SVGs)
    if (obj := content.find("object", attrs={"data": True})):
        return obj["data"]

    return None

def getSlideshowSrc(content):
    return list({tag["src"] for tag in content.find_all(attrs={"src": True})})

def getVideoSrc(content):
    divs = content.find_all("div")
    if divs and "data-file" in divs[0].attrs:
        return divs[0]["data-file"]
    return None

def getVideoPoster(content):
    divs = content.find_all("div")
    return divs[0].get("data-image") if divs else None

def getPdfSrc(content):
    if (obj := content.find("object", attrs={"data": True})):
        return obj["data"]
    if (a := content.find("a", href=True)):
        return a["href"]
    return None


# ------------------------------
# Base + specific attributes
# ------------------------------
def getBaseAttributes(tool, extra=None):
    content = getContent(tool)
    base = {
        "id": getId(tool),
        "style": getStyle(tool),
        "dimensions": getStyleAttributes(getStyle(tool)),
        "content": str(content),
        "tool": str(tool),
        "last-modified-by": getAuthor(tool),
        "last-modified-at": getDate(tool),
    }
    if extra:
        base.update(extra)
    return base

def getPdfAttributes(tool):
    return getBaseAttributes(tool, {"src": getPdfSrc(getContent(tool))})

def getImageAttributes(tool):
    return getBaseAttributes(tool, {"src": getImageSrc(getContent(tool))})

def getSlideshowAttributes(tool):
    return getBaseAttributes(tool, {"src": getSlideshowSrc(getContent(tool))})

def getAudioAttributes(tool):
    return getBaseAttributes(tool, {"src": getVideoSrc(getContent(tool))})

def getVideoAttributes(tool):
    content = getContent(tool)
    return getBaseAttributes(tool, {
        "src": getVideoSrc(content),
        "poster": getVideoPoster(content),
    })

def getTextAttributes(tool):
    content = getContent(tool)
    return getBaseAttributes(tool, {"src": removeStyle(str(content))})

def getSimpleTextAttributes(tool):
    content = getContent(tool)
    return getBaseAttributes(tool, {"src": removeStyle(str(content))})

def getToolAttributes(tool):
    return getBaseAttributes(tool)


# ------------------------------
# Dispatcher for tools
# ------------------------------
TOOL_DISPATCH = {
    "tool-picture": getImageAttributes,
    "tool-slideshow": getSlideshowAttributes,
    "tool-pdf": getPdfAttributes,
    "tool-audio": getAudioAttributes,
    "tool-video": getVideoAttributes,
    "tool-text": getTextAttributes,
    "tool-simpletext": getSimpleTextAttributes,
}


# ------------------------------
# Main entrypoints
# ------------------------------
def getTexts(driver, which, debug=False):
    try:
        texts = driver.find_all(class_=which)
        fn = TOOL_DISPATCH.get(which, getToolAttributes)
        attributes = list(map(fn, texts))
    except Exception:
        if debug: print(f"found 0 {which}")
        return []
    if debug: print(f"found {len(texts)} {which}")
    return attributes

def getTools(page, which, debug=False):
    try:
        tools = page.find_all(class_=which)
        fn = TOOL_DISPATCH.get(which, getToolAttributes)
        attributes = list(map(fn, tools))
    except Exception:
        if debug: print(f"found 0 {which}")
        return []
    if debug: print(f"found {len(tools)} {which}")
    return attributes

def process_tool_cells(attributes, tools, row_index):
    cells = list(map(cellPercentage, tools))
    attributes = [{**attr, "dimensions": cell} for attr, cell in zip(attributes, cells)]
    for attr in attributes:
        attr["row"] = row_index
    return attributes

def getBlockTools(page, which, debug=False):
    rows = page.find_all(class_="row")
    all_attributes = []

    for row_index, row in enumerate(rows):
        try:
            tools = row.find_all(class_=which)
            fn = TOOL_DISPATCH.get(which, getToolAttributes)
            attributes = list(map(fn, tools))
            attributes = process_tool_cells(attributes, tools, row_index)
            all_attributes.extend(attributes)
        except Exception as e:
            if debug:
                print(f"Error processing row {row_index}: {e}")
            continue

    if debug:
        print(f"Found {len(all_attributes)} {which}")

    return all_attributes

def getIframe(soup):
    """
    Finds the first iframe src attribute in a BeautifulSoup parsed HTML object.
    
    Args:
        soup: BeautifulSoup object containing parsed HTML
        
    Returns:
        str: The src attribute value of the first iframe, or None if no iframe found
    """
    iframe = soup.find('iframe')
    if iframe and iframe.get('src'):
        return iframe.get('src')
    return None