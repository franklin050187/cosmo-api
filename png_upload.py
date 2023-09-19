import requests
import os

from dotenv import load_dotenv

load_dotenv()

def upload_image_to_imgbb(image_base64, api_try=0):
    api_key = os.getenv('imagebb_api')
    api_key2 = os.getenv('imagebb_api_backup')
    url = "https://api.imgbb.com/1/upload"
    if api_try == 0:
        # print("APITRY == 0")
    # Prepare the upload request
        payload = {
            "key": api_key,
            "image": image_base64
        }
    else :
        # print("APITRY != 0")
        payload = {
            "key": api_key2,
            "image": image_base64
        }

    try:
        # Send the upload request
        response = requests.post(url, payload)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        # print(response.status_code)
        # print(response.text)
        # Parse the response
        data = response.json()
        image_url = data["data"]["url"]

        return image_url
    except requests.exceptions.RequestException as e:
        # print("fallback : ", e)
        if api_try == 0:
            # print("except APITRY == 0")
            api_try += 1
            return upload_image_to_imgbb(image_base64, api_try)
        else:
            # print("except APITRY != 0")
            return upload_image_to_cloudinary(image_base64)

def upload_image_to_cloudinary(image_base64):
    # Set your Cloudinary credentials
    cloudinary_url = "https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
    api_key = os.getenv('cloud_api_key')
    api_secret = os.getenv('cloud_api_secret')
    cloud_name = os.getenv('cloud_name')
    upload_preset = os.getenv('upload_preset')

    # Create the payload
    payload = {
        "file": "data:image/png;base64,"+image_base64,
        "upload_preset": "xttg4crr",
        "api_key": api_key,
        "api_secret": api_secret,
    }

    # Make the POST request
    response = requests.post(cloudinary_url.format(cloud_name=cloud_name), data=payload)

    # Process the response
    if response.status_code == 200:
        json_response = response.json()
        # Extract the URL of the uploaded image
        image_url = json_response["secure_url"]
        # print("Image uploaded successfully. URL:", image_url)
        return image_url
    else:
        print("Error uploading image:", response.text)
        return "ko"

