import json
import requests
import os
import time
from dotenv import load_dotenv
from api_front import ShipImageDatabase

load_dotenv()
db_manager = ShipImageDatabase()

def get_ship_formatted_db_data():
    data = db_manager.get_search_plus(query_params="page=-1")
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
            "number_fav": item.get("fav", ""),
            "db_name": item.get("name", ""),
        }
        formatted_data.append(formatted_item)

    return formatted_data


def call_upload_gist():
    """Uploads all JSON files in one single PATCH request."""
    token = os.getenv("GIST_TOKEN")
    gist_id = os.getenv("GIST_ID")
    if not token or not gist_id:
        print("Missing GIST_TOKEN or GIST_ID, skipping upload.")
        return

    # collect all data
    ship_data = get_ship_formatted_db_data()
    author_data = get_author()
    tags_data = get_tags()
    time_data = get_timestamp()

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # prepare all files for one PATCH
    payload = {
        "description": "Cosmoteer Ship Database",
        "public": True,
        "files": {
            "cosmoteer_ships.json": {"content": json.dumps(ship_data, indent=4)},
            "cosmoteer_authors.json": {"content": json.dumps(author_data, indent=4)},
            "cosmoteer_tags.json": {"content": json.dumps(tags_data, indent=4)},
            "cosmoteer_timestamp.json": {"content": json.dumps(time_data, indent=4)},
        },
    }

    # single request for all files
    response = requests.patch(
        f"https://api.github.com/gists/{gist_id}",
        headers=headers,
        json=payload,
        timeout=10,
    )

    if response.status_code in (200, 201):
        print("✅ Successfully updated all Gist files at once.")
    else:
        print(f"❌ Failed to update Gist: {response.status_code} - {response.text}")


def get_author():
    authors_list = db_manager.get_authors()
    author_names = [author["author"] for author in authors_list]
    return {"authors": author_names}


def get_tags():
    tags_list = db_manager.get_tags()
    tag_names = [tag["tag"] for tag in tags_list]
    return {"tags": tag_names}


def get_timestamp():
    return {"last_updated": int(time.time())}


# testing
# print("author_data", get_author())
# print("tags_data", get_tags())
# print("time_data", get_timestamp())
# print("ship_data", get_ship_formatted_db_data())
# import time
# timestart = time.time()
# print("call_upload_gist", call_upload_gist())
# print("time", time.time() - timestart)