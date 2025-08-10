Migrate to the Google GenAI SDK

Starting with the Gemini 2.0 release in late 2024, we introduced a new set of libraries called the Google GenAI SDK. It offers an improved developer experience through an updated client architecture, and simplifies the transition between developer and enterprise workflows.

The Google GenAI SDK is now in General Availability (GA) across all supported platforms. If you're using one of our legacy libraries, we strongly recommend you to migrate.

This guide provides before-and-after examples of migrated code to help you get started.

Note: The Go examples omit imports and other boilerplate code to improve readability.
Installation
Before

Python
JavaScript
Go

pip install -U -q "google-generativeai"
After

Python
JavaScript
Go

pip install -U -q "google-genai"
API access
The old SDK implicitly handled the API client behind the scenes using a variety of ad hoc methods. This made it hard to manage the client and credentials. Now, you interact through a central Client object. This Client object acts as a single entry point for various API services (e.g., models, chats, files, tunings), promoting consistency and simplifying credential and configuration management across different API calls.

Before (Less Centralized API Access)

Python
JavaScript
Go
The old SDK didn't explicitly use a top-level client object for most API calls. You would directly instantiate and interact with GenerativeModel objects.


import google.generativeai as genai

# Directly create and use model objects
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(...)
chat = model.start_chat(...)
After (Centralized Client Object)

Python
JavaScript
Go

from google import genai

# Create a single client object
client = genai.Client()

# Access API methods through services on the client object
response = client.models.generate_content(...)
chat = client.chats.create(...)
my_file = client.files.upload(...)
tuning_job = client.tunings.tune(...)
Authentication
Both legacy and new libraries authenticate using API keys. You can create your API key in Google AI Studio.

Before

Python
JavaScript
Go
The old SDK handled the API client object implicitly.


import google.generativeai as genai

genai.configure(api_key=...)
After

Python
JavaScript
Go
With Google GenAI SDK, you create an API client first, which is used to call the API. The new SDK will pick up your API key from either one of the GEMINI_API_KEY or GOOGLE_API_KEY environment variables, if you don't pass one to the client.


export GEMINI_API_KEY="YOUR_API_KEY"

from google import genai

client = genai.Client() # Set the API key using the GEMINI_API_KEY env var.
                        # Alternatively, you could set the API key explicitly:
                        # client = genai.Client(api_key="your_api_key")
Generate content
Text
Before

Python
JavaScript
Go
Previously, there were no client objects, you accessed APIs directly through GenerativeModel objects.


import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    'Tell me a story in 300 words'
)
print(response.text)
After

Python
JavaScript
Go
The new Google GenAI SDK provides access to all the API methods through the Client object. Except for a few stateful special cases (chat and live-api sessions), these are all stateless functions. For utility and uniformity, objects returned are pydantic classes.


from google import genai
client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Tell me a story in 300 words.'
)
print(response.text)

print(response.model_dump_json(
    exclude_none=True, indent=4))
Image
Before

Python
JavaScript
Go

import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content([
    'Tell me a story based on this image',
    Image.open(image_path)
])
print(response.text)
After

Python
JavaScript
Go
Many of the same convenience features exist in the new SDK. For example, PIL.Image objects are automatically converted.


from google import genai
from PIL import Image

client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        'Tell me a story based on this image',
        Image.open(image_path)
    ]
)
print(response.text)
Streaming
Before

Python
JavaScript
Go

import google.generativeai as genai

response = model.generate_content(
    "Write a cute story about cats.",
    stream=True)
for chunk in response:
    print(chunk.text)
After

Python
JavaScript
Go

from google import genai

client = genai.Client()

for chunk in client.models.generate_content_stream(
  model='gemini-2.0-flash',
  contents='Tell me a story in 300 words.'
):
    print(chunk.text)
Configuration
Before

Python
JavaScript
Go

import google.generativeai as genai

model = genai.GenerativeModel(
  'gemini-1.5-flash',
    system_instruction='you are a story teller for kids under 5 years old',
    generation_config=genai.GenerationConfig(
      max_output_tokens=400,
      top_k=2,
      top_p=0.5,
      temperature=0.5,
      response_mime_type='application/json',
      stop_sequences=['\n'],
    )
)
response = model.generate_content('tell me a story in 100 words')
After

Python
JavaScript
Go
For all methods in the new SDK, the required arguments are provided as keyword arguments. All optional inputs are provided in the config argument. Config arguments can be specified as either Python dictionaries or Config classes in the google.genai.types namespace. For utility and uniformity, all definitions within the types module are pydantic classes.


from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
  model='gemini-2.0-flash',
  contents='Tell me a story in 100 words.',
  config=types.GenerateContentConfig(
      system_instruction='you are a story teller for kids under 5 years old',
      max_output_tokens= 400,
      top_k= 2,
      top_p= 0.5,
      temperature= 0.5,
      response_mime_type= 'application/json',
      stop_sequences= ['\n'],
      seed=42,
  ),
)
Safety settings
Generate a response with safety settings:

Before

Python
JavaScript

import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    'say something bad',
    safety_settings={
        'HATE': 'BLOCK_ONLY_HIGH',
        'HARASSMENT': 'BLOCK_ONLY_HIGH',
  }
)
After

