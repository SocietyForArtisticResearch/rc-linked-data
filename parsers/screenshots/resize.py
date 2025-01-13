# get all images in folder, remove alpha channel, rescale to 1920x1080, convert to jpg
from PIL import Image
from os import path, chdir, mkdir, listdir, makedirs, getcwd
from pathlib import Path

def scaleByWidth(img):
    basewidth = 1920
    wpercent = basewidth / float(img.size[0])
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Image.LANCZOS)
    return img, basewidth, hsize


def scaleByHeight(img):
    baseheight = 1080
    hpercent = baseheight / float(img.size[1])
    wsize = int((float(img.size[0]) * float(hpercent)))
    img = img.resize((wsize, baseheight), Image.LANCZOS)
    return img, wsize, baseheight


def resizeScreenshotSimple(file):
    # input is for example 0.png 1.png etc..
    # generates 1 resized  resized-0.jpg
    # generates 1 compressed compressed-0.jpg
    file_name = path.basename(file)
    folder_path = path.dirname(file)
    img = Image.open(file)
    img = img.convert("RGB")
    if img.size[0] < img.size[1]:
        img = scaleByHeight(img)
    else:
        img = scaleByWidth(img)
    #print("folder path", folder_path)
    img[0].save(folder_path + "/resized_" + path.splitext(file_name)[0] + ".jpg")
    img[0].save(
        (folder_path + "/compressed_" + path.splitext(file_name)[0] + ".jpg"),
        "JPEG",
        quality=75,
    )


def resizeScreenshot(pathh):
    directory = Path(pathh)
    i = 0
    pages = []

    for page in directory.iterdir():
        if page.is_dir():
            pages.append(page.name)

    chdir(pathh)

    for page in pages:
        makedirs(page, exist=True)
        makedirs("compressed", exist=True)
        images = []
        for file in listdir():
            if file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg"):
                images.append(file)

        for image in images:
            i = i + 1
            print(str(i) + "/" + str(len(images)))
            print(image)
            file = image
            file_name = path.basename(file)
            img = Image.open(file)
            img = img.convert("RGB")
            if img.size[0] < img.size[1]:
                img = scaleByHeight(img)
            else:
                img = scaleByWidth(img)
            img[0].save(
                "resized/"
                + path.splitext(file_name)[0]
                + "_"
                + str(img[1])
                # + "x"
                # + str(img[2])
                + ".jpg"
            )
            img[0].save(
                "compressed/" + path.splitext(file_name)[0] + "-compressed.jpg",
                "JPEG",
                quality=50,
            )

        chdir("..")
    chdir("..")
    chdir("..")
