"""
server for the api
"""

import json
import os
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Union
import base64

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Path, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

from center_of_mass import com
from read_ship import get_ship_data
from write_ship_from_json import write_ship_png
from api_front import ShipImageDatabase
from tagextractor import PNGTagExtractor
from center_of_mass import calculate_price
from cosmoteer_save_tools_new import Ship as new_ship
from png_upload import upload_image_to_imgbb

load_dotenv()
db_manager = ShipImageDatabase()





# Define response models
class ShipData(BaseModel):
    ship_id:int
    ship_name: str
    ship_png: str
    ship_author: str
    ship_description: str
    ship_cost: int
    ship_crew: int
    ship_popularity: int
    ship_date_submitted: str
    ship_submitted_by: str
    ship_tags: List[str]
    brand: str
    number_fav:Optional[Union[int, str]] = None
    is_in_user_fav: Optional[Union[int, str]] = None
    is_owner: Optional[Union[int, str]] = None

class ShipDataInsert(BaseModel):
    token: str
    image: str
    user_description: Optional[str] = None
    user_tags:  Optional[List[str]] = []


class ErrorResponse(BaseModel):
    warning: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None
    type: Optional[str] = None


class SuccessResponse(BaseModel):
    success: str


class SearchResponse(BaseModel):
    data: Optional[List[ShipData]] = []
    page: Optional[int] = None
    max_page: Optional[int] = None


class AuthorsResponse(BaseModel):
    authors: List[str]


app = FastAPI(
    title="Cosmoteer API",
    description="API for managing and analyzing Cosmoteer ships",
    version="0.26.2",
    contact={
        "name": "Cosmoteer API Support",
        "url": "https://hport.dev",
    },
    license_info={
        "name": "MIT",
    },
)

SECRET_KEY = os.getenv("SECRET_KEY") # Make sure to set this in your environment variables


@app.get("/", response_model=Dict[str, str])
def read_root():
    """
    Root endpoint that returns the current version of the Cosmoteer API.

    Returns:
        Dict[str, str]: A dictionary containing the Cosmoteer version.
    """
    return {"Cosmoteer version": "0.26.2"}

@app.get("/authors", response_model=AuthorsResponse)
async def get_authors():
    # get list of authors
    authors_list = db_manager.get_authors()
    # Extract just the author names from the list of dictionaries
    author_names = [author["author"] for author in authors_list]
    return {"authors": author_names}

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
    if request.url.path == "/search" and request.method == "GET":
        response.headers["Access-Control-Allow-Origin"] = "*"  # adjust as needed
        response.headers["Access-Control-Allow-Methods"] = "GET"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.get("/edit", response_model=Union[Dict[str, Any], ErrorResponse])
async def get_ship_data_from_url(request: Request):
    """
    Retrieves ship data from a given URL and returns it as a JSON object.

    Args:
        request (Request): The HTTP request object containing the query parameters.
            - url (str): The URL of the ship data to retrieve.

    Returns:
        Union[Dict[str, Any], ErrorResponse]:
            - If successful: A dictionary containing the ship data
            - If error: An error response with details about what went wrong
    """
    url = request.query_params.get("url")

    if not url:
        return {"error": "No URL provided"}

    try:
        ship_data = get_ship_data(url)
    except Exception as e:
        return {"error": str(e)}
    return ship_data


@app.post("/generate", response_model=Dict[str, str])
async def generate_png(request: Request):
    """
    Generates a PNG image from ship data provided in JSON format.

    Args:
        request (Request): The HTTP request containing the ship data in JSON format.

    Returns:
        Dict[str, str]: A dictionary containing the URL of the generated PNG image.
    """
    request_json = await request.json()
    data_json = request_json
    data_url = write_ship_png(data_json)
    return {"url": data_url}


@app.get("/analyze", response_model=Union[Dict[str, Any], str])
async def analyze(request: Request):
    """
    Analyzes a ship from a given URL and returns detailed analysis data.

    Args:
        request (Request): The HTTP request containing query parameters:
            - url (str): The URL of the ship to analyze
            - draw (bool, optional): Whether to draw the analysis
            - flip_vectors (bool, optional): Whether to flip vectors
            - draw_all_com (bool, optional): Whether to draw all centers of mass
            - draw_all_cot (bool, optional): Whether to draw all centers of thrust
            - draw_cot (bool, optional): Whether to draw center of thrust
            - draw_com (bool, optional): Whether to draw center of mass
            - boost (bool, optional): Whether to apply boost
            - analyze (bool, optional): Whether to perform analysis

    Returns:
        Union[Dict[str, Any], str]:
            - If successful: A dictionary containing detailed ship analysis
            - If no data: "No data" string
    """
    query = request.query_params
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

    placeholder = "placeholder"
    if not url:
        return "No data"

    result = com(url, placeholder, args)
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


