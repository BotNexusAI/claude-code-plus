Function calling with the Gemini API

Function calling lets you connect models to external tools and APIs. Instead of generating text responses, the model determines when to call specific functions and provides the necessary parameters to execute real-world actions. This allows the model to act as a bridge between natural language and real-world actions and data. Function calling has 3 primary use cases:

Augment Knowledge: Access information from external sources like databases, APIs, and knowledge bases.
Extend Capabilities: Use external tools to perform computations and extend the limitations of the model, such as using a calculator or creating charts.
Take Actions: Interact with external systems using APIs, such as scheduling appointments, creating invoices, sending emails, or controlling smart home devices.
Get Weather Schedule Meeting Create Chart

Python
JavaScript
REST

from google import genai
from google.genai import types

# Define the function declaration for the model
schedule_meeting_function = {
    "name": "schedule_meeting",
    "description": "Schedules a meeting with specified attendees at a given time and date.",
    "parameters": {
        "type": "object",
        "properties": {
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of people attending the meeting.",
            },
            "date": {
                "type": "string",
                "description": "Date of the meeting (e.g., '2024-07-29')",
            },
            "time": {
                "type": "string",
                "description": "Time of the meeting (e.g., '15:00')",
            },
            "topic": {
                "type": "string",
                "description": "The subject or topic of the meeting.",
            },
        },
        "required": ["attendees", "date", "time", "topic"],
    },
}

# Configure the client and tools
client = genai.Client()
tools = types.Tool(function_declarations=[schedule_meeting_function])
config = types.GenerateContentConfig(tools=[tools])

# Send request with function declarations
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Schedule a meeting with Bob and Alice for 03/14/2025 at 10:00 AM about the Q3 planning.",
    config=config,
)

# Check for a function call
if response.candidates[0].content.parts[0].function_call:
    function_call = response.candidates[0].content.parts[0].function_call
    print(f"Function to call: {function_call.name}")
    print(f"Arguments: {function_call.args}")
    #  In a real app, you would call your function here:
    #  result = schedule_meeting(**function_call.args)
else:
    print("No function call found in the response.")
    print(response.text)
How function calling works
function calling
overview

Function calling involves a structured interaction between your application, the model, and external functions. Here's a breakdown of the process:

Define Function Declaration: Define the function declaration in your application code. Function Declarations describe the function's name, parameters, and purpose to the model.
Call LLM with function declarations: Send user prompt along with the function declaration(s) to the model. It analyzes the request and determines if a function call would be helpful. If so, it responds with a structured JSON object.
Execute Function Code (Your Responsibility): The Model does not execute the function itself. It's your application's responsibility to process the response and check for Function Call, if
Yes: Extract the name and args of the function and execute the corresponding function in your application.
No: The model has provided a direct text response to the prompt (this flow is less emphasized in the example but is a possible outcome).
Create User friendly response: If a function was executed, capture the result and send it back to the model in a subsequent turn of the conversation. It will use the result to generate a final, user-friendly response that incorporates the information from the function call.
This process can be repeated over multiple turns, allowing for complex interactions and workflows. The model also supports calling multiple functions in a single turn (parallel function calling) and in sequence (compositional function calling).

Step 1: Define a function declaration
Define a function and its declaration within your application code that allows users to set light values and make an API request. This function could call external services or APIs.

Python
JavaScript

# Define a function that the model can call to control smart lights
set_light_values_declaration = {
    "name": "set_light_values",
    "description": "Sets the brightness and color temperature of a light.",
    "parameters": {
        "type": "object",
        "properties": {
            "brightness": {
                "type": "integer",
                "description": "Light level from 0 to 100. Zero is off and 100 is full brightness",
            },
            "color_temp": {
                "type": "string",
                "enum": ["daylight", "cool", "warm"],
                "description": "Color temperature of the light fixture, which can be `daylight`, `cool` or `warm`.",
            },
        },
        "required": ["brightness", "color_temp"],
    },
}

# This is the actual function that would be called based on the model's suggestion
def set_light_values(brightness: int, color_temp: str) -> dict[str, int | str]:
    """Set the brightness and color temperature of a room light. (mock API).

    Args:
        brightness: Light level from 0 to 100. Zero is off and 100 is full brightness
        color_temp: Color temperature of the light fixture, which can be `daylight`, `cool` or `warm`.

    Returns:
        A dictionary containing the set brightness and color temperature.
    """
    return {"brightness": brightness, "colorTemperature": color_temp}
Step 2: Call the model with function declarations
Once you have defined your function declarations, you can prompt the model to use them. It analyzes the prompt and function declarations and decides whether to respond directly or to call a function. If a function is called, the response object will contain a function call suggestion.

Python
JavaScript

from google.genai import types

# Configure the client and tools
client = genai.Client()
tools = types.Tool(function_declarations=[set_light_values_declaration])
config = types.GenerateContentConfig(tools=[tools])

