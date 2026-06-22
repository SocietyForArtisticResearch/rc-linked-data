# tools to parse RC tools in expositions
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
import re

# Media URL patterns
MEDIA_BASE_URL = "https://media.researchcatalogue.net"

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


def convert_media_url(url: str) -> str:
    """
    Convert RC media URLs from /resources/generate format to the actual cache format.
    
    Example:
        /resources/generate/35b87a4a3245bf226642e5ea25565179/199/159?_expiration=...&_hash=...
        becomes:
        https://media.researchcatalogue.net/rc/cache/35/b8/7a/4a/35b87a4a3245bf226642e5ea25565179_199x159.png?_expiration=...&_hash=...
    """
    if not url:
        return url
    
    # Check if it's already a full absolute URL
    if url.startswith("http://") or url.startswith("https://"):
        return url
    
    # Match the /resources/generate/ pattern
    pattern = r'/resources/generate/([a-f0-9]+)/(\d+)/(\d+)(\?.*)?'
    match = re.match(pattern, url)
    
    if match:
        hash_value = match.group(1)
        width = match.group(2)
        height = match.group(3)
        query_string = match.group(4) or ""
        
        # Split hash into subdirectory parts (2 chars each for first 3 parts, rest is full hash)
        hash_parts = [hash_value[i:i+2] for i in range(0, 8, 2)]  # First 8 chars = 4 parts of 2 chars
        cache_path = "/".join(hash_parts)
        
        # Construct the media cache URL
        converted_url = f"{MEDIA_BASE_URL}/rc/cache/{cache_path}/{hash_value}_{width}x{height}.png{query_string}"
        return converted_url
    
    # If it doesn't match the pattern, return as-is (might be a relative or absolute URL already)
    if url.startswith("/"):
        return f"https://www.researchcatalogue.net{url}"
    
    return url


# ------------------------------
# Generic helpers
# ------------------------------
def getId(tool):
    return tool.find("a")["id"]

def getStyle(tool):
    return tool["style"]

def getStyleAttributes(style: str):
    """Parses top, left, width, height from an inline style string."""
    result = {}
    for prop in style.split(";"):
        prop = prop.strip()
        if ":" not in prop:
            continue
        key, value = prop.split(":", 1)
        key = key.strip().lower()
        if key in ("top", "left", "width", "height"):
            value = value.strip().replace("px", "")
            try:
                result[key] = int(value)
            except ValueError:
                pass
    return [result.get(k, 0) for k in ("top", "left", "width", "height")]

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
def safe_get(func, tool, default=None):
    try:
        return func(tool)
    except Exception as e:
        print(f"{func.__name__} failed: {e}")
        return default


def getBaseAttributes(tool, extra=None):
    style = safe_get(getStyle, tool, "")

    base = {
        "id": safe_get(getId, tool),
        "style": style,
        "dimensions": safe_get(lambda t: getStyleAttributes(style), tool, {}),
        "content": safe_get(getContent, tool, ""),
        "tool": str(tool),
        "last-modified-by": safe_get(getAuthor, tool),
        "last-modified-at": safe_get(getDate, tool),
    }

    # Convert content to string if it exists
    if base["content"] is not None:
        base["content"] = str(base["content"])

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
    print(f"getToolAttributes called with: {tool}")
    content = getContent(tool)
    print(f"Extracted content: {content}")
    arttributes = getBaseAttributes(tool, {"src": removeStyle(str(content))})
    print(f"Extracted attributes: {arttributes}")
    return arttributes

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
        print(f"getTexts found {len(texts)} elements of type '{which}'")
        fn = TOOL_DISPATCH.get(which, getToolAttributes)
        print(f"Using function: {fn.__name__} for type '{which}'")
        attributes = list(map(fn, texts))
        print(f"Extracted attributes for {len(attributes)} elements of type '{which}'")
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
        #print(f"Processing row {row_index + 1}/{len(rows)}")
        try:
            tools = row.find_all(class_=which)
            #print(f"  Found {len(tools)} tools of type '{which}' in this row.")
            fn = TOOL_DISPATCH.get(which, getToolAttributes)
            #print(f"  Using function: {fn.__name__}")
            attributes = list(map(fn, tools))
            #print(f"  Extracted attributes for {len(attributes)} tools.")
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