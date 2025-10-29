"""
price analysis
"""

import base64
import json
import math

import cv2
import numpy as np

from png_upload import upload_image_to_imgbb
from part_data import parts_resources, resource_cost

# star chart
# armor, struct, corridor
# mouvement, thrusters, engine room
# shield, small and large
# weapons including point defense
# crew
# storage
# utilities, the rest like doors


cat_armor = ["cosmoteer.armor", "cosmoteer.armor_1x2_wedge", "cosmoteer.armor_1x3_wedge", "cosmoteer.armor_2x1", "cosmoteer.armor_structure_hybrid_1x1", "cosmoteer.armor_structure_hybrid_1x2", "cosmoteer.armor_structure_hybrid_1x3", "cosmoteer.armor_structure_hybrid_tri", "cosmoteer.armor_tri", "cosmoteer.armor_wedge", "cosmoteer.structure", "cosmoteer.structure_1x2_wedge", "cosmoteer.structure_1x3_wedge", "cosmoteer.structure_tri", "cosmoteer.structure_wedge"]
cat_crew = ["cosmoteer.crew_quarters_med", "cosmoteer.crew_quarters_small"]
cat_mouvement = ["cosmoteer.engine_room", "cosmoteer.thruster_boost", "cosmoteer.thruster_huge", "cosmoteer.thruster_large", "cosmoteer.thruster_med", "cosmoteer.thruster_small", "cosmoteer.thruster_small_2way", "cosmoteer.thruster_small_3way"]
cat_power = ["cosmoteer.power_storage", "cosmoteer.reactor_large", "cosmoteer.reactor_med", "cosmoteer.reactor_small"]
cat_shield = ["cosmoteer.shield_gen_large", "cosmoteer.shield_gen_small"]
cat_storage = ["cosmoteer.storage_2x2", "cosmoteer.storage_3x2", "cosmoteer.storage_3x3", "cosmoteer.storage_4x3", "cosmoteer.storage_4x4"]
cat_utility = ["cosmoteer.airlock", "cosmoteer.control_room_large", "cosmoteer.control_room_med", "cosmoteer.control_room_small", "cosmoteer.conveyor", "cosmoteer.corridor", "cosmoteer.door", "cosmoteer.explosive_charge", "cosmoteer.factory_ammo", "cosmoteer.factory_coil", "cosmoteer.factory_coil2", "cosmoteer.factory_diamond", "cosmoteer.factory_emp", "cosmoteer.factory_he", "cosmoteer.factory_mine", "cosmoteer.factory_nuke", "cosmoteer.factory_processor", "cosmoteer.factory_steel", "cosmoteer.factory_tristeel", "cosmoteer.factory_uranium", "cosmoteer.fire_extinguisher", "cosmoteer.hyperdrive_beacon", "cosmoteer.hyperdrive_small", "cosmoteer.roof_headlight", "cosmoteer.roof_light", "cosmoteer.sensor_array", "cosmoteer.tractor_beam_emitter"]
cat_weapons = ["cosmoteer.cannon_deck", "cosmoteer.cannon_large", "cosmoteer.cannon_med", "cosmoteer.disruptor", "cosmoteer.flak_cannon_large", "cosmoteer.ion_beam_emitter", "cosmoteer.ion_beam_prism", "cosmoteer.laser_blaster_large", "cosmoteer.laser_blaster_small", "cosmoteer.mining_laser_small", "cosmoteer.missile_launcher", "cosmoteer.point_defense", "cosmoteer.railgun_accelerator", "cosmoteer.railgun_launcher", "cosmoteer.railgun_loader", "he_missiles", "nukes", "mines", "emp_missiles", "cosmoteer.chaingun", "cosmoteer.chaingun_magazine", "cosmoteer.resonance_beam_turret"]