# Define user prompt
contents = [
    types.Content(
        role="user", parts=[types.Part(text="Turn the lights down to a romantic level")]
    )
]

# Send request with function declarations
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents
    config=config,
)

print(response.candidates[0].content.parts[0].function_call)
The model then returns a functionCall object in an OpenAPI compatible schema specifying how to call one or more of the declared functions in order to respond to the user's question.

Python
JavaScript

id=None args={'color_temp': 'warm', 'brightness': 25} name='set_light_values'
Step 3: Execute set_light_values function code
Extract the function call details from the model's response, parse the arguments , and execute the set_light_values function.

Python
JavaScript

# Extract tool call details, it may not be in the first part.
tool_call = response.candidates[0].content.parts[0].function_call

if tool_call.name == "set_light_values":
    result = set_light_values(**tool_call.args)
    print(f"Function execution result: {result}")
Step 4: Create user friendly response with function result and call the model again
Finally, send the result of the function execution back to the model so it can incorporate this information into its final response to the user.

Python
JavaScript

# Create a function response part
function_response_part = types.Part.from_function_response(
    name=tool_call.name,
    response={"result": result},
)

# Append function call and result of the function execution to contents
contents.append(response.candidates[0].content) # Append the content from the model's response.
contents.append(types.Content(role="user", parts=[function_response_part])) # Append the function response

final_response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=config,
    contents=contents,
)

print(final_response.text)
This completes the function calling flow. The model successfully used the set_light_values function to perform the request action of the user.

Function declarations
When you implement function calling in a prompt, you create a tools object, which contains one or more function declarations. You define functions using JSON, specifically with a select subset of the OpenAPI schema format. A single function declaration can include the following parameters:

name (string): A unique name for the function (get_weather_forecast, send_email). Use descriptive names without spaces or special characters (use underscores or camelCase).
description (string): A clear and detailed explanation of the function's purpose and capabilities. This is crucial for the model to understand when to use the function. Be specific and provide examples if helpful ("Finds theaters based on location and optionally movie title which is currently playing in theaters.").
parameters (object): Defines the input parameters the function expects.
type (string): Specifies the overall data type, such as object.
properties (object): Lists individual parameters, each with:
type (string): The data type of the parameter, such as string, integer, boolean, array.
description (string): A description of the parameter's purpose and format. Provide examples and constraints ("The city and state, e.g., 'San Francisco, CA' or a zip code e.g., '95616'.").
enum (array, optional): If the parameter values are from a fixed set, use "enum" to list the allowed values instead of just describing them in the description. This improves accuracy ("enum": ["daylight", "cool", "warm"]).
required (array): An array of strings listing the parameter names that are mandatory for the function to operate.
You can also construct FunctionDeclarations from Python functions directly using types.FunctionDeclaration.from_callable(client=client, callable=your_function).

Function calling with thinking
Enabling "thinking" can improve function call performance by allowing the model to reason through a request before suggesting function calls.

However, because the Gemini API is stateless, this reasoning context is lost between turns, which can reduce the quality of function calls as they require multiple turn requests.

To preserve this context you can use thought signatures. A thought signature is an encrypted representation of the model's internal thought process that you pass back to the model on subsequent turns.

To use thought signatures:

Receive the signature: When thinking is enabled, the API response will include a thought_signature field containing an encrypted representation of the model's reasoning.
Return the signature: When you send the function's execution result back to the server, include the thought_signature you received.
This allows the model to restore its previous thinking context and will likely result in better function calling performance.

Receiving signatures from the server

Signatures are returned in the part after the model's thinking phase, which typically is a text or function call.

Here are some examples of what thought signatures look like returned in each type of part, in response to the request "What's the weather in Lake Tahoe?" using the Get Weather example:

Text part
Function call part

[{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "Here's what the weather in Lake Tahoe is today",
            "thoughtSignature": "ClcBVKhc7ru7KzUI7SrdUoIdAYLm/+i93aHjfIt4xHyAoO/G70tApxnK2ujBhOhC1PrRy1pkQa88fqFvpHNVd1HDjNLO7mkp6/hFwE+SPPEB3fh0hs4oM8MKhgIBVKhc7uIGvrS7i/T4HpfbnYrluFfWNjZ62gewqe4cVdR/Dlh+zbjtYmDD0gPZ+SuBO7vvHQdzsjePRP+2Y5XddX6LEf/cGGgakq8EhVvw/a6IVzUO6XmpHg2Ag1sl8E9+VFH/lC0R0ZuYdFWligtDuYwp5p5q3o59G0TtWeU2MC1y2MJfE9u/KWd313ldka80/X2W/xF2O/4djMp5G2WKcULfve75zeRCy0mc5iS3SB9mTH0cT6x0vtKjeBx50gcg+CQWtJcRuwTVzz54dmvmK9xvnqA8gKGw3DuaM9wfy5hyY7Qg0z3iyyWdP8T/lbjKim8IEQOk7O1vVwP1Ko7oMYH8JgA1CsoBAVSoXO6v4c5RSyd1cn6EIU0pEFQsjW7rYWPuZdOFq/tsGJT9BCfW7KGkPGwlNSq8jTJFvbcJ/DjtndISQYXwiXd2kGa5JfdS2Kh4zOxCxiWtOk+2nCc3+XQk2nonhO+esGJpkDdbbHZSqRgcUtYKq7q28iPFOQvOFyCiZNB7K86Z/6Hnagu2snSlN/BcTMaFGaWpcCClSUo4foRZn3WbNCoM8rcpD7qEJMp4a5baaSxyyeL1ZTGd2HLpFys/oiW6e3oAnhxuIysCwg=="
          }
        ],
        "role": "model"
      },
      "index": 0
    }
  ],
  # Remainder of response...
