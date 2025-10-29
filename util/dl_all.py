# # dl all png from a list
# import os
# import requests
# from api_front import ShipImageDatabase

# db_manager = ShipImageDatabase()
# data = db_manager.get_all_url()

# # Create png folder if it doesn't exist
# os.makedirs("png", exist_ok=True)

# for item in data:
#     try:
#         url = item['data']  # Get the URL from the 'data' key
#         # Get the filename from the URL
#         filename = url.split("/")[-1]
#         filepath = os.path.join("png", filename)
        
#         # Download the file
#         response = requests.get(url)
#         response.raise_for_status()  # Raise an exception for bad status codes
        
#         # Save the file
#         with open(filepath, "wb") as f:
#             f.write(response.content)
            
#         print(f"Downloaded: {filename}")
#     except Exception as e:
#         print(f"Error downloading {url}: {str(e)}")
    