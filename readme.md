# RC Linked Data

Collection of tools to fetch and link data from different parts of the Research Catalogue. 

# todo

* make posix based update of expo-data
* metrics

# done

[x] sort by weave type
[x] replace screenshots/toc.json with screenshots/index.json (see below)

# later

* have a merged json that also includes page type for each weave within an exposition.
* total word count (or character count, if easier) of the exposition

# parse only screenshots of expositions marked in the redo-ids.txt file
python3 parsers/parse_rc.py --screenshots-root /mnt/screenshots/screenshots --screenshot-ids PATH

# screenshots/index.json

When rc_parse.py is run with --shot, it creates screenshots, and within each exposition's
screenshots folder, an index.json (implemented in parsers/parse_expo.py, following the
ScreenshotsToc shape below). Only weaves whose screenshot actually succeeded (a .png file)
are listed. `default_page_type` is the type of the exposition's own default/entry page.
`page_title` comes from the exposition's own contents navigation and can be null if no
matching chapter-entry was found. Paths under `screenshots` are relative to the exposition's
screenshots folder, e.g. `2143139/1.png`.

Example:
```json
{
  "id": 998689,
  "default_page_type": "Graphical",
  "screenshots": [
    {
      "weave_id": 2143139,
      "page_title": "Eight to Infinite",
      "url": "https://www.researchcatalogue.net/view/998689/2143139",
      "screenshots": {
        "normal": "2143139/1.png",
        "compressed": "2143139/compressed_1.jpg",
        "resized": "2143139/resized_1.jpg"
      }
    }
  ]
}
```

This replaced the old toc.json, which used to look like this:
```json 

{"id": "998689", "type": "weave-graphical", "toc": [{"page": "2143139", "page_title": "Eight to Infinite", "url": "https://www.researchcatalogue.net/view/998689/2143139", "file": "0.png", "weave_size": "54%"}, {"page": "2023850", "page_title": "Main performance video", "url": "https://www.researchcatalogue.net/view/998689/2023850", "file": "1.png", "weave_size": "43%"}, {"page": "2023850", "page_title": "Music and Visual Scores", "url": "https://www.researchcatalogue.net/view/998689/2023850", "file": "2.png", "weave_size": "43%"}, {"page": "2143687", "page_title": "Question and Answer", "url": "https://www.researchcatalogue.net/view/998689/2143687", "file": "3.png", "weave_size": "93%"}, {"page": "2143505", "page_title": "Biographies", "url": "https://www.researchcatalogue.net/view/998689/2143505", "file": "4.png", "weave_size": "50%"}, {"page": "2225318", "page_title": "Music", "url": "https://www.researchcatalogue.net/view/998689/2225318", "file": "5.png", "weave_size": "86%"}]}
```

a folder with screenshots looks like this:
```bash
998689
│   ├── 2023850
│   │   ├── 1.png
│   │   ├── 2.png
│   │   ├── compressed_1.jpg
│   │   ├── compressed_2.jpg
│   │   ├── resized_1.jpg
│   │   └── resized_2.jpg
│   ├── 2143139
│   │   ├── 0.png
│   │   ├── compressed_0.jpg
│   │   └── resized_0.jpg
│   ├── 2143505
│   │   ├── 4.png
│   │   ├── compressed_4.jpg
│   │   └── resized_4.jpg
│   ├── 2143687
│   │   ├── 3.png
│   │   ├── compressed_3.jpg
│   │   └── resized_3.jpg
│   ├── 2225318
│   │   ├── 5.png
│   │   ├── compressed_5.jpg
│   │   └── resized_5.jpg
│   └── toc.json
```

```elm 
-- I am using elm types to express what information I want to get.

type alias AbsoluteUrl = 
    String -- these are absolute urls to RC pages
    -- for example https://www.researchcatalogue.net/view/4739597/4739598

type alias RelativeUrl =
    String -- these are just urls in the folder
    -- for example 2023850/1.png or 2023850/1-compressed.png

type PageType  
    = Graphical
    | Text
    | Block
    | Iframe
    | HTML

type alias Variants = 
    {
        normal : Url 
        compressed : Url
        resized : Url
    }

type alias = WeaveScreenshot 
    {
        weave_id : Int
        ,page_title : String
        ,url : Url -- this is a full RC url, can even have a fragment at the end.
        ,screenshots : Variants 

    }

type ScreenshotsToc = 
    { id : Int
    , default_page_type : PageType
    , screenshots : List WeaveScreenshot
    }