Python
JavaScript

from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
  model='gemini-2.0-flash',
  contents='say something bad',
  config=types.GenerateContentConfig(
      safety_settings= [
          types.SafetySetting(
              category='HARM_CATEGORY_HATE_SPEECH',
              threshold='BLOCK_ONLY_HIGH'
          ),
      ]
  ),
)
Async
Before

Python

import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content_async(
    'tell me a story in 100 words'
)
After

Python
To use the new SDK with asyncio, there is a separate async implementation of every method under client.aio.


from google import genai

client = genai.Client()

response = await client.aio.models.generate_content(
    model='gemini-2.0-flash',
    contents='Tell me a story in 300 words.'
)
Chat
Start a chat and send a message to the model:

Before

Python
JavaScript
Go

import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
chat = model.start_chat()

response = chat.send_message(
    "Tell me a story in 100 words")
response = chat.send_message(
    "What happened after that?")
After

Python
JavaScript
Go

from google import genai

client = genai.Client()

chat = client.chats.create(model='gemini-2.0-flash')

response = chat.send_message(
    message='Tell me a story in 100 words')
response = chat.send_message(
    message='What happened after that?')
Function calling
Before

Python

import google.generativeai as genai
from enum import Enum

def get_current_weather(location: str) -> str:
    """Get the current whether in a given location.

    Args:
        location: required, The city and state, e.g. San Franciso, CA
        unit: celsius or fahrenheit
    """
    print(f'Called with: {location=}')
    return "23C"

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[get_current_weather]
)

response = model.generate_content("What is the weather in San Francisco?")
function_call = response.candidates[0].parts[0].function_call
After

Python
In the new SDK, automatic function calling is the default. Here, you disable it.


from google import genai
from google.genai import types

client = genai.Client()

def get_current_weather(location: str) -> str:
    """Get the current whether in a given location.

    Args:
        location: required, The city and state, e.g. San Franciso, CA
        unit: celsius or fahrenheit
    """
    print(f'Called with: {location=}')
    return "23C"

response = client.models.generate_content(
  model='gemini-2.0-flash',
  contents="What is the weather like in Boston?",
  config=types.GenerateContentConfig(
      tools=[get_current_weather],
      automatic_function_calling={'disable': True},
  ),
)

function_call = response.candidates[0].content.parts[0].function_call
Automatic function calling
Before

Python
The old SDK only supports automatic function calling in chat. In the new SDK this is the default behavior in generate_content.


import google.generativeai as genai

def get_current_weather(city: str) -> str:
    return "23C"

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[get_current_weather]
)

chat = model.start_chat(
    enable_automatic_function_calling=True)
result = chat.send_message("What is the weather in San Francisco?")
After

Python

from google import genai
from google.genai import types
client = genai.Client()

def get_current_weather(city: str) -> str:
    return "23C"

response = client.models.generate_content(
  model='gemini-2.0-flash',
  contents="What is the weather like in Boston?",
  config=types.GenerateContentConfig(
      tools=[get_current_weather]
  ),
)
Code execution
Code execution is a tool that allows the model to generate Python code, run it, and return the result.

Before

Python
JavaScript

import google.generativeai as genai

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools="code_execution"
)

result = model.generate_content(
  "What is the sum of the first 50 prime numbers? Generate and run code for "
  "the calculation, and make sure you get all 50.")
After

Python
JavaScript

from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the sum of the first 50 prime numbers? Generate and run '
            'code for the calculation, and make sure you get all 50.',
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)],
    ),
)
Search grounding
GoogleSearch (Gemini>=2.0) and GoogleSearchRetrieval (Gemini < 2.0) are tools that allow the model to retrieve public web data for grounding, powered by Google.

Before

Python

import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    contents="what is the Google stock price?",
    tools='google_search_retrieval'
)
After

Python

from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='What is the Google stock price?',
    config=types.GenerateContentConfig(
        tools=[
            types.Tool(
                google_search=types.GoogleSearch()
            )
        ]
    )
)
JSON response
Generate answers in JSON format.

Before

Python
JavaScript
By specifying a response_schema and setting response_mime_type="application/json" users can constrain the model to produce a JSON response following a given structure.


import google.generativeai as genai
import typing_extensions as typing

class CountryInfo(typing.TypedDict):
    name: str
    population: int
    capital: str
    continent: str
    major_cities: list[str]
    gdp: int
    official_language: str
    total_area_sq_mi: int

model = genai.GenerativeModel(model_name="gemini-1.5-flash")
result = model.generate_content(
    "Give me information of the United States",
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema = CountryInfo
    ),
)
After

Python
JavaScript
The new SDK uses pydantic classes to provide the schema (although you can pass a genai.types.Schema, or equivalent dict). When possible, the SDK will parse the returned JSON, and return the result in response.parsed. If you provided a pydantic class as the schema the SDK will convert that JSON to an instance of the class.


from google import genai
from pydantic import BaseModel

client = genai.Client()

class CountryInfo(BaseModel):
    name: str
    population: int
    capital: str
    continent: str
    major_cities: list[str]
    gdp: int
    official_language: str
    total_area_sq_mi: int

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='Give me information of the United States.',
    config={
        'response_mime_type': 'application/json',
        'response_schema': CountryInfo,
    },
)

