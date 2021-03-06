GOOGLE_APPLICATION_CREDITIALS = './My First Project-cc40bf076871.json'

import io
import os
import argparse
from enum import Enum
from tkinter import *

# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types
#from google.cloud.vision_v1.types.Vertex
from PIL import Image, ImageDraw, ImageTk

WIDTH = 300

class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


def get_crop_hint(path, upper, lower):
    """Detect crop hints on a single image and return the first result."""
    #client = vision.ImageAnnotatorClient()

    #with io.open(path, 'rb') as image_file:
    #    content = image_file.read()

    #image = types.Image(content=content)

    #crop_hints_params = types.CropHintsParams(aspect_ratios=[1.77])
    #image_context = types.ImageContext(crop_hints_params=crop_hints_params)

    #response = client.crop_hints(image=image, image_context=image_context)
    #hints = response.crop_hints_annotation.crop_hints

    # Get bounds for the first crop hint using an aspect ratio of 1.77.
    #vertices = hints[0].bounding_poly.vertices
    Vertex = types.Vertex
    #print(Vertex.__dict__)
    # make a list of vertices
    bottomLeft = Vertex()
    bottomLeft.x = int(upper[0])
    bottomLeft.y = int(lower[1])
    bottomRight = Vertex()
    bottomRight.x = int(lower[0])
    bottomRight.y = int(lower[1])
    upperRight = Vertex()
    upperRight.x = int(lower[0])
    upperRight.y = int(upper[1])
    upperLeft = Vertex()
    upperLeft.x = int(upper[0])
    upperLeft.y = int(upper[1])
    vertices = [bottomLeft, bottomRight, upperRight, upperLeft]
    return vertices

def draw_hint(image_file, upper, lower):
    """Draw a border around the image using the hints in the vector list."""
    vects = get_crop_hint(image_file, upper, lower)

    im = Image.open(image_file)
    draw = ImageDraw.Draw(im)
    draw.polygon([
        vects[0].x, vects[0].y,
        vects[1].x, vects[1].y,
        vects[2].x, vects[2].y,
        vects[3].x, vects[3].y], None, 'red')
    im.save('output-hint.jpg', 'jpg')

def crop_to_hint(image_file, upper, lower):
    """Crop the image using the hints in the vector list."""
    #vects = get_crop_hint(image_file, upper, lower)

    im = Image.open(image_file)
    w, h = im.size
    im2 = im.crop([0, upper,
                  w-1, lower])
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
    y_coordinate_error = 10 # value subject to change
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
    y_coordinate_error = 25 # subject to change
    finalDict = {}
    # add all the phrases into the dict
    for y_coord in phrases:
        finalDict[y_coord] = [False, phrases[y_coord]]
    # add all the prices into the dict
    for price in prices:
        #y_coord = price[1]
        upperPriceY = price[1][1]
        lowerPriceY = price[1][2]
        lowestKey = -1
        min_sum_squared = 100000000 #an arbitrary large number
        #min(finalDict, key = lambda k: (upperDiff**2)+)
        for key in finalDict:
            intKey = float(key)
            
            upperDiff = upperPriceY - intKey
            lowerDiff = lowerPriceY - intKey
            sum_squared = (upperDiff)**2 + (lowerDiff)**2 # getting a measure for how 'horizontal' a price is with value
            if sum_squared < min_sum_squared: #and finalDict[key][0] == False:
                lowestKey = intKey
                min_sum_squared = sum_squared

        finalDict[str(lowestKey)].append(price[0])
        finalDict[str(lowestKey)][0] = True
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
                        num = str(num) + "." + word_text
                        average_y = get_average_y(word)
                        priceList.append((num, average_y))
                        count = -1
                    elif word_text == '.' and count == 1:
                        count = 0
                    else: # if normal text
                        average_y = get_average_y(word)
                        wordList.append((word_text, average_y[0]))
                        count = -1
                    prevWord = word_text
    phrasesDict = get_phrase_dict(wordList)
    finalDict = join_phrase_price(phrasesDict, priceList)
    print(phrasesDict)
    print("\n")
    print(priceList)
    print("\n")
    print(finalDict)
    print("\n")
    return (finalDict.values())

                    #for symbol in word.symbols:
                    #    print('\tSymbol: {} (confidence: {})'.format(
                    #        symbol.text, symbol.confidence))


def gui(path):
    window = Frame()
    window.pack(expand=YES,fill=BOTH)
    window.master.title('wobba wobba')

    img = Image.open(path)

    width, height = img.size
    ratio = (height/width)
    img = img.resize((WIDTH, int(ratio * WIDTH)), Image.ANTIALIAS)
    image = ImageTk.PhotoImage(img)

    panel = Label(window, image=image)
    #window.geometry("700x" + str(int(ratio * 700)))
    panel.pack(fill = "both", expand = "yes")

    text = StringVar()
    text.set('Choose upper bound')
    label = Label(window, textvariable = text)
    label.pack(side = "bottom")
    upper = None
    lower = None
    count = 2
    def onRelease(event):
        nonlocal count, upper, lower
        if count == 2:
            text.set('Choose lower bound')
            upper = event.y
            count -= 1
        elif count == 1:
            text.set('Close window')
            lower = event.y
    panel.bind("<ButtonRelease-1>", onRelease )
    window.mainloop()
    if upper is None or lower is None:
        raise Exception("didn't pick upper and lower bounds")
    upper = upper * width/WIDTH
    lower = lower * width/WIDTH
    return int(upper), int( lower)

if __name__ == '__main__':


    # open the image to show users
    #img = Image.open(args.detect_file)
    #img.show()

    # make users crop the photo
    #draw_hint(args.detect_file, upper, lower)
    good = False
    while (good == False):
        parser = argparse.ArgumentParser()
        parser.add_argument('detect_file', help='The image for text detection.')
        parser.add_argument('-out_file', help='Optional output file', default=0)
        args = parser.parse_args()
        parser = argparse.ArgumentParser()
        render_doc_text(args.detect_file, args.out_file)

    # get user values to prepare for crop
        upper, lower = gui(args.detect_file)
        crop_to_hint(args.detect_file, upper, lower)

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
            good = True
        elif (userDecision == 'n'):
            continue

    # text detection
    final_dict = read_text(correctImage)
    #distribute prices
    print(final_dict)
    count = 1
    person_dict = {}
    userInput = input("how many people?")
    tax = input("tax? (input in decimals. e.g. .09 for 9%)  ")
    tips = input("tips? (input in decimals. e.g. .15 for 15%)  ")
    while count <= int(userInput):
        person_dict[count] = []
        count += 1
    for key in final_dict:
        string = ""
        for word in key[1]:
            string += word
            string += " "   
        if(key[0] == False):
            use = input("Couldn't find price for: " + string + ". Input price here: ")
            use2 = input("Which person (1~" + userInput + ")")
            person_dict[int(use2)].append(use)
            continue
        print("Item: " + string + " Price: $" + str(key[2]))
        userIn = input("Which person (1~" + userInput + ")")
        userIn = userIn.lower()
        # while(userIn != '1' and userIn != '2'):
        #     userIn = input("Type '1' or '2'")
        person_dict[int(userIn)].append(key[2])
    print(person_dict) 
    for person in person_dict:
        price_total = 0
        for price in person_dict[person]:
            price_total += float(price)
        print("Person " + str(person) + ", pay $" + str(price_total * (1 + float(tax)) * (1 + float(tips))))

