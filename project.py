GOOGLE_APPLICATION_CREDITIALS = './My First Project-cc40bf076871.json'

import io
import os
import argparse
from enum import Enum
import tkinter as tk
import matplotlib
matplotlib.use('Agg')

# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types
from PIL import Image, ImageDraw, ImageTk

class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


def get_crop_hint(path):
    """Detect crop hints on a single image and return the first result."""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    crop_hints_params = types.CropHintsParams(aspect_ratios=[1.77])
    image_context = types.ImageContext(crop_hints_params=crop_hints_params)

    response = client.crop_hints(image=image, image_context=image_context)
    hints = response.crop_hints_annotation.crop_hints

    # Get bounds for the first crop hint using an aspect ratio of 1.77.
    vertices = hints[0].bounding_poly.vertices

    return vertices

def draw_hint(image_file):
    """Draw a border around the image using the hints in the vector list."""
    vects = get_crop_hint(image_file)

    im = Image.open(image_file)
    draw = ImageDraw.Draw(im)
    draw.polygon([
        vects[0].x, vects[0].y,
        vects[1].x, vects[1].y,
        vects[2].x, vects[2].y,
        vects[3].x, vects[3].y], None, 'red')
    im.save('output-hint.jpg', 'JPEG')

def crop_to_hint(image_file):
    """Crop the image using the hints in the vector list."""
    vects = get_crop_hint(image_file)

    im = Image.open(image_file)
    im2 = im.crop([vects[0].x, vects[0].y,
                  vects[2].x - 1, vects[2].y - 1])
    im2.save('cropped.jpg', 'JPEG')

def draw_boxes(image, bounds, color):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.polygon([
            bound.vertices[0].x, bound.vertices[0].y,
            bound.vertices[1].x, bound.vertices[1].y,
            bound.vertices[2].x, bound.vertices[2].y,
            bound.vertices[3].x, bound.vertices[3].y], None, color)
    return image


def get_document_bounds(image_file, feature):
    """Returns document bounds given an image."""
    client = vision.ImageAnnotatorClient()

    bounds = []

    with io.open(image_file, 'rb') as image_file:
        content = image_file.read()

    image = types.Image(content=content)

    response = client.document_text_detection(image=image)
    document = response.full_text_annotation

    # Collect specified feature bounds by enumerating all document features
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        if (feature == FeatureType.SYMBOL):
                            bounds.append(symbol.bounding_box)

                    if (feature == FeatureType.WORD):
                        bounds.append(word.bounding_box)

                if (feature == FeatureType.PARA):
                    bounds.append(paragraph.bounding_box)

            if (feature == FeatureType.BLOCK):
                bounds.append(block.bounding_box)

        if (feature == FeatureType.PAGE):
            bounds.append(block.bounding_box)

    # The list `bounds` contains the coordinates of the bounding boxes.
    return bounds


def render_doc_text(filein, fileout):
    image = Image.open(filein)
    bounds = get_document_bounds(filein, FeatureType.PAGE)
    draw_boxes(image, bounds, 'blue')
    bounds = get_document_bounds(filein, FeatureType.PARA)
    draw_boxes(image, bounds, 'red')
    bounds = get_document_bounds(filein, FeatureType.WORD)
    draw_boxes(image, bounds, 'yellow')

    if fileout is not 0:
        image.save(fileout)
    else:
        image.show()

# get the average y-coordinate for a particular WORD
def get_average_y(word):
    vertices = word.bounding_box.vertices
    BL_y = vertices[0].y
    UL_y = vertices[3].y
    return [(BL_y + UL_y)/2, UL_y, BL_y]

# make wordList into a list of phrases that share 'same' y-avg
def get_phrase_dict(wordList):
    phrases = {}
    y_coordinate_error = 5 # value subject to change
    for word in wordList:
        wordplaced = False # to ensure that the word is placed in dict somewhere
        y_coord = word[1]
        upperY = y_coord + y_coordinate_error
        lowerY = y_coord - y_coordinate_error
        for key in phrases:
            intKey = int(float(key)) # convert the string key values of dict to int
            if intKey <= upperY and intKey >= lowerY:
                phrases[key].append(word[0])
                wordplaced = True
        if (wordplaced == False):
            phrases[str(word[1])] = [word[0]]
    return phrases

