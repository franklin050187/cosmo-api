"""
upload image to imgbb
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()


def upload_image_to_imgbb(image_base64):
    """
    Uploads an image to ImgBB using the provided base64 image data.

    Parameters:
        image_base64 (str): The base64 encoded image data to be uploaded.

    Returns:
        str: The URL of the uploaded image.
    """
    api_key = os.getenv("imagebb_api")
    url = "https://api.imgbb.com/1/upload"
    payload = {"key": api_key, "image": image_base64}
    # Send the upload request
    headers = {"content-encoding": "gzip"}
    response = requests.post(url, payload, headers=headers, timeout=8)
    response.raise_for_status()  # Raise an exception for non-2xx status codes
    # print(response.status_code)
    # print(response.text)
    # Parse the response
    data = response.json()
    image_url = data["data"]["url"]
    return image_url


def upload_image_to_cloudinary(image_base64):
    """
    Uploads an image to Cloudinary using the provided base64 image data.

    Args:
        image_base64 (str): The base64 encoded image data to be uploaded.

    Returns:
        str: The URL of the uploaded image.

    Raises:
        requests.exceptions.RequestException: If the request to Cloudinary fails.

    """
    # Set your Cloudinary credentials
    cloudinary_url = "https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
    api_key = os.getenv("cloud_api_key")
    api_secret = os.getenv("cloud_api_secret")
    cloud_name = os.getenv("cloud_name")
    # upload_preset = os.getenv('upload_preset') # hardcoded

    # Create the payload
    payload = {
        "file": "data:image/png;base64," + image_base64,
        "upload_preset": "xttg4crr",
        "api_key": api_key,
        "api_secret": api_secret,
    }

    # Make the POST request
    response = requests.post(cloudinary_url.format(cloud_name=cloud_name), data=payload, timeout=8)

    # Process the response
    if response.status_code == 200:
        json_response = response.json()
        # Extract the URL of the uploaded image
        image_url = json_response["secure_url"]
        # print("Image uploaded successfully. URL:", image_url)
        return image_url
    print("Error uploading image:", response.text)
    return "ko"
