# Meta-page parsers

Tools to parse rc exposition meta-pages. 

## License and Copyright

Extract copyright and licenses from simple-media list and save to json format. Usage:

```
python extract_copyrights.py "https://www.researchcatalogue.net/profile/show-exposition?exposition=EXPOID"
```

Will create a folder called "copyrights" and save output to EXPOID.json, in this format:

```
{
    "name": "Beautiful Picture"
    "copyright": "Tizio Caio"
    "license": "All rights reserved"
    "tool": "https://www.researchcatalogue.net/view/EXPOID/EXPOPAGE#tool-ID"
    "id": "tool-ID"
    "usages": "picture"
}
```

The tool "id" is unique and consistent with the one parsed by the expo parser, so that the entries can be combined. 