You can confirm that you received a signature and see what a signature looks like using the following code:


# Step 2: Call the model with function declarations
# ...Generation config, Configure the client, and Define user prompt (No changes)

# Send request with declarations (using a thinking model)
response = client.models.generate_content(
  model="gemini-2.5-flash", config=config, contents=contents)

# See thought signatures
for part in response.candidates[0].content.parts:
  if part.thought_signature:
    print("Thought signature:")
    print(part.thought_signature)
Returning signatures back to the server

In order to return signatures back:

You should return signatures along with their containing parts back to the server
You shouldn't merge a part with a signature with another part which also contains a signature. The signature string is not concatenable
You shouldn't merge one part with a signature with another part without a signature. This breaks the correct positioning of the thought represented by the signature.
The code will remain the same as in Step 4 of the previous section. But in this case (as indicated in the comment below) you will return signatures to the model along with the result of the function execution so the model can incorporate the thoughts into its final response:

Python
JavaScript

# Step 4: Create user friendly response with function result and call the model again
# ...Create a function response part (No change)

# Append thought signatures, function call and result of the function execution to contents
function_call_content = response.candidates[0].content
# Append the model's function call message, which includes thought signatures
contents.append(function_call_content)
contents.append(types.Content(role="user", parts=[function_response_part])) # Append the function response

final_response = client.models.generate_content(
    model="gemini-2.5-flash",
    config=config,
    contents=contents,
)

print(final_response.text)
The following shows what a request returning a thought signature may look like:


[{
  "contents": [
    {
      "role": "user",
      "parts": [
        {
          "text": "what is the weather in Lake Tahoe?"
        }
      ]
    },
    {
      "parts": [
        {
          "functionCall": {
            "name": "getWeather",
            "args": {
              "city": "Lake Tahoe"
            }
          },
          "thoughtSignature": "CiIBVKhc7oDPpCaXyJKKssjqr4g3JNOSgJ/M2V+1THC1icsWCmwBVKhc7pBABbZ+zR3e9234WnWWS6GFXmf8IVwpnzjd5KYd7vyJbn/4vTorWBGayj/vbd9JPaZQjxdAIXhoE5mX/MDsQ7M9N/b0qJjHm39tYIBvS4sIWkMDHqTJqXGLzhhKtrTkfbV3RbaJEkQKmwEBVKhc7qVUgC3hfTXZLo9R3AJzUUIx50NKvJTb9B+UU+LBqgg7Nck1x5OpjWVS2R+SsveprIuYOruk2Y0H53J2OJF8qsxTdIq2si8DGW2V7WK8xyoJH5kbqd7drIw1jLb44b6lx4SMyB0VaULuTBki4d+Ljjg1tJTwR0IYMKqDLDZt9mheINsi0ZxcNjfpnDydRXdWbcSwzmK/wgqJAQFUqFzuKgNVElxs3cbO+xebr2IwcOro84nKTisi0tTp9bICPC9fTUhn3L+rvQWA+d3J1Za8at2bakrqiRj7BTh+CVO9fWQMAEQAs3ni0Z2hfaYG92tOD26E4IoZwyYEoWbfNudpH1fr5tEkyqnEGtWIh7H+XoZQ2DXeiOa+br7Zk88SrNE+trJMCogBAVSoXO5e9fBLg7hnbkmKsrzNLnQtLsQm1gNzjcjEC7nJYklYPp0KI2uGBE1PkM8XNsfllAfHVn7LzHcHNlbQ9pJ7QZTSIeG42goS971r5wNZwxaXwCTphClQh826eqJWo6A/28TtAVQWLhTx5ekbP7qb4nh1UblESZ1saxDQAEo4OKPbDzx5BgqKAQFUqFzuVyjNm5i0wN8hTDnKjfpDroEpPPTs531iFy9BOX+xDCdGHy8D+osFpaoBq6TFekQQbz4hIoUR1YEcP4zI80/cNimEeb9IcFxZTTxiNrbhbbcv0969DSMWhB+ZEqIz4vuw4GLe/xcUvqhlChQwFdgIbdOQHSHpatn5uDlktnP/bi26nKuXIwo0AVSoXO7US22OUH7d1f4abNPI0IyAvhqkPp12rbtWLx9vkOtojE8IP+xCfYtIFuZIzRNZqA=="
        }
      ],
      "role": "model"
    },
    {
      "role": "user",
      "parts": [
        {
          "functionResponse": {
            "name": "getWeather",
            "response": {
              "response": {
                "stringValue": "Sunny and hot. 90 degrees Fahrenheit"
              }
            }
          }
        }
      ]
    }
  ],
  # Remainder of request...
Learn more about limitations and usage of thought signatures, and about thinking models in general, on the Thinking page.

Parallel function calling
In addition to single turn function calling, you can also call multiple functions at once. Parallel function calling lets you execute multiple functions at once and is used when the functions are not dependent on each other. This is useful in scenarios like gathering data from multiple independent sources, such as retrieving customer details from different databases or checking inventory levels across various warehouses or performing multiple actions such as converting your apartment into a disco.

Python
JavaScript

power_disco_ball = {
    "name": "power_disco_ball",
    "description": "Powers the spinning disco ball.",
    "parameters": {
        "type": "object",
        "properties": {
            "power": {
                "type": "boolean",
                "description": "Whether to turn the disco ball on or off.",
            }
        },
        "required": ["power"],
    },
}

start_music = {
    "name": "start_music",
    "description": "Play some music matching the specified parameters.",
    "parameters": {
        "type": "object",
        "properties": {
            "energetic": {
                "type": "boolean",
                "description": "Whether the music is energetic or not.",
            },
            "loud": {
                "type": "boolean",
                "description": "Whether the music is loud or not.",
            },
        },
        "required": ["energetic", "loud"],
    },
}

dim_lights = {
    "name": "dim_lights",
    "description": "Dim the lights.",
    "parameters": {
        "type": "object",
        "properties": {
            "brightness": {
                "type": "number",
                "description": "The brightness of the lights, 0.0 is off, 1.0 is full.",
            }
        },
        "required": ["brightness"],
    },
}
Configure the function calling mode to allow using all of the specified tools. To learn more, you can read about configuring function calling.

Python
JavaScript

from google import genai
from google.genai import types

# Configure the client and tools
client = genai.Client()
house_tools = [
    types.Tool(function_declarations=[power_disco_ball, start_music, dim_lights])
]
config = types.GenerateContentConfig(
    tools=house_tools,
    automatic_function_calling=types.AutomaticFunctionCallingConfig(
        disable=True
    ),
    # Force the model to call 'any' function, instead of chatting.
    tool_config=types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(mode='ANY')
    ),
)

chat = client.chats.create(model="gemini-2.5-flash", config=config)
response = chat.send_message("Turn this place into a party!")

# Print out each of the function calls requested from this single call
print("Example 1: Forced function calling")
for fn in response.function_calls:
    args = ", ".join(f"{key}={val}" for key, val in fn.args.items())
    print(f"{fn.name}({args})")
Each of the printed results reflects a single function call that the model has requested. To send the results back, include the responses in the same order as they were requested.

The Python SDK supports automatic function calling, which automatically converts Python functions to declarations, handles the function call execution and response cycle for you. Following is an example for the disco use case.

Note: Automatic Function Calling is a Python SDK only feature at the moment.
Python

from google import genai
from google.genai import types

# Actual function implementations
def power_disco_ball_impl(power: bool) -> dict:
    """Powers the spinning disco ball.

    Args:
        power: Whether to turn the disco ball on or off.

    Returns:
        A status dictionary indicating the current state.
    """
    return {"status": f"Disco ball powered {'on' if power else 'off'}"}

def start_music_impl(energetic: bool, loud: bool) -> dict:
    """Play some music matching the specified parameters.

    Args:
        energetic: Whether the music is energetic or not.
        loud: Whether the music is loud or not.

    Returns:
        A dictionary containing the music settings.
    """
    music_type = "energetic" if energetic else "chill"
    volume = "loud" if loud else "quiet"
    return {"music_type": music_type, "volume": volume}

def dim_lights_impl(brightness: float) -> dict:
    """Dim the lights.

    Args:
        brightness: The brightness of the lights, 0.0 is off, 1.0 is full.

    Returns:
        A dictionary containing the new brightness setting.
    """
    return {"brightness": brightness}

# Configure the client
client = genai.Client()
config = types.GenerateContentConfig(
    tools=[power_disco_ball_impl, start_music_impl, dim_lights_impl]
)

# Make the request
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Do everything you need to this place into party!",
    config=config,
)

print("\nExample 2: Automatic function calling")
print(response.text)
# I've turned on the disco ball, started playing loud and energetic music, and dimmed the lights to 50% brightness. Let's get this party started!
Compositional function calling
Compositional or sequential function calling allows Gemini to chain multiple function calls together to fulfill a complex request. For example, to answer "Get the temperature in my current location", the Gemini API might first invoke a get_current_location() function followed by a get_weather() function that takes the location as a parameter.