response.parsed
Files
Upload
Upload a file:

Before

Python

import requests
import pathlib
import google.generativeai as genai

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

file = genai.upload_file(path='a11.txt')

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content([
    'Can you summarize this file:',
    my_file
])
print(response.text)
After

Python

import requests
import pathlib
from google import genai

client = genai.Client()

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

my_file = client.files.upload(file='a11.txt')

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents=[
        'Can you summarize this file:',
        my_file
    ]
)
print(response.text)
List and get
List uploaded files and get an uploaded file with a filename:

Before

Python

import google.generativeai as genai

for file in genai.list_files():
  print(file.name)

file = genai.get_file(name=file.name)
After

Python

from google import genai
client = genai.Client()

for file in client.files.list():
    print(file.name)

file = client.files.get(name=file.name)
Delete
Delete a file:

Before

Python

import pathlib
import google.generativeai as genai

pathlib.Path('dummy.txt').write_text(dummy)
dummy_file = genai.upload_file(path='dummy.txt')

file = genai.delete_file(name=dummy_file.name)
After

Python

import pathlib
from google import genai

client = genai.Client()

pathlib.Path('dummy.txt').write_text(dummy)
dummy_file = client.files.upload(file='dummy.txt')

response = client.files.delete(name=dummy_file.name)
Context caching
Context caching allows the user to pass the content to the model once, cache the input tokens, and then refer to the cached tokens in subsequent calls to lower the cost.

Before

Python
JavaScript

import requests
import pathlib
import google.generativeai as genai
from google.generativeai import caching

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

# Upload file
document = genai.upload_file(path="a11.txt")

# Create cache
apollo_cache = caching.CachedContent.create(
    model="gemini-1.5-flash-001",
    system_instruction="You are an expert at analyzing transcripts.",
    contents=[document],
)

# Generate response
apollo_model = genai.GenerativeModel.from_cached_content(
    cached_content=apollo_cache
)
response = apollo_model.generate_content("Find a lighthearted moment from this transcript")
After

Python
JavaScript

import requests
import pathlib
from google import genai
from google.genai import types

client = genai.Client()

# Check which models support caching.
for m in client.models.list():
  for action in m.supported_actions:
    if action == "createCachedContent":
      print(m.name)
      break

# Download file
response = requests.get(
    'https://storage.googleapis.com/generativeai-downloads/data/a11.txt')
pathlib.Path('a11.txt').write_text(response.text)

# Upload file
document = client.files.upload(file='a11.txt')

# Create cache
model='gemini-1.5-flash-001'
apollo_cache = client.caches.create(
      model=model,
      config={
          'contents': [document],
          'system_instruction': 'You are an expert at analyzing transcripts.',
      },
  )

# Generate response
response = client.models.generate_content(
    model=model,
    contents='Find a lighthearted moment from this transcript',
    config=types.GenerateContentConfig(
        cached_content=apollo_cache.name,
    )
)
Count tokens
Count the number of tokens in a request.

Before

Python
JavaScript

import google.generativeai as genai

model = genai.GenerativeModel('gemini-1.5-flash')
response = model.count_tokens(
    'The quick brown fox jumps over the lazy dog.')
After

Python
JavaScript

from google import genai

client = genai.Client()

response = client.models.count_tokens(
    model='gemini-2.0-flash',
    contents='The quick brown fox jumps over the lazy dog.',
)
Generate images
Generate images:

Before

Python

#pip install https://github.com/google-gemini/generative-ai-python@imagen
import google.generativeai as genai

imagen = genai.ImageGenerationModel(
    "imagen-3.0-generate-001")
gen_images = imagen.generate_images(
    prompt="Robot holding a red skateboard",
    number_of_images=1,
    safety_filter_level="block_low_and_above",
    person_generation="allow_adult",
    aspect_ratio="3:4",
)
After

Python

from google import genai

client = genai.Client()

gen_images = client.models.generate_images(
    model='imagen-3.0-generate-001',
    prompt='Robot holding a red skateboard',
    config=types.GenerateImagesConfig(
        number_of_images= 1,
        safety_filter_level= "BLOCK_LOW_AND_ABOVE",
        person_generation= "ALLOW_ADULT",
        aspect_ratio= "3:4",
    )
)

for n, image in enumerate(gen_images.generated_images):
    pathlib.Path(f'{n}.png').write_bytes(
        image.image.image_bytes)
Embed content
Generate content embeddings.

Before

Python
JavaScript

import google.generativeai as genai

response = genai.embed_content(
  model='models/text-embedding-004',
  content='Hello world'
)
After

Python
JavaScript

from google import genai

client = genai.Client()

response = client.models.embed_content(
  model='text-embedding-004',
  contents='Hello world',
)
Tune a Model
Create and use a tuned model.

The new SDK simplifies tuning with client.tunings.tune, which launches the tuning job and polls until the job is complete.

Before

Python

import google.generativeai as genai
import random

# create tuning model
train_data = {}
for i in range(1, 6):
  key = f'input {i}'
  value = f'output {i}'
  train_data[key] = value