@app.get("/ship/{ship_id}", response_model=Union[SearchResponse, ErrorResponse])  # OK
async def get_ship(ship_id: int = Path(..., description="Id if the ship"), token: str = Query(None, description="Token for auth")):
    user = None
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user = payload.get("user")
            iat = payload.get("iat")
            if iat < (datetime.now(tz=timezone.utc) - timedelta(minutes=5)).timestamp():
                user = None
        except Exception as e:
            user = None

    if user:
        fav_list = db_manager.get_my_favorite(user=user)["data"]
        owner_list = db_manager.get_my_ships(user=user)["data"]
        ids = {item.get("id") for item in fav_list if "id" in item}
        fav = 1 if ship_id in ids else 0
        ids = [item.get("id") for item in owner_list if "id" in item]
        is_owner = 1 if ship_id in ids else 0
    else:
        fav = "no user provided"
        is_owner = "no user provided"

    db_data = db_manager.get_image_data(ship_id)

    if not db_data:
        return {"error": "Ship not found"}
    formatted_data = []
    formatted_item = {
        "ship_id": db_data.get("id", 0),
        "ship_name": db_data.get("ship_name", ""),
        "ship_png": db_data.get("data", ""),
        "ship_author": db_data.get("author", ""),
        "ship_description": db_data.get("description", ""),
        "ship_cost": db_data.get("price", 0),
        "ship_crew": db_data.get("crew", 0),
        "ship_popularity": db_data.get("downloads", 0),
        "ship_date_submitted": str(db_data.get("date", "")),
        "ship_submitted_by": db_data.get("submitted_by", ""),
        "ship_tags": db_data.get("tags", []),
        "brand": db_data.get("brand", "gen"),
        "is_in_user_fav": fav,
        "is_owner": is_owner,
    }
    formatted_data.append(formatted_item)

    response_data = {"data": formatted_data, "page": None, "max_page": None}
    try:
        # Validate against the model explicitly
        valid_response = SearchResponse(**response_data)
        return valid_response
    except ValidationError as e:
        # Log or return detailed validation info
        return JSONResponse(
            status_code=500,
            content={
                "error": "Validation error",
                "details": e.errors(),  # This will show which fields failed
                "original_data": response_data,
            },
        )

    return {"data": formatted_data, "page": None, "max_page": None}


@app.post("/ship/{ship_id}/addfav", response_model=Union[SuccessResponse, ErrorResponse])  # OK
async def add_fav(ship_id: int, request: Request):
    """
    Adds a ship to the user's favorites.

    Args:
        ship_id (int): The ID of the ship to add to favorites
        request (Request): The HTTP request containing query parameters:
            - token (str): JWT token for user authentication

    Returns:
        Union[SuccessResponse, ErrorResponse]:
            - If successful: Success message
            - If error: Error details including message and type
    """
    query = request.query_params
    token = query.get("token")

    if not token:
        return {"error": "Token is missing"}
    if not ship_id:
        return {"error": "Ship_id is missing"}

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = payload.get("user")
        iat = payload.get("iat")
        if iat < (datetime.now(tz=timezone.utc) - timedelta(minutes=5)).timestamp():
            return {"error": "Token is too old"}
    except Exception as e:
        return {"error": "invalid token", "message": str(e), "type": type(e).__name__}

    db_return = db_manager.add_to_favorites(user=user, ship_id=ship_id)

    return (
        db_return if db_return else {"success": f"Ship {ship_id} added to favorite of user {user}"}
    )


