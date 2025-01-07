#tools to parse RC tools in expositions
from bs4 import BeautifulSoup

TOOLS = [
    "tool-picture",
    "tool-audio",
    "tool-video",
    "tool-shape",
    "tool-pdf",
    "tool-slideshow",
    "tool-embed",
    "tool-iframe"
    ]

TEXTTOOLS = [
    "tool-text",
    "tool-simpletext"
    ]

ALLTOOLS = TEXTTOOLS + TOOLS

def getId(tool):
    anchor = tool.find("a")
    tool_id = anchor["id"]
    return tool_id

def getStyleAttributes(style):
    attributes = []
    attrs = style.split("px;")
    for x in range(4):
        attr = attrs[x].split(":")
        attributes.append(int(attr[1]))
    return attributes

def getStyle(tool):
    style = tool['style']
    return style 

def getContent(tool):
    content = tool.find("div", {"class": "tool-content"})
    return content

def getImageSrc(tool_content):
    anchor = tool_content.find("img")
    if anchor and "src" in anchor.attrs:
        return anchor["src"]
    
    anchor = tool_content.find(attrs={"src": True})
    if anchor:
        return anchor["src"]

    return None

#this is also for audiosrc
def getVideoSrc(tool_content):
    divs = tool_content.find_all("div")
    
    if divs and "data-file" in divs[0].attrs:
        return divs[0]["data-file"]

    return None

def getVideoPoster(tool_content):
    divs = tool_content.find_all("div")
    return divs[0]["data-image"]

def getImageAttributes(tool):
    tool_id = getId(tool)
    tool_style = getStyle(tool)
    tool_dimensions = getStyleAttributes(tool_style)
    tool_content = getContent(tool)
    tool_src = getImageSrc(tool_content)
    tool_dict = {
        "id": tool_id,
        "style": tool_style,
        "dimensions": tool_dimensions,
        "content": str(tool_content),
        "src": tool_src,
        "tool": str(tool)
        }
    return tool_dict

def getAudioAttributes(tool):
    tool_id = getId(tool)
    tool_style = getStyle(tool)
    tool_dimensions = getStyleAttributes(tool_style)
    tool_content = getContent(tool)
    tool_src = getVideoSrc(tool_content)
    tool_dict = {
        "id": tool_id,
        "style": tool_style,
        "dimensions": tool_dimensions,
        "content": str(tool_content),
        "src": tool_src,
        "tool": str(tool)
        }
    return tool_dict

def getVideoAttributes(tool):
    tool_id = getId(tool)
    tool_style = getStyle(tool)
    tool_dimensions = getStyleAttributes(tool_style)
    tool_content = getContent(tool)
    tool_src = getVideoSrc(tool_content)
    tool_poster = getVideoPoster(tool_content)
    tool_dict = {
        "id": tool_id,
        "style": tool_style,
        "dimensions": tool_dimensions,
        "content": str(tool_content),
        "src": tool_src,
        "poster": tool_poster,
        "tool": str(tool)
        }
    return tool_dict

def getToolAttributes(tool):
    tool_id = getId(tool)
    tool_style = getStyle(tool)
    tool_dimensions = getStyleAttributes(tool_style)
    tool_content = getContent(tool)
    tool_dict = {
        "id": tool_id,
        "style": tool_style,
        "dimensions": tool_dimensions,
        "content": str(tool_content),
        "tool": str(tool)
        }
    return tool_dict

def getStyledText(tool):
    text = getContent(tool)
    text = text['innerHTML']
    return text

def removeStyle(text):
    soup = BeautifulSoup(text, features="html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    # break into lines and remove leading and trailing space on each
    #lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    #chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    #text = '\n'.join(chunk for chunk in chunks if chunk)
    return text

def getTextAttributes(tool):
    tool_id = getId(tool)
    tool_style = getStyle(tool)
    tool_dimensions = getStyleAttributes(tool_style)
    tool_content = getContent(tool)
    tool_source = removeStyle(str(tool_content))
    tool_dict = {
        "id": tool_id,
        "style": tool_style,
        "dimensions": tool_dimensions,
        "content": str(tool_content),
        "src": tool_source,
        "tool": str(tool)
        }
    return tool_dict

def getTexts(driver, which, debug):
    try:
        texts = driver.find_all(class_= which)
        attributes = list(map(getTextAttributes, texts))
    except:
        if debug: print("found 0 " + which)
        return []
    if debug: print("found " + str(len(texts)) + " " + which)
    return attributes

def getTools(page, which, debug):
    try:
        tools = page.find_all(class_= which)
        if which in ["tool-picture", "tool-pdf", "tool-slideshow"]:
            attributes = list(map(getImageAttributes, tools))
        elif which in ["tool-audio"]:
            attributes = list(map(getAudioAttributes, tools))
        elif which in ["tool-video"]:
            attributes = list(map(getVideoAttributes, tools))
        else:
            attributes = list(map(getToolAttributes, tools))
    except:
        if debug: print("found 0 " + which)
        return []
    if debug: print("found " + str(len(tools)) + " " + which)
    return attributes