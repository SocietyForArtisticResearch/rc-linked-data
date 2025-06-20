# RC Parsers

Collection of tools to parse Research Catalogue content. It links data found in meta page and exposition weaves, converting expositions to json structures that contain licenses and copyrights for its media. 

## Parse Single Exposition

*parse_expo.py* parses a single exposition. It writes content to a json file and optionally downloads related media, maps and screenshots.

### Usage:
```
python3 parse_expo.py <url> <debug> <download> <shot> [auth]
    
Arguments:
    <url>       : Default page of the exposition to process.
    <debug>     : Debug mode (1 for enabled, 0 for disabled).
    <download>  : Download assets (1 for enabled, 0 for disabled).
    <shot>      : Take screenshots (1 for enabled, 0 for disabled).
    <force>     : Always parse an exposition, even when it has been parsed before (1 for enabled, 0 for disabled).
    [auth]      : Optional. If provided, prompts for authentication.
```
### Examples:
Without authentication:
```
python3 parse_expo.py "default-page" 0 1 0 0
```
With authentication:
```
python3 parse_expo.py "default-page" 0 1 0 0 auth
```
## Parse Multiple Expositions

*parse_rc.py* parses multiple expositions. It writes content to a json file and optionally downloads related media, maps and screenshots for each expositions. It also produces a json containing all parsed expositions.

### Usage:
```
python3 parse_rc.py <debug> <download> <shot> <map> <force> [auth] [lookup]
    
Arguments:
    <debug>     : Debug mode (1 for enabled, 0 for disabled).
    <download>  : Download assets (1 for enabled, 0 for disabled).
    <shot>      : Take screenshots (1 for enabled, 0 for disabled).
    <map>       : Generates a map of the tool positions for each page (1 for enabled, 0 for disabled)
    <force>     : Always parse an exposition, even when it has been parsed before (1 for enabled, 0 for disabled).
    [auth]      : Optional. If provided, prompts for authentication (email and password).
    [lookup]    : Provide a url, will look for any exposition links in the content of the page and download only those
```
### Examples:
Without authentication:
```
python3 parse_rc.py 0 1 0 0 0
```
With authentication:
```
python3 parse_rc.py 0 1 0 0 0 auth
```
With lookup:
```
python3 parse_rc.py 0 1 0 0 0 auth "lookup_url"
```

# some bug

```python 
raise InvalidSchema(f"No connection adapters were found for {url!r}")
requests.exceptions.InvalidSchema: No connection adapters were found for '"https://www.researchcatalogue.net/view/428159/428160/909/85'

Traceback (most recent call last):
  File "/home/casper/devel/rc-linked-data/parsers/parse_rc.py", line 130, in <module>
    expo = parse_expo(url, debug, download, shot, maps, force, session, **meta)
  File "/home/casper/devel/rc-linked-data/parsers/parse_expo.py", line 169, in main
    exp_dict["pages"] = insert_copyrights(copyrights, exp_dict["pages"], session, media_folder, download)
                        ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/casper/devel/rc-linked-data/parsers/media/rc_merge_data.py", line 6, in insert_copyrights
    for page_id, page_data in exposition.items():
                              ^^^^^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'items'
Process 2681377 dead!
Process 2681377 detected```
