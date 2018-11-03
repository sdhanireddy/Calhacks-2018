GOOGLE_APPLICATION_CREDITIALS = './My First Project-cc40bf076871.json'

import io
import os

# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types

# Instantiates a client
client = vision.ImageAnnotatorClient()