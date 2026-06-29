import datetime

# THIS WILL NO LONGER WORK


# casper: 9/4/2025

root = "screenshots/"

research = pd.read_json("internal_research.json")
with open("internal_research.json", "r") as file:
    research_json = json.load(file)
# print(research.to_string())
res = research["default-page"]
# print(res)

# 5k mac size:
ultraHD_width = 5120
ultraHD_height = 2880

# Full HD
fullHD_width = 1920
fullHD_height = 1080

# the screenwidth
# virtual_screen_width = 5120
# virtual_screen_height = 2880

#res = ["https://www.researchcatalogue.net/view/3296693/3296692"]
# res = ["https://www.researchcatalogue.net/view/2297977/2297978"]
# res = ["https://www.researchcatalogue.net/view/106821/243746/2748/688"]  # timeline
# res = ["https://www.researchcatalogue.net/view/718740/718741"]
# res = ["https://www.researchcatalogue.net/view/1735361/1735362"] #this sometime times out
# res = ["https://www.researchcatalogue.net/view/106821/243746/2748/688"] #timeline

force = True

# res = ["https://www.researchcatalogue.net/view/2346286/2346287"]
# res = ["https://www.researchcatalogue.net/view/2346286/2346287"]
# res = ["https://www.researchcatalogue.net/view/2269674/2269673"] #pdf
# res = ["https://www.researchcatalogue.net/view/81827/81828"] # here hrefs in page are http and not https

options = Options()
options.add_argument("--headless=new")
options.add_argument("--hide-scrollbars")


#options.add_argument("--no-sandbox")

options.add_argument(f"window-size={fullHD_width},{fullHD_height}")


RESSIZE = len(res)
total = 0
failed = 0
counterTOC = 0
counterInferred = 0
counterSinglePage = 0
failedUrls = []
weaveFound = 0
weaveNotFound = 0

if not os.path.exists("toc.json"):
    tocs_dict = {}
else:
    with open("toc.json") as toc:
        tocs_dict = json.load(toc)


def getTitle(atag):
    return atag.get_attribute("innerHTML")


def getURL(atag):
    return atag.get_attribute("href")


def notAuthor(atag):
    if atag.get_attribute("rel") == "author":
        return False
    else:
        return True


def getExpositionUrl(fullUrl):
    parts = fullUrl.split("/")[:5]
    url = "/".join(parts)
    return url


def getDomainView(fullUrl):
    parts = fullUrl.split("/")[:4]
    url = "/".join(parts)
    return url


def getExpositionId(fullUrl):
    return fullUrl.split("/")[4]


def remove_query_part(url: str) -> str:
    """
    Remove everything after the '?' character in a given string.

    :param url: The input string potentially containing a '?' character.
    :return: The string with everything after the '?' character removed.
    """
    return url.split('?')[0]

def getPageNumber(fullUrl):
    withoutQ = remove_query_part(fullUrl)
    return withoutQ.split("/")[5].split("#")[0]


def notContainsHash(fullUrl):
    page = fullUrl.split("/")[5]
    if "#" not in page:
        return True
    else:
        return False


def notAnchorAtOrigin(fullUrl):
    try:
        anchor = "0".join(fullUrl.split("/")[6:])
        if anchor == "000":
            return False
        else:
            return True
    except:
        return True


def isSubPage(expositionUrl, url):
    try:
        expID = getExpositionId(expositionUrl)
        pageID = getExpositionId(url)
        if expID == pageID:
            return True
        else:
            return False
    except:
        return False


def isDomainView(url):
    try:
        base = getDomainView(url)
        if base == "https://www.researchcatalogue.net/view":
            return True
        else:
            return False
    except:
        return False


def smartScreenSize(weaveSize):
    width = weaveSize["width"]
    height = weaveSize["height"]
    try:
        if width > 3840:
            return {"width": ultraHD_width, "height": ultraHD_height}
        else:
            return {"width": fullHD_width, "height": fullHD_height}
    except TypeError:
        print("error parsing weave size")


def smartZoom(driver):
    try:
        weave = driver.find_element(By.ID, "weave")
        global weaveFound
        weaveFound = weaveFound + 1
        size = weave.size
        height = size["height"]
        width = size["width"]
        screen = smartScreenSize({"width": width, "height": height})
        screen_width = screen["width"]
        screen_height = screen["height"]
        if width < screen_width:
            scale = 100
        elif height < screen_height:
            scale = 100
        else:
            # scale = int(max(100 - ((width * height) / (1920 * 1440)), 25))
            raw_scaling = (
                min(
                    float(screen_width) / width,
                    float(screen_height) / height,
                )
                * 100.0
            )
            scale = max(min(100, int(raw_scaling)), 25)
            print("w, h, raw scaling, final scale", (width, height, raw_scaling, scale))
    except:
        global weaveNotFound
        weaveNotFound = weaveNotFound + 1
        print("| no weave found")
        scale = 100
        size = "weave not found"
    return {"scale": scale, "size": size, "screen": screen}


