import requests
import os
from dotenv import load_dotenv

load_dotenv()

def upload_image_to_imgbb(image_base64):
    api_key = os.getenv('imagebb_api')
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": api_key,
        "image": image_base64
    }
    # Send the upload request
    headers = {'content-encoding': 'gzip'}
    response = requests.post(url, payload, headers=headers)
    response.raise_for_status()  # Raise an exception for non-2xx status codes
    # print(response.status_code)
    # print(response.text)
    # Parse the response
    data = response.json()
    image_url = data["data"]["url"]
    return image_url
