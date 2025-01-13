# Exposition parsers

Tools to parse rc expositions, mainly tested for graphical and block pages. 

## Parse Single Exposition

*rc_soup_main* looks for:

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

And stores the result in a json file. Usage:

```
python rc_soup_main.py "https://www.researchcatalogue.net/profile/show-exposition?exposition=EXPOID"
```