name = f'generate-num-{random.randint(0,10000)}'
operation = genai.create_tuned_model(
    source_model='models/gemini-1.5-flash-001-tuning',
    training_data=train_data,
    id = name,
    epoch_count = 5,
    batch_size=4,
    learning_rate=0.001,
)
# wait for tuning complete
tuningProgress = operation.result()

# generate content with the tuned model
model = genai.GenerativeModel(model_name=f'tunedModels/{name}')
response = model.generate_content('55')
After

Python

from google import genai
from google.genai import types

client = genai.Client()

# Check which models are available for tuning.
for m in client.models.list():
  for action in m.supported_actions:
    if action == "createTunedModel":
      print(m.name)
      break

# create tuning model
training_dataset=types.TuningDataset(
        examples=[
            types.TuningExample(
                text_input=f'input {i}',
                output=f'output {i}',
            )
            for i in range(5)
        ],
    )
tuning_job = client.tunings.tune(
    base_model='models/gemini-1.5-flash-001-tuning',
    training_dataset=training_dataset,
    config=types.CreateTuningJobConfig(
        epoch_count= 5,
        batch_size=4,
        learning_rate=0.001,
        tuned_model_display_name="test tuned model"
    )
)

# generate content with the tuned model
response = client.models.generate_content(
    model=tuning_job.tuned_model.model,
    contents='55',
)


Files API
Files API

The Gemini family of artificial intelligence (AI) models is built to handle various types of input data, including text, images, and audio. Since these models can handle more than one type or mode of data, the Gemini models are called multimodal models or explained as having multimodal capabilities.

This guide shows you how to work with media files using the Files API. The basic operations are the same for audio files, images, videos, documents, and other supported file types.

For file prompting guidance, check out the File prompt guide section.

Upload a file
You can use the Files API to upload a media file. Always use the Files API when the total request size (including the files, text prompt, system instructions, etc.) is larger than 20 MB.

The following code uploads a file and then uses the file in a call to generateContent.

Python
JavaScript
Go
REST

from google import genai

client = genai.Client()

myfile = client.files.upload(file="path/to/sample.mp3")

response = client.models.generate_content(
    model="gemini-2.0-flash", contents=["Describe this audio clip", myfile]
)

print(response.text)
Get metadata for a file
You can verify that the API successfully stored the uploaded file and get its metadata by calling files.get.

Python
JavaScript
Go
REST

myfile = client.files.upload(file='path/to/sample.mp3')
file_name = myfile.name
myfile = client.files.get(name=file_name)
print(myfile)
List uploaded files
You can upload multiple files using the Files API. The following code gets a list of all the files uploaded:

Python
JavaScript
Go
REST

print('My files:')
for f in client.files.list():
    print(' ', f.name)
Delete uploaded files
Files are automatically deleted after 48 hours. You can also manually delete an uploaded file:

Python
JavaScript
Go
REST

myfile = client.files.upload(file='path/to/sample.mp3')
client.files.delete(name=myfile.name)
Usage info
You can use the Files API to upload and interact with media files. The Files API lets you store up to 20 GB of files per project, with a per-file maximum size of 2 GB. Files are stored for 48 hours. During that time, you can use the API to get metadata about the files, but you can't download the files. The Files API is available at no cost in all regions where the Gemini API is available.



Image understanding

Gemini models are built to be multimodal from the ground up, unlocking a wide range of image processing and computer vision tasks including but not limited to image captioning, classification, and visual question answering without having to train specialized ML models.

Tip: In addition to their general multimodal capabilities, Gemini models (2.0 and newer) offer improved accuracy for specific use cases like object detection and segmentation, through additional training. See the Capabilities section for more details.
Passing images to Gemini
You can provide images as input to Gemini using two methods:

Passing inline image data: Ideal for smaller files (total request size less than 20MB, including prompts).
Uploading images using the File API: Recommended for larger files or for reusing images across multiple requests.
Passing inline image data
You can pass inline image data in the request to generateContent. You can provide image data as Base64 encoded strings or by reading local files directly (depending on the language).

The following example shows how to read an image from a local file and pass it to generateContent API for processing.

Python
JavaScript
Go
REST

from google.genai import types

with open('path/to/small-sample.jpg', 'rb') as f:
image_bytes = f.read()

response = client.models.generate_content(
model='gemini-2.5-flash',
contents=[
types.Part.from_bytes(
data=image_bytes,
mime_type='image/jpeg',
),
'Caption this image.'
]
)

print(response.text)
You can also fetch an image from a URL, convert it to bytes, and pass it to generateContent as shown in the following examples.

Python
JavaScript
Go
REST

from google import genai
from google.genai import types

import requests

image_path = "https://goo.gle/instrument-img"
image_bytes = requests.get(image_path).content
image = types.Part.from_bytes(
data=image_bytes, mime_type="image/jpeg"
)

client = genai.Client()

response = client.models.generate_content(
model="gemini-2.5-flash",
contents=["What is this image?", image],
)

print(response.text)
Note: Inline image data limits your total request size (text prompts, system instructions, and inline bytes) to 20MB. For larger requests, upload image files using the File API. Files API is also more efficient for scenarios that use the same image repeatedly.
Uploading images using the File API
For large files or to be able to use the same image file repeatedly, use the Files API. The following code uploads an image file and then uses the file in a call to generateContent. See the Files API guide for more information and examples.