def convert_bytes_to_base64(data):
    if isinstance(data, bytes):
        return base64.b64encode(data).decode('utf-8')
    elif isinstance(data, list):
        return [convert_bytes_to_base64(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_bytes_to_base64(value) for key, value in data.items()}
    else:
        return data

def price_analysis(data_json): ## take json instead of png
    price_weapons = 0
    price_armor = 0
    price_crew = 0
    price_movement = 0
    price_power = 0
    price_shield = 0
    price_storage = 0
    price_utility = 0
    
    data = convert_bytes_to_base64(data_json)
    parts = data["Parts"]
    doors = data["Doors"]
    missile_mapping = {
            0: 'he_missiles',
            1: 'emp_missiles',
            2: 'nukes',
            3: 'mines',
            4: 'thermal_missiles'
        }
    missile_types = []
    try :
        for entry in data.get("PartUIToggleStates", []):
            key = entry.get("Key", [])
            if (
                isinstance(key, list)
                and len(key) == 2
                and isinstance(key[0], dict)
                and key[0].get("ID") == "cosmoteer.missile_launcher"
                and key[1] == "missile_type"
            ):
                missile_types.append(entry.get("Value"))
    except :
        pass
    mapped_output = [] # missile type and number
    for item in missile_types:
        if item in missile_mapping:
            mapped_output.append(missile_mapping[item])
    try:
        storage = data["NewFlexResourceGridTypes"]
    except KeyError:
        storage = None
    total_price = 0
    # calculate price for parts
    for item in parts:
        item_id = item['ID']
        resources = None
        for part in parts_resources:
            if part['ID'] == item_id:
                resources = part['Resources']
                break
        if resources:
            item_price = 0
            for resource in resources:
                resource_id = resource[0]
                resource_quantity = int(resource[1])
                for cost in resource_cost:
                    if cost['ID'] == resource_id:
                        resource_price = cost['BuyPrice']
                        item_price += resource_price * resource_quantity
                        break
            total_price += item_price
            # put price in category
            if item_id in cat_weapons:
                price_weapons += item_price
            elif item_id in cat_armor:
                price_armor += item_price
            elif item_id in cat_crew:
                price_crew += item_price
            elif item_id in cat_mouvement:
                price_movement += item_price
            elif item_id in cat_power:
                price_power += item_price
            elif item_id in cat_shield:
                price_shield += item_price
            elif item_id in cat_storage:
                price_storage += item_price
            # elif item_id in cat_utility:
            else: # put the rest in utility
                price_utility += item_price
                
                
    # calculate price for missiles
    for item in mapped_output:
        item_id = item
        resources = None
        for part in parts_resources:
            if part['ID'] == item_id:
                resources = part['Resources']
                break
        if resources:
            item_price = 0
            for resource in resources:
                resource_id = resource[0]
                resource_quantity = int(resource[1])
                for cost in resource_cost:
                    if cost['ID'] == resource_id:
                        resource_price = cost['BuyPrice']
                        item_price += resource_price * resource_quantity
                        break
            total_price += item_price
            # add to weapon price
            price_weapons += item_price
    # calculate price for doors
    door_price = 0
    if doors is not None and isinstance(doors, list):
        for door in doors:
            door_id = door['ID']
            for part in parts_resources:
                if part['ID'] == door_id:
                    resources = part['Resources']
                    break
            if resources:
                for resource in resources:
                    resource_id = resource[0]
                    resource_quantity = int(resource[1])
                    for cost in resource_cost:
                        if cost['ID'] == resource_id:
                            resource_price = cost['BuyPrice']
                            door_price += resource_price * resource_quantity
                            break
    # add door price to utility
    price_utility += door_price
    total_price += door_price
    crew_quarters_small_price = 0
    crew_quarters_med_price = 0
    crew_quarters_large_price = 0
    for item in parts:
        item_id = item['ID']
        if item_id == 'cosmoteer.crew_quarters_small':
            crew_quarters_small_price += 1000
        elif item_id == 'cosmoteer.crew_quarters_med':
            crew_quarters_med_price += 3000
        elif item_id == 'cosmoteer.crew_quarters_large':
            crew_quarters_large_price += 6000
            
    crew = 0
    for item in parts:
        item_id = item['ID']
        if item_id == 'cosmoteer.crew_quarters_small':
            crew += 2
        elif item_id == 'cosmoteer.crew_quarters_med':
            crew += 6
        elif item_id == 'cosmoteer.crew_quarters_large':
            crew += 24
    # add price to crew
    price_crew += crew_quarters_small_price + crew_quarters_med_price + crew_quarters_large_price
    total_price += crew_quarters_small_price + crew_quarters_med_price + crew_quarters_large_price
    
    # storage
    storage_price = 0
    if storage is not None:
        for item in storage:
            if 'Value' in item:
                resource_id = item['Value']
                for cost in resource_cost:
                    if cost['ID'] == resource_id:
                        resource_price = cost['BuyPrice']
                        max_stack = cost['MaxStackSize']
                        storage_price += resource_price * max_stack
    # add price to storage
    price_storage += storage_price
    total_price += storage_price
    
    # Define the categories and values
    categories = ['Shield', 'Weapon', 'Thrust', 'Misc', 'Crew', 'Power', 'Armor', 'Storage']
    values = [price_shield, price_weapons, price_movement, price_utility, price_crew, price_power, price_armor, price_storage]

    # Create a blank image
    width, height = 800, 800
    image = np.ones((height, width, 3), np.uint8) * 255  # Initialize with white background

    # Center coordinates
    center_x, center_y = width // 2, height // 2

    # Number of categories
    num_categories = len(categories)

    # Calculate the angle between each category
    angle = 360 / num_categories

    # Maximum value for scaling
    max_value = max(values)
    # max_value = sum(values)

    # Radius of the radar chart
    radius = min(center_x, center_y) - 150
    
    data_points = []

    for i in range(num_categories):
        # normalized_value = values[i] / max_value + 0.05
        normalized_value = max(values[i] / max_value, 0.05)
        x = int(center_x + radius * normalized_value * math.cos(math.radians(i * angle)))
        y = int(center_y + radius * normalized_value * math.sin(math.radians(i * angle)))

        # print(x, y)
        data_points.append((x, y))

    # Convert the image to BGR format (OpenCV uses BGR by default)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # # Draw lines between data points to create a polygon
    data_points = np.array(data_points, np.int32)
    data_points = data_points.reshape((-1, 1, 2))
    cv2.fillPoly(image, [data_points], (230, 216, 173))  # Light blue color (R, G, B)

    # Draw the polygon outline (if needed)
    cv2.polylines(image, [data_points], isClosed=True, color=(128, 128, 128), thickness=1)

    # Draw the radar chart axes
    for i in range(num_categories):
        x1 = int(center_x + radius * math.cos(math.radians(i * angle)))
        y1 = int(center_y + radius * math.sin(math.radians(i * angle)))
        cv2.line(image, (center_x, center_y), (x1, y1), (128, 128, 128), 1)
        x1 = int(center_x + radius * math.cos(math.radians(i * angle)))
        y1 = int(center_y + radius * math.sin(math.radians(i * angle)))
        x2 = int(center_x + radius * math.cos(math.radians((i + 1) * angle)))
        y2 = int(center_y + radius * math.sin(math.radians((i + 1) * angle)))
        cv2.line(image, (x1, y1), (x2, y2), (128, 128, 128), 1)

    # Draw the data points on the radar chart and add labels
    font = cv2.FONT_HERSHEY_SIMPLEX


    for i in range(num_categories):
        normalized_value = values[i] / max_value
        x = int(center_x + radius * normalized_value * math.cos(math.radians(i * angle)))
        y = int(center_y + radius * normalized_value * math.sin(math.radians(i * angle)))
        cv2.circle(image, (x, y), 5, (0, 0, 255), -1)  # Red circles for data points

        # Add labels
        label_x = int(center_x + (radius + 20) * math.cos(math.radians(i * angle)))
        label_y = int(center_y + (radius + 20) * math.sin(math.radians(i * angle)))
        label = f"{categories[i]}: {values[i]} | {round(values[i] / total_price * 100, 2)}%"
        cv2.putText(image, label, (label_x-100, label_y), font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    # Add label title in the middle top
    title = f"Price Analysis - Total cost : {total_price}"
    text_size = cv2.getTextSize(title, font, 1, 2)[0]
    title_width = text_size[0]
    cv2.putText(image, title, (center_x - title_width // 2, 50), font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    # save the file
    # cv2.imwrite('output.png', image)
    
    img_np = np.asarray(image)
    _, buffer = cv2.imencode('.png', img_np)
    base64_encoded = base64.b64encode(buffer).decode("utf-8")

    url_analysis = 'testing/error'

    # print(base64_encoded)
    url_analysis = upload_image_to_imgbb(base64_encoded)
    # print(url_analysis)
    data = {
        "url_analysis": url_analysis,
        "total_price": {"price": total_price, "percent": 1},
        "price_crew": {"price": price_crew, "percent": price_crew / total_price},
        "price_weapons": {"price": price_weapons, "percent": price_weapons / total_price},
        "price_armor": {"price": price_armor, "percent": price_armor / total_price},
        "price_mouvement": {"price": price_movement, "percent": price_movement / total_price},
        "price_power": {"price": price_power, "percent": price_power / total_price},
        "price_shield": {"price": price_shield, "percent": price_shield / total_price},
        "price_storage": {"price": price_storage, "percent": price_storage / total_price},
        "price_utility": {"price": price_utility, "percent": price_utility / total_price},
    }
    # Convert the dictionary to a JSON string
    json_data = json.dumps(data)
    return json_data