The following example demonstrates how to implement compositional function calling using the Python SDK and automatic function calling.

Python
JavaScript
This example uses the automatic function calling feature of the google-genai Python SDK. The SDK automatically converts the Python functions to the required schema, executes the function calls when requested by the model, and sends the results back to the model to complete the task.


import os
from google import genai
from google.genai import types

# Example Functions
def get_weather_forecast(location: str) -> dict:
    """Gets the current weather temperature for a given location."""
    print(f"Tool Call: get_weather_forecast(location={location})")
    # TODO: Make API call
    print("Tool Response: {'temperature': 25, 'unit': 'celsius'}")
    return {"temperature": 25, "unit": "celsius"}  # Dummy response

def set_thermostat_temperature(temperature: int) -> dict:
    """Sets the thermostat to a desired temperature."""
    print(f"Tool Call: set_thermostat_temperature(temperature={temperature})")
    # TODO: Interact with a thermostat API
    print("Tool Response: {'status': 'success'}")
    return {"status": "success"}

# Configure the client and model
client = genai.Client()
config = types.GenerateContentConfig(
    tools=[get_weather_forecast, set_thermostat_temperature]
)

# Make the request
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="If it's warmer than 20°C in London, set the thermostat to 20°C, otherwise set it to 18°C.",
    config=config,
)

# Print the final, user-facing response
print(response.text)
Expected Output

When you run the code, you will see the SDK orchestrating the function calls. The model first calls get_weather_forecast, receives the temperature, and then calls set_thermostat_temperature with the correct value based on the logic in the prompt.


Tool Call: get_weather_forecast(location=London)
Tool Response: {'temperature': 25, 'unit': 'celsius'}
Tool Call: set_thermostat_temperature(temperature=20)
Tool Response: {'status': 'success'}
OK. I've set the thermostat to 20°C.
Compositional function calling is a native Live API feature. This means Live API can handle the function calling similar to the Python SDK.

Python
JavaScript

# Light control schemas
turn_on_the_lights_schema = {'name': 'turn_on_the_lights'}
turn_off_the_lights_schema = {'name': 'turn_off_the_lights'}

prompt = """
  Hey, can you write run some python code to turn on the lights, wait 10s and then turn off the lights?
  """

tools = [
    {'code_execution': {}},
    {'function_declarations': [turn_on_the_lights_schema, turn_off_the_lights_schema]}
]

await run(prompt, tools=tools, modality="AUDIO")
Function calling modes
The Gemini API lets you control how the model uses the provided tools (function declarations). Specifically, you can set the mode within the.function_calling_config.

AUTO (Default): The model decides whether to generate a natural language response or suggest a function call based on the prompt and context. This is the most flexible mode and recommended for most scenarios.
ANY: The model is constrained to always predict a function call and guarantees function schema adherence. If allowed_function_names is not specified, the model can choose from any of the provided function declarations. If allowed_function_names is provided as a list, the model can only choose from the functions in that list. Use this mode when you require a function call response to every prompt (if applicable).
NONE: The model is prohibited from making function calls. This is equivalent to sending a request without any function declarations. Use this to temporarily disable function calling without removing your tool definitions.

Python
JavaScript

from google.genai import types

# Configure function calling mode
tool_config = types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(
        mode="ANY", allowed_function_names=["get_current_temperature"]
    )
)

# Create the generation config
config = types.GenerateContentConfig(
    tools=[tools],  # not defined here.
    tool_config=tool_config,
)
Automatic function calling (Python only)
When using the Python SDK, you can provide Python functions directly as tools. The SDK automatically converts the Python function to declarations, handles the function call execution and the response cycle for you. The Python SDK then automatically:

Detects function call responses from the model.
Call the corresponding Python function in your code.
Sends the function response back to the model.
Returns the model's final text response.
To use this, define your function with type hints and a docstring, and then pass the function itself (not a JSON declaration) as a tool:

Python

from google import genai
from google.genai import types

# Define the function with type hints and docstring
def get_current_temperature(location: str) -> dict:
    """Gets the current temperature for a given location.

    Args:
        location: The city and state, e.g. San Francisco, CA

    Returns:
        A dictionary containing the temperature and unit.
    """
    # ... (implementation) ...
    return {"temperature": 25, "unit": "Celsius"}

# Configure the client
client = genai.Client()
config = types.GenerateContentConfig(
    tools=[get_current_temperature]
)  # Pass the function itself

# Make the request
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What's the temperature in Boston?",
    config=config,
)

print(response.text)  # The SDK handles the function call and returns the final text
You can disable automatic function calling with:

Python

config = types.GenerateContentConfig(
    tools=[get_current_temperature],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
)
Automatic function schema declaration
Automatic schema extraction from Python functions doesn't work in all cases. For example, it doesn't handle cases where you describe the fields of a nested dictionary-object. The API is able to describe any of the following types:

Python