Python
JavaScript
Go
REST

from google import genai

client = genai.Client()

my_file = client.files.upload(file="path/to/sample.jpg")

response = client.models.generate_content(
model="gemini-2.5-flash",
contents=[my_file, "Caption this image."],
)

print(response.text)
Prompting with multiple images
You can provide multiple images in a single prompt by including multiple image Part objects in the contents array. These can be a mix of inline data (local files or URLs) and File API references.

Python
JavaScript
Go
REST

from google import genai
from google.genai import types

client = genai.Client()

# Upload the first image
image1_path = "path/to/image1.jpg"
uploaded_file = client.files.upload(file=image1_path)

# Prepare the second image as inline data
image2_path = "path/to/image2.png"
with open(image2_path, 'rb') as f:
img2_bytes = f.read()

# Create the prompt with text and multiple images
response = client.models.generate_content(

    model="gemini-2.5-flash",
    contents=[
        "What is different between these two images?",
        uploaded_file,  # Use the uploaded file reference
        types.Part.from_bytes(
            data=img2_bytes,
            mime_type='image/png'
        )
    ]
)

print(response.text)
Object detection
From Gemini 2.0 onwards, models are further trained to detect objects in an image and get their bounding box coordinates. The coordinates, relative to image dimensions, scale to [0, 1000]. You need to descale these coordinates based on your original image size.

Python

from google import genai
from google.genai import types
from PIL import Image
import json

client = genai.Client()
prompt = "Detect the all of the prominent items in the image. The box_2d should be [ymin, xmin, ymax, xmax] normalized to 0-1000."

image = Image.open("/path/to/image.png")

config = types.GenerateContentConfig(
response_mime_type="application/json"
)

response = client.models.generate_content(model="gemini-2.5-flash",
contents=[image, prompt],
config=config
)

width, height = image.size
bounding_boxes = json.loads(response.text)

converted_bounding_boxes = []
for bounding_box in bounding_boxes:
abs_y1 = int(bounding_box["box_2d"][0]/1000 * height)
abs_x1 = int(bounding_box["box_2d"][1]/1000 * width)
abs_y2 = int(bounding_box["box_2d"][2]/1000 * height)
abs_x2 = int(bounding_box["box_2d"][3]/1000 * width)
converted_bounding_boxes.append([abs_x1, abs_y1, abs_x2, abs_y2])

print("Image size: ", width, height)
print("Bounding boxes:", converted_bounding_boxes)

Note: The model also supports generating bounding boxes based on custom instructions, such as: "Show bounding boxes of all green objects in this image". It also support custom labels like "label the items with the allergens they can contain".
For more examples, check following notebooks in the Gemini Cookbook:

2D spatial understanding notebook
Experimental 3D pointing notebook
Segmentation
Starting with Gemini 2.5, models not only detect items but also segment them and provide their contour masks.

The model predicts a JSON list, where each item represents a segmentation mask. Each item has a bounding box ("box_2d") in the format [y0, x0, y1, x1] with normalized coordinates between 0 and 1000, a label ("label") that identifies the object, and finally the segmentation mask inside the bounding box, as base64 encoded png that is a probability map with values between 0 and 255. The mask needs to be resized to match the bounding box dimensions, then binarized at your confidence threshold (127 for the midpoint).

Note: For better results, disable thinking by setting the thinking budget to 0. See code sample below for an example.
Python

from google import genai
from google.genai import types
from PIL import Image, ImageDraw
import io
import base64
import json
import numpy as np
import os

client = genai.Client()

def parse_json(json_output: str):
# Parsing out the markdown fencing
lines = json_output.splitlines()
for i, line in enumerate(lines):
if line == "```json":
      json_output = "\n".join(lines[i+1:])  # Remove everything before "```json"
output = json_output.split("```")[0]  # Remove everything after the closing "```"
break  # Exit the loop once "```json" is found
return json_output

def extract_segmentation_masks(image_path: str, output_dir: str = "segmentation_outputs"):
# Load and resize image
im = Image.open(image_path)
im.thumbnail([1024, 1024], Image.Resampling.LANCZOS)

prompt = """
Give the segmentation masks for the wooden and glass items.
Output a JSON list of segmentation masks where each entry contains the 2D
bounding box in the key "box_2d", the segmentation mask in key "mask", and
the text label in the key "label". Use descriptive labels.
"""

config = types.GenerateContentConfig(
thinking_config=types.ThinkingConfig(thinking_budget=0) # set thinking_budget to 0 for better results in object detection
)

response = client.models.generate_content(
model="gemini-2.5-flash",
contents=[prompt, im], # Pillow images can be directly passed as inputs (which will be converted by the SDK)
config=config
)

