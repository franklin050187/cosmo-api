# from tagextractor import PNGTagExtractor
from center_of_mass import calculate_price
from cosmoteer_save_tools_new import Ship as new_ship
from tagextractor import PNGTagExtractor
from center_of_mass import com
from price_analysis_ocv import price_analysis
import json


url = "https://i.ibb.co/zVQJQKv5/0f6df16b5e93.png" # new update ship
# url = "https://i.ibb.co/Swn33zPz/fecf46a8ce7e.png" # old ship

data_ship = new_ship(image_path="newup.ship.png").data
data = data_ship

# test extractor
mapped_output, author = PNGTagExtractor().extract_tags(data_json=data_ship)
print(mapped_output, author)

# test pricegen
price, crew = calculate_price(data_ship)
print(price, crew)

# test price ocv (upload)
# ocv = price_analysis(data_ship)
# print(ocv)

# test com
result = com(url, "testoutput.png", {})
print(result)

