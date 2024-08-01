"""
server for the api
"""

import json
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request

from center_of_mass import com
from comparetool import compare_ships
from read_ship import get_ship_data
from write_ship_from_json import write_ship_png

app = FastAPI()


@app.get("/")
def read_root():
    """
    A function that reads the root endpoint.
    """
    return {"Cosmoteer version": "0.26.2"}


@app.middleware("http")
async def add_cors_headers(request, call_next):
    """
    Adds CORS headers to the HTTP response.

    This middleware function is used to add CORS headers to the HTTP response. 
    It allows cross-origin requests
    from any origin by setting the "Access-Control-Allow-Origin" header to "*". 
    It also allows POST and GET
    methods by setting the "Access-Control-Allow-Methods" header to "POST, GET". 
    The "Access-Control-Allow-Headers" header is set to "Content-Type" to allow 
    requests with the "Content-Type" header.

    Parameters:
        request (Request): The HTTP request object.
        call_next (Callable): The next middleware or route handler in the chain.

    Returns:
        Response: The HTTP response with the added CORS headers.
    """
    response = await call_next(request)
    if request.url.path == "/edit" and request.method == "GET":
        response.headers["Access-Control-Allow-Origin"] = "*"  # adjust as needed
        response.headers["Access-Control-Allow-Methods"] = "GET"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    if request.url.path == "/generate" and request.method == "POST":
        response.headers["Access-Control-Allow-Origin"] = "*"  # adjust as needed
        response.headers["Access-Control-Allow-Methods"] = "POST"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.get("/edit")
async def get_ship_data_from_url(request: Request):
    """
    Retrieves ship data from a given URL and returns it as a JSON object.

    Args:
        request (Request): The HTTP request object containing the query parameters.

    Returns:
        dict: A JSON object containing the ship data retrieved from the URL.
              If the URL is not provided, returns {"error": "No URL provided"}.
              If an error occurs while retrieving the ship data, returns
              {"error": str(error)}.
    """
    url = request.query_params.get("url")

    if not url:
        return {"error": "No URL provided"}

    try:
        ship_data = get_ship_data(url)
    except Exception as e:
        return {"error": str(e)}
    return ship_data

@app.post("/generate")  # endpoint for CosmoShipBuilder, in = json, out = png
async def generate_png(request: Request):
    request_json = await request.json()
    data_json = request_json
    data_url = write_ship_png(data_json)
    return {"url": data_url}


@app.get("/analyze")  # get a url
async def analyze(request: Request):
    """
    Retrieves ship analysis data from a given URL.

    Args:
        request (Request): The HTTP request object containing the query parameters.

    Returns:
        Union[str, dict]: If the URL is not provided, returns "No data".
        Otherwise, returns a dictionary containing
        ship analysis data.

    Raises:
        None

    Examples:
        >>> request = Request()
        >>> request.query_params = {"url": "https://example.com/ship.png"}
        >>> analyze(request)
        {
            "url_com": "string",
            "center_of_mass_x": float,
            "center_of_mass_y": float,
            "total_mass": float,
            "top_speed": float,
            "crew": int,
            "price": int,
            "tags": ["string", ...],
            "author": "string",
            "all_direction_speeds": {
                "NW": float,
                "N": float,
                "NE": float,
                "E": float,
                "SE": float,
                "S": float,
                "SW": float,
                "W": float
            },
            "analysis": {
                "url_analysis": "string",
                "total_price": {"price": float, "percent": float},
                "price_crew": {"price": float, "percent": float},
                "price_weapons": {"price": float, "percent": float},
                "price_armor": {"price": float, "percent": float},
                "price_mouvement": {"price": float, "percent": float},
                "price_power": {"price": float, "percent": float},
                "price_shield": {"price": float, "percent": float},
                "price_storage": {"price": float, "percent": float},
                "price_utility": {"price": float, "percent": float},
            }
        }
    """
    query = request.query_params
    # get data from url
    url = query["url"]
    args = {}
    query_keys = [
        "draw",
        "flip_vectors",
        "draw_all_com",
        "draw_all_cot",
        "draw_cot",
        "draw_com",
        "boost",
        "analyze",
    ]

    for key in query_keys:
        if key in query:
            args[key] = query[key]

    placeholder = "placeholder"  # we do not output a file here
    # data = unquote_plus(data)
    # print(data)
    if not url:
        return "No data"

    result = com(url, placeholder, args)
    result = json.loads(result)
    return result


@app.get("/compare")  # usage : http://127.0.0.1:8001/compare?ship1=776&ship2=777
async def compare(request: Request):
    """
    This function is a GET endpoint that compares two ships based on their IDs provided in the
    query parameters.

    Parameters:
        - request (Request): The incoming request object.

    Returns:
        - If either ship ID is missing, it returns a string "Missing ship id".
        - Otherwise, it calls the `compare_ships` function with the ship IDs and optional scale
        parameter.
        - If the scale parameter is provided and is "True", it calls `compare_ships` with the
        scale parameter.
        - If the scale parameter is not provided or is not "True", it calls `compare_ships`
        without the scale parameter.
        - The result of `compare_ships` is parsed as JSON and returned as the response.
    """
    query = request.query_params
    # get data from url
    ship1 = query["ship1"]
    ship2 = query["ship2"]

    if not ship1 or not ship2:
        return "Missing ship id"

    # if key scale in query then return its value
    if "scale" in query:
        # print("scale")
        scale = query["scale"]
        # print(scale)
        if scale == "True":
            # print("scale True")
            result = compare_ships(ship1, ship2, scale)
        else:
            result = compare_ships(ship1, ship2)
    else:
        result = compare_ships(ship1, ship2)
    result = json.loads(result)
    return result


@app.post("/analyze")  # get a url
async def analyzepost(request: Request):
    """
    This function is an asynchronous handler for the '/analyze' POST endpoint.
    It receives a JSON payload containing an image URL and optional analysis parameters.

    Parameters:
        - request (Request): The incoming request object containing the JSON payload.

    Returns:
        - If the JSON payload is missing the 'image' field, it returns a string "No data".
        - Otherwise, it extracts the 'args' and 'image' fields from the JSON payload
        and converts them to Python dictionaries.
        - It then checks if the 'args' dictionary contains any of the supported analysis
        parameters and adds them to the 'args' dictionary.
        - If the 'image' field is missing, it returns a string "No data".
        - It then calls the 'com' function with the extracted URL, a placeholder string,
        and the 'args' dictionary as arguments.
        - The result of the 'com' function is parsed as JSON and returned as the response.
    """
    request_json = await request.json()
    # convert request_json string to dict
    data_json = json.loads(request_json)
    json_args = data_json["args"]
    json_image = data_json["image"]

    args = {}
    query_keys = [
        "draw",
        "flip_vectors",
        "draw_all_com",
        "draw_all_cot",
        "draw_cot",
        "draw_com",
        "boost",
        "analyze",
    ]

    for key in query_keys:
        if key in json_args:
            args[key] = json_args[key]

    if not json_image:
        return "No data"

    url = json_image
    placeholder = "placeholder"
    result = com(url, placeholder, args)
    result = json.loads(result)
    return result


app.add_middleware(SessionMiddleware, secret_key=os.getenv("secret_session"))
app.add_middleware(GZipMiddleware, minimum_size=1000)

if __name__ == "__main__":
    # uvicorn.run("server:app", host="0.0.0.0", port=8001)
    uvicorn.run("server:app", host="0.0.0.0", port=8001, workers=5)