# Parse JSON response
items = json.loads(parse_json(response.text))

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Process each mask
for i, item in enumerate(items):
# Get bounding box coordinates
box = item["box_2d"]
y0 = int(box[0] / 1000 * im.size[1])
x0 = int(box[1] / 1000 * im.size[0])
y1 = int(box[2] / 1000 * im.size[1])
x1 = int(box[3] / 1000 * im.size[0])

      # Skip invalid boxes
      if y0 >= y1 or x0 >= x1:
          continue

      # Process mask
      png_str = item["mask"]
      if not png_str.startswith("data:image/png;base64,"):
          continue

      # Remove prefix
      png_str = png_str.removeprefix("data:image/png;base64,")
      mask_data = base64.b64decode(png_str)
      mask = Image.open(io.BytesIO(mask_data))

      # Resize mask to match bounding box
      mask = mask.resize((x1 - x0, y1 - y0), Image.Resampling.BILINEAR)

      # Convert mask to numpy array for processing
      mask_array = np.array(mask)

      # Create overlay for this mask
      overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
      overlay_draw = ImageDraw.Draw(overlay)

      # Create overlay for the mask
      color = (255, 255, 255, 200)
      for y in range(y0, y1):
          for x in range(x0, x1):
              if mask_array[y - y0, x - x0] > 128:  # Threshold for mask
                  overlay_draw.point((x, y), fill=color)

      # Save individual mask and its overlay
      mask_filename = f"{item['label']}_{i}_mask.png"
      overlay_filename = f"{item['label']}_{i}_overlay.png"

      mask.save(os.path.join(output_dir, mask_filename))

      # Create and save overlay
      composite = Image.alpha_composite(im.convert('RGBA'), overlay)
      composite.save(os.path.join(output_dir, overlay_filename))
      print(f"Saved mask and overlay for {item['label']} to {output_dir}")

# Example usage
if __name__ == "__main__":
extract_segmentation_masks("path/to/image.png")

Check the segmentation example in the cookbook guide for a more detailed example.

A table with cupcakes, with the wooden and glass objects highlighted
An example segmentation output with objects and segmentation masks
Supported image formats
Gemini supports the following image format MIME types:

PNG - image/png
JPEG - image/jpeg
WEBP - image/webp
HEIC - image/heic
HEIF - image/heif
Capabilities
All Gemini model versions are multimodal and can be utilized in a wide range of image processing and computer vision tasks including but not limited to image captioning, visual question and answering, image classification, object detection and segmentation.

Gemini can reduce the need to use specialized ML models depending on your quality and performance requirements.

Some later model versions are specifically trained improve accuracy of specialized tasks in addition to generic capabilities:

Gemini 2.0 models are further trained to support enhanced object detection.

Gemini 2.5 models are further trained to support enhanced segmentation in addition to object detection.

Limitations and key technical information
File limit
Gemini 2.5 Pro/Flash, 2.0 Flash, 1.5 Pro, and 1.5 Flash support a maximum of 3,600 image files per request.

Token calculation
Gemini 1.5 Flash and Gemini 1.5 Pro: 258 tokens if both dimensions <= 384 pixels. Larger images are tiled (min tile 256px, max 768px, resized to 768x768), with each tile costing 258 tokens.
Gemini 2.0 Flash and Gemini 2.5 Flash/Pro: 258 tokens if both dimensions <= 384 pixels. Larger images are tiled into 768x768 pixel tiles, each costing 258 tokens.
Tips and best practices
Verify that images are correctly rotated.
Use clear, non-blurry images.
When using a single image with text, place the text prompt after the image part in the contents array.
What's next
This guide shows you how to upload image files and generate text outputs from image inputs. To learn more, see the following resources:

Files API: Learn more about uploading and managing files for use with Gemini.
System instructions: System instructions let you steer the behavior of the model based on your specific needs and use cases.
File prompting strategies: The Gemini API supports prompting with text, image, audio, and video data, also known as multimodal prompting.
Safety guidance: Sometimes generative AI models produce unexpected outputs, such as outputs that are inaccurate, biased, or offensive. Post-processing and human evaluation are essential to limit the risk of harm from such outputs.



Structured output

You can configure Gemini for structured output instead of unstructured text, allowing precise extraction and standardization of information for further processing. For example, you can use structured output to extract information from resumes, standardize them to build a structured database.

Gemini can generate either JSON or enum values as structured output.

Generating JSON
There are two ways to generate JSON using the Gemini API:

Configure a schema on the model
Provide a schema in a text prompt
Configuring a schema on the model is the recommended way to generate JSON, because it constrains the model to output JSON.

Configuring a schema (recommended)
To constrain the model to generate JSON, configure a responseSchema. The model will then respond to any prompt with JSON-formatted output.

Python
JavaScript
Go
REST

from google import genai
from pydantic import BaseModel

class Recipe(BaseModel):
    recipe_name: str
    ingredients: list[str]

client = genai.Client()
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="List a few popular cookie recipes, and include the amounts of ingredients.",
    config={
        "response_mime_type": "application/json",
        "response_schema": list[Recipe],
    },
)
# Use the response as a JSON string.
print(response.text)

# Use instantiated objects.
my_recipes: list[Recipe] = response.parsed
Note: Pydantic validators are not yet supported. If a pydantic.ValidationError occurs, it is suppressed, and .parsed may be empty/null.
The output might look like this:


[
  {
    "recipeName": "Chocolate Chip Cookies",
    "ingredients": [
      "1 cup (2 sticks) unsalted butter, softened",
      "3/4 cup granulated sugar",
      "3/4 cup packed brown sugar",
      "1 teaspoon vanilla extract",
      "2 large eggs",
      "2 1/4 cups all-purpose flour",
      "1 teaspoon baking soda",
      "1 teaspoon salt",
      "2 cups chocolate chips"
    ]
  },
  ...
]
Providing a schema in a text prompt
Instead of configuring a schema, you can supply a schema as natural language or pseudo-code in a text prompt. This method is not recommended, because it might produce lower quality output, and because the model is not constrained to follow the schema.

Warning: Don't provide a schema in a text prompt if you're configuring a responseSchema. This can produce unexpected or low quality results.
Here's a generic example of a schema provided in a text prompt:


List a few popular cookie recipes, and include the amounts of ingredients.

Produce JSON matching this specification:

Recipe = { "recipeName": string, "ingredients": array<string> }
Return: array<Recipe>
Since the model gets the schema from text in the prompt, you might have some flexibility in how you represent the schema. But when you supply a schema inline like this, the model is not actually constrained to return JSON. For a more deterministic, higher quality response, configure a schema on the model, and don't duplicate the schema in the text prompt.

Generating enum values
In some cases you might want the model to choose a single option from a list of options. To implement this behavior, you can pass an enum in your schema. You can use an enum option anywhere you could use a string in the responseSchema, because an enum is an array of strings. Like a JSON schema, an enum lets you constrain model output to meet the requirements of your application.

For example, assume that you're developing an application to classify musical instruments into one of five categories: "Percussion", "String", "Woodwind", "Brass", or ""Keyboard"". You could create an enum to help with this task.

In the following example, you pass an enum as the responseSchema, constraining the model to choose the most appropriate option.

Python
JavaScript
REST

from google import genai
import enum

class Instrument(enum.Enum):
  PERCUSSION = "Percussion"
  STRING = "String"
  WOODWIND = "Woodwind"
  BRASS = "Brass"
  KEYBOARD = "Keyboard"

client = genai.Client()
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='What type of instrument is an oboe?',
    config={
        'response_mime_type': 'text/x.enum',
        'response_schema': Instrument,
    },
)

print(response.text)
# Woodwind
The Python library will translate the type declarations for the API. However, the API accepts a subset of the OpenAPI 3.0 schema (Schema).