AllowedType = (int | float | bool | str | list['AllowedType'] | dict[str, AllowedType])
To see what the inferred schema looks like, you can convert it using from_callable:

Python

def multiply(a: float, b: float):
    """Returns a * b."""
    return a * b

fn_decl = types.FunctionDeclaration.from_callable(callable=multiply, client=client)

# to_json_dict() provides a clean JSON representation.
print(fn_decl.to_json_dict())
Multi-tool use: Combine native tools with function calling
You can enable multiple tools combining native tools with function calling at the same time. Here's an example that enables two tools, Grounding with Google Search and code execution, in a request using the Live API.

Note: Multi-tool use is a-Live API only feature at the moment. The run() function declaration, which handles the asynchronous websocket setup, is omitted for brevity.
Python
JavaScript

# Multiple tasks example - combining lights, code execution, and search
prompt = """
  Hey, I need you to do three things for me.

    1.  Turn on the lights.
    2.  Then compute the largest prime palindrome under 100000.
    3.  Then use Google Search to look up information about the largest earthquake in California the week of Dec 5 2024.

  Thanks!
  """

tools = [
    {'google_search': {}},
    {'code_execution': {}},
    {'function_declarations': [turn_on_the_lights_schema, turn_off_the_lights_schema]} # not defined here.
]

# Execute the prompt with specified tools in audio modality
await run(prompt, tools=tools, modality="AUDIO")
Python developers can try this out in the Live API Tool Use notebook.

Model context protocol (MCP)
Model Context Protocol (MCP) is an open standard for connecting AI applications with external tools and data. MCP provides a common protocol for models to access context, such as functions (tools), data sources (resources), or predefined prompts.

The Gemini SDKs have built-in support for the MCP, reducing boilerplate code and offering automatic tool calling for MCP tools. When the model generates an MCP tool call, the Python and JavaScript client SDK can automatically execute the MCP tool and send the response back to the model in a subsequent request, continuing this loop until no more tool calls are made by the model.

Here, you can find an example of how to use a local MCP server with Gemini and mcp SDK.

Python
JavaScript
Make sure the latest version of the mcp SDK is installed on your platform of choice.


pip install mcp
Note: Python supports automatic tool calling by passing in the ClientSession into the tools parameters. If you want to disable it, you can provide automatic_function_calling with disabled True.

import os
import asyncio
from datetime import datetime
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai

client = genai.Client()

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="npx",  # Executable
    args=["-y", "@philschmid/weather-mcp"],  # MCP Server
    env=None,  # Optional environment variables
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Prompt to get the weather for the current day in London.
            prompt = f"What is the weather in London in {datetime.now().strftime('%Y-%m-%d')}?"

            # Initialize the connection between client and server
            await session.initialize()

            # Send request to the model with MCP function declarations
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0,
                    tools=[session],  # uses the session, will automatically call the tool
                    # Uncomment if you **don't** want the SDK to automatically call the tool
                    # automatic_function_calling=genai.types.AutomaticFunctionCallingConfig(
                    #     disable=True
                    # ),
                ),
            )
            print(response.text)

# Start the asyncio event loop and run the main function
asyncio.run(run())
Limitations with built-in MCP support
Built-in MCP support is a experimental feature in our SDKs and has the following limitations:

Only tools are supported, not resources nor prompts
It is available for the Python and JavaScript/TypeScript SDK.
Breaking changes might occur in future releases.
Manual integration of MCP servers is always an option if these limit what you're building.

Supported models
This section lists models and their function calling capabilities. Experimental models are not included. You can find a comprehensive capabilities overview on the model overview page.

Model	Function Calling	Parallel Function Calling	Compositional Function Calling
Gemini 2.5 Pro	✔️	✔️	✔️
Gemini 2.5 Flash	✔️	✔️	✔️
Gemini 2.5 Flash-Lite	✔️	✔️	✔️
Gemini 2.0 Flash	✔️	✔️	✔️
Gemini 2.0 Flash-Lite	X	X	X
Best practices
Function and Parameter Descriptions: Be extremely clear and specific in your descriptions. The model relies on these to choose the correct function and provide appropriate arguments.
Naming: Use descriptive function names (without spaces, periods, or dashes).
Strong Typing: Use specific types (integer, string, enum) for parameters to reduce errors. If a parameter has a limited set of valid values, use an enum.
Tool Selection: While the model can use an arbitrary number of tools, providing too many can increase the risk of selecting an incorrect or suboptimal tool. For best results, aim to provide only the relevant tools for the context or task, ideally keeping the active set to a maximum of 10-20. Consider dynamic tool selection based on conversation context if you have a large total number of tools.
Prompt Engineering:
Provide context: Tell the model its role (e.g., "You are a helpful weather assistant.").
Give instructions: Specify how and when to use functions (e.g., "Don't guess dates; always use a future date for forecasts.").
Encourage clarification: Instruct the model to ask clarifying questions if needed.
Temperature: Use a low temperature (e.g., 0) for more deterministic and reliable function calls.
Validation: If a function call has significant consequences (e.g., placing an order), validate the call with the user before executing it.
Error Handling: Implement robust error handling in your functions to gracefully handle unexpected inputs or API failures. Return informative error messages that the model can use to generate helpful responses to the user.
Security: Be mindful of security when calling external APIs. Use appropriate authentication and authorization mechanisms. Avoid exposing sensitive data in function calls.
Token Limits: Function descriptions and parameters count towards your input token limit. If you're hitting token limits, consider limiting the number of functions or the length of the descriptions, break down complex tasks into smaller, more focused function sets.
Notes and limitations
Only a subset of the OpenAPI schema is supported.
Supported parameter types in Python are limited.
Automatic function calling is a Python SDK feature only.


