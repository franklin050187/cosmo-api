# API Documentation: Ship Analysis API

## Introduction

The Ship Analysis API allows you to analyze ships by providing a URL to a PNG image of the ship. It processes the image and returns various ship-related data in JSON format, including information about the ship's characteristics, such as its center of mass, total mass, top speed, crew count, price, tags, author, and speed in different directions.

### Endpoint

The API has two endpoints for analyzing ship data:

- **GET /analyze**: Allows you to submit ship data by providing a URL as a query parameter.
- **POST /analyze**: Allows you to submit ship data by sending a JSON payload containing an image and optional analysis parameters.

## Request and Response

### GET /analyze

#### Request

- **URL Parameters**:
  - `url` (string, required): The URL of the PNG image of the ship you want to analyze.

#### Response

The response from the GET request will be a JSON object with the following structure:

```json
{
    "url_com": "string",                // URL of the picture generated
    "center_of_mass_x": float,          // Coordinate x of center of mass
    "center_of_mass_y": float,          // Coordinate y of center of mass
    "total_mass": float,               // Total mass
    "top_speed": float,                // Top speed in the ship's orientation
    "crew": int,                       // Number of crew
    "price": float,                    // Price
    "tags": ["string", ...],           // Tags
    "author": "string",                // Author of the ship
    "all_direction_speeds": {
        "NW": float,
        "N": float,
        "NE": float,
        "E": float,
        "SE": float,
        "S": float,
        "SW": float,
        "W": float
    }                                  // JSON with a list of speeds in all directions
}
```

### POST /analyze

#### Request

- **JSON Payload**:
  - `image` (string, required): Base64-encoded image of the ship in PNG format.
  - `args` (object, optional): Additional analysis parameters. You can include the following parameters:
    - `draw` (boolean, optional): Draw specific ship characteristics.
    - `flip_vectors` (boolean, optional): Flip vectors.
    - `draw_all_com` (boolean, optional): Draw all center of mass.
    - `draw_all_cot` (boolean, optional): Draw all center of thrust.
    - `draw_cot` (boolean, optional): Draw center of thrust.
    - `draw_com` (boolean, optional): Draw center of mass.
    - `boost` (boolean, optional): Boost analysis.

Example JSON request payload:

```json
{
    "image": "base64_encoded_image_string",
    "args": {
        "draw": true,
        "flip_vectors": false,
        "draw_all_com": true,
        "draw_all_cot": false,
        "draw_cot": false,
        "draw_com": true,
        "boost": true
    }
}
```

#### Response

The response from the POST request will have the same JSON structure as described in the GET /analyze response section.

## Example Usage

### GET Request

```http
GET /analyze?url=<image_url>
```

### POST Request

```http
POST /analyze
Content-Type: application/json

{
    "image": "base64_encoded_image_string",
    "args": {
        "draw": true
    }
}
```

## Speed Calculation

The API calculates the speed in different directions based on the ship's orientation. The direction mapping is as follows:

- 0: "NW"
- 1: "N"
- 2: "NE"
- 3: "E"
- 4: "SE"
- 5: "S"
- 6: "SW"
- 7: "W"

The speed in each direction is calculated using the ship's total mass and thrust direction.

## Error Handling

If no image URL or image data is provided, the API will return a "No data" response.

## Example Python Code

Here's an example Python code snippet to call the API using the `requests` library:

```python
import requests

# GET Request
url = "https://your-api-url.com/analyze?url=<image_url>"
response = requests.get(url)
data = response.json()

# POST Request
url = "https://your-api-url.com/analyze"
payload = {
    "image": "base64_encoded_image_string",
    "args": {
        "draw": True
    }
}
response = requests.post(url, json=payload)
data = response.json()
```

Please replace `"https://your-api-url.com"` with the actual URL of the API.

## Conclusion

The Ship Analysis API provides a convenient way to extract valuable ship-related information from images and can be used in various applications related to ship analysis and design.