There are two other ways to specify an enumeration. You can use a Literal: ```

Python

Literal["Percussion", "String", "Woodwind", "Brass", "Keyboard"]
And you can also pass the schema as JSON:

Python

from google import genai

client = genai.Client()
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='What type of instrument is an oboe?',
    config={
        'response_mime_type': 'text/x.enum',
        'response_schema': {
            "type": "STRING",
            "enum": ["Percussion", "String", "Woodwind", "Brass", "Keyboard"],
        },
    },
)

print(response.text)
# Woodwind
Beyond basic multiple choice problems, you can use an enum anywhere in a JSON schema. For example, you could ask the model for a list of recipe titles and use a Grade enum to give each title a popularity grade:

Python

from google import genai

import enum
from pydantic import BaseModel

class Grade(enum.Enum):
    A_PLUS = "a+"
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    F = "f"

class Recipe(BaseModel):
  recipe_name: str
  rating: Grade

client = genai.Client()
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='List 10 home-baked cookie recipes and give them grades based on tastiness.',
    config={
        'response_mime_type': 'application/json',
        'response_schema': list[Recipe],
    },
)

print(response.text)
The response might look like this:


[
  {
    "recipe_name": "Chocolate Chip Cookies",
    "rating": "a+"
  },
  {
    "recipe_name": "Peanut Butter Cookies",
    "rating": "a"
  },
  {
    "recipe_name": "Oatmeal Raisin Cookies",
    "rating": "b"
  },
  ...
]
About JSON schemas
Configuring the model for JSON output using responseSchema parameter relies on Schema object to define its structure. This object represents a select subset of the OpenAPI 3.0 Schema object, and also adds a propertyOrdering field.

Tip: On Python, when you use a Pydantic model, you don't need to directly work with Schema objects, as it gets automatically converted to the corresponding JSON schema. To learn more, see JSON schemas in Python.
Here's a pseudo-JSON representation of all the Schema fields:


{
  "type": enum (Type),
  "format": string,
  "description": string,
  "nullable": boolean,
  "enum": [
    string
  ],
  "maxItems": integer,
  "minItems": integer,
  "properties": {
    string: {
      object (Schema)
    },
    ...
  },
  "required": [
    string
  ],
  "propertyOrdering": [
    string
  ],
  "items": {
    object (Schema)
  }
}
The Type of the schema must be one of the OpenAPI Data Types, or a union of those types (using anyOf). Only a subset of fields is valid for each Type. The following list maps each Type to a subset of the fields that are valid for that type:

string -> enum, format, nullable
integer -> format, minimum, maximum, enum, nullable
number -> format, minimum, maximum, enum, nullable
boolean -> nullable
array -> minItems, maxItems, items, nullable
object -> properties, required, propertyOrdering, nullable
Here are some example schemas showing valid type-and-field combinations:


{ "type": "string", "enum": ["a", "b", "c"] }

{ "type": "string", "format": "date-time" }

{ "type": "integer", "format": "int64" }

{ "type": "number", "format": "double" }

{ "type": "boolean" }

{ "type": "array", "minItems": 3, "maxItems": 3, "items": { "type": ... } }

{ "type": "object",
  "properties": {
    "a": { "type": ... },
    "b": { "type": ... },
    "c": { "type": ... }
  },
  "nullable": true,
  "required": ["c"],
  "propertyOrdering": ["c", "b", "a"]
}
For complete documentation of the Schema fields as they're used in the Gemini API, see the Schema reference.

Property ordering
Warning: When you're configuring a JSON schema, make sure to set propertyOrdering[], and when you provide examples, make sure that the property ordering in the examples matches the schema.
When you're working with JSON schemas in the Gemini API, the order of properties is important. By default, the API orders properties alphabetically and does not preserve the order in which the properties are defined (although the Google Gen AI SDKs may preserve this order). If you're providing examples to the model with a schema configured, and the property ordering of the examples is not consistent with the property ordering of the schema, the output could be rambling or unexpected.

To ensure a consistent, predictable ordering of properties, you can use the optional propertyOrdering[] field.


"propertyOrdering": ["recipeName", "ingredients"]
propertyOrdering[] – not a standard field in the OpenAPI specification – is an array of strings used to determine the order of properties in the response. By specifying the order of properties and then providing examples with properties in that same order, you can potentially improve the quality of results. propertyOrdering is only supported when you manually create types.Schema.

Schemas in Python
When you're using the Python library, the value of response_schema must be one of the following:

A type, as you would use in a type annotation (see the Python typing module)
An instance of genai.types.Schema
The dict equivalent of genai.types.Schema
The easiest way to define a schema is with a Pydantic type (as shown in the previous example):

Python

config={'response_mime_type': 'application/json',
        'response_schema': list[Recipe]}
When you use a Pydantic type, the Python library builds out a JSON schema for you and sends it to the API. For additional examples, see the Python library docs.

The Python library supports schemas defined with the following types (where AllowedType is any allowed type):

int
float
bool
str
list[AllowedType]
AllowedType|AllowedType|...
For structured types:
dict[str, AllowedType]. This annotation declares all dict values to be the same type, but doesn't specify what keys should be included.
User-defined Pydantic models. This approach lets you specify the key names and define different types for the values associated with each of the keys, including nested structures.
JSON Schema support
JSON Schema is a more recent specification than OpenAPI 3.0, which the Schema object is based on. Support for JSON Schema is available as a preview using the field responseJsonSchema which accepts any JSON Schema with the following limitations:

It only works with Gemini 2.5.
While all JSON Schema properties can be passed, not all are supported. See the documentation for the field for more details.
Recursive references can only be used as the value of a non-required object property.
Recursive references are unrolled to a finite degree, based on the size of the schema.
Schemas that contain $ref cannot contain any properties other than those starting with a $.
Here's an example of generating a JSON Schema with Pydantic and submitting it to the model:


curl "https://generativelanguage.googleapis.com/v1alpha/models/\
gemini-2.5-flash:generateContent" \
    -H "x-goog-api-key: $GEMINI_API_KEY"\
    -H 'Content-Type: application/json' \
    -d @- <<EOF
{
  "contents": [{
    "parts":[{
      "text": "Please give a random example following this schema"
    }]
  }],
  "generationConfig": {
    "response_mime_type": "application/json",
    "response_json_schema": $(python3 - << PYEOF
from enum import Enum
from typing import List, Optional, Union, Set
from pydantic import BaseModel, Field, ConfigDict
import json

class UserRole(str, Enum):
    ADMIN = "admin"
    VIEWER = "viewer"

class Address(BaseModel):
    street: str
    city: str

class UserProfile(BaseModel):
    username: str = Field(description="User's unique name")
    age: Optional[int] = Field(ge=0, le=120)
    roles: Set[UserRole] = Field(min_items=1)
    contact: Union[Address, str]
    model_config = ConfigDict(title="User Schema")

# Generate and print the JSON Schema
print(json.dumps(UserProfile.model_json_schema(), indent=2))
PYEOF
)
  }
}
EOF
Passing JSON Schema directly is not yet supported when using the SDK.

Best practices
Keep the following considerations and best practices in mind when you're using a response schema:

The size of your response schema counts towards the input token limit.
By default, fields are optional, meaning the model can populate the fields or skip them. You can set fields as required to force the model to provide a value. If there's insufficient context in the associated input prompt, the model generates responses mainly based on the data it was trained on.
A complex schema can result in an InvalidArgument: 400 error. Complexity might come from long property names, long array length limits, enums with many values, objects with lots of optional properties, or a combination of these factors.

If you get this error with a valid schema, make one or more of the following changes to resolve the error:

Shorten property names or enum names.
Flatten nested arrays.
Reduce the number of properties with constraints, such as numbers with minimum and maximum limits.
Reduce the number of properties with complex constraints, such as properties with complex formats like date-time.
Reduce the number of optional properties.
Reduce the number of valid values for enums.
If you aren't seeing the results you expect, add more context to your input prompts or revise your response schema. For example, review the model's response without structured output to see how the model responds. You can then update your response schema so that it better fits the model's output.