@app.post("/ship/{ship_id}/rmfav", response_model=Union[SuccessResponse, ErrorResponse])  # OK
async def rm_fav(ship_id: int, request: Request):
    """
    Removes a ship from the user's favorites.

    Args:
        ship_id (int): The ID of the ship to remove from favorites
        request (Request): The HTTP request containing query parameters:
            - token (str): JWT token for user authentication

    Returns:
        Union[SuccessResponse, ErrorResponse]:
            - If successful: Success message
            - If error: Error details including message and type
    """
    query = request.query_params
    token = query.get("token")

    if not token:
        return {"error": "Token is missing"}

    if not ship_id:
        return {"error": "Ship_id is missing"}

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = payload.get("user")
        iat = payload.get("iat")
        if iat < (datetime.now(tz=timezone.utc) - timedelta(minutes=5)).timestamp():
            return {"error": "Token is too old"}
    except Exception as e:
        return {"error": "invalid token", "message": str(e), "type": type(e).__name__}

    db_return = db_manager.delete_from_favorites(user=user, ship_id=ship_id)
    return (
        db_return
        if db_return
        else {"success": f"Ship {ship_id} removed to favorite of user {user}"}
    )


@app.get("/myfavorite", response_model=Union[SearchResponse, ErrorResponse])  # OK
async def myfavorite(
    token: str = Query(..., description="JWT token for user authentication"),
    page: int = Query(
        1,
        description="Page to request data for, default 1, if above max page default to max_page",
    ),
):
    """
    Retrieves the list of ships in favorite of the authenticated user.

    Parameters:
        token (str): JWT token for user authentication.
        page (int): Page number to request data for. Defaults to 1. If the requested page is above the maximum page, it defaults to max_page.

    Returns:
        Union[ShipData, ErrorResponse]:
            - If successful: A dictionary containing the user's ships, the current page, and the maximum page.
            - If error: An error response with details about the issue.
    """
    if not token:
        return {"error": "Token is missing"}

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = payload.get("user")
        iat = payload.get("iat")
        if iat < (datetime.now(tz=timezone.utc) - timedelta(minutes=5)).timestamp():
            return {"error": "Token is too old"}
    except Exception as e:
        return {"error": "invalid token", "message": str(e), "type": type(e).__name__}

    data = db_manager.get_my_favorite(user=user, page=page)
    # Format the data to match ShipData model
    formatted_data = []
    for item in data["data"]:
        formatted_item = {
            "ship_id": item.get("id", 0),
            "ship_name": item.get("ship_name", ""),
            "ship_png": item.get("data", ""),
            "ship_author": item.get("author", ""),
            "ship_description": item.get("description", ""),
            "ship_cost": item.get("price", 0),
            "ship_crew": item.get("crew", 0),
            "ship_popularity": item.get("downloads", 0),
            "ship_date_submitted": str(item.get("date", "")),
            "ship_submitted_by": item.get("submitted_by", ""),
            "ship_tags": item.get("tags", []),
            "brand": item.get("brand", "gen"),
        }
        formatted_data.append(formatted_item)

    return {"data": formatted_data, "page": data["page"], "max_page": data["max_page"]}

# @app.get("/search", response_model=Union[SearchResponse, ErrorResponse])  # OK
@app.get("/search")  # OK
async def search_plus(request: Request):
    data = db_manager.get_search_plus(query_params=request.query_params)
    # Format the data to match ShipData model
    raw_items = data["data"]
    items = raw_items if isinstance(raw_items, list) else [raw_items]

    formatted_data = []
    for item in items:
        formatted_item = {
            "ship_id": item.get("id", 0),
            "ship_name": item.get("ship_name", ""),
            "ship_png": item.get("data", ""),
            "ship_author": item.get("author", ""),
            "ship_description": item.get("description", ""),
            "ship_cost": item.get("price", 0),
            "ship_crew": item.get("crew", 0),
            "ship_popularity": item.get("downloads", 0),
            "ship_date_submitted": str(item.get("date", "")),
            "ship_submitted_by": item.get("submitted_by", ""),
            "ship_tags": item.get("tags", []),
            "brand": item.get("brand", ""),
            "number_fav": item.get("fav", "")
        }
        formatted_data.append(formatted_item)

    return {"data": formatted_data, "page": data["page"], "max_page": data["max_page"]}