Gemini thinking

The Gemini 2.5 series models use an internal "thinking process" that significantly improves their reasoning and multi-step planning abilities, making them highly effective for complex tasks such as coding, advanced mathematics, and data analysis.

This guide shows you how to work with Gemini's thinking capabilities using the Gemini API.

Before you begin
Ensure you use a supported 2.5 series model for thinking. You might find it beneficial to explore these models in AI Studio before diving into the API:

Try Gemini 2.5 Flash in AI Studio
Try Gemini 2.5 Pro in AI Studio
Try Gemini 2.5 Flash-Lite in AI Studio
Generating content with thinking
Initiating a request with a thinking model is similar to any other content generation request. The key difference lies in specifying one of the models with thinking support in the model field, as demonstrated in the following text generation example:

Python
JavaScript
Go
REST

from google import genai

client = genai.Client()
prompt = "Explain the concept of Occam's Razor and provide a simple, everyday example."
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents=prompt
)

print(response.text)
Thinking budgets
The thinkingBudget parameter guides the model on the number of thinking tokens to use when generating a response. A higher token count generally allows for more detailed reasoning, which can be beneficial for tackling more complex tasks. If latency is more important, use a lower budget or disable thinking by setting thinkingBudget to 0. Setting the thinkingBudget to -1 turns on dynamic thinking, meaning the model will adjust the budget based on the complexity of the request.

The thinkingBudget is only supported in Gemini 2.5 Flash, 2.5 Pro, and 2.5 Flash-Lite. Depending on the prompt, the model might overflow or underflow the token budget.

The following are thinkingBudget configuration details for each model type.

Model	Default setting
(Thinking budget is not set)	Range	Disable thinking	Turn on dynamic thinking
2.5 Pro	Dynamic thinking: Model decides when and how much to think	128 to 32768	N/A: Cannot disable thinking	thinkingBudget = -1
2.5 Flash	Dynamic thinking: Model decides when and how much to think	0 to 24576	thinkingBudget = 0	thinkingBudget = -1
2.5 Flash Lite	Model does not think	512 to 24576	thinkingBudget = 0	thinkingBudget = -1
Python
JavaScript
Go
REST

from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="Provide a list of 3 famous physicists and their key contributions",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=1024)
        # Turn off thinking:
        # thinking_config=types.ThinkingConfig(thinking_budget=0)
        # Turn on dynamic thinking:
        # thinking_config=types.ThinkingConfig(thinking_budget=-1)
    ),
)

print(response.text)
Thought summaries
Thought summaries are synthesized versions of the model's raw thoughts and offer insights into the model's internal reasoning process. Note that thinking budgets apply to the model's raw thoughts and not to thought summaries.

You can enable thought summaries by setting includeThoughts to true in your request configuration. You can then access the summary by iterating through the response parameter's parts, and checking the thought boolean.

Here's an example demonstrating how to enable and retrieve thought summaries without streaming, which returns a single, final thought summary with the response:

Python
JavaScript
Go

from google import genai
from google.genai import types

client = genai.Client()
prompt = "What is the sum of the first 50 prime numbers?"
response = client.models.generate_content(
  model="gemini-2.5-pro",
  contents=prompt,
  config=types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(
      include_thoughts=True
    )
  )
)

for part in response.candidates[0].content.parts:
  if not part.text:
    continue
  if part.thought:
    print("Thought summary:")
    print(part.text)
    print()
  else:
    print("Answer:")
    print(part.text)
    print()

And here is an example using thinking with streaming, which returns rolling, incremental summaries during generation:

Python
JavaScript
Go

from google import genai
from google.genai import types

client = genai.Client()

prompt = """
Alice, Bob, and Carol each live in a different house on the same street: red, green, and blue.
The person who lives in the red house owns a cat.
Bob does not live in the green house.
Carol owns a dog.
The green house is to the left of the red house.
Alice does not own a cat.
Who lives in each house, and what pet do they own?
"""

thoughts = ""
answer = ""