def takeFirstImage(url, path, i, title):
    page = getPageNumber(url)
    path = path + "/" + str(i) + ".png"
    print("| " + path)
    print(path)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img")
    urls = [img["src"] for img in img_tags]
    urll = urls[0]
    print(path)
    with open(path, "wb") as f:
        response = requests.get(urll)
        print("| ⬇ downloading")
        print("| " + urll)
        # print("| " + response)
        f.write(response.content)

    return {
        "page": page,
        "page_title": title,
        "url": url,
        "file": str(i) + ".png",
        "weave_size": 100,
    }


def remove_query_part(url):
    return url.split("?")[0]


def ensure_directories_exist(file_path: str) -> None:
    """
    Ensures that all directories in the given file path exist. If they do not exist, they are created.

    Args:
    file_path (str): The full file path including directories and file name.
    """
    # Extract the directory path from the file path
    directory = os.path.dirname(file_path)

    # Create the directories if they do not exist
    if directory:
        os.makedirs(directory, exist_ok=True)


def saveScreenshotAndResize(driver, path):
    driver.save_screenshot(path)  # replaced by a function that does both.
    #resizeScreenshotSimple(path)


def takeScreenshot(url, path, i, title):
    # path = path + "/" + str(i) + " " + title + ".png" #uncomment to name with title
    page = getPageNumber(url)
    path = path + "/" + str(i) + ".png"
    print("| " + path)
    ensure_directories_exist(path)
    try:
        cleanUrl = remove_query_part(url)
        driver.get(cleanUrl)
        expositionType = getExpositionType(driver)
        match expositionType:
            case "weave-graphical":
                print("| detected graphical weave")
                scale = smartZoom(driver)
                print("| scale is now: ", scale)
                scal = scale["scale"]
                screen = scale["screen"]
                zoom = str(scal) + "%"
                print("| zoom: " + zoom)
                driver.set_window_size(screen["width"], screen["height"])
                setWindowSize = driver.get_window_size()
                setW = setWindowSize["width"]
                setH = setWindowSize["height"]
                print(f"| current screen dimensions: {setW},{setH}")
                driver.execute_script("document.body.style.zoom='" + zoom + "'")
                saveScreenshotAndResize(
                    driver, path
                )  # driver.save_screenshot(path)  # replaced by a function that does both.
                print("| ⬇ downloading")
                print("------------------")
            case "weave-block":
                zoom = "150%"
                print("| zoom: " + zoom)
                driver.execute_script("document.body.style.zoom='" + zoom + "'")
                saveScreenshotAndResize(driver, path)
                print("| ⬇ downloading")
                print("------------------")
            case "weave-text":
                try:
                    takeFirstImage(cleanUrl, path, i, titles[i], False)
                except:
                    print("no image found. default to screenshot")
                    zoom = "200%"
                    print(
                        "Found type: "
                        + expositionType
                        + ". Waiting for PDF to load . . . "
                    )
                    driver.implicitly_wait(30)  # seconds
                    print("| zoom: " + zoom)
                    driver.execute_script("document.body.style.zoom='" + zoom + "'")
                    saveScreenshotAndResize(driver, path)
                    print("| ⬇ downloading")
                    print("------------------")
                    driver.implicitly_wait(0)
            case _:
                print("| could not decide weave type")
                scal = scale["scale"] * 2
                zoom = str(scal) + "%"
                print("| zoom: " + zoom)
                driver.execute_script("document.body.style.zoom='" + zoom + "'")
                saveScreenshotAndResize(driver, path)
                print("| ⬇ downloading")
                print("------------------")
    except Exception as e:
        i = 404
        title = "failed"
        print("| the error is", e)
        print("| download failed")
        print("------------------")
    # else:
    # print("| ✓ already available")
    # print("------------------")
    return {
        "page": page,
        "page_title": title,
        "url": cleanUrl,
        "file": str(i) + ".png",
        "weave_size": zoom,  # this is inconsistent, but for back compatibility
    }


def makeDir(num):
    path = root + num
    if not os.path.exists(path):
        print("creating directory " + path)
        os.makedirs(path)
    return path


