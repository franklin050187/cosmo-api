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
        self._conn = None

    def connect_to_server(self) -> psycopg.Connection:
        """
        Establish and return a new connection to the PostgreSQL database.
        Uses environment variables for configuration.
        
        Returns:
            psycopg.Connection: A connection to the PostgreSQL database
            
        Raises:
            OperationalError: If connection to the database fails
        """
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg.connect(
                    host=os.getenv('POSTGRES_HOST'),
                    port=os.getenv('POSTGRES_PORT', 6543),
                    dbname=os.getenv('POSTGRES_DATABASE'),
                    user=os.getenv('POSTGRES_USER'),
                    password=os.getenv('POSTGRES_PASSWORD'),
                    sslmode="require"  # Supabase requires SSL
                )
            except OperationalError as e:
                raise OperationalError(f"Database connection failed: {e}") from e
        return self._conn

    def execute_query(self, query: str, values: tuple | None = None) -> None:
        """
        Execute a query that doesn't return results.
        
        Args:
            query (str): SQL query to execute
            values (tuple | None): Parameters for the query
        """
        with self.connect_to_server() as conn:
            with conn.cursor() as cur:
                if values is not None:
                    cur.execute(query, values)
                else:
                    cur.execute(query)
                conn.commit()
    
    def execute_query_fetchone(self, query: str, values: tuple | None = None):
        """
        Execute a query and fetch one result.
        
        Args:
            query (str): SQL query to execute
            values (tuple | None): Parameters for the query
            
        Returns:
            The first row fetched from the result.
        """
        with self.connect_to_server() as conn:
            with conn.cursor() as cur:
                if values is not None:
                    cur.execute(query, values)
                else:
                    cur.execute(query)
                result = cur.fetchone()
                conn.commit()
                return result


    def fetch_data(self, query: str, values: tuple | None = None) -> list[dict] | dict:
        """
        Execute a query and return the results as a list of dictionaries.
        
        Args:
            query (str): SQL query to execute
            values (tuple | None): Parameters for the query
            
        Returns:
            list[dict] | dict: Query results as dictionaries. Returns a single dict if only one row
        """
        with self.connect_to_server() as conn:
            with conn.cursor() as cur:
                if values is not None:
                    cur.execute(query, values)
                else:
                    cur.execute(query)
                
                if cur.description is None:
                    return []
                    
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
                
                return data[0] if len(data) == 1 else data



    def get_my_favorite(self, user: str, page: int = 1): # no pagination
        query = "SELECT * FROM shipdb WHERE id = ANY (SELECT UNNEST(favorite) FROM favoritedb WHERE name = %s) " # LIMIT %s OFFSET %s"
        data = self.fetch_data(query, (user,)) # MAX_SHIPS_PER_PAGE, offset))

        return {"data": data, "page": 1, "max_page": 1}

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
        if (user != image_data.get("submitted_by")) : #or (user not in self.modlist):
            print("error")
            return {"error": "user provided is not the owner"}
        query = "DELETE FROM shipdb WHERE id=%s"
        self.execute_query(query, (ship_id,))
        print("success")
        return {"success": "ship {ship_id} deleted"}

    def get_my_ships(self, user: str, page: int = 1): # no pagination here
        query = "SELECT * FROM shipdb WHERE submitted_by=%s"
        data = self.fetch_data(query, (user,))

        return {"data": data, "page": 1, "max_page": 1}

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

        if page == -1:
            limit = 100000 # debug max json size
            max_page = 1
        else:
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
        # print(authors)
        return authors

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

        result = self.execute_query_fetchone(insert_query, values)
        inserted_id = result[0] if result else None
        return {"success": f"{inserted_id}"}

    def update_ship(
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
            UPDATE shipdb SET 
            (name, data, submitted_by, description, ship_name, author, price, brand, crew, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::text[])
            WHERE id = %s
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

        try:
            self.execute_query(insert_query, values)
        except Exception as e:
            return {"error":e}
        return {"success": "ship updated"}