# join the phrases with their respective price
def join_phrase_price(phrases, prices):
    y_coordinate_error = 5 # subject to change
    finalDict = {}
    # add all the phrases into the dict
    for y_coord in phrases:
        finalDict[y_coord] = [False, phrases[y_coord]]
    # add all the prices into the dict
    for price in prices:
        #y_coord = price[1]
        upperPriceY = price[1][1]
        lowerPriceY = price[1][2]

        min_sum_squared = 100000000 #an arbitrary large number
        #min(finalDict, key = lambda k: (upperDiff**2)+)
        for key in finalDict:
            intKey = float(key)
            upperDiff = upperPriceY - intKey
            lowerDiff = lowerPriceY - intKey
            sum_squared = (upperDiff)**2 + (lowerDiff)**2 # getting a measure for how 'horizontal' a price is with value
            if sum_squared < min_sum_squared: #and finalDict[key][0] == False:
                finalDict[key].append(price[0])
                finalDict[key][0] = True
                min_sum_squared = sum_squared
    return finalDict

def read_text(image):
    from google.cloud import vision_v1p3beta1 as vision
    client = vision.ImageAnnotatorClient()

    with io.open(image, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)
    response = client.document_text_detection(image=image)

    priceList = [] # a list of all the values with their coordinates
    wordList = [] # a list of all the words
    count = -1
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            print('\nBlock confidence: {}\n'.format(block.confidence))

            for paragraph in block.paragraphs:
                print('Paragraph confidence: {}'.format(
                    paragraph.confidence))

                prevWord = None
                for word in paragraph.words:
                    print(word.bounding_box.vertices)
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])
                    print('Word text: {} (confidence: {})'.format(
                        word_text, word.confidence))

                    # put the words in the right list
                    if word_text.isdigit() and prevWord != ".":
                        num = int(word_text)
                        count = 1
                    elif word_text.isdigit() and prevWord == "." and count == 0:
                        num = num + int(word_text)/100
                        average_y = get_average_y(word)
                        priceList.append((num, average_y))
                    elif word_text == '.' and count ==1:
                        prevWord = '.'
                        count = 0
                        continue
                    else: # if normal text
                        average_y = get_average_y(word)
                        wordList.append((word_text, average_y[0]))
                    prevWord = word_text
                    count -= 1
    phrasesDict = get_phrase_dict(wordList)
    finalDict = join_phrase_price(phrasesDict, priceList)
    print(phrasesDict)
    print("\n")
    print(priceList)
    print("\n")
    print(finalDict)
    print("\n")
    print(finalDict.values())

                    #for symbol in word.symbols:
                    #    print('\tSymbol: {} (confidence: {})'.format(
                    #        symbol.text, symbol.confidence))


def gui(path):
    window = tk.Tk()
    window.title("Join")
    #window.geometry("700x700")
    window.configure(background = 'grey')

    img = Image.open(path)
    width, height = img.size
    ratio = (height/width)
    window.geometry("700x" + str(int(ratio * 700)))
    imgResized = img.resize((700, int(ratio * 700)), Image.ANTIALIAS)
    image = ImageTk.PhotoImage(imgResized)
    panel = tk.Label(window, image=image)
    panel.pack(side="right")

    window.mainloop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('detect_file', help='The image for text detection.')
    parser.add_argument('-out_file', help='Optional output file', default=0)
    args = parser.parse_args()
    parser = argparse.ArgumentParser()
    render_doc_text(args.detect_file, args.out_file)
    gui(args.detect_file)
    # open the image to show users
    img = Image.open(args.detect_file)
    img.show()

    # make users crop the photo
    input("Draw where to crop the image")
    draw_hint(args.detect_file)
    crop_to_hint(args.detect_file)

    render_doc_text("cropped.jpg", args.out_file)
    croppedImage = Image.open(args.out_file)
    croppedImage.show()
    # give users the option to say yes or no to the boardered image
    userDecision = input("Are these borders correct? (y/n)")
    userDecision = userDecision.lower()
    while (userDecision != 'y' and userDecision != 'n'):
        userDecision = input("Type 'y' or 'n'")
    if (userDecision == 'y'):
        correctImage = args.out_file
    elif (userDecision == 'n'):
        pass

    # text detection
    read_text(correctImage)