@app.get("/myships", response_model=Union[SearchResponse, ErrorResponse])  # OK
async def myships(
    token: str = Query(..., description="JWT token for user authentication"),
    page: int = Query(
        1,
        description="Page to request data for, default 1, if above max page default to max_page",
    ),
):
    """
    Retrieves the list of ships submitted by the authenticated user.

    Parameters:
        token (str): JWT token for user authentication.
        page (int): Page number to request data for. Defaults to 1. If the requested page is above the maximum page, it defaults to max_page.

    Returns:
        Union[ShipData, ErrorResponse]:
            - If successful: A dictionary containing the user's ships, the current page, and the maximum page.
            - If error: An error response with details about the issue.
    """
    if not token:
        return {"error": "Token is missing"}

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = payload.get("user")
        iat = payload.get("iat")
        if iat < (datetime.now(tz=timezone.utc) - timedelta(minutes=5)).timestamp():
            return {"error": "Token is too old"}
    except Exception as e:
        return {"error": "invalid token", "message": str(e), "type": type(e).__name__}

    data = db_manager.get_my_ships(user=user, page=page)
    # Format the data to match ShipData model
    formatted_data = []
    for item in data["data"]:
        formatted_item = {
            "ship_id": item.get("id", 0),
            "ship_name": item.get("ship_name", ""),
            "ship_png": item.get("data", ""),
            "ship_author": item.get("author", ""),
            "ship_description": item.get("description", ""),
            "ship_cost": item.get("price", 0),
            "ship_crew": item.get("crew", 0),
            "ship_popularity": item.get("downloads", 0),
            "ship_date_submitted": str(item.get("date", "")),
            "ship_submitted_by": item.get("submitted_by", ""),
            "ship_tags": item.get("tags", []),
            "brand": item.get("brand", ""),
            "number_fav": item.get("fav", "")
        }
        formatted_data.append(formatted_item)

    return {"data": formatted_data, "page": data["page"], "max_page": data["max_page"]}


# post delete
@app.post("/delete/{ship_id}", response_model=Union[SuccessResponse, ErrorResponse])  # TESTME
async def delete_ship(
    ship_id: int = Path(..., description="Ship id in the database"),
    token: str = Query(..., description="JWT token for user authentication"),
):
    """
    Retrieves detailed information about a specific ship.

    Args:
        ship_id (int): The ID of the ship to retrieve
        token (str): JWT token for user authentication.

    Returns:
        Union[ShipData, ErrorResponse]:
            - If successful: success
            - If ship not found: Error response
            - If user not owner : Error response
    """
    user = None
    if not token:
        return {"error": "Token is missing"}

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = payload.get("user")
        iat = payload.get("iat")
        if iat < (datetime.now(tz=timezone.utc) - timedelta(minutes=5)).timestamp():
            return {"error": "Token is too old"}
    except Exception as e:
        return {"error": "invalid token", "message": str(e), "type": type(e).__name__}

    return db_manager.delete_ship(ship_id=ship_id, user=user)



# post add_ship
@app.post("/insert_ship") # ok
async def insert_ship(data: ShipDataInsert = Body(...)):
    # Validate token
    try:
        payload = jwt.decode(data.token, SECRET_KEY, algorithms=["HS256"])
        user = payload.get("user")
        iat = payload.get("iat")

        if not user or iat is None:
            raise HTTPException(status_code=400, detail="Invalid token structure")

        token_age = datetime.now(tz=timezone.utc) - datetime.fromtimestamp(iat, tz=timezone.utc)
        if token_age > timedelta(minutes=5):
            raise HTTPException(status_code=401, detail="Token is too old")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail={"error": "Invalid token", "message": str(e)})

    # return {data.image}
    # Validate base64 and PNG
    try:
        image_data = base64.b64decode(data.image)
        if not image_data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(
                status_code=400, detail="Invalid image format. Only PNG files are allowed."
            )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail={"error": "Invalid base64 string", "message": str(e)}
        )

    # Extract data from image
    try:
        data_ship = new_ship(data.image).data
        if not data_ship:
            raise HTTPException(status_code=422, detail="Invalid image data. No data found.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "Error processing image", "message": str(e)}
        )

    # Upload image
    try:
        url = upload_image_to_imgbb(data.image)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "Error uploading image", "message": str(e)}
        )

    # Extract tags
    try:
        tags, author = PNGTagExtractor().extract_tags(data_json=data_ship)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "Error processing tags", "message": str(e)}
        )

    # Calculate price and crew
    try:
        price, crew = calculate_price(data_ship)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"error": "Error calculating price", "message": str(e)}
        )

    # Combine user tags
    tags.extend(data.user_tags or [])

    # Fallbacks for ship name and description
    ship_name = data_ship.get("Name", "Unnamed")
    # print("SHIPNAME: ", ship_name)
    description = data_ship.get("Description", "No description")
    if data.user_description:
        description = f"{description} {data.user_description}"

    name = f"{ship_name}.ship.png"

    # Final data for DB
    db_return = db_manager.insert_ship(
        name=name,
        data=url,
        submitted_by=user,
        description=description,
        ship_name=ship_name,
        author=author,
        price=price,
        brand="gen",
        crew=crew,
        tags=tags,
    )
    ship_id = int(db_return["success"])
    if ship_id:
        return {
            "success": True,
            "message": "Ship successfully added",
            "data": {"ship_id": ship_id,"name": name, "url": url, "submitted_by": user, "tags": tags},
        }
    return {"error": "db error"}