def makeDirFromURL(url):
    num = getExpositionId(url)
    page = getPageNumber(url)
    path = root + num + "/" + page
    if not os.path.exists(path):
        print("making the directory")
        os.makedirs(path)
    return path


def countElements():
    # produce also copy single json for single exposition (TOC too)
    try:
        weave = driver.find_element(By.ID, "weave")
        print("weave size: " + str(weave.size))
    except:
        print("!!! weave not found !!!")

    try:
        contents = driver.find_element(By.XPATH, "/html/body/div[5]/ul/li[1]/ul")
        print("GRAPHICAL EXPOSITION")
    # except NoSuchElementException:
    # try:
    #   contents = driver.find_element(By.ID, "content")
    #  print("BLOCK EXPOSITION")
    # except:
    #   print("!!! contents not found !!!")
    except:
        print("!!! contents not found !!!")

    print("--------------------")
    # pages = contents.find_elements(By.TAG_NAME, "a")
    # print("weaves: " + str(len(pages)))
    pictures = driver.find_elements(By.CLASS_NAME, "tool-picture")
    print("pictures: " + str(len(pictures)))
    texts = driver.find_elements(By.CLASS_NAME, "tool-text")
    simpletexts = driver.find_elements(By.CLASS_NAME, "tool-simpletext")
    print("texts: " + str(len(texts) + len(simpletexts)))
    shapes = driver.find_elements(By.CLASS_NAME, "tool-shape")
    print("shapes: " + str(len(shapes)))
    videos = driver.find_elements(By.CLASS_NAME, "tool-video")
    print("videos: " + str(len(videos)))
    print("--------------------")


def findNav(driver):
    xpath = xpath
    try:
        nav = driver.find_element(By.XPATH, xpath)
        return nav
    except NoSuchElementException:
        print("| No nav found at xpath: " + xpath)


def getExpositionType(driver):
    html = driver.find_element(By.TAG_NAME, "html")
    return html.get_attribute("class")


def findHrefsInPage(driver):
    links = driver.find_elements(By.TAG_NAME, "a")
    return list(map(getURL, links))


def screenShotPages(fullUrl):
    cleanUrl = remove_query_part(fullUrl)
    num = getExpositionId(cleanUrl)
    path = root + num
    expositionType = getExpositionType(driver)
    try:
        toc = []
        print("makedir")
        path = makeDir(num)
        print("path:", path)
        xpath = "/html/body/div[5]/ul/li[1]/ul"
        xpathFonts = (
            "/html/body/div[6]/ul/li[1]/ul"  # this is the xpath when fonts not loaded
        )
        try:
            nav = driver.find_element(By.XPATH, xpath)  # nav > contents
            print("nav", nav)
        except:
            try:
                nav = driver.find_element(By.XPATH, xpathFonts)
            except:
                print("| " + cleanUrl)
                print("| No nav found at xpath")

        navList = nav.find_elements(By.TAG_NAME, "a")  # list of content elements
        filteredList = list(filter(notAuthor, navList))  # remove authors URLS
        titles = list(map(getTitle, filteredList))  # get contents titles
        contents = list(map(getURL, filteredList))  # get contents urls
        numEntries = len(contents)
        if (
            contents and numEntries != 1
        ):  # TOC exists. we cycle through TOC to get screenshots
            for i in range(numEntries):
                print("CONTENTS = ", contents)
                url = contents[i]
                cleanUrl = remove_query_part(url)
                path = makeDirFromURL(cleanUrl)
                print("| " + cleanUrl)
                # countElements()
                j = takeScreenshot(cleanUrl, path, i, titles[i])
                toc.append(j)
            global counterTOC
            counterTOC = counterTOC + 1
        else:  # TOC not available or TOC available but single entry
            print("no toc available, just taking default page")
            expositionUrl = getExpositionUrl(cleanUrl)
            hrefs = list(set(findHrefsInPage(driver)))  # find all links in page
            subpages = list(
                filter(lambda href: isSubPage(cleanUrl, href), hrefs)
            )  # filter to get only exposition subpages
            subpages = list(
                filter(notAnchorAtOrigin, subpages)
            )  # filter out urls with anchor at 0/0
            subpages = list(
                filter(notContainsHash, subpages)
            )  # filter out urls with hash
            print(subpages)
            
            path = makeDirFromURL(cleanUrl)
            if len(subpages) > 1:  # if subpages found takes screenshot
                for i in range(len(subpages)):
                    url = subpages[i]
                    cleanUrl = remove_query_part(url)
                    path = makeDirFromURL(cleanUrl)
                    print("| " + url)
                    # countElements()
                    j = takeScreenshot(cleanUrl, path, i, "no title")
                    toc.append(j)
                global counterInferred
                counterInferred = counterInferred + 1
            else:  # if no TOC and no subpages found take second screenshot
                print("no TOC or inferred subpages found")
                j = takeScreenshot(cleanUrl, path, 0, "default page")
                toc.append(j)
                global counterSinglePage
                counterSinglePage = counterSinglePage + 1
    except Exception as e:
        # Print the error message
        print(f"An error occurred: {e}")
        print("!!! screenshot failed for exposition: " + cleanUrl)
        global failed
        failed = failed + 1
        global failedUrls
        failedUrls.append(cleanUrl)
    toc_dict = {"id": num, "type": expositionType, "toc": toc}
    toc_json = json.dumps(toc_dict)
    local_toc_json_path = root + num + "/" + "toc.json"
    print("local toc json path: " + local_toc_json_path)
    ensure_directories_exist(local_toc_json_path)
    try:
        with open(local_toc_json_path, "w") as outfile:
            outfile.write(toc_json)
    except:
        print("sorry could not open directory")
    return toc_dict


