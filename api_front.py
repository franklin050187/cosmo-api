import psycopg
from psycopg import OperationalError
import os

from urllib.parse import unquote_plus
from dotenv import load_dotenv

load_dotenv()

MAX_SHIPS_PER_PAGE = 24


class ShipImageDatabase:
    """
    Handles connection to the ship image PostgreSQL database.
    """

    def __init__(self):
        pass  # Delay connection until needed

    def connect_to_server(self):
        """
        Establish and return a new connection to the PostgreSQL database.
        Uses environment variables for configuration.
        """
        try:
            conn = psycopg.connect(
                dbname=os.getenv("POSTGRES_DATABASE"),
                host=os.getenv("POSTGRES_HOST"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                port=int(os.getenv("POSTGRES_PORT", 6543)),
            )
            return conn
        except OperationalError as e:
            print(f"Database connection failed: {e}")
            raise

    def execute_query(self, query, values=None):
        conn = self.connect_to_server()
        cursor = conn.cursor()
        if values is not None:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        conn.commit()
        cursor.close()
        conn.close()

    def fetch_data(self, query, values=None):
        conn = self.connect_to_server()
        cursor = conn.cursor()
        if values is not None:
            cursor.execute(query, values)
        else:
            cursor.execute(query)
        # Get column names from cursor description
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        # Fetch all rows and convert to dictionaries
        rows = cursor.fetchall()
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        cursor.close()
        conn.close()
        return data[0] if len(data) == 1 else data



    def get_my_favorite(self, user: str, page: int = 1):
        count_query = "SELECT COUNT(*) FROM shipdb WHERE id = ANY (SELECT UNNEST(favorite) FROM favoritedb WHERE name = %s)"
        total_count_result = self.fetch_data(count_query, (user,))
        total_count = total_count_result.get("count", 0)  # Extract the count value
        max_page = (total_count + MAX_SHIPS_PER_PAGE - 1) // MAX_SHIPS_PER_PAGE

        # Ensure the page is within the valid range
        if page > max_page:
            page = max_page
        elif page < 1:
            page = 1

        offset = (page - 1) * MAX_SHIPS_PER_PAGE
        query = "SELECT * FROM shipdb WHERE id = ANY (SELECT UNNEST(favorite) FROM favoritedb WHERE name = %s) LIMIT %s OFFSET %s"
        data = self.fetch_data(query, (user, MAX_SHIPS_PER_PAGE, offset))

        return {"data": data, "page": page, "max_page": max_page}

    def update_downloads(self, ship_id: int):
        query = "UPDATE shipdb SET downloads = downloads + 1 WHERE id = %s"
        self.execute_query(query, (ship_id,))

    def add_fav(self, ship_id: int):
        query = "UPDATE shipdb SET fav = fav + 1 WHERE id = %s"
        self.execute_query(query, (ship_id,))

    def remove_fav(self, ship_id: int):
        query = "UPDATE shipdb SET fav = fav - 1 WHERE id = %s"
        self.execute_query(query, (ship_id,))

    def get_image_data(self, ship_id: int):
        query = "SELECT * FROM shipdb WHERE id=%s"
        return self.fetch_data(query, (ship_id,))

    # def get_all_url(self):
    #     query = "SELECT data FROM shipdb"
    #     return self.fetch_data(query)

    def add_to_favorites(self, user: str, ship_id: int):
        query = "SELECT * FROM favoritedb WHERE name = %s"
        result = self.fetch_data(query, (user,))
        if not result:
            query = "INSERT INTO favoritedb (name, favorite) VALUES (%s, ARRAY[%s])"
            self.execute_query(query, (user, ship_id))
        else:
            favorites = result.get("favorite")
            if ship_id not in favorites:
                favorites.append(ship_id)
                query = "UPDATE favoritedb SET favorite = favorite || ARRAY[%s] WHERE name = %s"
                self.execute_query(query, (ship_id, user))
                self.add_fav(ship_id=ship_id)
            else:
                print("Already in favorites, skipping update")
                return {"warning": "ship already in favorite of user"}

    def delete_from_favorites(self, user: str, ship_id: int):
        query = "SELECT * FROM favoritedb WHERE name = %s"
        result = self.fetch_data(query, (user,))
        if result:
            favorites = result.get("favorite")
            if ship_id in favorites:
                favorites.remove(ship_id)
                if not favorites:
                    query = "DELETE FROM favoritedb WHERE name = %s"
                    self.execute_query(query, (user,))
                    self.remove_fav(ship_id=ship_id)
                else:
                    query = "UPDATE favoritedb SET favorite = %s WHERE name = %s"
                    self.execute_query(query, (favorites, user))
                    self.remove_fav(ship_id=ship_id)
            else:
                return {"warning": "ship not in favorite of user"}  # ship is not in favorite user
        else:
            return {"warning": "ship not in favorite of user*"}  # user has not favorite

    def delete_ship(self, ship_id: int, user: str):
        query = "SELECT submitted_by FROM shipdb WHERE id=%s"
        image_data = self.fetch_data(query, (ship_id,))
        if (user != image_data.get("submitted_by")) or (user not in self.modlist):
            return {"error": "user provided is not the owner"}
        query = "DELETE FROM shipdb WHERE id=%s"
        self.execute_query(query, (ship_id,))
        return {"success": "ship {ship_id} deleted"}

    def get_my_ships(self, user: str, page: int = 1):
        count_query = "SELECT COUNT(*) FROM shipdb WHERE submitted_by=%s"
        total_count_result = self.fetch_data(count_query, (user,))
        total_count = total_count_result.get("count", 0)  # Extract the count value
        max_page = (total_count + MAX_SHIPS_PER_PAGE - 1) // MAX_SHIPS_PER_PAGE

        # Ensure the page is within the valid range
        if page > max_page:
            page = max_page
        elif page < 1:
            page = 1

        offset = (page - 1) * MAX_SHIPS_PER_PAGE
        query = "SELECT * FROM shipdb WHERE submitted_by=%s LIMIT %s OFFSET %s"
        data = self.fetch_data(query, (user, MAX_SHIPS_PER_PAGE, offset))

        return {"data": data, "page": page, "max_page": max_page}

    def get_search_plus(self, query_params):
        query_params = str(query_params)
        params = {}
        conditions = []
        sql_args = []
        page = 1

        if query_params:
            for param in query_params.split("&"):
                if "=" not in param:
                    continue
                key, value = param.split("=", 1)
                value = unquote_plus(value)

                if key == "page":
                    page = int(value)
                elif key in (
                    "author",
                    "desc",
                    "minprice",
                    "maxprice",
                    "max-crew",
                    "order",
                    "fulltext",
                    "brand",
                ):
                    params[key] = value
                elif value == "1":
                    params.setdefault("conditions", []).append(key)
                elif value == "0":
                    params.setdefault("not_conditions", []).append(key)

        # Tags conditions
        if "conditions" in params:
            placeholders = ",".join(["%s"] * len(params["conditions"]))
            conditions.append(f"tags @> ARRAY[{placeholders}]")
            sql_args.extend(params["conditions"])
        if "not_conditions" in params:
            placeholders = ",".join(["%s"] * len(params["not_conditions"]))
            conditions.append(f"NOT tags @> ARRAY[{placeholders}]")
            sql_args.extend(params["not_conditions"])

        # Price range
        if "minprice" in params:
            conditions.append("price >= %s")
            sql_args.append(params["minprice"])
        if "maxprice" in params:
            conditions.append("price <= %s")
            sql_args.append(params["maxprice"])

        # Author
        if "author" in params:
            conditions.append("author ILIKE %s")
            sql_args.append(f"%{params['author']}%")

        # Description / ship name
        if "desc" in params:
            conditions.append("(description ILIKE %s OR ship_name ILIKE %s)")
            sql_args.extend([f"%{params['desc']}%", f"%{params['desc']}%"])

        # Max crew
        if "max-crew" in params:
            conditions.append("crew <= %s")
            sql_args.append(params["max-crew"])

        # Brand
        if params.get("brand") == "exl":
            conditions.append("brand = %s")
            sql_args.append("exl")

        # Fulltext search
        if "fulltext" in params:
            conditions.append("EXISTS (SELECT 1 FROM unnest(tags) AS tag WHERE tag LIKE %s)")
            sql_args.append(f"{params['fulltext']}%")

        # Get total count for pagination
        count_query = "SELECT COUNT(*) FROM shipdb"
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)
        total_count_result = self.fetch_data(count_query, sql_args)
        total_count = total_count_result.get("count", 0)
        max_page = (total_count + MAX_SHIPS_PER_PAGE - 1) // MAX_SHIPS_PER_PAGE

        # Final SQL composition
        base_query = "SELECT * FROM shipdb"
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        # Order by
        if params.get("order") == "fav":
            base_query += " ORDER BY fav DESC"
        elif params.get("order") == "pop":
            base_query += " ORDER BY downloads DESC"
        else:
            base_query += " ORDER BY date DESC"

        # Pagination
        limit = MAX_SHIPS_PER_PAGE
        offset = (page - 1) * limit
        base_query += f" LIMIT {limit} OFFSET {offset}"

        # Get the data
        data = self.fetch_data(base_query, sql_args)

        # Return data with pagination info
        return {"data": data, "page": page, "max_page": max_page}

    def get_authors(self):  # TODO
        """
        Retrieves a list of distinct authors from the ship database.

        :return: A dictionary containing the list of authors.
        """
        query = "SELECT DISTINCT author FROM shipdb;"
        authors = self.fetch_data(query)
        print(authors)
        return {"authors": authors}

    # get all unique tags from the ship database
    def get_tags(self):  # TODO
        """
        Retrieves a list of distinct tags from the ship database.

        Returns:
            dict: A dictionary containing the list of tags. The keys are 'tags'
            and the values are a list of strings.
        """
        # tags are tags TEXT[]
        query = "SELECT DISTINCT unnest(tags) AS tag FROM shipdb;"
        tagsdict = self.fetch_data(query)
        # print(tagsdict)
        return tagsdict

    # def post_edit_ship(self, ship_id, form_data, user): # TODO (update)
    #     """
    #     Updates a ship in the database.

    #     Args:
    #         id (int): The ID of the ship to be updated.
    #         form_data (dict): The data containing the updated information for the ship.
    #         user (str): The username of the user performing the update.

    #     Returns:
    #         None

    #     Raises:
    #         None.

    #     """
    #     query = "SELECT * FROM shipdb WHERE id=%s"
    #     image_data = self.fetch_data(query, (ship_id,))
    #     # print("image_data = ", image_data)
    #     # print("post_edit_ship_form_data = ",form_data)
    #     if user != image_data[0][3] and user not in self.modlist:
    #         return "ko"

    #     # print("form_data = ", form_data)

    #     tup_for = []
    #     if 'thrust_type' in form_data:
    #         tup_for.append(form_data['thrust_type'])
    #     if 'defense_type' in form_data:
    #         tup_for.append(form_data['defense_type'])
    #     for key, value in form_data.items():
    #         if value == 'on':
    #             tup_for.append(key)
    #     # generate ship tags
    #     url_png = image_data[0][2]
    #     # extractor = PNGTagExtractor()
    #     # tags = extractor.extract_tags(url_png)
    #     data_ship = extract_tags_v2(url_png) # FIXME
    #     tags = data_ship[0]

    #     # add tup for to tags

    #     print("tags = ",tags) # tags are good here
    #     if tags :
    #         tup_for.extend(tags)
    #     # prepare data
    #     image_data = {
    #         'description': form_data.get('description', ''),
    #         'ship_name': form_data.get('ship_name', ''),
    #         'author': form_data.get('author', ''),
    #         'submitted_by': form_data.get('submitted_by', ''),
    #         'price': int(form_data.get('price', 0)),
    #         'brand': form_data.get('brand', ''),
    #         'tags' : tup_for,
    #         'id' : ship_id
    #     }
    #     print("tup_for = ", tup_for)
    #     # prepare query
    #     insert_query = """
    #         UPDATE shipdb SET
    #         description = %s,
    #         ship_name = %s,
    #         author = %s,
    #         price = %s,
    #         submitted_by = %s,
    #         brand = %s,
    #         tags = %s::text[]
    #         WHERE id = %s
    #     """

    #     # prepare values
    #     values = (
    #         image_data['description'],
    #         image_data['ship_name'],
    #         image_data['author'],
    #         image_data['price'],
    #         image_data['submitted_by'],
    #         image_data['brand'],
    #         image_data['tags'],
    #         image_data['id'],
    #     )

    #     self.execute_query(insert_query, values)
    #     return None

    def insert_ship(
        self,
        name: str,
        data: str,
        submitted_by: str,
        description: str,
        ship_name: str,
        author: str,
        price: int,
        brand: str,
        crew: int,
        tags: list[str],
    ) -> dict:
        insert_query = """
            INSERT INTO shipdb
            (name, data, submitted_by, description, ship_name, author, price, brand, crew, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::text[])
            RETURNING id
        """

        values = (
            name,
            data,
            submitted_by,
            description,
            ship_name,
            author,
            price,
            brand,
            crew,
            tags,
        )

        inserted_id = self.execute_query(insert_query, values)
        return {"success": f"Ship added to the library with ID {inserted_id}"}

        # link = "https://cosmo-lilac.vercel.app/ship/"+str(insertedid)
        # call webhook # FIXME
        # send_message(link, image_data['name'], image_data['description'],
        #              image_data['data'], image_data['price'], image_data['submitted_by'],
        #              image_data['author'])
        # self.insert_json(image_data['data'], insertedid, image_data['name']) # insert json in db

    # def upload_update(self, data):
    #     """
    # 	Updates the ship information in the database based on the provided data.

    #     Parameters:
    #     - self: the object itself
    #     - data: a dictionary containing the ship information including
    #     'id', 'url_png', 'price', 'crew', and 'tags'

    #     Returns:
    #     - None
    # 	"""

    #     url_png = data.get('url_png')
    #     tags = data.get('tags', [])

    #     image_data = {
    #         'data': url_png,  # change to store URL of the image instead of the base64 image
    #         'price': data.get('price', 0),
    #         'crew': int(data.get('crew', 0)),
    #         'tags': tags,  # Use getlist() to get all values of 'tags' as a list
    #     }

    #     insert_query = """
    #         UPDATE shipdb
    #         SET
    #         data = %s,
    #         price = %s,
    #         crew = %s,
    #         tags = %s::text[]
    #         WHERE id = %s
    #     """

    #     values = (
    #         image_data['data'],
    #         image_data['price'],
    #         image_data['crew'],
    #         image_data['tags'],
    #         data['id']
    #     )

    #     self.execute_query(insert_query, values)
