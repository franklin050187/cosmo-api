
import json
import requests
import os
from dotenv import load_dotenv
from api_front import ShipImageDatabase
import time

load_dotenv()
db_manager = ShipImageDatabase()

def get_ship_formatted_db_data():
    data = db_manager.get_search_plus(query_params="page=-1")
    raw_items = data["data"]
    items = raw_items if isinstance(raw_items, list) else [raw_items]

    formatted_data = []
    for item in items:
        formatted_item = {
            "ship_id": item.get("id", 0), #
            "ship_name": item.get("ship_name", ""), #
            "ship_png": item.get("data", ""), #
            "ship_author": item.get("author", ""), #
            "ship_description": item.get("description", ""), #
            "ship_cost": item.get("price", 0), #
            "ship_crew": item.get("crew", 0), #
            "ship_popularity": item.get("downloads", 0), #
            "ship_date_submitted": str(item.get("date", "")), #
            "ship_submitted_by": item.get("submitted_by", ""), #
            "ship_tags": item.get("tags", []), #
            "brand": item.get("brand", ""), #
            "number_fav": item.get("fav", ""), #
            "db_name": item.get("name", ""), #

        }
        formatted_data.append(formatted_item)
    # add "last_updated": epoch to json
    # formatted_data.append({"last_updated": int(time.time())})

    return formatted_data

def call_upload_gist(): # tis is the call
    ship_data = get_ship_formatted_db_data()
    author_data = get_author()
    tags_data = get_tags()
    time_data = get_timestamp()
    try : 
        upload_to_gist(ship_data, "cosmoteer_ships.json")
        upload_to_gist(author_data, "cosmoteer_authors.json")
        upload_to_gist(tags_data, "cosmoteer_tags.json")
        # print(time_data)
        upload_to_gist(time_data, "cosmoteer_timestamp.json")
    except Exception as e:
        print(e)

def upload_to_gist(data, gist_file):
    """
    Uploads data to a GitHub Gist.
    """
    # Replace with your GitHub API token
    token = os.getenv("GIST_TOKEN")
    if not token:
        print("GIST_TOKEN not found, skipping gist upload.")
        return

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "description": "Cosmoteer Ship Database",
        "public": True,
        "files": {
            f"{gist_file}": {
                "content": json.dumps(data, indent=4)
            }
        }
    }
    # get the gist id from the environment variables
    gist_id = os.getenv("GIST_ID")
    if gist_id:
        response = requests.patch(f"https://api.github.com/gists/{gist_id}", headers=headers, json=payload)
    else:
        response = requests.post("https://api.github.com/gists", headers=headers, json=payload)

    if response.status_code == 200 or response.status_code == 201:
        print("Successfully created/updated Gist.")
    else:
        print(f"Failed to create/update Gist {gist_file}: {response.content}")

def get_author():
    authors_list = db_manager.get_authors() # TODO
    author_names = [author["author"] for author in authors_list]
    return {"authors": author_names}

def get_tags():
    tags_list = db_manager.get_tags() # TODO
    tag_names = [tag["tag"] for tag in tags_list]
    return {"tags": tag_names}

def get_timestamp():
    return {"last_updated": int(time.time())}

# testing
# print("author_data", get_author())
# print("tags_data", get_tags())
# print("time_data", get_timestamp())
# print("ship_data", get_ship_formatted_db_data())

# print("call_upload_gist", call_upload_gist())