def downloadExposition(exposition):
    print("GET")
    try:
        driver.get(exposition)
        driver.add_cookie({"name": "navigationtooltip", "value": "1"})
        # driver.implicitly_wait(180) # seconds

        toc_dict = screenShotPages(exposition)
        tocs_dict.update({toc_dict["id"]: toc_dict["toc"]})
    except:
        tocs_dict.update({getExpositionId(exposition): []})
        global failed
        failed = failed + 1
    tocs_json = json.dumps(tocs_dict)
    with open("toc.json", "w") as outfile:
        outfile.write(tocs_json)
    global total
    total = total + 1
    print("")
    #print(tocs_dict)
    print(str(total) + "/" + str(RESSIZE))
    print("TOC: " + str(counterTOC))
    print("Inferred: " + str(counterInferred))
    print("Single Page: " + str(counterSinglePage))
    print("Failed: " + str(failed))
    print(failedUrls)
    print("Found Weaves: " + str(weaveFound))
    print("No Weaves: " + str(weaveNotFound))
    print("")
    driver.quit()

def latest_modification_time(directory):
    """
    Returns the latest modification time of any file within the directory or its subdirectories.

    :param directory: Relative path to the directory (str or Path)
    :return: datetime of the most recent file modification, or None if no files are found
    """
    directory = Path(directory)
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"'{directory}' is not a valid directory")

    latest_time = None

    for file in directory.rglob("*.png"):
        if file.is_file():
            mtime = file.stat().st_mtime
            if latest_time is None or mtime > latest_time:
                latest_time = mtime

    return datetime.datetime.fromtimestamp(latest_time) if latest_time else None

outdated_expositions = []

for index, exposition in enumerate(research_json):
    print('exposition =',exposition)
    print('\n\n\n')
    url = exposition["default-page"]
    print('url = ',url)
    id = getExpositionId(url)

    folder_path = Path("screenshots/" + id)

    if folder_path.exists() and folder_path.is_dir():
        mod_time = latest_modification_time(folder_path)
        #mod_time = folder_path.stat().st_mtime
        last_modified = exposition["last-modified"]

        if mod_time is None:
            print(f"Folder '{id}' is outdated.")
            #outdated_expositions.append(exposition)
        else:
            tstamp = mod_time.timestamp()
            if float(tstamp) < float(last_modified):
                print(f"Folder '{id}' is outdated. timestamp = '{tstamp}', last_modified = '{last_modified}'")
                outdated_expositions.append(exposition)
            else:
                print(f"Folder '{id}' is up to date.")
    else:
        print(f"Folder '{id}' does not exist — treating as outdated.")
        outdated_expositions.append(exposition)

print(f"{len(outdated_expositions)} new or outfdated expositions found.")

if force:
    for exposition in outdated_expositions:
        print("outdated exposition")
        print(exposition)
        num = getExpositionId(exposition["default-page"])
        path = root + num
        driver = webdriver.Chrome(options=options)
        downloadExposition(exposition["default-page"])
        # resizeScreenshot(path)
else:
    for exposition in outdated_expositions:
        print("")
        print(exposition)
        num = getExpositionId(exposition["default-page"])
        path = root + num
        if not os.path.exists(path):
            driver = webdriver.Chrome(options=options)
            downloadExposition(exposition["default-page"])
            # resizeScreenshot(path)
        else:
            print("folder " + str(num) + " already exists.")
            total = total + 1
            print(str(total) + "/" + str(RESSIZE))
            print("")
