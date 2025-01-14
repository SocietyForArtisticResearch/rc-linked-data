from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from .resize import *

# 5k mac size:
ultraHD_width = 5120
ultraHD_height = 2880

# Full HD
fullHD_width = 1920
fullHD_height = 1080

options = Options()
options.add_argument("--headless=new")
options.add_argument("--hide-scrollbars")
options.add_argument(f"window-size={fullHD_width},{fullHD_height}")

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
    except Exception as e:
        print(e)
        scale = 100
        size = "weave not found"
        screen = "weave not found"
    return {"scale": scale, "size": size, "screen": screen}

def saveScreenshotAndResize(driver, path):
    driver.save_screenshot(path)  # replaced by a function that does both.
    resizeScreenshotSimple(path)
    
def screenshotGraphical(url, path, num):
    driver = webdriver.Chrome(options=options)
    print(f"Trying screenshot of {url}")
    driver.get(url)
    source = driver.page_source
    try:
        scale = smartZoom(driver)
        scal = scale["scale"]
        screen = scale["screen"]
        zoom = str(scal) + "%"
        driver.set_window_size(screen["width"], screen["height"])
        driver.execute_script("document.body.style.zoom='" + zoom + "'")
        path = f"{path}/{num}.png"
        saveScreenshotAndResize(driver, path)
        print(f"Saved screenshot at {path}")
    except Exception as e:
        path = str(e)
        zoom =  source#debug
        print(f"screenshot failed for url: {url}. Error: {e}")
        
    driver.quit()
        
    return {
        "file": path,
        "weave_size": zoom
    }
    
def screenshotBlock(url, path, num):
    driver = webdriver.Chrome(options=options)
    print(f"Trying screenshot of {url}")
    driver.get(url)
    source = driver.page_source
    try:
        zoom = "150%"
        driver.execute_script("document.body.style.zoom='" + zoom + "'")
        path = f"{path}/{num}.png"
        saveScreenshotAndResize(driver, path)
        print(f"Saved screenshot at {path}")
    except Exception as e:
        path = str(e)
        zoom =  source#debug
        print(f"screenshot failed for url: {url}. Error: {e}")
        
    driver.quit()
        
    return {
        "file": path,
        "weave_size": zoom
    }
  
"""  
def takeFirstImage(url, path, i):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    img_tags = soup.find_all("img")
    urls = [img["src"] for img in img_tags]
    first_url = urls[0]
    print(path)
    with open(path, "wb") as f:
        response = requests.get(first_url)
        print("| ⬇ downloading")
        print("| " + first_url)
        # print("| " + response)
        f.write(response.content)

    return {
        "file": str(i) + ".png",
        "weave_size": 100,
    }
      
def screenshotText(driver, url, path, i):    
    try:
        takeFirstImage(url, path, i, False)
    except:
        try:
            print("no image found. default to screenshot")
            zoom = "200%"
            driver.implicitly_wait(30)  # seconds
            print("| zoom: " + zoom)
            driver.execute_script("document.body.style.zoom='" + zoom + "'")
            saveScreenshotAndResize(driver, path)
            print("| ⬇ downloading")
            print("------------------")
            driver.implicitly_wait(0)
        except Exception as e:
            title = "failed"
            print("| the error is", e)
            print("| download failed")
            print("------------------")
    return {
        "file": str(i) + ".png",
        "weave_size": zoom,  # this is inconsistent, but for back compatibility
    }
"""