for chunk in client.models.generate_content_stream(
    model="gemini-2.5-pro",
    contents=prompt,
    config=types.GenerateContentConfig(
      thinking_config=types.ThinkingConfig(
        include_thoughts=True
      )
    )
):
  for part in chunk.candidates[0].content.parts:
    if not part.text:
      continue
    elif part.thought:
      if not thoughts:
        print("Thoughts summary:")
      print(part.text)
      thoughts += part.text
    else:
      if not answer:
        print("Answer:")
      print(part.text)
      answer += part.text
Thought signatures
Because standard Gemini API text and content generation calls are stateless, when using thinking in multi-turn interactions (such as chat), the model doesn't have access to thought context from previous turns.

You can maintain thought context using thought signatures, which are encrypted representations of the model's internal thought process. The model returns thought signatures in the response object when thinking and function calling are enabled. To ensure the model maintains context across multiple turns of a conversation, you must provide the thought signatures back to the model in the subsequent requests.

You will receive thought signatures when:

Thinking is enabled and thoughts are generated.
The request includes function declarations.
Note: Thought signatures are only available when you're using function calling, specifically, your request must include function declarations.
You can find an example of thinking with function calls on the Function calling page.

Other usage limitations to consider with function calling include:

Signatures are returned from the model within other parts in the response, for example function calling or text parts. Return the entire response with all parts back to the model in subsequent turns.
Don't concatenate parts with signatures together.
Don't merge one part with a signature with another part without a signature.
Pricing
Note: Summaries are available in the free and paid tiers of the API. Thought signatures will increase the input tokens you are charged when sent back as part of the request.
When thinking is turned on, response pricing is the sum of output tokens and thinking tokens. You can get the total number of generated thinking tokens from the thoughtsTokenCount field.

Python
JavaScript
Go

# ...
print("Thoughts tokens:",response.usage_metadata.thoughts_token_count)
print("Output tokens:",response.usage_metadata.candidates_token_count)
Thinking models generate full thoughts to improve the quality of the final response, and then output summaries to provide insight into the thought process. So, pricing is based on the full thought tokens the model needs to generate to create a summary, despite only the summary being output from the API.

You can learn more about tokens in the Token counting guide.

Supported models
Thinking features are supported on all the 2.5 series models. You can find all model capabilities on the model overview page.

Best practices
This section includes some guidance for using thinking models efficiently. As always, following our prompting guidance and best practices will get you the best results.

Debugging and steering
Review reasoning: When you're not getting your expected response from the thinking models, it can help to carefully analyze Gemini's thought summaries. You can see how it broke down the task and arrived at its conclusion, and use that information to correct towards the right results.

Provide Guidance in Reasoning: If you're hoping for a particularly lengthy output, you may want to provide guidance in your prompt to constrain the amount of thinking the model uses. This lets you reserve more of the token output for your response.

Task complexity
Easy Tasks (Thinking could be OFF): For straightforward requests where complex reasoning isn't required, such as fact retrieval or classification, thinking is not required. Examples include:
"Where was DeepMind founded?"
"Is this email asking for a meeting or just providing information?"
Medium Tasks (Default/Some Thinking): Many common requests benefit from a degree of step-by-step processing or deeper understanding. Gemini can flexibly use thinking capability for tasks like:
Analogize photosynthesis and growing up.
Compare and contrast electric cars and hybrid cars.
Hard Tasks (Maximum Thinking Capability): For truly complex challenges, such as solving complex math problems or coding tasks, we recommend setting a high thinking budget. These types of tasks require the model to engage its full reasoning and planning capabilities, often involving many internal steps before providing an answer. Examples include:
Solve problem 1 in AIME 2025: Find the sum of all integer bases b > 9 for which 17b is a divisor of 97b.
Write Python code for a web application that visualizes real-time stock market data, including user authentication. Make it as efficient as possible.
Thinking with tools and capabilities
Thinking models work with all of Gemini's tools and capabilities. This allows the models to interact with external systems, execute code, or access real-time information, incorporating the results into their reasoning and final response.

The search tool allows the model to query Google Search to find up-to-date information or information beyond its training data. This is useful for questions about recent events or highly specific topics.

The code execution tool enables the model to generate and run Python code to perform calculations, manipulate data, or solve problems that are best handled algorithmically. The model receives the code's output and can use it in its response.

With structured output, you can constrain Gemini to respond with JSON. This is particularly useful for integrating the model's output into applications.

Function calling connects the thinking model to external tools and APIs, so it can reason about when to call the right function and what parameters to provide.

URL Context provides the model with URLs as additional context for your prompt. The model can then retrieve content from the URLs and use that content to inform and shape its response.

You can try examples of using tools with thinking models in the Thinking cookbook.

What's next?
To work through more in depth examples, like:

Using tools with thinking
Streaming with thinking
Adjusting the thinking budget for different results
and more, try our Thinking cookbook.

Thinking coverage is now available in our OpenAI Compatibility guide.

For more info about Gemini 2.5 Pro, Gemini Flash 2.5, and Gemini 2.5 Flash-Lite, visit the model page.