# post edit
@app.post("/edit/{ship_id}") 
async def edit_ship(ship_id: int = Path(...), data: Dict[str, Any] = Body(...)):
    try:
        payload = jwt.decode(data["token"], SECRET_KEY, algorithms=["HS256"])
        user = payload.get("user")
        iat = payload.get("iat")

        if not user or iat is None:
            raise HTTPException(status_code=400, detail="Invalid token structure")

        token_age = datetime.now(tz=timezone.utc) - datetime.fromtimestamp(iat, tz=timezone.utc)
        if token_age > timedelta(minutes=5):
            raise HTTPException(status_code=401, detail="Token is too old")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail={"error": "Invalid token", "message": str(e)})

    # prepare data
    name = (data["data"].get("filename", "unnamed") + ".ship.png" if not data["data"].get("filename", "").endswith(".ship.png") else data["data"].get("filename", "unnamed")) # filename
    data_url = data["data"]["url_png"] # url
    submitted_by = data["data"]["submitted_by"]  # user transfert
    description = data["data"]["description"]  # user desc
    ship_name = data["data"]["ship_name"]  # ship name
    author = data["data"]["author"]  # ship author
    price = int(data["data"]["price"])  # price
    brand = data["data"].get("brand", "gen")  # toggle exl or gen
    crew = int(data["data"]["crew"])  # crew
    tags = data["data"]["tags"]  # tags

    # tag from the extractor to keep always
    auto_tags = {
            'cannon',
            'deck_cannon',
            'flak_battery',
            'large_cannon',
            'railgun',
            'factories',
            'disruptors',
            'heavy_laser',
            'ion_beam',
            'ion_prism',
            'laser',
            'mining_laser',
            'point_defense',
            'boost_thruster',
            'airlock',
            'campaign_factories',
            'explosive_charges',
            'fire_extinguisher',
            'large_reactor',
            'large_shield',
            'medium_reactor',
            'sensor',
            'small_hyperdrive',
            'small_reactor',
            'small_shield',
            'tractor_beams',
            'hyperdrive_relay',
            'chaingun',
            'rocket_thruster',
            'large_hyperdrive',
        }
        
    # Filter tags to only include valid auto_tags and convert to set for faster lookups
    if tags:
        tags = list(set(tag for tag in tags if tag in auto_tags))
    else:
        tags = []

    # add user tags
    for key, value in data["data"].items():
        if value == "on":
            tags.append(key)
        elif key in {"defense_type", "thrust_type"}:
            tags.append(value)
    # check user
    if submitted_by != user:
        return {"error":"user not allowed"}
    
    # check_data = {
    #     "name":name,
    #     "data":data_url,
    #     "submitted_by":submitted_by,
    #     "description":description,
    #     "ship_name":ship_name,
    #     "author":author,
    #     "price":price,
    #     "brand":brand,
    #     "crew":crew,
    #     "tags":tags,
    # }
    # print(check_data)
    # update db, replace description, ship name, author, submitted_by, user tags = appends ship tags
    db_manager.update_ship(name=name,
        data=data_url,
        submitted_by=submitted_by,
        description=description,
        ship_name=ship_name,
        author=author,
        price=price,
        brand=brand,
        crew=crew,
        tags=tags,)
    return {"success":"ship updated"}




app.add_middleware(SessionMiddleware, secret_key=os.getenv("secret_session"))
app.add_middleware(GZipMiddleware, minimum_size=1000)

if __name__ == "__main__":
    # uvicorn.run("server:app", host="0.0.0.0", port=8001)
    uvicorn.run("server:app", host="0.0.0.0", port=8001, workers=5)
